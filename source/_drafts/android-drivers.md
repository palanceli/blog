---
title: android drivers
tags:
toc: true
---
# module_init和device_initcall宏
kernel/goldfish/include/linux/init.h:267
``` c
    #define module_init(x)  __initcall(x);
```
kernel/goldfish/include/linux/init.h:213
``` c
    #define __initcall(fn) device_initcall(fn)
```
kernel/goldfish/include/linux/init.h:208
``` c
    #define device_initcall(fn)     __define_initcall("6",fn,6)
```
kernel/goldfish/include/linux/init.h:178
``` c
#define __define_initcall(level,fn,id) \
    static initcall_t __initcall_##fn##id __used \
    __attribute__((__section__(".initcall" level ".init"))) = fn
```
于是展开`device_initcall(binder_init)`为
`__define_initcall("6", binder_init, 6)`，
再展开为
``` c
static initcall_t __initcall_binder_init6 __used 
    __attribute__((__section__(".initcall6.init")) = binder_init
```
# 编译驱动drivers-freg
## 完成代码编写
代码放在[这里](https://github.com/palanceli/androidex)，其中的drivers-freg即是，它是从《Android系统源代码情景分析》第2章抄过来的，完成了一个简单的字符设备驱动。
## 配置Kconfig和Makefile
1 找到kernel/goldfish/drivers/Kconfig，在末尾追加`source "drivers/freg/Kconfig"`
2 在kernel/goldfish/drivers/Makefile末尾追加`obj-$(CONFIG_FREG) += freg/`
## 配置menuconfig
在kernel/goldfish下执行`make menuconfig`配置drivers-freg的编译方式。
``` bash
[*] Enable loadable module support  --->
    --- Enable loadable module support
        [*]   Forced module loading
        [*]   Module unloading
        [*]     Forced module unloading
        [ ]   Module versioning support
        [ ]   Source checksum for all modules
......
Device Drivers  --->
    ......
    <M> Fake Register Driver
```
主要是把`Enable loadable module support`设为Y，这样内核就支持动态加载模块。然后到`Device Drivers`下找到`Fake Register Driver`并设为M，这样该模块就是个动态加载模块了。

## 编译android内核
``` bash
$ cd kernel/goldfish
$ export ARCH=arm
$ export SUBARCH=arm
$ export CROSS_COMPILE=arm-eabi-
$ export PATH=WORKING_DIRECTORY/prebuilts/gcc/darwin-x86/arm/arm-eabi-4.8/bin:$PATH
$ make goldfish_armv7_defconfig
$ make -j4
```
完成后在kernel/goldfish/drivers/freg下就会生成freg.ko文件

# 查看freg.ko文件
在`android-6.0.1_r11/prebuilts/gcc/darwin-x86/arm/arm-eabi-4.8/bin/`下有好多好东西，
``` bash
$ android-6.0.1_r11/prebuilts/gcc/darwin-x86/arm/arm-eabi-4.8/bin/arm-eabi-readelf -a /Volumes/android-6.0.1_r11g/androidex/drivers-freg/freg.ko
```
显示ko文件的全部elf信息。
<font color="red">我预期应该能看到`.initcall6.init`段才对的，不知道为什么看不到？</font>

# binder驱动的入口binder_init()
kernel/goldfish/drivers/staging/android/binder.c:3678
``` c
static int __init binder_init(void)
{
    int ret;

    binder_deferred_workqueue = create_singlethread_workqueue("binder");
    if (!binder_deferred_workqueue)
        return -ENOMEM;

    binder_debugfs_dir_entry_root = debugfs_create_dir("binder", NULL);
    if (binder_debugfs_dir_entry_root)
        binder_debugfs_dir_entry_proc = debugfs_create_dir("proc",
                         binder_debugfs_dir_entry_root);
    ret = misc_register(&binder_miscdev);
    if (binder_debugfs_dir_entry_root) {
        debugfs_create_file("state",
                    S_IRUGO,
                    binder_debugfs_dir_entry_root,
                    NULL,
                    &binder_state_fops);
        debugfs_create_file("stats",
                    S_IRUGO,
                    binder_debugfs_dir_entry_root,
                    NULL,
                    &binder_stats_fops);
        debugfs_create_file("transactions",
                    S_IRUGO,
                    binder_debugfs_dir_entry_root,
                    NULL,
                    &binder_transactions_fops);
        debugfs_create_file("transaction_log",
                    S_IRUGO,
                    binder_debugfs_dir_entry_root,
                    &binder_transaction_log,
                    &binder_transaction_log_fops);
        debugfs_create_file("failed_transaction_log",
                    S_IRUGO,
                    binder_debugfs_dir_entry_root,
                    &binder_transaction_log_failed,
                    &binder_transaction_log_fops);
    }
    return ret;
}
```
第一行就被卡住了`create_singlethread_workqueue`是什么？
>[Linux workqueue工作原理](http://blog.csdn.net/myarrow/article/details/8090504)

# 从服务端addService触发的`binder_transaction(...)`
从native层的调用过程同[binder学习笔记（十）—— 穿越到驱动层](http://palanceli.github.io/blog/2016/05/28/2016/0528BinderLearning10/)。
传入的`binder_transaction_data`输入参见：![addService组织的请求数据](http://palanceli.github.io/blog/2016/05/11/2016/0514BinderLearning6/img02.png)

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
# 智能指针
Binder的学习历程爬到驱动的半山腰明显感觉越来越陡峭，停下业务层的学习，补补基础层知识吧，这首当其冲的就是智能指针了，智能指针的影子在Android源码中随处可见。打开frameworkds/rs/cpp/util，RefBase.h和StrongPointer.h两个文件，代码多读几遍都能读懂，可是串起来总感觉摸不到骨架，把不住主线。闭上眼零零星星的点串不成一条线。究其原因应该是此处使用了模式，最好先剔除掉业务层的皮肉，把模式的骨架摸个门清，再回来看代码就会势如破竹了。

不是多么高深的设计模式，智能指针和引用计数的混合而已。但，不要轻敌。翻开书，对这两个模式的描述竟有50页之多。我读的是Scott Meyers的《More Effective C++》，侯sir翻译的版本，十年前读这本书的时候囫囵吞枣很多读不懂，有一些概念依稀留下点印象。这些印象就构成了日后遇到问题时的路标，告诉我答案在哪里。这本书条款28、29讲的正是智能指针和引用计数，两章结尾处的代码几乎就是Android源码中LightRefBase和sp的原型。每一个条款都从一个简单的目标入手，不断地解决问题，再升级提出它的不足，再找答案，直到把这个问题打穿打透为止。这两个条款的内容就不赘述了，书里写的更精彩。接下来我把模式和Android源码的智能指针对接起来。

《More Effective C++》第203页，条款29描绘了具有引用计数功能的智能指针模式图如下：
![《More Effective C++》条款29](img02.png)
这张图还是把业务逻辑和模式框架混在一起了：
* String代表业务逻辑
* RCPtr是具备引用计数功能的智能指针
* RCObject用来履行引用计数的职责
* StringValue和HeapMemory又是局部的业务逻辑了

所以该模式本质上是由RCPtr和RCObject联袂完成，RCPtr负责智能指针，RCObject负责引用计数，如下：
![具备引用计数功能得智能指针](img03.png)
一个对象如果要配备引用计数和智能指针，则需要：
``` c++
class MyClass : public RCObject // 让该对象的类从RCObject派生
{...};
RCPtr<MyClass> pObj; // 声明对象
```
对应到Android源码中，LightRefBase就是RCObject，sp就是RCPtr：
![Android源码中的轻量级智能指针](img04.png)

我在初读Android源码的时候一直琢磨为什么搞得这么复杂，不能把智能指针封装在一个基类里。如果可以的话，MyClass只需要从这个类派生就好了。答案是不可以。因为RCPtr本质上要充当指针的角色，ptr1可以指向A，也可以指向B，当从A转向了B，应该让A的引用计数递减，让B的引用计数递增，这个计数只能是被指对象的属性，而不能是指针的。

我之所以会有合二为一的年头，是因为过去接触的智能指针大都是为了解决遇到Exception或错误返回时防止内存或资源泄露，又不想使用goto语句，比如：
``` c++
int fun(char * filename)
{
    FILE* fp = fopen(filename, "r");
    int result = 0
    ... ...
    if(error){
        result = -1;
        goto exit;
    }
exit:
    fclose(fp);
    return result;
}
```
如果在函数中打开了多种资源，则要么记住它们的状态，在exit中根据状态擦屁股；要么就得有多个goto标记。此时就可以使用智能指针的思想，给文件做个封装：
``` c++
void fun(char * filename)
{
    MyFile file;  // MyFile在析构的时候会自动关闭文件
    if(!file.open(filename, "r"))
        return -1;
    ... ...
}
```
这一类的智能指针可以看做“具备引用计数的智能指针”的特例，它的引用计数最多为1，且不存在所有权的转移，可以把引用计数RCObject模块退化掉，指针指向资源即代表引用计数为1，不指向任何资源则代表引用计数为0。因此这种情况可以让MyClass仅派生自RCPtr基类即可，一旦引用计数允许大于1，就必须带上RCObject的角色了。

回到Android源码上来，轻量级的智能指针：
* LightRefBase负责维护引用计数，并提供递增/递减的接口。
* sp履行智能指针的角色，负责构造析构、拷贝和赋值、提领。

还有一个问题：LightRefBase和《More Effective C++》条款29中的RCObject相比多出一个模板参数，在该类的定义中几乎没有用到这个模板参数，这是为什么？我分析应该是出于性能的考虑——这样做可以省去虚表的开销：
``` c++
RCObject::removeReference()
{if(--refCount == 0) delete this;}
```
这里要经由基类的指针删除派生类的对象，在《Effecive C++（第三版）》（刚刚发现这本书的第二版和第三版调整很大！）第7条中说到:
> 当派生类的对象经由基类指针被删除时，基类必须有虚析构函数，否则会导致未定义的行为，通常是对象的devrived成分没被销毁。

RCObject确实声明了析构函数为virtual，也因此不得不引入虚表。再看LightRefBase：
``` c++
template <class T>
class LightRefBase
{
... ...
    inline void decStrong(const Void* id) const{
        if(android_atomic_dec(&mCount) == 1){
            // 这里并没有delete this，而是先转成子类再delete，这就不再是
            // “经由基类指针删除子类对象”，而是“由子类指针删除子类对象”了，
            // 怎么得到子类指针？模板参数T呀！为这段代码拍案叫绝！
            delete static_cast<const T*>(this);
        }
    }
};
```