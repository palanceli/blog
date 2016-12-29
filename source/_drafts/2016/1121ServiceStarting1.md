---
layout: post
title: Service启动过程学习笔记（一）
date: 2016-11-21 23:59:58 +0800
categories: Android
tags: Service启动过程
toc: true
comments: true
---
当客户端通过startService(...)启动Service组件时，它调用的是ContextWrapper::startService(...)，接下来就以此函数为起点学习Service组件的启动。<!-- more -->
# Step1 ContextWrapper::startService(...)
``` java
public class ContextWrapper extends Context {
    Context mBase;  // mBase实际指向一个ContextImpl对象，用来描述所运行的上下文环境
... ...
// frameworks/base/core/java/android/content/ContextWrapper.java:580
    public ComponentName startService(Intent service) {
        return mBase.startService(service); // 🏁
    }
... ...
}
```
# Step2 ContextImpl::startService(...)
``` java
// frameworks/base/core/java/android/app/ContextImpl.java:1220
    public ComponentName startService(Intent service) {
        ... 
        return startServiceCommon(service, mUser); // 🏁
    }

// frameworks/base/core/java/android/app/ContextImpl.java:1236
    private ComponentName startServiceCommon(Intent service, UserHandle user) {
        try {
            validateServiceIntent(service);
            service.prepareToLeaveProcess();

            // getDefault()获得ActivityManagerService的代理对象
            // startService(...)向ActivityManagerService发送进程间通信请求，启动Service组件
            // mMainThread类型为ActivityThread，其getApplicationThread()
            // 函数获得当前进程ApplicationThread的Binder本地对象，将此对象传递给
            // ActivityManagerService以便它知道是谁请求启动Service组件
            ComponentName cn = ActivityManagerNative.getDefault().startService(
                mMainThread.getApplicationThread(), service, 
                service.resolveTypeIfNeeded(
                            getContentResolver()), getOpPackageName(), 
                            user.getIdentifier()); // 🏁
            ...
            return cn;
        } catch (RemoteException e) { ... }
    }
```
# Step3 ActivityManagerProxy::startService(...)
``` java
class ActivityManagerProxy implements IActivityManager
{
...
// frameworks/base/core/java/android/app/ActivityManagerNative.java:3670
    public ComponentName startService(IApplicationThread caller, Intent service,
            String resolvedType, String callingPackage, int userId) throws RemoteException
    {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        data.writeStrongBinder(caller != null ? caller.asBinder() : null);
        service.writeToParcel(data, 0);
        data.writeString(resolvedType);
        data.writeString(callingPackage);
        data.writeInt(userId);
        mRemote.transact(START_SERVICE_TRANSACTION, data, reply, 0);
        reply.readException();
        ComponentName res = ComponentName.readFromParcel(reply);
        data.recycle();
        reply.recycle();
        return res;
    }
...
}
```
它向ActivityManagerService发送一个类型为START_SERVICE_TRANSACTION的进程间通信请求。以上是在应用程序中执行，接下来转入ActivityManagerService中执行。
# Step4 ActivityManagerService
``` java
public final class ActivityManagerService extends ActivityManagerNative        implements Watchdog.Monitor, BatteryStatsImpl.BatteryCallback {
...
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:15763
    ComponentName startServiceInPackage(int uid, Intent service, String resolvedType,
            String callingPackage, int userId)
            throws TransactionTooLargeException {
        synchronized(this) {
            ...
            final long origId = Binder.clearCallingIdentity();
            ComponentName res = mServices.startServiceLocked(null, service,
                    resolvedType, -1, uid, callingPackage, userId); // 🏁
            Binder.restoreCallingIdentity(origId);
            return res;
        }
    }
...
}
```