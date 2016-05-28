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

# 先不要恋战，因为不会的东西太多，以后慢慢补，单刀直入我的问题。
问题是什么？客户端为test()组织的请求数据是：
![](http://palanceli.github.io/blog/2016/05/14/2016/0514BinderLearning8/img01.png)驱动程序是如何处理这个数据包的？
为此，还需要先从应用层往下看，frameworks/native/libs/binder/IPCThreadState.cpp:548
来看客户端组织test()请求数据时，调用到IPCThreadState::transact(...)
``` c
status_t IPCThreadState::transact(int32_t handle,
                                  uint32_t code, const Parcel& data,
                                  Parcel* reply, uint32_t flags)
{   // code=TEST, flag=0

    flags |= TF_ACCEPT_FDS;
    ......
    
        err = writeTransactionData(BC_TRANSACTION, flags, handle, code, data, NULL);
    
        ......
        if (reply) {
            err = waitForResponse(reply);  // 这次重点看这里
        } else {
            Parcel fakeReply;
            err = waitForResponse(&fakeReply);
        }
        ......
    
    return err;
}
```
函数前面使用writeTransactionData(...)打包好数据后，接下来调用waitForResponse(...)把数据发出去。
frameworks/native/libs/binder/IPCThreadState.cpp:712
``` c
status_t IPCThreadState::waitForResponse(Parcel *reply, status_t *acquireResult)
{
    uint32_t cmd;
    int32_t err;

    while (1) {
        if ((err=talkWithDriver()) < NO_ERROR) break;
        ......
        }
        ......
    
    return err;
}
```
继续调用talkWithDriver()和驱动对话,frameworks/native/libs/binder/IPCThreadState.cpp:803
``` c
status_t IPCThreadState::talkWithDriver(bool doReceive)
{   // doReceive=true
    ......
    binder_write_read bwr;
    ......
    const bool needRead = mIn.dataPosition() >= mIn.dataSize();// mIn有上一轮IO中读出尚未解析的数据，因此needRead=true
    ......
    const size_t outAvail = (!doReceive || needRead) ? mOut.dataSize() : 0; // outAvail=mOut.dataSize()
    
    bwr.write_size = outAvail;
    bwr.write_buffer = (uintptr_t)mOut.data();
    ......
    if (doReceive && needRead) {
        bwr.read_size = mIn.dataCapacity();
        bwr.read_buffer = (uintptr_t)mIn.data();
    } else {
        bwr.read_size = 0;
        bwr.read_buffer = 0;
    }
    ......
    bwr.write_consumed = 0;
    bwr.read_consumed = 0;
    status_t err;
    do {
        ......
        if (ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &bwr) >= 0) // 重点在这
            err = NO_ERROR;
        else
            err = -errno;
        ......
    } while (err == -EINTR);
    ......
    if (err >= NO_ERROR) {
        if (bwr.write_consumed > 0) {
            if (bwr.write_consumed < mOut.dataSize())
                mOut.remove(0, bwr.write_consumed);
            else
                mOut.setDataSize(0);
        }
        if (bwr.read_consumed > 0) {
            mIn.setDataSize(bwr.read_consumed);
            mIn.setDataPosition(0);
        }
        ......
        return NO_ERROR;
    }
    
    return err;
}
```
doReceive取默认值为true，前文中刚刚往mOut内组织完要发送的数据，此时还没有发出去，也没有读取应答数据，因此mIn应该没有内容，所以needRead=false，outAvail=0。
## 组织一个gdb确认mIn此时的内容：
需要开启三个终端完成调试：
1. Target1 在模拟器上启动server
``` bash
$ adb shell /data/local/tmp/testservice/TestServer
```
2. Target2 在模拟器上通过gdbserver启动客户端
``` bash
$ adb shell gdbserver :1234 /data/local/tmp/testservice/TestClient
Process /data/local/tmp/testservice/TestClient created; pid = 1254
Listening on port 1234
Remote debugging from host 127.0.0.1
```
3. Host1 在宿主端启动gdb
``` bash
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient
......
(gdb) b main
Breakpoint 1 at 0xb6f571fc: file external/testservice/TestClient.cpp, line 14.
(gdb) c
Continuing.
......
(gdb) set solib-absolute-prefix out/debug/target/product/generic/symbols/
Reading symbols from ...... linker...done.
......
Loaded symbols for ......
......
(gdb) b IPCThreadState.cpp:846 # 在talkWithDriver(...)内下断点
Breakpoint 2 at 0xb6eaf884: file frameworks/native/libs/binder/IPCThreadState.cpp, line 846.
(gdb) c
......
# 然后就是若干轮的continue和backtrace，直到停在由test()调用触发的talkWithDriver(...)
......

Breakpoint 2, android::IPCThreadState::talkWithDriver (this=this@entry=0xb6c24000, doReceive=doReceive@entry=true) at frameworks/native/libs/binder/IPCThreadState.cpp:846
846     if ((bwr.write_size == 0) && (bwr.read_size == 0)) return NO_ERROR;
(gdb) bt
#0  android::IPCThreadState::talkWithDriver (this=this@entry=0xb6c24000, doReceive=doReceive@entry=true) at frameworks/native/libs/binder/IPCThreadState.cpp:846
#1  0xb6eafed2 in android::IPCThreadState::waitForResponse (this=0xb6c24000, reply=0xbeaa1ad4, acquireResult=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:718
#2  0xb6eb0088 in android::IPCThreadState::transact (this=0xb6c24000, handle=1, code=code@entry=1, data=..., reply=reply@entry=0xbeaa1ad4, flags=16, flags@entry=0) at frameworks/native/libs/binder/IPCThreadState.cpp:604
#3  0xb6eab08e in android::BpBinder::transact (this=0xb6c090c0, code=1, data=..., reply=0xbeaa1ad4, flags=0) at frameworks/native/libs/binder/BpBinder.cpp:165
#4  0xb6f3e42e in android::BpTestService::test (this=<optimized out>) at external/testservice/TestClient.cpp:10
#5  0xb6f3e23c in main () at external/testservice/TestClient.cpp:18
(gdb) p mIn
$1 = {mError = 0, mData = 0xb6c27000 "\fr", mDataSize = 48, mDataCapacity = 256, mDataPos = 48, mObjects = 0x0, mObjectsSize = 0, mObjectsCapacity = 0, mNextObjectHint = 0, mFdsKnown = true, mHasFds = false, mAllowFds = true, mOwner = 0x0, mOwnerCookie = 0x0,
  mOpenAshmemSize = 0}
(gdb) p needRead
$2 = true
# 结果和我猜测的一致
```
综上所述，在`IPCThreadState::talkWithDriver(...)`中调用
``` c
ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &brw)
```
传入的数据bwr即为：
![](img01.png)
# 驱动层如何处理Test()请求
binder驱动层对接ioctl的函数是binder_ioctl(...)，kernel/goldfish/drivers/staging/android/binder.c:2716
``` c
static long binder_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{   // cmd=BINDER_WRITE_READ
    int ret;
    struct binder_proc *proc = filp->private_data;
    struct binder_thread *thread;
    unsigned int size = _IOC_SIZE(cmd);
    void __user *ubuf = (void __user *)arg;

    /*printk(KERN_INFO "binder_ioctl: %d:%d %x %lx\n", proc->pid, current->pid, cmd, arg);*/

    trace_binder_ioctl(cmd, arg);

    ret = wait_event_interruptible(binder_user_error_wait, binder_stop_on_user_error < 2);
    if (ret)
        goto err_unlocked;

    binder_lock(__func__);
    thread = binder_get_thread(proc);
    ......

    switch (cmd) {
    case BINDER_WRITE_READ: {
        struct binder_write_read bwr;
        ......
        if (copy_from_user(&bwr, ubuf, sizeof(bwr))) {// 把上图总用户空间的bwr复制到内核
            ......
        }
        ......
        if (bwr.write_size > 0) {
            // 重点在这里
            ret = binder_thread_write(proc, thread, (void __user *)bwr.write_buffer, bwr.write_size, &bwr.write_consumed);
            trace_binder_write_done(ret);
            ......
        }
        if (bwr.read_size > 0) {
            ret = binder_thread_read(proc, thread, (void __user *)bwr.read_buffer, bwr.read_size, &bwr.read_consumed, filp->f_flags & O_NONBLOCK);
            trace_binder_read_done(ret);
            ......
        }
        binder_debug(BINDER_DEBUG_READ_WRITE,
                 "binder: %d:%d wrote %ld of %ld, read return %ld of %ld\n",
                 proc->pid, thread->pid, bwr.write_consumed, bwr.write_size,
                 bwr.read_consumed, bwr.read_size);
        if (copy_to_user(ubuf, &bwr, sizeof(bwr))) {
            ret = -EFAULT;
            goto err;
        }
        break;
    }
    ......
    }
    ret = 0;
err:
    if (thread)
        thread->looper &= ~BINDER_LOOPER_STATE_NEED_RETURN;
    binder_unlock(__func__);
    wait_event_interruptible(binder_user_error_wait, binder_stop_on_user_error < 2);
    if (ret && ret != -ERESTARTSYS)
        printk(KERN_INFO "binder: %d:%d ioctl %x %lx returned %d\n", proc->pid, current->pid, cmd, arg, ret);
err_unlocked:
    trace_binder_ioctl_done(ret);
    return ret;
}
```
来看重点调用
``` c
binder_thread_write(proc, thread, (void __user *)bwr.write_buffer,
                            bwr.write_size, &bwr.write_consumed);
```
kernel/goldfish/drivers/staging/android/binder.c:1837
``` c
int binder_thread_write(struct binder_proc *proc, struct binder_thread *thread,
            void __user *buffer, int size, signed long *consumed)
{
    uint32_t cmd;
    void __user *ptr = buffer + *consumed;
    void __user *end = buffer + size;

    while (ptr < end && thread->return_error == BR_OK) {
        if (get_user(cmd, (uint32_t __user *)ptr))
            return -EFAULT;
        ptr += sizeof(uint32_t);
        trace_binder_command(cmd);
        if (_IOC_NR(cmd) < ARRAY_SIZE(binder_stats.bc)) {
            binder_stats.bc[_IOC_NR(cmd)]++;
            proc->stats.bc[_IOC_NR(cmd)]++;
            thread->stats.bc[_IOC_NR(cmd)]++;
        }
        switch (cmd) {
        ......
        case BC_TRANSACTION:
        case BC_REPLY: {
            struct binder_transaction_data tr;

            if (copy_from_user(&tr, ptr, sizeof(tr)))
                return -EFAULT;
            ptr += sizeof(tr); // 对照前面的图逆向拆解
            binder_transaction(proc, thread, &tr, cmd == BC_REPLY);
            break;
        }
        ......
        default:
            printk(KERN_ERR "binder: %d:%d unknown command %d\n",
                   proc->pid, thread->pid, cmd);
            return -EINVAL;
        }
        *consumed = ptr - buffer;
    }
    return 0;
}
```
这个cmd的值是BC_TRANSACTION，因此继续`binder_transaction(proc, thread, &tr, false)`, kernel/goldfish/drivers/staging/android/binder.c:1402
``` c
static void binder_transaction(struct binder_proc *proc,
                   struct binder_thread *thread,
                   struct binder_transaction_data *tr, int reply)
{
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
        if (tr->target.handle) {
            struct binder_ref *ref;
            ref = binder_get_ref(proc, tr->target.handle);
            if (ref == NULL) {
                binder_user_error("binder: %d:%d got "
                    "transaction to invalid handle\n",
                    proc->pid, thread->pid);
                return_error = BR_FAILED_REPLY;
                goto err_invalid_target_handle;
            }
            target_node = ref->node;
        } else {
            target_node = binder_context_mgr_node;
            if (target_node == NULL) {
                return_error = BR_DEAD_REPLY;
                goto err_no_context_mgr_node;
            }
        }
        e->to_node = target_node->debug_id;
        target_proc = target_node->proc;
        if (target_proc == NULL) {
            return_error = BR_DEAD_REPLY;
            goto err_dead_binder;
        }
        if (security_binder_transaction(proc->tsk, target_proc->tsk) < 0) {
            return_error = BR_FAILED_REPLY;
            goto err_invalid_target_handle;
        }
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
    } else {
        target_list = &target_proc->todo;
        target_wait = &target_proc->wait;
    }
    e->to_proc = target_proc->pid;

    /* TODO: reuse incoming transaction for reply */
    t = kzalloc(sizeof(*t), GFP_KERNEL);
    if (t == NULL) {
        return_error = BR_FAILED_REPLY;
        goto err_alloc_t_failed;
    }
    binder_stats_created(BINDER_STAT_TRANSACTION);

    tcomplete = kzalloc(sizeof(*tcomplete), GFP_KERNEL);
    if (tcomplete == NULL) {
        return_error = BR_FAILED_REPLY;
        goto err_alloc_tcomplete_failed;
    }
    binder_stats_created(BINDER_STAT_TRANSACTION_COMPLETE);

    t->debug_id = ++binder_last_id;
    e->debug_id = t->debug_id;

    if (reply)
        binder_debug(BINDER_DEBUG_TRANSACTION,
                 "binder: %d:%d BC_REPLY %d -> %d:%d, "
                 "data %p-%p size %zd-%zd\n",
                 proc->pid, thread->pid, t->debug_id,
                 target_proc->pid, target_thread->pid,
                 tr->data.ptr.buffer, tr->data.ptr.offsets,
                 tr->data_size, tr->offsets_size);
    else
        binder_debug(BINDER_DEBUG_TRANSACTION,
                 "binder: %d:%d BC_TRANSACTION %d -> "
                 "%d - node %d, data %p-%p size %zd-%zd\n",
                 proc->pid, thread->pid, t->debug_id,
                 target_proc->pid, target_node->debug_id,
                 tr->data.ptr.buffer, tr->data.ptr.offsets,
                 tr->data_size, tr->offsets_size);

    if (!reply && !(tr->flags & TF_ONE_WAY))
        t->from = thread;
    else
        t->from = NULL;
    t->sender_euid = proc->tsk->cred->euid;
    t->to_proc = target_proc;
    t->to_thread = target_thread;
    t->code = tr->code;
    t->flags = tr->flags;
    t->priority = task_nice(current);

    trace_binder_transaction(reply, t, target_node);

    t->buffer = binder_alloc_buf(target_proc, tr->data_size,
        tr->offsets_size, !reply && (t->flags & TF_ONE_WAY));
    if (t->buffer == NULL) {
        return_error = BR_FAILED_REPLY;
        goto err_binder_alloc_buf_failed;
    }
    t->buffer->allow_user_free = 0;
    t->buffer->debug_id = t->debug_id;
    t->buffer->transaction = t;
    t->buffer->target_node = target_node;
    trace_binder_transaction_alloc_buf(t->buffer);
    if (target_node)
        binder_inc_node(target_node, 1, 0, NULL);

    offp = (size_t *)(t->buffer->data + ALIGN(tr->data_size, sizeof(void *)));

    if (copy_from_user(t->buffer->data, tr->data.ptr.buffer, tr->data_size)) {
        binder_user_error("binder: %d:%d got transaction with invalid "
            "data ptr\n", proc->pid, thread->pid);
        return_error = BR_FAILED_REPLY;
        goto err_copy_data_failed;
    }
    if (copy_from_user(offp, tr->data.ptr.offsets, tr->offsets_size)) {
        binder_user_error("binder: %d:%d got transaction with invalid "
            "offsets ptr\n", proc->pid, thread->pid);
        return_error = BR_FAILED_REPLY;
        goto err_copy_data_failed;
    }
    if (!IS_ALIGNED(tr->offsets_size, sizeof(size_t))) {
        binder_user_error("binder: %d:%d got transaction with "
            "invalid offsets size, %zd\n",
            proc->pid, thread->pid, tr->offsets_size);
        return_error = BR_FAILED_REPLY;
        goto err_bad_offset;
    }
    off_end = (void *)offp + tr->offsets_size;
    for (; offp < off_end; offp++) {
        struct flat_binder_object *fp;
        if (*offp > t->buffer->data_size - sizeof(*fp) ||
            t->buffer->data_size < sizeof(*fp) ||
            !IS_ALIGNED(*offp, sizeof(void *))) {
            binder_user_error("binder: %d:%d got transaction with "
                "invalid offset, %zd\n",
                proc->pid, thread->pid, *offp);
            return_error = BR_FAILED_REPLY;
            goto err_bad_offset;
        }
        fp = (struct flat_binder_object *)(t->buffer->data + *offp);
        switch (fp->type) {
        case BINDER_TYPE_BINDER:
        case BINDER_TYPE_WEAK_BINDER: {
            struct binder_ref *ref;
            struct binder_node *node = binder_get_node(proc, fp->binder);
            if (node == NULL) {
                node = binder_new_node(proc, fp->binder, fp->cookie);
                if (node == NULL) {
                    return_error = BR_FAILED_REPLY;
                    goto err_binder_new_node_failed;
                }
                node->min_priority = fp->flags & FLAT_BINDER_FLAG_PRIORITY_MASK;
                node->accept_fds = !!(fp->flags & FLAT_BINDER_FLAG_ACCEPTS_FDS);
            }
            if (fp->cookie != node->cookie) {
                binder_user_error("binder: %d:%d sending u%p "
                    "node %d, cookie mismatch %p != %p\n",
                    proc->pid, thread->pid,
                    fp->binder, node->debug_id,
                    fp->cookie, node->cookie);
                goto err_binder_get_ref_for_node_failed;
            }
            if (security_binder_transfer_binder(proc->tsk, target_proc->tsk)) {
                return_error = BR_FAILED_REPLY;
                goto err_binder_get_ref_for_node_failed;
            }
            ref = binder_get_ref_for_node(target_proc, node);
            if (ref == NULL) {
                return_error = BR_FAILED_REPLY;
                goto err_binder_get_ref_for_node_failed;
            }
            if (fp->type == BINDER_TYPE_BINDER)
                fp->type = BINDER_TYPE_HANDLE;
            else
                fp->type = BINDER_TYPE_WEAK_HANDLE;
            fp->handle = ref->desc;
            binder_inc_ref(ref, fp->type == BINDER_TYPE_HANDLE,
                       &thread->todo);

            trace_binder_transaction_node_to_ref(t, node, ref);
            binder_debug(BINDER_DEBUG_TRANSACTION,
                     "        node %d u%p -> ref %d desc %d\n",
                     node->debug_id, node->ptr, ref->debug_id,
                     ref->desc);
        } break;
        case BINDER_TYPE_HANDLE:
        case BINDER_TYPE_WEAK_HANDLE: {
            struct binder_ref *ref = binder_get_ref(proc, fp->handle);
            if (ref == NULL) {
                binder_user_error("binder: %d:%d got "
                    "transaction with invalid "
                    "handle, %ld\n", proc->pid,
                    thread->pid, fp->handle);
                return_error = BR_FAILED_REPLY;
                goto err_binder_get_ref_failed;
            }
            if (security_binder_transfer_binder(proc->tsk, target_proc->tsk)) {
                return_error = BR_FAILED_REPLY;
                goto err_binder_get_ref_failed;
            }
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
        BUG_ON(t->buffer->async_transaction != 0);
        binder_pop_transaction(target_thread, in_reply_to);
    } else if (!(t->flags & TF_ONE_WAY)) {
        BUG_ON(t->buffer->async_transaction != 0);
        t->need_reply = 1;
        t->from_parent = thread->transaction_stack;
        thread->transaction_stack = t;
    } else {
        BUG_ON(target_node == NULL);
        BUG_ON(t->buffer->async_transaction != 1);
        if (target_node->has_async_transaction) {
            target_list = &target_node->async_todo;
            target_wait = NULL;
        } else
            target_node->has_async_transaction = 1;
    }
    t->work.type = BINDER_WORK_TRANSACTION;
    list_add_tail(&t->work.entry, target_list);
    tcomplete->type = BINDER_WORK_TRANSACTION_COMPLETE;
    list_add_tail(&tcomplete->entry, &thread->todo);
    if (target_wait)
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

