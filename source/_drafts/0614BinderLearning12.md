---
title: Binder学习笔记（十二）—— binder_transaction(...)都干了什么？
categories: Android
tags:   binder
toc: true
comments: true
layout: post
---
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
        // thread未被操作过，骨transaction_stack为0
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
    // 首先，从用户态获取所传输的数据，以及数据里的binder对象偏移信息
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
            // 这里得到的是个BnTestService::getWeakRefs()
            // 这到底是个啥？为什么几乎当做指针用？
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