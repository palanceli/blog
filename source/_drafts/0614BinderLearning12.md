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
在回答binder_transaction(...)之前，还有一些基础设施要去探究，比如binder_open(...)，binder_mmap(...)，这些调用是在打开设备文件/dev/binder之后必须完成的程式化操作，而在它们内部需要做一些数据结构的准备。首先来看binder_open(...)
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
binder_open(...)生成并初始化binder_proc结构体如下：
![binder_open(...)初始化的binder_proc结构体](img04.png)

## struct binder_proc
struct binder_proc描述一个“正在使用Binder进程间通信机制”的进程，它的定义参见kernel/goldfish/drivers/staging/android/binder.c:286
``` c++
struct binder_proc {
    // 进程打开设备文件/dev/binder时，Binder驱动会为它创建一个binder_proc结构体，并将它
    // 保存在全局hash列表中，proc_node是该hash列表的节点。
    struct hlist_node proc_node;

    // 每个使用了Binder机制的进程都有一个Binder线程池，用来处理进程间通信请求。threads以
    // 线程ID作为key来组织进程的Binder线程池。进程可以调用ioctl将线程注册到Binder驱动中
    // 当没有足够的空闲线程处理进程间通信请求时，驱动可以要求进程注册更多的线程到Binder线程
    // 池中
    struct rb_root threads; 

    struct rb_root nodes;           // 组织Binder实体对象，它以成员ptr作为key
    struct rb_root refs_by_desc;    // 组织Binder引用对象，它以成员desc作为key
    struct rb_root refs_by_node;    // 组织Binder引用对象，它以成员node作为key
    int pid;                        // 指向进程组ID
    struct vm_area_struct *vma;     // 内核缓冲区的用户空间地址，供应用程序使用
    struct mm_struct *vma_vm_mm;
    struct task_struct *tsk;        // 指向进程任务控制块
    struct files_struct *files;     // 指向进程打开文件结构体数组

    // 一个hash表，保存进程可以延迟执行的工作项，这些延迟工作有三种类型
    // BINDER_DEFERRED_PUT_FILES、BINDER_DEFERRED_FLUSH、BINDER_DEFERRED_RELEASE
    // 驱动为进程分配内核缓冲区时，会为该缓冲区创建一个文件描述符，进程可以通过该描述符将该内
    // 核缓冲区映射到自己的地址空间。当进程不再需要使用Binder机制时，就会通知驱动关闭该文件
    // 描述符并释放之前所分配的内核缓冲区。由于这不是一个马上就要完成的操作，因此驱动会创建一
    // 个BINDER_DEFERRED_PUT_FILES类型的工作来延迟执行；
    // Binder线程池中的空闲Binder线程是睡眠在一个等待队列中的，进程可以通过调用函数flush
    // 来唤醒这些线程，以便它们可以检查进程是否有新的工作项需要处理。此时驱动会创建一个
    // BINDER_DEFERRED_FLUSH类型的工作项，以便延迟执行唤醒空闲Binder线程的操作；
    // 当进程不再使用Binder机制时，会调用函数close关闭文件/dev/binder，此时驱动会释放之
    // 前为它分配的资源，由于资源释放是个比较耗时的操作，驱动会创建一个
    // BINDER_DEFERRED_RELEASE类型的事务来延迟执行
    struct hlist_node deferred_work_node;

    int deferred_work;              // 描述该延迟工作项的具体类型
    void *buffer;                   // 内核缓冲区的内核空间地址，供驱动程序使用
    ptrdiff_t user_buffer_offset;   // vma和buffer之间的差值

    // buffer指向一块大的内核缓冲区，驱动程序为方便管理，将它划分成若干小块，这些小块的内核缓
    // 冲区用binder_buffer描述保存在列表中，按地址从小到大排列。buffers指向该列表的头部。
    struct list_head buffers; 

    struct rb_root free_buffers;      // buffers中的小块有的正在使用，被保存在此红黑树
    struct rb_root allocated_buffers;   // buffers中的空闲小块被保存在此红黑树
    size_t free_async_space;            // 当前可用的保存异步事务数据的内核缓冲区的大小

    struct page **pages;    // buffer和vma都是虚拟地址，它们对应的物理页面保存在pages
                            // 中，这是一个数组，每个元素指向一个物理页面
    size_t buffer_size;     // 进程调用mmap将它映射到进程地址空间，实际上是请求驱动为它
                            // 分配一块内核缓冲区，缓冲区大小保存在该成员中
    uint32_t buffer_free;   // 空闲内核缓冲区的大小
    struct list_head todo;  // 当进程接收到一个进程间通信请求时，Binder驱动就将该请求封
                            // 装成一个工作项，并且加入到进程的待处理工作向队列中，该队列
                            // 使用成员变量todo来描述。
    wait_queue_head_t wait; // 线程池中空闲Binder线程会睡眠在由该成员所描述的等待队列中
                            // 当宿主进程的待处理工作项队列增加新工作项后，驱动会唤醒这
                            // 些线程，以便处理新的工作项
    struct binder_stats stats;  // 用来统计进程数据

    // 当进程所引用的Service组件死亡时，驱动会向该进程发送一个死亡通知。这个正在发出的通知被
    // 封装成一个类型为BINDER_WORK_DEAD_BINDER或BINDER_WORK_DEAD_BINDER_AND_CLEAR
    // 的工作项，并保存在由该成员描述的队列中删除
    struct list_head delivered_death;  

    int max_threads;        // 驱动程序最多可以主动请求进程注册的线程数
    int requested_threads;
    int requested_threads_started;
    int ready_threads;      // 进程当前的空闲Binder线程数
    long default_priority;  // 进程的优先级，当线程处理一个工作项时，线程优先级可能被
                            // 设置为宿主进程的优先级
    struct dentry *debugfs_entry;
};
```
## binder_proc中的链表
在binder_proc内部有若干个list_head类型的字段，用来把binder_proc串到不同的链表中去。一般写链表的做法是在链表节点结构体中追加业务逻辑字段，顺着链表的prev、next指针到达指定节点，然后再访问业务逻辑字段：
![一般的链表做法](img01.png)
在Linux代码中则常常反过来，先定义业务逻辑的结构体，在其内部嵌入链表字段list_head，顺着该字段遍历链表，在每个节点上根据该字段与所在结构体的偏移量找到所在结构体，访问业务逻辑字段：
![Linux中常用的链表做法](img02.png)
这样做的好处是让业务逻辑和链表逻辑分离，Linux还定义了宏用于操作链表，以及根据链表字段找到所在结构体。如binder_proc结构体内部盛放多个list_head，表示把该结构体串入了不同的链表。
具体技巧可参见《Linux内核设计与实现》第6章。

