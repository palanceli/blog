---
title: Binder学习笔记（十二）—— binder_transaction(...)都干了什么？
date:   2016-06-14 00:20:23 +0800
categories: Android
tags:   binder
toc: true
comments: true
layout: post
---
# binder_open(...)都干了什么？
在回答binder_transaction(...)之前，还有一些技术设施要去探究，比如binder_open(...)，binder_mmap(...)，这些调用是在打开设备文件/dev/binder之后必须完成的程式化操作，而在它们内部需要做一些数据结构的准备。首先来看binder_open(...)
kernel/drivers/staging/android/binder.c:2979
``` c++
static int binder_open(struct inode *nodp, struct file *filp)
{
    struct binder_proc *proc;
    ......
    proc = kzalloc(sizeof(*proc), GFP_KERNEL); // 创建binder_proc结构体
    ......
    get_task_struct(current);
    proc->tsk = current;
    INIT_LIST_HEAD(&proc->todo);  // 初始化链表头
    init_waitqueue_head(&proc->wait);   
    proc->default_priority = task_nice(current);

    ......
    // 将proc_node串入全局链表binder_procs中
    hlist_add_head(&proc->proc_node, &binder_procs); 
    proc->pid = current->group_leader->pid;
    INIT_LIST_HEAD(&proc->delivered_death);
    filp->private_data = proc;

    ......
    return 0;
}
```
结构体binder_proc描述一个“正在使用Binder进程间通信机制”的进程，它的定义参见kernel/goldfish/drivers/staging/android/binder.c:286
``` c++
struct binder_proc {
    struct hlist_node proc_node;
    struct rb_root threads;
    struct rb_root nodes;
    struct rb_root refs_by_desc;
    struct rb_root refs_by_node;
    int pid;
    struct vm_area_struct *vma;
    struct mm_struct *vma_vm_mm;
    struct task_struct *tsk;
    struct files_struct *files;
    struct hlist_node deferred_work_node;
    int deferred_work;
    void *buffer;
    ptrdiff_t user_buffer_offset;

    struct list_head buffers;
    struct rb_root free_buffers;
    struct rb_root allocated_buffers;
    size_t free_async_space;

    struct page **pages;
    size_t buffer_size;
    uint32_t buffer_free;
    struct list_head todo;
    wait_queue_head_t wait;
    struct binder_stats stats;
    struct list_head delivered_death;
    int max_threads;
    int requested_threads;
    int requested_threads_started;
    int ready_threads;
    long default_priority;
    struct dentry *debugfs_entry;
};
```
在其内部有若干个list_head类型的字段，用来把binder_proc串到不同的链表中去。一般写链表的做法是在链表节点结构体中追加业务逻辑字段，顺着链表的prev、next指针到达指定节点，然后再访问业务逻辑字段：
![一般的链表做法](img01.png)
在Linux代码中则常常反过来，先定义业务逻辑的结构体，在其内部嵌入链表字段list_head，顺着该字段遍历链表，在每个节点上根据该字段与所在结构体的偏移量找到所在结构体，访问业务逻辑字段：
![Linux中常用的链表做法](img02.png)
这样做的好处是让业务逻辑和链表逻辑分离，Linux还定义了宏用于操作链表，以及根据链表字段找到所在结构体。如binder_proc结构体内部盛放多个list_head，表示把该结构体串入了不同的链表。
具体技巧可参见《Linux内核设计与实现》第6章。

回到binder_open(...)，除了直接字段赋值，需要解释的是几个链表字段的处理。
`INIT_LIST_HEAD(&proc->todo)`用于将todo的next、prev指针指向自己，该宏的定义在kernel/goldfish/include/linux/lish.t:24
``` c++
static inline void INIT_LIST_HEAD(struct list_head *list)
{
    list->next = list;
    list->prev = list;
}
```

`init_waitqueue_head(...)`这个宏定义在kernel/goldfish/include/linux/wait.h:81
``` c++
#define init_waitqueue_head(q)              \
    do {                        \
        static struct lock_class_key __key; \
                            \
        __init_waitqueue_head((q), #q, &__key); \
    } while (0)
```
`__init_waitqueue_head(...)`定义在kernel/goldfish/kernel/wait.c:13，主要完成了对task_list字段的初始化：
``` c++
void __init_waitqueue_head(wait_queue_head_t *q, const char *name, struct lock_class_key *key)
{
    spin_lock_init(&q->lock);
    lockdep_set_class_and_name(&q->lock, key, name);
    INIT_LIST_HEAD(&q->task_list);
}
```

