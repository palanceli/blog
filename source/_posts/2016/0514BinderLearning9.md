---
title:  "Binder学习笔记（九）—— 服务端如何响应Test()请求？"
date:   2016-05-15 11:26:44 +0800
categories: Android
tags:   Binder学习笔记
toc: true
comments: true
---
从服务端代码出发，TestServer.cpp
``` c++
int main() {
    sp < ProcessState > proc(ProcessState::self());
    sp < IServiceManager > sm = defaultServiceManager();
    sm->addService(String16("service.testservice"), new BnTestService());
    ProcessState::self()->startThreadPool();
    IPCThreadState::self()->joinThreadPool();
    return 0;
}
```
前三行代码在之前的Binder学习笔记系列中都分析过了，继续往下看。
# ProcessState::self()->startThreadPool()做了什么？
frameworks/native/libs/binder/ProcessState.cpp:132
``` c++
void ProcessState::startThreadPool()
{
    AutoMutex _l(mLock);
    if (!mThreadPoolStarted) {
        mThreadPoolStarted = true;
        spawnPooledThread(true);
    }
}
```
继续spawnPooledThread(true)，frameworks/native/libs/binder/ProcessState.cpp:286
``` c++
void ProcessState::spawnPooledThread(bool isMain)
{
    if (mThreadPoolStarted) {
        String8 name = makeBinderThreadName();
        ALOGV("Spawning new pooled thread, name=%s\n", name.string());
        sp<Thread> t = new PoolThread(isMain);
        t->run(name.string());
    }
}
```
PoolThread是一个线程类，暂时先不去深究，它的run(...)函数最终会落实到线程函数threadLoop()的调用上，这个函数很简单,frameworks/native/libs/binder/ProcessState.cpp:61
``` c++
class PoolThread : public Thread
{
......
protected:
    virtual bool threadLoop()
    {
        IPCThreadState::self()->joinThreadPool(mIsMain);
        return false;
    }
    ......
};
```
它调到了`IPCThreadState::joinThreadPool(true);`这个函数在main函数中接下来也被调到了，那我们就并案调查吧。
# IPCThreadState::self()->joinThreadPool(...)做了什么？
frameworks/native/libs/binder/IPCThreadState.cpp:477
``` c++
void IPCThreadState::joinThreadPool(bool isMain)
{
    ......
    mOut.writeInt32(isMain ? BC_ENTER_LOOPER : BC_REGISTER_LOOPER);
    ......
        
    status_t result;
    do {
        processPendingDerefs();             // 处理上次循环尚未完成的内容
        // now get the next command to be processed, waiting if necessary
        result = getAndExecuteCommand();    // 重点看这里
        ......
        if(result == TIMED_OUT && !isMain) {
            break;
        }
    } while (result != -ECONNREFUSED && result != -EBADF);

    ......
    
    mOut.writeInt32(BC_EXIT_LOOPER);
    talkWithDriver(false);
}
```
frameworks/native/libs/binder/IPCThreadState.cpp:414
``` c++
status_t IPCThreadState::getAndExecuteCommand()
{
    status_t result;
    int32_t cmd;
    result = talkWithDriver();  // 这里完成一次对binder的IO
    ......
        size_t IN = mIn.dataAvail();
        if (IN < sizeof(int32_t)) return result;
        cmd = mIn.readInt32();
        ......
        result = executeCommand(cmd);
    ......
    return result;
}
```
也是一个`IO-解析`的模式，重点来看解析executeCommand(...)，frameworks/native/libs/binder/IPCThreadState.cpp:947
``` c++
status_t IPCThreadState::executeCommand(int32_t cmd)
{
    BBinder* obj;
    RefBase::weakref_type* refs;
    status_t result = NO_ERROR;
    
    switch ((uint32_t)cmd) {
    ......
    
    case BR_TRANSACTION:
        {
            binder_transaction_data tr;
            result = mIn.read(&tr, sizeof(tr));
            ......
            
            Parcel buffer;
            buffer.ipcSetDataReference(
                reinterpret_cast<const uint8_t*>(tr.data.ptr.buffer),
                tr.data_size,
                reinterpret_cast<const binder_size_t*>(tr.data.ptr.offsets),
                tr.offsets_size/sizeof(binder_size_t), freeBuffer, this);
            
            const pid_t origPid = mCallingPid;
            const uid_t origUid = mCallingUid;
            const int32_t origStrictModePolicy = mStrictModePolicy;
            const int32_t origTransactionBinderFlags = mLastTransactionBinderFlags;

            mCallingPid = tr.sender_pid;
            mCallingUid = tr.sender_euid;
            mLastTransactionBinderFlags = tr.flags;

            ......

            Parcel reply;
            status_t error;
            ......
            if (tr.target.ptr) {
                sp<BBinder> b((BBinder*)tr.cookie);  // 注意：这里是重点！！！
                error = b->transact(tr.code, buffer, &reply, tr.flags);

            } else {
                error = the_context_object->transact(tr.code, buffer, &reply, tr.flags);
            }

            
            if ((tr.flags & TF_ONE_WAY) == 0) {
                ......
                sendReply(reply, 0);
            } 
            ......
            
            mCallingPid = origPid;
            mCallingUid = origUid;
            mStrictModePolicy = origStrictModePolicy;
            mLastTransactionBinderFlags = origTransactionBinderFlags;

            ......
        }
        break;
    
    ......
    }

    ......
    
    return result;
}
```
tr.cookie是什么玩意？我们回到[《客户端如何组织Test()请求 ？》](http://palanceli.github.io/blog/2016/05/14/2016/0514BinderLearning8/)末尾那张图上，此时服务端收到的tr就应该是客户端请求test时组织的数据，可是那张图里cookie明明是0呀？怎么可能用空指针来初始化sp<BBinder>呢？而且后面还有对这个指针的调用！

## 客户端发出的test请求中tr.cookie是什么？
为了确认那张图中cookie的正确性，我用gdb调试到源码内部，这是能得到最确凿结论的方法。
* 部署环境 
编译[《Binder学习笔记（一）》](http://palanceli.github.io/blog/2016/04/25/2016/0511BinderLearning1/)中的代码。我将该代码放到了android源码的external/testservice下，执行
``` bash
$ mmm external/testservice
$ emulator&    # 启动模拟器，把编译出的可执行文件上传到模拟器并修改可执行权限
$ adb shell mkdir /data/local/tmp/testservice
$ adb push prebuilts/misc/android-arm/gdbserver/ /data/local/tmp/testservice
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestServer_intermediates/LINKED/TestServer /data/local/tmp/testservice
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient /data/local/tmp/testservice
$ adb shell chmod 755 /data/local/tmp/testservice/*
```
* 调试
需要开三个终端：
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
(gdb) b IPCThreadState.cpp:937 # 在我们要查看的位置下断点
Breakpoint 2 at 0xb6ec89f8: file frameworks/native/libs/binder/IPCThreadState.cpp, line 937.
(gdb) c
Continuing.
......
(gdb) bt  # 注意：一定要通过bt查看是不是由test到达该断点，如果不是，需要再continue
#0  android::IPCThreadState::writeTransactionData (this=this@entry=0xb6c64000, cmd=cmd@entry=1076388608, binderFlags=binderFlags@entry=16, handle=handle@entry=1, code=code@entry=1, data=..., statusBuffer=statusBuffer@entry=0x0)
    at frameworks/native/libs/binder/IPCThreadState.cpp:937
#1  0xb6ec903c in android::IPCThreadState::transact (this=0xb6c64000, handle=1, code=code@entry=1, data=..., reply=reply@entry=0xbec50ad4, flags=16, flags@entry=0) at frameworks/native/libs/binder/IPCThreadState.cpp:566
#2  0xb6ec408e in android::BpBinder::transact (this=0xb6c490c0, code=1, data=..., reply=0xbec50ad4, flags=0) at frameworks/native/libs/binder/BpBinder.cpp:165
#3  0xb6f5742e in android::BpTestService::test (this=<optimized out>) at external/testservice/TestClient.cpp:10
#4  0xb6f5723c in main () at external/testservice/TestClient.cpp:18
(gdb) p tr
$2 = {target = {handle = 1, ptr = 1}, cookie = 0, code = 1, flags = 16, sender_pid = 0, sender_euid = 0, data_size = 72, offsets_size = 0, data = {ptr = {buffer = 3066360032, offsets = 0}, buf = "\340\360Ķ\000\000\000"}}
(gdb)
```
> 非常确认，客户端发出的数据包中tr.cookie就是0！

那就奇了怪了，客户端发出的是0，为什么到了服务端还要用它？
## 服务端接收到的test请求中tr.cookie是什么？
继续用gdb调试服务端，一探究竟。调试服务端也需要三个终端：
1. Target1 在模拟器上通过gdbserver启动server
``` bash
$ adb shell gdbserver :1234  /data/local/tmp/testservice/TestServer
Process /data/local/tmp/testservice/TestServer created; pid = 1273
Listening on port 1234
``` 
2. Host1 在宿主机调试server
``` bash
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestServer_intermediates/LINKED/TestServer
......
(gdb) b main
Breakpoint 1 at 0x19e8: file external/testservice/TestServer.cpp, line 30.
(gdb) c
The program is not being run.
(gdb) target remote :1234
......
0xb6f5c658 in ?? ()
(gdb) c
Continuing.
......
(gdb) set solib-absolute-prefix out/debug/target/product/generic/symbols/
......
(gdb) b IPCThreadState.cpp:1087
Breakpoint 2 at 0xb6eeec52: file frameworks/native/libs/binder/IPCThreadState.cpp, line 1087.
(gdb) c
Continuing.
```
3. Target2 在模拟器启动Client，触发断点
``` bash
$ adb shell /data/local/tmp/testservice/TestClient
BpTestService::test()
```

然后在Host1上就会看到如下结果：
``` bash
Breakpoint 2, android::IPCThreadState::executeCommand (this=this@entry=0xb6c64000, cmd=cmd@entry=-2144833022) at frameworks/native/libs/binder/IPCThreadState.cpp:1087
1087                    error = b->transact(tr.code, buffer, &reply, tr.flags);
(gdb) bt  # 打印调用堆栈，确认走到了我们想要断点
#0  android::IPCThreadState::executeCommand (this=this@entry=0xb6c64000, cmd=cmd@entry=-2144833022) at frameworks/native/libs/binder/IPCThreadState.cpp:1087
#1  0xb6eeedbc in android::IPCThreadState::getAndExecuteCommand (this=this@entry=0xb6c64000) at frameworks/native/libs/binder/IPCThreadState.cpp:433
#2  0xb6eeee20 in android::IPCThreadState::joinThreadPool (this=0xb6c64000, isMain=<optimized out>) at frameworks/native/libs/binder/IPCThreadState.cpp:492
#3  0xb6f7dabc in main () at external/testservice/TestServer.cpp:35
(gdb) p tr  # cookie非0！！
$1 = {target = {handle = 3066421360, ptr = 3066421360}, cookie = 3066323044, code = 1, flags = 16, sender_pid = 1276, sender_euid = 0, data_size = 72, offsets_size = 0, data = {ptr = {buffer = 3065258024, offsets = 3065258096}, buf = "( \264\266p \264\266"}}

```
见了鬼了，cookie非0！发送端和接收端看到的值不一样！服务端此时收到的这个cookie是什么呢？服务端把cookie直接当作地址转换成了BBinder，能这么搞说明cookie里记录的地址一定是服务端自己地址空间的，接下来又调用b->transact(...)执行具体服务，那这个服务应该就是服务端的BnTestService吧？
BnTestService是在addService时创建，而且还记得嘛，这个地址是被发送给了ServiceManager。参见[《binder服务端是如何组织addService数据的？》](http://palanceli.github.io/blog/2016/05/11/2016/0514BinderLearning6/)末尾的图，服务端调用addService向ServiceManager注册自己，并把自己的BnTestService对象指针传给了cookie。在那张图中有两个cookie，左边是向ServiceManager发送的ADD_SERVICE_TRANSACTION命令数据，右边Parcel是该命令包含的注册信息数据。
## cookie是否就是当初注册的时候new出来的BnTestService呢？
继续用gdb验证！
* 服务端收到的tr.cookie是否就是注册时呢我出来的BnTestService？
还是调试服务端，很多命令是重复的，如果嫌烦可以写一个gdb脚本。
Target1和Target2与上一小节没有任何差别，来看Host1，先写好gdb脚本，20160515.gdb：
``` bash
define server_test
    target remote :1234
    b main
    c
    set solib-absolute-prefix out/debug/target/product/generic/symbols/
    b IServiceManager.cpp:161
    b IPCThreadState.cpp:1087
    c
end 
```
然后执行gdb：
``` bash
$ ./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestServer_intermediates/LINKED/TestServer
......
(gdb) source ../androidex/external/testservice/20160515.gdb
(gdb) server_test
......
Breakpoint 2, android::BpServiceManager::addService (this=0xb6c0e040, name=..., service=..., allowIsolated=<optimized out>) at frameworks/native/libs/binder/IServiceManager.cpp:161
161         data.writeStrongBinder(service);
(gdb) p service  # 查看addService时BnTestService的地址
$1 = (const android::sp<android::IBinder> &) @0xbeb99b14: {m_ptr = 0xb6c06064}
(gdb) c
Continuing.

Breakpoint 3, android::IPCThreadState::executeCommand (this=this@entry=0xb6c24000, cmd=cmd@entry=-2144833022) at frameworks/native/libs/binder/IPCThreadState.cpp:1087
1087                    error = b->transact(tr.code, buffer, &reply, tr.flags);
(gdb) p tr  # cookie=3066060900=0xb6c06064，正是BnTestService！
$2 = {target = {handle = 3066159216, ptr = 3066159216}, cookie = 3066060900, code = 1, flags = 16, sender_pid = 1297, sender_euid = 0, data_size = 72, offsets_size = 0, data = {ptr = {buffer = 3064995880, offsets = 3064995952}, buf = "( \260\266p \260\266"}}
(gdb)
```

证实！
>服务端接收到test()请求时，tr.cookie就是BnTestService的指针

至于为什么客户端发来时组的数据包中cookie为0，服务端收到时自动变成了BnTestService？我们以后再探究。先把test()的流程看完。

BnTestService继承自BnInterface<ITestService>，后者又继承自ITestService和BBinder。即BBinder是BnTestService基类的基类，故将cookie转换成BBinder*是合法的。
在看接下来的调用b->transact(...)，frameworks/native/libs/binder/Binder.cpp:97
``` c++
status_t BBinder::transact(
    uint32_t code, const Parcel& data, Parcel* reply, uint32_t flags)
{   // code=TEST
    ......
    switch (code) {
        case PING_TRANSACTION:
            reply->writeInt32(pingBinder());
            break;
        default:
            err = onTransact(code, data, reply, flags); // 走到这里
            break;
    }
    ......
    return err;
}
```
BBinder::onTransact(...)是一个虚函数，b实际指向的是BnTestService，因此该虚函数实际应看BnTestService::onTransact(...)版本：
``` c++
status_t BnTestService::onTransact(uint_t code, const Parcel& data,
        Parcel* reply, uint32_t flags) {
    switch (code) {
    case TEST: {
        printf("BnTestService::onTransact, code: TEST\n");
        CHECK_INTERFACE(ITest, data, reply);
        test();
        reply->writeInt32(100);
        return NO_ERROR;
    }
        break;
    default:
        break;
    }
    return NO_ERROR;
}
```
终于到达了test()的实现！服务端的test服务被调用，如果有返回值，将被写入reply，打成包裹发给客户端，打包和发送过程就前面都有，不再重复分析了。

# 总结
至此，通过静态、动态代码走查，我把Binder的ServiceManager、服务端、客户端的角色基本梳理清晰了：
* 服务端通过addService向ServiceManager注册服务，后者缓存下服务的名称和在服务端的进程内指针，这两个变量就可以唯一确定一个服务。
* 服务端公开了服务接口，为每一个接口定义一个唯一编码，并负责实现这些服务接口。
* 客户端通过getService获取指定名称的服务端handle，该handle在客户端被伪装成指向服务的指针，通过该指针可以调用服务接口。实际上framework把handle和服务接口打成数据包发送给服务端。
* 服务端在接收到打包请求时，解析接口，并执行对应的实现，将结果返回给客户端。

当然，Binder的天空下还剩一小片乌云，就是那个tr.cookie，为什么客户端发送的时候填入的是0，而服务端却接收到了自己的BnTestService指针？现在可以考虑这个问题了。我猜测这是驱动层干的事儿。有没有点平行宇宙的意思？双缝干涉之所以出现了干涉条纹，是因为我们所在的世界和另一个平行宇宙世界的粒子发生了叠加！
接下来就继续穿越到驱动层一探究竟吧。