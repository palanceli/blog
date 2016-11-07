---
layout: post
title:  "Binder学习笔记（三）—— binder客户端是如何组织checkService数据的？"
date:   2016-05-08 01:20:48 +0800
categories: Android
tags:   Binder学习笔记
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
<!-- more -->

前文已经分析过sm是new BpServiceManager(new BpBinder(0))，于是sm->getService(…)的行为应该找BpServiceManager::getService(…)，frameworks/native/libs/binder/IServiceManager.cpp:134
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
![客户端请求checkService时发送出去的数据，由ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &bwr)
发出](0514BinderLearning3/img01.png)

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
        // talkWithDriver()只有在发生错误的时候才会退出，收到的响应数据长度为0不是错误，
        // 因此正常的逻辑是收到BR_REPLY才退出循环
        if ((err=talkWithDriver()) < NO_ERROR) break;
        err = mIn.errorCheck();
        if (err < NO_ERROR) break;
        if (mIn.dataAvail() == 0) continue;
        
        cmd = (uint32_t)mIn.readInt32();
        ... ...

        switch (cmd) {
        case BR_TRANSACTION_COMPLETE:
            if (!reply && !acquireResult) goto finish; // 显然这里永远不可能finish
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
                if (!acquireResult) continue;   // 这也不可能finish
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
`调试的结果在#46行的位置断过三次，可是我并没有把每次断到这里的数据解析明白，在这里徘徊了两天，每天脑子里就在想这块代码，好难受！Android的C++源码编译的时候应该有优化选项，导致调试的行号和执行位置不能精确吻合，tr的成员如何解释又是依赖数据的，而数据是从Server端发过来的，从客户端代码正向追查是查不到的。前进的道路似乎走不通了，那就走另一条路吧，从Server端出发，看看当Server端收到checkService的请求后如何响应，再根据响应数据来分析Client端的处理逻辑。`

## IPCThreadState::talkWithDriver(bool doReceive)
在`IPCThreadState::waitForResponse(...)`中首先调用了该函数，其声明在frameworks/native/include/binder/IPCThreadState.h:98:
`status_t            talkWithDriver(bool doReceive=true);`
再看其定义frameworks/native/include/binder/IPCThreadState.cpp:803
``` c
status_t IPCThreadState::talkWithDriver(bool doReceive)
{   // doReceive = true
    ... ...
    binder_write_read bwr;
    
    // Is the read buffer empty?
    // 游标位置大于等于数据大小，说明读入的数据都已经被消化了
    const bool needRead = mIn.dataPosition() >= mIn.dataSize();
    
    // We don't want to write anything if we are still reading
    // from data left in the input buffer and the caller
    // has requested to read the next data.
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

# waitForResponse最终交出了什么样的reply
![getService(...)的调用关系（蓝色表示函数定义位置，绿色表示函数被调用的位置）](0514BinderLearning3/img02.png)
第二天想想不死心，尽管`waitForResponse()`内部的分析遇到障碍了，暂且搁置。但可以把`waitForResponse()`最终交出了什么样的reply分析出来。因为在函数`checkService()`中，在执行完`remote()->transact(...)`之后会从reply提取出StrongBinder，这说明`waitForResponse()`的成果就是reply。

调试的过程详见[调试waitForResponse组装的reply](#anchor2)

具体的函数调用是在frameworks/native/libs/binder/IServiceManager.cpp:152
``` c
   virtual sp<IBinder> checkService( const String16& name) const
    {
        Parcel data, reply;
        data.writeInterfaceToken(IServiceManager::getInterfaceDescriptor());
        data.writeString16(name);
        remote()->transact(CHECK_SERVICE_TRANSACTION, data, &reply);
        return reply.readStrongBinder();
    }
```
调用关系如下：
![Parcel::readStrongBinder()的调用关系](0514BinderLearning3/img03.png)
从调试结果来看，flat->type为BINDER_TYPE_HANDLE，handle=1
frameworks/native/libs/binder/Parcel.cpp:293
``` c
status_t unflatten_binder(const sp<ProcessState>& proc,
    const Parcel& in, sp<IBinder>* out)
{
    const flat_binder_object* flat = in.readObject(false);

    if (flat) {
        switch (flat->type) {
            case BINDER_TYPE_BINDER:
                *out = reinterpret_cast<IBinder*>(flat->cookie);
                return finish_unflatten_binder(NULL, *flat, in);
            case BINDER_TYPE_HANDLE:    // 于是走这里
                *out = proc->getStrongProxyForHandle(flat->handle);
                return finish_unflatten_binder(
                    static_cast<BpBinder*>(out->get()), *flat, in);
        }
    }
    return BAD_TYPE;
}
```
于是又回到了`ProcessState::getStrongProxyForHandle(...)`，本质上返回的是`new BpBinder(handle)`

------
# 调试应答数据
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
## 在模拟器上运行Server
``` bash
$ adb shell /data/local/tmp/testservice/TestServer
```
## 在模拟器上通过gdbserver运行客户端
``` bash
$ adb shell gdbserver :1234 /data/local/tmp/testservice/TestClient
```
## 在调试机上运行gdb
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
(gdb) p /x BR_TRANSACTION_COMPLETE  # 可以打印这些常量
$7 = 0x7206
```
cmd的值被优化掉了，只好采用笨办法，在关键的逻辑分支上多加一些断点，而且我发现把断点往后打，cmd就能打印出来了。再次正式调试之前，先用`p /x BR_xxx`把这些常量的值打出来：

常量|值
---|----
BR_OK|0x7201
BR_DEAD_REPLY|0x7205
BR_TRANSACTION_COMPLETE|0x7206
BR_NOOP|0x720c
BR_SPAWN_LOOPER|0x720d
BR_FINISHED|0x720e
BR_FAILED_REPLY|0x7211
BR_ERROR|0x80047200
BR_TRANSACTION|0x80287202
BR_REPLY|0x80287203
BR_ACQUIRE_RESULT|0x80047204
BR_INCREFS|0x80087207
BR_ACQUIRE|0x80087208
BR_RELEASE|0x80087209
BR_DECREFS|0x8008720a
BR_ATTEMPT_ACQUIRE|0x800c720b
BR_DEAD_BINDER|0x8004720f
BR_CLEAR_DEATH_NOTIFICATION_DONE|0x80047210

我把通用的调试命令写成脚本，放在了external-testservice/debug.gdb中，继续第三个终端的调试过程：
``` bash
$ adb forward tcp:1234 tcp:1234    # forward端口
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient
(gdb) source ../androidex/external-testservice/debug.gdb
(gdb) common        # 初始化
... ...
(gdb) binder03a     # 在761、768处设置断点

(gdb) c
Continuing.

Breakpoint 2, android::IPCThreadState::waitForResponse (this=this@entry=0xb6be4000, reply=reply@entry=0xbe84fa24, acquireResult=acquireResult@entry=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:766
766                             freeBuffer, this);
(gdb) p tr
$1 = {target = {handle = 0, ptr = 0}, cookie = 0, code = 0, flags = 0, sender_pid = 0, sender_euid = 1000, data_size = 0, offsets_size = 0, data = {ptr = {buffer = 3064733736, offsets = 3064733736}, buf = "( \254\266( \254\266"}}
(gdb) c
Continuing.

Breakpoint 2, android::IPCThreadState::waitForResponse (this=0xb6be4000, reply=0xbe84fa9c, acquireResult=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:766
766                             freeBuffer, this);
(gdb) p tr
$2 = {target = {handle = 0, ptr = 0}, cookie = 0, code = 0, flags = 0, sender_pid = 0, sender_euid = 1000, data_size = 16, offsets_size = 4, data = {ptr = {buffer = 3064733736, offsets = 3064733752}, buf = "( \254\266\070 \254\266"}}
(gdb) x /3uwx 3064733736
0xb6ac2028: 0x73682a85  0x0000017f  0x00000001
(gdb) c
Continuing.

Breakpoint 2, android::IPCThreadState::waitForResponse (this=0xb6be4000, reply=0xbe84fad4, acquireResult=0x0) at frameworks/native/libs/binder/IPCThreadState.cpp:766
766                             freeBuffer, this);
(gdb) p tr
$3 = {target = {handle = 0, ptr = 0}, cookie = 0, code = 0, flags = 0, sender_pid = 0, sender_euid = 0, data_size = 4, offsets_size = 0, data = {ptr = {buffer = 3064733736, offsets = 3064733740}, buf = "( \254\266, \254\266"}}
(gdb) c
Continuing.
[Inferior 1 (process 1293) exited normally]
```
实际上是在761初命中3次。但是对其中的数据含义，目前还没有梳理清楚。

# 调试waitForResponse组装的reply
<a name="anchor2"></a>
``` bash
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient
(gdb) source ../androidex/external-testservice/debug.gdb
(gdb) common
... ...

Breakpoint 1, main () at external/testservice/TestClient.cpp:14
14  int main() {
(gdb) b IServiceManager.cpp:152     # 断在reply.readStrongBinder()
Breakpoint 2 at 0xb6e7fe0c: file frameworks/native/libs/binder/IServiceManager.cpp, line 152.
(gdb) c
Continuing.

Breakpoint 2, android::BpServiceManager::checkService (this=<optimized out>, name=...) at frameworks/native/libs/binder/IServiceManager.cpp:152
152         return reply.readStrongBinder();
(gdb) b Parcel.cpp:296  # 断在unflatten_binder(...)开头
Breakpoint 3 at 0xb6e82104: file frameworks/native/libs/binder/Parcel.cpp, line 296.
(gdb) c
Continuing.

Breakpoint 3, android::unflatten_binder (proc=..., in=..., out=out@entry=0xbe9a9ae8) at frameworks/native/libs/binder/Parcel.cpp:296
296     const flat_binder_object* flat = in.readObject(false);
(gdb) n
295 {
(gdb) n
296     const flat_binder_object* flat = in.readObject(false);
(gdb) n
298     if (flat) {
(gdb) p *flat       # 查看从reply中读出的flat_binder_object
$3 = {type = 1936206469, flags = 383, {binder = 1, handle = 1}, cookie = 0}
(gdb) p BINDER_TYPE_BINDER
$4 = BINDER_TYPE_BINDER
(gdb) p /x BINDER_TYPE_BINDER
$5 = 0x73622a85
(gdb) p /x BINDER_TYPE_HANDLE
$6 = 0x73682a85
(gdb) p /x 1936206469   # 所以这个flat_binder_object类型就是BINDER_TYPE_HANDLE
$7 = 0x73682a85
```
