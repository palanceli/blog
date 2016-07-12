---
layout: post
title:  "Binder学习笔记（三）—— binder客户端是如何组织checkService数据的
？"
date:   2016-05-08 01:20:48 +0800
categories: Android
tags:   binder
toc: true
comments: true
---
起点从TestClient.cpp的main函数发起：
``` c++
int main() {
    sp < IServiceManager > sm = defaultServiceManager();
    sp < IBinder > binder = sm->getService(String16("service.testservice"));
    sp<ITestService> cs = interface_cast < ITestService > (binder);
    cs->test();
    return 0;
}
```
前文已经分析过sm是new BpServiceManager(new BpBinder(0))，于是sm->getService(…)的行为应该找BpServiceManager::getService(…)，frameworks/native/libs/binder/IserviceManager.cpp:134
``` c++
    virtual sp<IBinder> getService(const String16& name) const
    {
        ... ...
            sp<IBinder> svc = checkService(name);  // 这里是关键代码
            if (svc != NULL) return svc;
        ... ...
        return NULL;
}
    virtual sp<IBinder> checkService( const String16& name) const
    {
        Parcel data, reply;
        data.writeInterfaceToken(IServiceManager::getInterfaceDescriptor());
        data.writeString16(name);
        remote()->transact(CHECK_SERVICE_TRANSACTION, data, &reply);
        return reply.readStrongBinder();
    }
```
# 追踪BpBinder::transaction(...)
BpServiceManager::remote()返回的就是成员变量mRemote，前文也分析过了，也即是new BpBinder(0)。因此remote()->transact(…)调用的是BpBinder::transact(…)，
frameworks/native/libs/binder/BpBinder.cpp:159
``` c++
status_t BpBinder::transact(
    uint32_t code, const Parcel& data, Parcel* reply, uint32_t flags)
{   // code=CHECK_SERVICE_TRANSACTION, flags=0
    // Once a binder has died, it will never come back to life.
    if (mAlive) {
        status_t status = IPCThreadState::self()->transact(
            mHandle, code, data, reply, flags);
        if (status == DEAD_OBJECT) mAlive = 0;
        return status;
    }

    return DEAD_OBJECT;
}
```
IPCThreadState::self()从命名上来看应该又是个工厂类（前文遇到的ProcessState就是这么命名的），它是个线程单体，每线程一份。具体实现暂且不表，因为在当前上下文中其transact(…)跟线程单体没啥关系，我们直接进入IPCThreadState::transact(…)函数。
frameworks/native/libs/binder/IPCThreadState.cpp:548
``` c++
status_t IPCThreadState::transact(int32_t handle,
                                  uint32_t code, const Parcel& data,
                                  Parcel* reply, uint32_t flags)
{   // handle=0, code=CHECK_SERVICE_TRANSACTION, flags=0, reply非空
    ... ...
    flags |= TF_ACCEPT_FDS;
    ... ...
        err = writeTransactionData(BC_TRANSACTION, flags, handle, code, data, NULL);
    ... ...
    if ((flags & TF_ONE_WAY) == 0) {
        ... ...
        if (reply) {  // 在checkService(…)传入了非空的reply参数
            err = waitForResponse(reply);
        } else {
            Parcel fakeReply;
            err = waitForResponse(&fakeReply);
        }
        ... ...
    } else {
        err = waitForResponse(NULL, NULL);
    }
    
    return err;
}
```
这么长一大段，关键代码只有两行，从命名上来看就是一次请求和接收应答的过程。我们先研究请求数据。
## writeTransactionData(...)
frameworks/native/libs/binder/IPCThreadState.cpp:904
``` c++
status_t IPCThreadState::writeTransactionData(int32_t cmd, uint32_t binderFlags,
    int32_t handle, uint32_t code, const Parcel& data, status_t* statusBuffer)
{  // cmd=BC_TRANSACTION, binderFlags=TF_ACCEPT_FDS, handle=0, 
   // code=CHECK_SERVICE_TRANSACTION, 
    binder_transaction_data tr;

    tr.target.ptr = 0; /* Don't pass uninitialized stack data to a remote process */
    tr.target.handle = handle;
    tr.code = code;
    tr.flags = binderFlags;
    tr.cookie = 0;
    tr.sender_pid = 0;
    tr.sender_euid = 0;
    ... ...
        tr.data_size = data.ipcDataSize();
        tr.data.ptr.buffer = data.ipcData();
        tr.offsets_size = data.ipcObjectsCount()*sizeof(binder_size_t);
        tr.data.ptr.offsets = data.ipcObjects();
    ... ...    
    mOut.writeInt32(cmd);
    mOut.write(&tr, sizeof(tr));
    
    return NO_ERROR;
}
```
该函数就是把一堆参数组装进binder_transaction_data结构体，并写进mOut。其中data是在checkService(…)中组装的Parcel数据：
![客户端请求checkService时发送出去的数据](img01.png)
data.ipcObjectsCount()*sizeof(binder_size_t)以及data.ipcObjects()分别是什么呢？从命名上来看，他应该是指保存在data中的抽象数据类型的数据，显然在组织checkService时的Parcel数据中是没有抽象数据类型的，可以先不深究它。