`hlist_add_head(&proc->proc_node, &binder_procs)`将proc->proc_node节点串到全局链表binder_procs的头部，其定义在kernel/goldfish/include/linux/list.h:610
``` c++
static inline void hlist_add_head(struct hlist_node *n, struct hlist_head *h)
{
    struct hlist_node *first = h->first;
    n->next = first;
    if (first)
        first->pprev = &n->next;
    h->first = n;
    n->pprev = &h->first;
}
```
综上所述，binder_open(...)组织的数据结构proc为：
![binder_open(...)组织的proc数据结构图](img03.png)
# binder_mmap(...)都干了什么？
接下来就是binder_mmap(...)，当进程打开/dev/binder之后，必须调用mmap(...)函数把该文件映射到进程的地址空间。
kernel/goldfish/drivers/staging/android/binder.c:2883
``` c++
static int binder_mmap(struct file *filp, struct vm_area_struct *vma)
{
    int ret;
    struct vm_struct *area; // area描述内核地址空间；vma描述用户地址空间
    struct binder_proc *proc = filp->private_data;
    const char *failure_string;
    struct binder_buffer *buffer;

    ......
    vma->vm_flags = (vma->vm_flags | VM_DONTCOPY) & ~VM_MAYWRITE;

    ......
    // 在内核地址空间分配
    area = get_vm_area(vma->vm_end - vma->vm_start, VM_IOREMAP);
    ......
    proc->buffer = area->addr;
    proc->user_buffer_offset = vma->vm_start - (uintptr_t)proc->buffer;
    mutex_unlock(&binder_mmap_lock);
......
    // 创建物理页面结构体指针数组
    proc->pages = kzalloc(sizeof(proc->pages[0]) * ((vma->vm_end - vma->vm_start) / PAGE_SIZE), GFP_KERNEL);
    ......
    proc->buffer_size = vma->vm_end - vma->vm_start;

    vma->vm_ops = &binder_vm_ops;
    vma->vm_private_data = proc;

    if (binder_update_page_range(proc, 1, proc->buffer, proc->buffer + PAGE_SIZE, vma)) {
        ret = -ENOMEM;
        failure_string = "alloc small buf";
        goto err_alloc_small_buf_failed;
    }
    buffer = proc->buffer;
    INIT_LIST_HEAD(&proc->buffers);
    list_add(&buffer->entry, &proc->buffers); // 把entry串到buffers链表中
    buffer->free = 1;
    binder_insert_free_buffer(proc, buffer);
    proc->free_async_space = proc->buffer_size / 2;
    barrier();
    proc->files = get_files_struct(proc->tsk);
    proc->vma = vma;
    proc->vma_vm_mm = vma->vm_mm;

    /*printk(KERN_INFO "binder_mmap: %d %lx-%lx maps %p\n",
         proc->pid, vma->vm_start, vma->vm_end, proc->buffer);*/
    return 0;

err_alloc_small_buf_failed:
    kfree(proc->pages);
    proc->pages = NULL;
err_alloc_pages_failed:
    mutex_lock(&binder_mmap_lock);
    vfree(proc->buffer);
    proc->buffer = NULL;
err_get_vm_area_failed:
err_already_mapped:
    mutex_unlock(&binder_mmap_lock);
err_bad_arg:
    printk(KERN_ERR "binder_mmap: %d %lx-%lx %s failed %d\n",
           proc->pid, vma->vm_start, vma->vm_end, failure_string, ret);
    return ret;
}
```
`get_vm_area(...)`