## INIT_LIST_HEAD(&proc->todo)
回到binder_open(...)，除了直接字段赋值，需要解释的是几个链表字段的处理。
`INIT_LIST_HEAD(&proc->todo)`用于将todo的next、prev指针指向自己，该宏的定义在kernel/goldfish/include/linux/lish.t:24
``` c++
static inline void INIT_LIST_HEAD(struct list_head *list)
{
    list->next = list;
    list->prev = list;
}
```

## init_waitqueue_head(&proc->wait)
`init_waitqueue_head(&proc->wait)`这个宏定义在kernel/goldfish/include/linux/wait.h:81
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
// q=(&proc->todo)
{
    spin_lock_init(&q->lock);
    lockdep_set_class_and_name(&q->lock, key, name);
    INIT_LIST_HEAD(&q->task_list);  // 为什么使用符号->来提领task_list呢？
}
```
说到底还是初始化proc->wait->task_list字段。不过有点奇怪task_list是wait内的结构体，而不是结构体指针，为什么对task_list的提领使用符号`->`呢？
``` c
struct binder_proc {
    ......
    wait_queue_head_t wait;
    ......
};
```
kernel/goldfish/include/linux/wait.h:53
``` c 
struct __wait_queue_head {
    spinlock_t lock;
    struct list_head task_list;
};
typedef struct __wait_queue_head wait_queue_head_t;
```
## hlist_add_head(&proc->proc_node, &binder_procs)
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
kernel/goldfish/include/linux/types.h:233
``` c
struct hlist_head {
    struct hlist_node *first;
};

struct hlist_node {
    struct hlist_node *next, **pprev;
};
```
![将n插入到h](img05.png)

![插入后的结果](img06.png)
综上所述，binder_open(...)组织的数据结构proc为：
![binder_open(...)组织的proc数据结构图](img04.png)

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

    // 分配物理页面，并将之同时映射到用户和内核地址空间
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
到第28行调用binder_update_page_range(...)之前，binder_mmap(...)在内核地址空间申请了`struct vm_struct area`，并完成部分成员的初始化，如下：
![到28行为止binder_mmap(...)构造的数据结构](img07.png)

## binder_update_page_range(...)做了什么
kernel/goldfish/drivers/staging/android/binder.c:627
``` c
static int binder_update_page_range(struct binder_proc *proc, int allocate,
                    void *start, void *end,
                    struct vm_area_struct *vma)
{
    void *page_addr;
    unsigned long user_page_addr;
    struct vm_struct tmp_area;
    struct page **page;
    struct mm_struct *mm;

    ... ...

    if (vma)
        mm = NULL;
    else
        mm = get_task_mm(proc->tsk);

    if (mm) {
        down_write(&mm->mmap_sem);
        vma = proc->vma;
        ... ...
    }

    if (allocate == 0) 
        goto free_range;    // 执行释放逻辑

    ... ...