## struct binder_transaction_data
来看看这个数据结构，定义在external/kernel-headers/original/uapi/linux/binder.h:129
``` c
struct binder_transaction_data {
    union {
        /* target descriptor of command transaction */
        __u32   handle;
        /* target descriptor of return transaction */
        binder_uintptr_t ptr;
    } target;
    binder_uintptr_t    cookie; /* target object cookie */
    __u32       code;       /* transaction command */

    /* General information about the transaction. */
    __u32           flags;
    pid_t       sender_pid;
    uid_t       sender_euid;
    binder_size_t   data_size;  /* number of bytes of data */
    binder_size_t   offsets_size;   /* number of bytes of offsets */

    union {
        struct {
            /* transaction data */
            binder_uintptr_t    buffer;
            /* offsets from buffer to flat_binder_object structs */
            binder_uintptr_t    offsets;
        } ptr;
        __u8    buf[8];
    } data;
};
```
以上就是请求的数据，mOut的类型是Parcel，会在后面介绍，可以理解为就是数据的序列化。

## waitForResponse(reply)
接下来看对应答的处理，在深入函数之前，有必要调试一把代码，因为请求数据的处理逻辑从静态代码就能分析，而应答数据的处理则依赖于收到的应答数据是什么。调试过程请参见：[调试应答数据](#anchor1)

函数waitForResponse(reply)定义在frameworks/native/libs/binder/IPCThreadState.cpp:712
``` c
status_t IPCThreadState::waitForResponse(Parcel *reply, status_t *acquireResult)
{   // reply = 是在checkService函数中声明的栈变量，acquireResult=NULL
    uint32_t cmd;
    int32_t err;

    while (1) {
        if ((err=talkWithDriver()) < NO_ERROR) break;
        err = mIn.errorCheck();
        if (err < NO_ERROR) break;
        if (mIn.dataAvail() == 0) continue;
        
        cmd = (uint32_t)mIn.readInt32();
        ... ...

        switch (cmd) {
        case BR_TRANSACTION_COMPLETE:
            if (!reply && !acquireResult) goto finish;
            break;
        
        case BR_DEAD_REPLY:
            err = DEAD_OBJECT;
            goto finish;

        case BR_FAILED_REPLY:
            err = FAILED_TRANSACTION;
            goto finish;
        
        case BR_ACQUIRE_RESULT:
            {
                ALOG_ASSERT(acquireResult != NULL, "Unexpected brACQUIRE_RESULT");
                const int32_t result = mIn.readInt32();
                if (!acquireResult) continue;
                *acquireResult = result ? NO_ERROR : INVALID_OPERATION;
            }
            goto finish;
        
        case BR_REPLY:
            {
                binder_transaction_data tr;
                err = mIn.read(&tr, sizeof(tr));
                ALOG_ASSERT(err == NO_ERROR, "Not enough command data for brREPLY");
                if (err != NO_ERROR) goto finish;

                if (reply) {
                    if ((tr.flags & TF_STATUS_CODE) == 0) {
                        reply->ipcSetDataReference(
                            reinterpret_cast<const uint8_t*>(tr.data.ptr.buffer),
                            tr.data_size,
                            reinterpret_cast<const binder_size_t*>(tr.data.ptr.offsets),
                            tr.offsets_size/sizeof(binder_size_t),
                            freeBuffer, this);
                    } else {
                        err = *reinterpret_cast<const status_t*>(tr.data.ptr.buffer);
                        freeBuffer(NULL,
                            reinterpret_cast<const uint8_t*>(tr.data.ptr.buffer),
                            tr.data_size,
                            reinterpret_cast<const binder_size_t*>(tr.data.ptr.offsets),
                            tr.offsets_size/sizeof(binder_size_t), this);
                    }
                } else {
                    freeBuffer(NULL,
                        reinterpret_cast<const uint8_t*>(tr.data.ptr.buffer),
                        tr.data_size,
                        reinterpret_cast<const binder_size_t*>(tr.data.ptr.offsets),
                        tr.offsets_size/sizeof(binder_size_t), this);
                    continue;
                }
            }
            goto finish;

        default:
            err = executeCommand(cmd);
            if (err != NO_ERROR) goto finish;
            break;
        }
    }

finish:
    if (err != NO_ERROR) {
        if (acquireResult) *acquireResult = err;
        if (reply) reply->setError(err);
        mLastError = err;
    }
    
    return err;
}
```
在#7行，调用了talkWithDriver()，定义在frameworks/native/libs/binder/IPCThreadState.cpp:803
``` c
status_t IPCThreadState::talkWithDriver(bool doReceive)
{   // doReceive=true
    ... ...
    
    binder_write_read bwr;
    ... ...
    const bool needRead = mIn.dataPosition() >= mIn.dataSize();
    ... ...
    const size_t outAvail = (!doReceive || needRead) ? mOut.dataSize() : 0;
    
    bwr.write_size = outAvail;
    bwr.write_buffer = (uintptr_t)mOut.data();

    // This is what we'll read.
    if (doReceive && needRead) {
        bwr.read_size = mIn.dataCapacity();
        bwr.read_buffer = (uintptr_t)mIn.data();
    } else {
        bwr.read_size = 0;
        bwr.read_buffer = 0;
    }
    ... ...
    // Return immediately if there is nothing to do.
    if ((bwr.write_size == 0) && (bwr.read_size == 0)) return NO_ERROR;

    bwr.write_consumed = 0;
    bwr.read_consumed = 0;
    status_t err;
    do {
        ... ...
        if (ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &bwr) >= 0)
            err = NO_ERROR;
        else
            err = -errno;
        ... ...
    } while (err == -EINTR);
    ... ...
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
        ... ...
        return NO_ERROR;
    }
    
    return err;
}
```
------
## 调试应答数据
<a name="anchor1"></a>
初始化环境、编译、拷贝文件等：
``` bash
$ source build/envsetup.sh      # 设置环境变量
... ...
$ lunch aosp_arm-eng
... ...
$ make -j8                      # 编译源码
... ...
$ mmm external/testservice      # 编译testservice
... ...
$ emulator&                     # 启动模拟器
... ...
# 把文件拷到模拟器
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestServer_intermediates/LINKED/TestServer /data/local/tmp/testservice    
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient /data/local/tmp/testservice
$ adb shell chmod 755 /data/local/tmp/testservice/* # 赋予可执行权限 
```
接下来需要启动三个终端：1、在模拟器上运行Server；2、在模拟器上通过gdbserver运行客户端；3、在调试机上运行gdb
### 在模拟器上运行Server
``` bash
$ adb shell /data/local/tmp/testservice/TestServer
```
### 在模拟器上通过gdbserver运行客户端
``` bash
$ adb shell gdbserver :1234 /data/local/tmp/testservice/TestClient
```
### 在调试机上运行gdb
``` bash
$ adb forward tcp:1234 tcp:1234    # forward端口
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient
(gdb) target remote :1234
(gdb) b main                        # 设置断点
Breakpoint 1 at 0xb6f321fc: file external/testservice/TestClient.cpp, line 14.
(gdb) c                             # continue
Continuing.
... ...
Breakpoint 1, main () at external/testservice/TestClient.cpp:14
14  int main() {
# 设置lib搜索路径
(gdb) set solib-absolute-prefix out/debug/target/product/generic/symbols/
Reading symbols from out/debug/target/product/generic/symbols/system/bin/linker...done.
... ...
(gdb) b IPCThreadState.cpp:730      # 在waitForResponse(...)设置断点
Breakpoint 2 at 0xb6ea3eb2: file frameworks/native/libs/binder/IPCThreadState.cpp, line 730.
(gdb) c                             # continue
Continuing.

Breakpoint 2, android::IPCThreadState::waitForResponse (this=this@entry=0xb6c24000, reply=reply@entry=0xbebb7a24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:730
730         switch (cmd) {
(gdb) p cmd                         # 打印cmd的值
$1 = <optimized out>                # 被优化掉了
# 只好采用笨办法，在每个case处都加断点
(gdb) b IPCThreadState.cpp:732
Breakpoint 3 at 0xb6f6ef1c: file frameworks/native/libs/binder/IPCThreadState.cpp, line 732.
(gdb) b IPCThreadState.cpp:736
Breakpoint 4 at 0xb6f6efba: file frameworks/native/libs/binder/IPCThreadState.cpp, line 736.
(gdb) b IPCThreadState.cpp:740
Breakpoint 5 at 0xb6f6ef18: file frameworks/native/libs/binder/IPCThreadState.cpp, line 740.
(gdb) b IPCThreadState.cpp:745
Breakpoint 6 at 0xb6f6ef28: file frameworks/native/libs/binder/IPCThreadState.cpp, line 745.
(gdb) b IPCThreadState.cpp:754
Breakpoint 7 at 0xb6f6ef46: file frameworks/native/libs/binder/IPCThreadState.cpp, line 754.
(gdb) b IPCThreadState.cpp:787
Breakpoint 8 at 0xb6f6efac: file frameworks/native/libs/binder/IPCThreadState.cpp, line 787.
(gdb) b IPCThreadState.cpp:794
Breakpoint 9 at 0xb6f6ef3e: file frameworks/native/libs/binder/IPCThreadState.cpp, line 794.
(gdb) c
Continuing.

Breakpoint 8, android::IPCThreadState::waitForResponse (this=this@entry=0xb6ce4000, reply=reply@entry=0xbed19a24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:787
787             err = executeCommand(cmd);  # 不认识的cmd
(gdb) c                                     # 继续
Continuing.

Breakpoint 3, android::IPCThreadState::waitForResponse (this=this@entry=0xb6ce4000, reply=reply@entry=0xbed19a24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:732
732             if (!reply && !acquireResult) goto finish;
(gdb) p mIn                                 # 看看mIn的内容
$6 = {mError = 0, mData = 0xb6ce7000 "\fr", mDataSize = 8, mDataCapacity = 256, mDataPos = 8, mObjects = 0x0, mObjectsSize = 0, mObjectsCapacity = 0, mNextObjectHint = 0, mFdsKnown = true, mHasFds = false, mAllowFds = true, mOwner = 0x0, mOwnerCookie = 0x0,
  mOpenAshmemSize = 0}

# mData指向的内存地址是0bB6CE7000，去看看吧：
(gdb) x /8u 0xb6ce7000
0xb6ce7000: 29196   29190   0   0
0xb6ce7010: 0   0   0   0

# 这两个数的十六进制呢：
(gdb) p /x 29190
$8 = 0x7206
(gdb) p /x 29196
$9 = 0x720c

# 再看看case对应的几个常量的值：
(gdb) p /x BR_TRANSACTION_COMPLETE
$7 = 0x7206
(gdb) p /x BR_DEAD_REPLY
$10 = 0x7205
(gdb) p /x BR_FAILED_REPLY
$11 = 0x7211
(gdb) p /x BR_ACQUIRE_RESULT
$12 = 0x80047204
(gdb) p /x BR_REPLY
$13 = 0x80287203

# 这也印证了代码会执行到case BR_TRANSACTION_COMPLETE，但是reply非空，所以不会goto finish，继续：
(gdb) c
Continuing.

Breakpoint 8, android::IPCThreadState::waitForResponse (this=this@entry=0xb6ce4000, reply=reply@entry=0xbed19a24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:787
787             err = executeCommand(cmd);
(gdb) p cmd
$15 = 29196         # 不认识的命令
(gdb) c             # 继续
Continuing.

Breakpoint 7, android::IPCThreadState::waitForResponse (this=this@entry=0xb6ce4000, reply=reply@entry=0xbed19a24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:755
755                 err = mIn.read(&tr, sizeof(tr));
(gdb) p cmd
$17 = 2150134275    # BR_REPLY
(gdb) p mIn
$16 = {mError = 0, mData = 0xb6ce7000 "\fr", mDataSize = 48, mDataCapacity = 256, mDataPos = 8, mObjects = 0x0, mObjectsSize = 0, mObjectsCapacity = 0, mNextObjectHint = 0, mFdsKnown = true, mHasFds = false, mAllowFds = true, mOwner = 0x0, mOwnerCookie = 0x0,
  mOpenAshmemSize = 0}
# 再看看mData里的内容：
(gdb) x /12uwx 0xb6ce7000
0xb6ce7000: 0x0000720c  0x80287203  0x00000000  0x00000000
0xb6ce7010: 0x00000000  0x00000000  0x00000000  0x000003e8
0xb6ce7020: 0x00000000  0x00000000  0xb6bc2028  0xb6bc2028

```