# 从服务端addService触发的`binder_transaction(...)`
从native层的调用过程参见[binder学习笔记（十）—— 穿越到驱动层](http://palanceli.github.io/blog/2016/05/28/2016/0528BinderLearning10/)。
传入的`binder_transaction_data`输入参数为：![addService组织的请求数据](http://palanceli.github.io/blog/2016/05/11/2016/0514BinderLearning6/img02.png)

kernel/goldfish/drivers/staging/android/binder.c:1402
``` c
static void binder_transaction(struct binder_proc *proc,
                   struct binder_thread *thread,
                   struct binder_transaction_data *tr, int reply)
{   // reply=(cmd==BC_REPLY)即false，flags=TF_ACCEPT_FDS
    struct binder_transaction *t;
    struct binder_work *tcomplete;
    size_t *offp, *off_end;
    struct binder_proc *target_proc;
    struct binder_thread *target_thread = NULL;
    struct binder_node *target_node = NULL;
    struct list_head *target_list;
    wait_queue_head_t *target_wait;
    struct binder_transaction *in_reply_to = NULL;
    struct binder_transaction_log_entry *e;
    uint32_t return_error;

    ......

    if (reply) {
        ......
    } else {
        if (tr->target.handle) {  // tr->target.handle=0
            ......
        } else {
            target_node = binder_context_mgr_node; // service manager对应的节点
            ......
        }
        ......
        target_proc = target_node->proc; // 得到目标进程的binder_proc
        ......
        // 得到目标线程tr->flags=TF_ACCEPT_FDS
        // thread未被操作过，故transaction_stack为0
        if (!(tr->flags & TF_ONE_WAY) && thread->transaction_stack) {
            struct binder_transaction *tmp;
            tmp = thread->transaction_stack;
            if (tmp->to_thread != thread) {
                binder_user_error("binder: %d:%d got new "
                    "transaction with bad transaction stack"
                    ", transaction %d has target %d:%d\n",
                    proc->pid, thread->pid, tmp->debug_id,
                    tmp->to_proc ? tmp->to_proc->pid : 0,
                    tmp->to_thread ?
                    tmp->to_thread->pid : 0);
                return_error = BR_FAILED_REPLY;
                goto err_bad_call_stack;
            }
            while (tmp) {
                if (tmp->from && tmp->from->proc == target_proc)
                    target_thread = tmp->from;
                tmp = tmp->from_parent;
            }
        }
    }
    if (target_thread) {
        e->to_thread = target_thread->pid;
        target_list = &target_thread->todo;
        target_wait = &target_thread->wait;
    } else { // 走这里
        target_list = &target_proc->todo;
        target_wait = &target_proc->wait;
    }
    ......
    t = kzalloc(sizeof(*t), GFP_KERNEL);  // 创建binder_transaction节点
    ......

    tcomplete = kzalloc(sizeof(*tcomplete), GFP_KERNEL);//创建一个binder_work节点
    ......
    // 这里岂不是为真？thread来自binder_ioctl(...)中的binder_get_thread(proc)
    // 返回proc的当前线程
    if (!reply && !(tr->flags & TF_ONE_WAY)) 
        t->from = thread;
    else
        t->from = NULL;
    t->sender_euid = proc->tsk->cred->euid; // 源线程用户id
    t->to_proc = target_proc;               // 负责处理该事务的进程，sm
    t->to_thread = target_thread;           // 负责处理该事务的线程
    t->code = tr->code;                     // ADD_SERVICE_TRANSACTION
    t->flags = tr->flags;                   // TF_ACCEPT_FDS
    t->priority = task_nice(current);       // 源线程优先级

    trace_binder_transaction(reply, t, target_node);

    t->buffer = binder_alloc_buf(target_proc, tr->data_size,
        tr->offsets_size, !reply && (t->flags & TF_ONE_WAY));
    ......
    t->buffer->allow_user_free = 0;// Service处理完该事务后，驱动不会释放该内核缓冲区
    t->buffer->debug_id = t->debug_id;
    t->buffer->transaction = t; // 缓冲区正交给哪个事务使用
    t->buffer->target_node = target_node;   // 缓冲区正交给哪个Binder实体对象使用
    trace_binder_transaction_alloc_buf(t->buffer);
    if (target_node)
        binder_inc_node(target_node, 1, 0, NULL);
    // 分析所传数据中的所有binder对象，如果是binder实体，在红黑树中添加相应的节点。
    // 首先，从用户态获取所传输的数据，以及数据里的binder对象偏移信息。
    offp = (size_t *)(t->buffer->data + ALIGN(tr->data_size, sizeof(void *)));
    // 将服务端传来的Parcel的数据部分拷贝到内核空间
    if (copy_from_user(t->buffer->data, tr->data.ptr.buffer, tr->data_size)) {
        ......
    }
    // 将服务端传来的Parcel的偏移数组拷贝到内核空间
    if (copy_from_user(offp, tr->data.ptr.offsets, tr->offsets_size)) {
        ......
    }
    ......
    off_end = (void *)offp + tr->offsets_size;
    // 遍历每个flat_binder_object信息，创建必要的红黑树节点
    for (; offp < off_end; offp++) {
        struct flat_binder_object *fp;
        ......
        fp = (struct flat_binder_object *)(t->buffer->data + *offp);
        switch (fp->type) {
        case BINDER_TYPE_BINDER:
        case BINDER_TYPE_WEAK_BINDER: { // 如果是binder实体
            struct binder_ref *ref;
            // fp->binder是BnTestService::getWeakRefs()
            // 是BnTestService的影子对象
            struct binder_node *node = binder_get_node(proc, fp->binder);
            if (node == NULL) { // 如果没有则创建新的binder_node节点
                node = binder_new_node(proc, fp->binder, fp->cookie);
                ......
                node->min_priority = fp->flags & FLAT_BINDER_FLAG_PRIORITY_MASK;
                node->accept_fds = !!(fp->flags & FLAT_BINDER_FLAG_ACCEPTS_FDS);
            }
            ......
            // 必要时，会在目标进程的binder_proc中创建对应的binder_ref红黑树节点
            ref = binder_get_ref_for_node(target_proc, node);
            ......
            if (fp->type == BINDER_TYPE_BINDER)
                fp->type = BINDER_TYPE_HANDLE;
            else
                fp->type = BINDER_TYPE_WEAK_HANDLE;
            // 修改所传数据中的flat_binder_object信息，因为远端的binder实体到
            // 了目标端就变为binder代理了，所以要记录下binder句柄了。
            fp->handle = ref->desc;
            binder_inc_ref(ref, fp->type == BINDER_TYPE_HANDLE,
                       &thread->todo);

            trace_binder_transaction_node_to_ref(t, node, ref);
            ......
        } break;
        case BINDER_TYPE_HANDLE:
        case BINDER_TYPE_WEAK_HANDLE: { 
            // 对flat_binder_object做必要的修改，比如将BINDER_TYPE_HANDLE改为
            // BINDER_TYPE_BINDER
            struct binder_ref *ref = binder_get_ref(proc, fp->handle);
            ......
            if (ref->node->proc == target_proc) {
                if (fp->type == BINDER_TYPE_HANDLE)
                    fp->type = BINDER_TYPE_BINDER;
                else
                    fp->type = BINDER_TYPE_WEAK_BINDER;
                fp->binder = ref->node->ptr;
                fp->cookie = ref->node->cookie;
                binder_inc_node(ref->node, fp->type == BINDER_TYPE_BINDER, 0, NULL);
                trace_binder_transaction_ref_to_node(t, ref);
                binder_debug(BINDER_DEBUG_TRANSACTION,
                         "        ref %d desc %d -> node %d u%p\n",
                         ref->debug_id, ref->desc, ref->node->debug_id,
                         ref->node->ptr);
            } else {
                struct binder_ref *new_ref;
                new_ref = binder_get_ref_for_node(target_proc, ref->node);
                if (new_ref == NULL) {
                    return_error = BR_FAILED_REPLY;
                    goto err_binder_get_ref_for_node_failed;
                }
                fp->handle = new_ref->desc;
                binder_inc_ref(new_ref, fp->type == BINDER_TYPE_HANDLE, NULL);
                trace_binder_transaction_ref_to_ref(t, ref,
                                    new_ref);
                binder_debug(BINDER_DEBUG_TRANSACTION,
                         "        ref %d desc %d -> ref %d desc %d (node %d)\n",
                         ref->debug_id, ref->desc, new_ref->debug_id,
                         new_ref->desc, ref->node->debug_id);
            }
        } break;

        case BINDER_TYPE_FD: {
            int target_fd;
            struct file *file;

            if (reply) {
                if (!(in_reply_to->flags & TF_ACCEPT_FDS)) {
                    binder_user_error("binder: %d:%d got reply with fd, %ld, but target does not allow fds\n",
                        proc->pid, thread->pid, fp->handle);
                    return_error = BR_FAILED_REPLY;
                    goto err_fd_not_allowed;
                }
            } else if (!target_node->accept_fds) {
                binder_user_error("binder: %d:%d got transaction with fd, %ld, but target does not allow fds\n",
                    proc->pid, thread->pid, fp->handle);
                return_error = BR_FAILED_REPLY;
                goto err_fd_not_allowed;
            }

            file = fget(fp->handle);
            if (file == NULL) {
                binder_user_error("binder: %d:%d got transaction with invalid fd, %ld\n",
                    proc->pid, thread->pid, fp->handle);
                return_error = BR_FAILED_REPLY;
                goto err_fget_failed;
            }
            if (security_binder_transfer_file(proc->tsk, target_proc->tsk, file) < 0) {
                fput(file);
                return_error = BR_FAILED_REPLY;
                goto err_get_unused_fd_failed;
            }
            target_fd = task_get_unused_fd_flags(target_proc, O_CLOEXEC);
            if (target_fd < 0) {
                fput(file);
                return_error = BR_FAILED_REPLY;
                goto err_get_unused_fd_failed;
            }
            task_fd_install(target_proc, target_fd, file);
            trace_binder_transaction_fd(t, fp->handle, target_fd);
            binder_debug(BINDER_DEBUG_TRANSACTION,
                     "        fd %ld -> %d\n", fp->handle, target_fd);
            /* TODO: fput? */
            fp->handle = target_fd;
        } break;

        default:
            binder_user_error("binder: %d:%d got transactio"
                "n with invalid object type, %lx\n",
                proc->pid, thread->pid, fp->type);
            return_error = BR_FAILED_REPLY;
            goto err_bad_object_type;
        }
    }
    if (reply) {
        ......
    } else if (!(t->flags & TF_ONE_WAY)) {
        BUG_ON(t->buffer->async_transaction != 0);
        t->need_reply = 1;
        t->from_parent = thread->transaction_stack;
        thread->transaction_stack = t;
    } else {
        ......
        if (target_node->has_async_transaction) {
            target_list = &target_node->async_todo;
            target_wait = NULL;
        } else
            target_node->has_async_transaction = 1;
    }
    t->work.type = BINDER_WORK_TRANSACTION;
    // 把binder_transaction节点插入target_list（及目标todo队列）
    list_add_tail(&t->work.entry, target_list);
    tcomplete->type = BINDER_WORK_TRANSACTION_COMPLETE;
    list_add_tail(&tcomplete->entry, &thread->todo);
    if (target_wait) // 传输动作完毕，现在可以唤醒系统中其它相关线程，wake up!
        wake_up_interruptible(target_wait);
    return;

err_get_unused_fd_failed:
err_fget_failed:
err_fd_not_allowed:
err_binder_get_ref_for_node_failed:
err_binder_get_ref_failed:
err_binder_new_node_failed:
err_bad_object_type:
err_bad_offset:
err_copy_data_failed:
    trace_binder_transaction_failed_buffer_release(t->buffer);
    binder_transaction_buffer_release(target_proc, t->buffer, offp);
    t->buffer->transaction = NULL;
    binder_free_buf(target_proc, t->buffer);
err_binder_alloc_buf_failed:
    kfree(tcomplete);
    binder_stats_deleted(BINDER_STAT_TRANSACTION_COMPLETE);
err_alloc_tcomplete_failed:
    kfree(t);
    binder_stats_deleted(BINDER_STAT_TRANSACTION);
err_alloc_t_failed:
err_bad_call_stack:
err_empty_call_stack:
err_dead_binder:
err_invalid_target_handle:
err_no_context_mgr_node:
    binder_debug(BINDER_DEBUG_FAILED_TRANSACTION,
             "binder: %d:%d transaction failed %d, size %zd-%zd\n",
             proc->pid, thread->pid, return_error,
             tr->data_size, tr->offsets_size);

    {
        struct binder_transaction_log_entry *fe;
        fe = binder_transaction_log_add(&binder_transaction_log_failed);
        *fe = *e;
    }

    BUG_ON(thread->return_error != BR_OK);
    if (in_reply_to) {
        thread->return_error = BR_TRANSACTION_COMPLETE;
        binder_send_failed_reply(in_reply_to, return_error);
    } else
        thread->return_error = return_error;
}
```