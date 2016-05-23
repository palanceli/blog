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
# 和我猜测的不一致，mDataSize=48=mDataPos, mData里面是啥？
(gdb) x /48c mIn.mData
0xb6c27000: 12 '\f' 114 'r' 0 '\000'    0 '\000'    3 '\003'    114 'r' 40 '('  -128 '\200'
0xb6c27008: 0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'
0xb6c27010: 0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'    0 '\000'
0xb6c27018: 0 '\000'    0 '\000'    0 '\000'    0 '\000'
```