    // 遍历所有页面
    for (page_addr = start; page_addr < end; page_addr += PAGE_SIZE) {
        int ret;
        struct page **page_array_ptr;
        page = &proc->pages[(page_addr - proc->buffer) / PAGE_SIZE];

        BUG_ON(*page);
        *page = alloc_page(GFP_KERNEL | __GFP_HIGHMEM | __GFP_ZERO);
        ... ...
        // 映射内核地址空间
        tmp_area.addr = page_addr;
        tmp_area.size = PAGE_SIZE + PAGE_SIZE /* guard page? */;
        page_array_ptr = page;
        ret = map_vm_area(&tmp_area, PAGE_KERNEL, &page_array_ptr);
        ... ...

        // 映射用户地址空间
        user_page_addr =
            (uintptr_t)page_addr + proc->user_buffer_offset;
        ret = vm_insert_page(vma, user_page_addr, page[0]);
        ... ...
    }
    if (mm) {
        up_write(&mm->mmap_sem);
        mmput(mm);
    }
    return 0;

free_range:
    for (page_addr = end - PAGE_SIZE; page_addr >= start;
         page_addr -= PAGE_SIZE) {
        page = &proc->pages[(page_addr - proc->buffer) / PAGE_SIZE];
        // 解除物理页面在用户地址空间和内核地址空间的映射
        if (vma)
            zap_page_range(vma, (uintptr_t)page_addr +
                proc->user_buffer_offset, PAGE_SIZE, NULL);
err_vm_insert_page_failed:
        unmap_kernel_range((unsigned long)page_addr, PAGE_SIZE);
err_map_kernel_failed:
        __free_page(*page);     // 释放物理页面
        *page = NULL;
err_alloc_page_failed:
        ;
    }
err_no_vma:
    if (mm) {
        up_write(&mm->mmap_sem);
        mmput(mm);
    }
    return -ENOMEM;
}
```

## struct binder_buffer
之后在binder_mmap(...)第34行，buffer的类型是`struct binder_buffer*`，该结构体用来描述一个内核缓冲区，该缓冲区用于在进程间传输数据。
kernel/goldfish/drivers/staging/android/binder.c:263
``` c
struct binder_buffer {
    // 每一个使用Binder机制的进程在Binder驱动中都有一个内核缓冲区列表，用来保存Binder驱动
    // 程序为它分配的内核缓冲区，entry是该列表的一个节点
    struct list_head entry; /* free and allocated entries by address */ 

    // 进程使用两个红黑树分别保存使用中以及空闲的内核缓冲区。如果空闲，free=1，
    //rb_node就是空闲内核缓冲区红黑树中的节点，否则是使用中内核缓冲区红黑树中的节点
    struct rb_node rb_node; /* free entry by size or allocated entry */ 
                         /* by address */                       

    unsigned free:1;
    // Service处理完成该事务后，若发现allow_user_free为1，会请求驱动程序释放该内核缓冲区
    unsigned allow_user_free:1;         
    unsigned async_transaction:1;           // 与该内核缓冲区关联的是一个异步事务
    unsigned debug_id:29;

    struct binder_transaction *transaction; // 内核缓冲区正交给哪个事务使用
    struct binder_node *target_node;        // 内核缓冲区正交给哪个Binder实体对象使用
    size_t data_size;
    size_t offsets_size;

    // 保存通信数据，分两种类型：普通数据、Binder对象。驱动程序不关心普通数据，但必须知道里面
    // 的Binder对象，因为要根据它们来维护内核中Binder实体对象和Binder引用对象的生命周期。
    uint8_t data[0];                        
};
```

## list_add(&buffer->entry, &proc->buffers)
初始化完proc->buffers之后，第36行执行一个list_add(...)，该函数定义见kernel/goldfish/include/linux/list.h:37~60
``` c
static inline void __list_add(struct list_head *new,
                  struct list_head *prev,
                  struct list_head *next)
{
    next->prev = new;
    new->next = next;
    new->prev = prev;
    prev->next = new;
}
... ...
static inline void list_add(struct list_head *new, struct list_head *head)
{
    __list_add(new, head, head->next);
}
```
运算过程如下图：
![list_add操作过程](img08.png)
于是到`binder_mmap(...)`第37行为止，binder_mmap(...)构造的数据结构如下：
![到37行为止binder_mmap(...)构造的数据结构](img09.png)

## 函数binder_insert_free_buffer(...)
kernel/goldfish/drivers/statging/android/binder.c:545
``` c
static void binder_insert_free_buffer(struct binder_proc *proc,
                      struct binder_buffer *new_buffer)
{   // new_buffer就是之前分配的buffer，被转型成了binder_buffer
    struct rb_node **p = &proc->free_buffers.rb_node;
    struct rb_node *parent = NULL;
    struct binder_buffer *buffer;
    size_t buffer_size;
    size_t new_buffer_size;
    ... ...
    // 计算binder_buffer中data部分的大小
    new_buffer_size = binder_buffer_size(proc, new_buffer);

    ... ...
    // 根据new_buffer的大小，找到在proc->free_buffers红黑树中的正确位置，并插入
    while (*p) {
        parent = *p;
        buffer = rb_entry(parent, struct binder_buffer, rb_node);
        BUG_ON(!buffer->free);

        buffer_size = binder_buffer_size(proc, buffer);

        if (new_buffer_size < buffer_size)
            p = &parent->rb_left;
        else
            p = &parent->rb_right;
    }
    rb_link_node(&new_buffer->rb_node, parent, p);
    rb_insert_color(&new_buffer->rb_node, &proc->free_buffers);
}
```

于是到binder_mmap(...)结束，这个binder_proc结构体就被做成了这样：
![binder_mmap(...)调用完成后够早的binder_proc结构体](img10.png)

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