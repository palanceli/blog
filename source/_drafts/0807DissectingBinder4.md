---
layout: post
title:  "深度探索Binder（四）调用服务接口"
date:   2016-08-07 23:28:01 +0800
categories: Android
tags:   深度探索binder
toc: true
comments: true
---
# 调用服务接口
前一篇博文讲的《查找服务》其实就是“调用服务接口”，因为服务的注册与查找正是ServiceManager提供的服务接口，尤其是查找服务，既有请求又有响应。在native层和驱动层已经走了非常完备的“调用服务接口”的流程。在这一篇中我们查漏补缺，仅探索前面没有涉及到的点。

## 获取ServiceManager和获取普通Binder的代理
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

## 应用层的代码结构
我们的测试程序共四个文件：
* Test.h    提供Client和Server公用的ITestService接口定义以及函数编号枚举定义
* TestClient.cpp    Client端代码，定义BpTestService
* TestServer.cpp    Server端代码，定义BnTestService
* ITestService.cpp    定义Server端基类ITestService中与业务逻辑无关的函数，可以用一条宏IMPLEMENT_META_INTERFACE替代所有代码，但为了方便调试，我把宏展开了


