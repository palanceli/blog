---
layout: post
title:  "深度探索Binder（四）调用服务接口"
date:   2016-08-07 23:28:01 +0800
categories: Android
tags:   深度探索Binder
toc: true
comments: true
---
# 调用服务接口
前一篇博文讲的《查找服务》其实就是“调用服务接口”，因为服务的注册与查找正是ServiceManager提供的服务接口，尤其是查找服务，既有请求又有响应。在native层和驱动层已经走了非常完备的“调用服务接口”的流程。在这一篇中我们查漏补缺，仅探索前面没有涉及到的点。

## 获取ServiceManager VS 获取普通Binder的代理
Client端获取ServiceManager和获取普通Binder代理其实是一模一样的，这里的Client端是相对而言，通常所说的Client/Server是指Service的请求方和提供方，二者在请求ServiceManager服务的时候，又都是该服务的Client。
在讲注册服务[初始化sm](http://palanceli.github.io/blog/2016/08/06/2016/0806DissectingBinder2/#初始化sm)一节中，有如下代码：
``` c++
// frameworks/native/libs/binder/IServiceManager.cpp
// #33
sp<IServiceManager> defaultServiceManager()
{
    ... ...
    gDefaultServiceManager = interface_cast<IServiceManager>(
        ProcessState::self()->getContextObject(NULL));  
        ... ...
    return gDefaultServiceManager;
}
```
这是为了获取ServiceManager，在那一节中我们分析过`ProcessState::self()->getContextObject(NULL)`生成一个BpBinder(0)，`interface_cast<IServiceManager>()`把该对象交给BpServiceManager的构造函数产生一个BpServiceManager，再转型为IServiceManager。

再看普通Binder代理的获取方式：
``` c++
    // TestClient.cpp:16
    sp < IBinder > binder = sm->getService(String16("service.testservice"));
    sp<ITestService> cs = interface_cast < ITestService > (binder);
```
`sm->getService(...)`就是让驱动生成一个在本地唯一的整形数即handle，返回对象BpBinder(handle)，第二行把该对象交给BpTestService的构造函数，产生一个BpTestService，再转型为ITestService。

二者的不同之处仅在于ServiceManager的handle是约定好的0，而普通Binder的handle是由驱动层分配的。

## Client端如何把函数调用打包成数据
ServiceManager是怎么把函数调用打包成数据的？它的函数接口不多，定义在
``` c++
// frameworks/native/include/binder/IServiceManager.h30
class IServiceManager : public IInterface
{
public:
    DECLARE_META_INTERFACE(ServiceManager);
    ... ...
    virtual sp<IBinder>         getService( const String16& name) const = 0;
    virtual sp<IBinder>         checkService( const String16& name) const = 0;
    virtual status_t            addService( const String16& name,
                                            const sp<IBinder>& service,
                                            bool allowIsolated = false) = 0;
    virtual Vector<String16>    listServices() = 0;

    enum {
        GET_SERVICE_TRANSACTION = IBinder::FIRST_CALL_TRANSACTION,
        CHECK_SERVICE_TRANSACTION,
        ADD_SERVICE_TRANSACTION,
        LIST_SERVICES_TRANSACTION,
    };
};
```
四个虚函数就是ServiceManager提供的全部服务接口，每个函数对应一个枚举类型的变量，相当于给每个函数编了号。函数实现在
`frameworks/natvie/libs/binder/IServiceManager.cpp:126`。
每个函数把自己对应的编号以及参数塞到Parcel对象里，写入binder文件，数据到了服务端再按照同样的编号解析，找到对应函数并执行。

再来看客户端请求普通的服务接口：
``` c++
// TestClient.cpp
void BpTestService::test() {
    ... ...
    Parcel data, reply;
    data.writeInterfaceToken(ITestService::getInterfaceDescriptor());
    remote()->transact(TEST, data, &reply);
    ... ...
}
```
何其相似，TEST也是自定义的枚举变量，用来给每个函数编号。而且比较好的做法是只提供一份头文件，让Client端和Server端公用，这样才不容易产生歧义。

## Server端如何把数据包拆解成函数调用
其实在《深度探索Binder（二）注册服务》的[循环内做了什么](http://palanceli.github.io/blog/2016/08/06/2016/0806DissectingBinder2/#循环内做了什么？)已经讲了一半：客户端对Service的请求被封装成数据包，其中最重要的数据就是Binder的handle、请求接口的编号以及参数。该数据包在驱动层会被修改，主要是根据handle找到对应的`binder_node`，并把handle字段替换成影子对象——binder以及binder对象——cookie。到了Server端则直接拿cookie提领出Binder对象：
``` c++
// frameworks/native/libs/binder/IPCThreadState.cpp:947
status_t IPCThreadState::executeCommand(int32_t cmd)
{
    ... ...
    case BR_TRANSACTION:
        {
            binder_transaction_data tr;
            result = mIn.read(&tr, sizeof(tr));
            ... ...
            Parcel reply;
            ... ...
            if (tr.target.ptr) {
                sp<BBinder> b((BBinder*)tr.cookie);
                error = b->transact(tr.code, buffer, &reply, tr.flags);
            } else 
            ... ...
        }
        ... ...
    }
    ... ...
}
// frameworks/native/libs/binder/Binder.cpp:97
status_t BBinder::transact(
    uint32_t code, const Parcel& data, Parcel* reply, uint32_t flags)
{   // code     TEST
    data.setDataPosition(0);

    status_t err = NO_ERROR;
    switch (code) {
        case PING_TRANSACTION:
            reply->writeInt32(pingBinder());
            break;
        default:
            err = onTransact(code, data, reply, flags);
            break;
    }

    if (reply != NULL) {
        reply->setDataPosition(0);
    }

    return err;
}
```
`onTransact(...)`是一个虚函数：
``` c++
class BBinder : public IBinder
{
    ... ...
    virtual status_t    onTransact( uint32_t code,
                                    const Parcel& data,
                                    Parcel* reply,
                                    uint32_t flags = 0);
    ... ...
};
```

tr.cookie的值是在`addService`是添加的，它是在Server端`main()`函数中`new BnTestService()`的对象地址。所以在`IPCThreadState::executeCommand(...)`函数中尽管使用`BBinder`类型来提领，实际的内容仍然是个`BnTestService`对象。他继承自`BnInterface`，后者继承自`BBinder`，因此调用其虚函数`onTransact(...)`最终落地到`BnTestService::onTransact(...)`，该函数对定义在TestServer.cpp中，根据code的值调用对应的函数。

作为Binder机制的使用者来说，要写的代码其实很简单：
* 定义好服务接口以及编号。
* Server端定义服务的子类BnTestService，并覆盖虚函数`onTransact(...)`，实现每个服务接口。
* Client端定义服务的子类BpTestService，并实现每个服务接口的转发——将参数塞入Parcel，调用`remote()->transact(...)`把服务编号和参数发往Server端。

## 应用层的代码结构
我们的测试程序共四个文件：
* Test.h    提供Client和Server公用的ITestService接口定义以及函数编号枚举定义
* TestClient.cpp    Client端代码，定义BpTestService
* TestServer.cpp    Server端代码，定义BnTestService
* ITestService.cpp    定义Server端基类ITestService中与业务逻辑无关的函数，可以用一条宏IMPLEMENT_META_INTERFACE替代所有代码，但为了方便调试，我把宏展开了。

## testservice的调试
最后再补充一点关于调试的碎碎念，目前我还只会用gdb/gdbserver来调试，每次调试都有一些固定的步骤，我把它们记录下来每次拷贝/粘贴就好了。

### 前期的准备工作：
编译testservice：
`$ mmm external/testservice` 

启动模拟器：
`$ emulator&`   

把文件拷到模拟器的/data/local/tmp/testservice下：
``` bash
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestServer_intermediates/LINKED/TestServer /data/local/tmp/testservice    
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient /data/local/tmp/testservice
```
赋予可执行权限：
`$ adb shell chmod 755 /data/local/tmp/testservice/* `

### 调试Client端
调试Client端代码最好同时开启三个终端：
* 在模拟器上运行Server
`$ adb shell /data/local/tmp/testservice/TestServer`
* 在模拟器上通过gdbserver运行客户端
`$ adb shell gdbserver :1234 /data/local/tmp/testservice/TestClient`
* 在调试机上运行gdb
    - forward端口
    `$ adb forward tcp:1234 tcp:1234`
    - 启动gdb
    `$./prebuilts/gcc/darwin-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gdb out/debug/target/product/generic/obj/EXECUTABLES/TestClient_intermediates/LINKED/TestClient
    - target端口
    `(gdb) target remote :1234`
    - 调试吧
    ``` bash
(gdb) b main
Breakpoint 1 at 0xb6f321fc: file external/testservice/TestClient.cpp, line 14.
(gdb) c
Continuing.
... ...
Breakpoint 1, main () at external/testservice/TestClient.cpp:14
14  int main() {
(gdb) set solib-absolute-prefix out/debug/target/product/generic/symbols/
Reading symbols from out/debug/target/product/generic/symbols/system/bin/linker...done.
... ...
(gdb) b IPCThreadState.cpp:730
... ...
    ```

调试Server端和Client端没什么差别，只是需要用gdbserver跑Server程序。

### 调试ServiceManager
偶尔也需要调试ServiceManager，跟调Client/Server都不太一样，通常至少要同时开四个终端
* 在模拟器上运行Server
`$ adb shell /data/local/tmp/testservice/TestServer`
* 找到ServiceManager的pid，并用gdbserver启动
`$ adb shell ps |grep servicemanager`
`$ adb shell /data/local/tmp/gdbserver :1234 --attach <servicemanager pid> `
* 在调试机上运行gdb，第二个参数是端口号
`$ gdbclient <servicemanager pid> 1234`
* 在第四个终端上运行Client，触发ServiceManager中要调试的逻辑
`$ adb shell /data/local/tmp/testservice/TestClient`

也可以把一些反复、连续用到的命令写到gdb脚本中，在我的[debug.gdb](https://github.com/palanceli/androidex/blob/master/external-testservice/debug.gdb)中就是这类命令，把他们封装成函数。启动gdb后只需调用
`(gdb) source ../androidex/external-testservice/debug.gdb`
即可载入gdb脚本，然后直接敲入函数名如：
`(gdb) common`
即可直接执行。
