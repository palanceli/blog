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
# Step4 ActivityManagerService::startService(...)
``` java
public final class ActivityManagerService extends ActivityManagerNative        implements Watchdog.Monitor, BatteryStatsImpl.BatteryCallback {
...
    final ActiveServices mServices;
...
    // frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:15737
    public ComponentName startService(IApplicationThread caller, Intent service,
            String resolvedType, String callingPackage, int userId)
            throws TransactionTooLargeException {
        ...
        synchronized(this) {
            final int callingPid = Binder.getCallingPid();
            final int callingUid = Binder.getCallingUid();
            final long origId = Binder.clearCallingIdentity();
            // 🏁 继续执行启动Service组件操作
            ComponentName res = mServices.startServiceLocked(caller, service,
                    resolvedType, callingPid, callingUid, callingPackage, userId);
            Binder.restoreCallingIdentity(origId);
            return res;
        }
    }
...
}
```
# Step5 ActiveService::startServiceLocked(...)
``` java
    // frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:306
    ComponentName startServiceLocked(IApplicationThread caller, Intent service, String resolvedType,
            int callingPid, int callingUid, String callingPackage, int userId)
            throws TransactionTooLargeException {
        ...
        // 每个Service组件在ActivityManagerService中都有一个ServiceRecord来描述，
        // 此处获得service对应的ServiceRecord对象
        ServiceLookupResult res =
            retrieveServiceLocked(service, resolvedType, callingPackage,
                    callingPid, callingUid, userId, true, callerFg);
        ...
        ServiceRecord r = res.record; // 获得与res对应的ServiceRecord   
        ...
        // 🏁
        return startServiceInnerLocked(smap, service, r, callerFg, addToStarting);
    }
```
# Step6 ActiveService::startServiceInnerLocked(...)
``` java
    // frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:423
    ComponentName startServiceInnerLocked(ServiceMap smap, Intent service, ServiceRecord r,
            boolean callerFg, boolean addToStarting) throws TransactionTooLargeException {
        ...
        // 🏁 继续启动r所描述的service组件
        String error = bringUpServiceLocked(r, service.getFlags(), callerFg, false);
        ... 
        return r.name;
    }
```
# Step7 ActiveService::bringUpServiceLocked(...)
``` java
public final class ActiveServices {
...
final ActivityManagerService mAm;
...
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1371
    private final String bringUpServiceLocked(ServiceRecord r, int intentFlags, boolean execInFg,
            boolean whileRestarting) throws TransactionTooLargeException {
        ...
        final String procName = r.processName; //获取android:process属性
        ProcessRecord app;
        ...
            // 根据属性值查找是否已经有ProcessRecord对象与之对应，即进程是否存在
            app = mAm.getProcessRecordLocked(procName, r.appInfo.uid, false);
            ...
            if (app != null && app.thread != null) { //该进程已经存在
                try {
                    app.addPackage(r.appInfo.packageName, r.appInfo.versionCode, mAm.mProcessStats);
                    // 启动service组件
                    realStartServiceLocked(r, app, execInFg);
                    return null;
                } catch (TransactionTooLargeException e) {...}
                ...
            }
        ...
        // Not running -- get it started, and enqueue this service record
        // to be executed when the app comes up.
        if (app == null) {
            // 🏁 启动进程
            if ((app=mAm.startProcessLocked(procName, r.appInfo, true, intentFlags,
                    "service", r.name, false, isolated, false)) == null) {
                ...
                bringDownServiceLocked(r);
                return msg;
            }
            ...
        }
        ...
        return null;
    }
```
mAm的类型是ActivityManagerService。
# Step8 ActivityManagerService::startProcessLocked(...)
进入函数`ActivityManagerService::startProcessLocked(...)`可参见[Activity启动过程学习笔记（二）之Step30](http://palanceli.com/2016/10/27/2016/1027ActivityStarting2/#Step30-ActivityManagerService-startProcessLocked-…)，它最终调用到Process类的静态成员函数start(...)创建新进程，这个新进程以ActivityThread类的静态成员函数main(...)为入口。

以上都是在ActivityManagerService中执行的，接下来转入新进程中执行，可参见[Activity启动过程学习笔记（二）之Step31、Step32、Step33](http://palanceli.com/2016/10/27/2016/1027ActivityStarting2/#Step31-ActivityThread-main-…)。
在ActivityThread::main(...)。
# Step9 ActivityThread::main(…)
该函数中会在新进程中创建ActivityThread对象和ApplicationThread对象。
# Step10 ActivityThread::attach(…)
# Step11 ActivityManagerProxy::attachApplication(…)
通过ActivityThread::attach(…)调用ActivityManagerProxy::attachApplication(...)，会向ActivityManagerService发出类型为ATTACH_APPLICATION_TRANSACTION的进程间通信请求，并将前面创建的ApplicationThread对象传递给ActivityManagerService，以便和新进程进行Binder通信。接下来将转回ActivityManagerService处理ATTACH_APPLICATION_TRANSACTION请求。

# Step12 ActivityManagerService::attachApplication(…)
参照[Activity启动过程学习笔记（二）之Step34](http://palanceli.com/2016/10/27/2016/1027ActivityStarting2/#Step34-ActivityManagerService-attachApplication-…)，该函数用来处理ATTACH_APPLICATION_TRANSACTION请求。

# Step13 ActivityManagerService::attachApplicationLocked(…)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:6016
private final boolean attachApplicationLocked(IApplicationThread thread,
        int pid) {
    // pid为将要创建的进程PID，前面曾以此为关键字将ProcessRecord保存到
    // mPidSelfLocked中，此处先根据pid将它取出
    ...
    ProcessRecord app;
    if (pid != MY_PID && pid >= 0) {
        synchronized (mPidsSelfLocked) {
            app = mPidsSelfLocked.get(pid);
        }
    } 
    ...// 进程已经起来，对app做初始化
    // thread指向ApplicationThread代理对象，以便ActivityManagerService通过此对象
    // 和新创建的进程通信
    app.makeActive(thread, mProcessStats);
    app.curAdj = app.setAdj = -100;
    app.curSchedGroup = app.setSchedGroup = Process.THREAD_GROUP_DEFAULT;
    app.forcingToForeground = null;
    updateProcessForegroundLocked(app, false, false);
    app.hasShownUi = false;
    app.debugging = false;
    app.cached = false;
    app.killedByAm = false;

    // 删除此消息，因为新的应用程序已经在规定的时间内启动起来了
    mHandler.removeMessages(PROC_START_TIMEOUT_MSG, app);

    boolean normalMode = mProcessesReady || isAllowedWhileBooting(app.info);
    List<ProviderInfo> providers = normalMode ? generateApplicationProvidersLocked(app) : null;

    ...

    // See if the top visible activity is waiting to run in this process...
    if (normalMode) {
        try {
            // 请求进程启动一个Activity组件
            if (mStackSupervisor.attachApplicationLocked(app)) {
                didSomething = true;
            }
        } ...
    }

    // Find any services that should be running in this process...
    if (!badApp) {
        try { // 查找即将启动的进程中是否有service存在
            didSomething |= mServices.attachApplicationLocked(app, processName);
        } ...
    }
    ...
    return true;
}
```
mServices的类型为ActiveServices。
# Step14 ActiveServices::attachApplicationLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:2035
boolean attachApplicationLocked(ProcessRecord proc, String processName)
        throws RemoteException {
    boolean didSomething = false;
    // Collect any services that are waiting for this process to come up.
    if (mPendingServices.size() > 0) {
        ServiceRecord sr = null;
        try {
            for (int i=0; i<mPendingServices.size(); i++) {
                sr = mPendingServices.get(i);
                if (proc != sr.isolatedProc && (proc.uid != sr.appInfo.uid
                        || !processName.equals(sr.processName))) {
                    continue;
                }

                mPendingServices.remove(i);
                i--;
                proc.addPackage(sr.appInfo.packageName, sr.appInfo.versionCode,
                        mAm.mProcessStats);
                // 🏁 启动service
                realStartServiceLocked(sr, proc, sr.createdFromFg);
                didSomething = true;
                ...
            }
        } ...
    }
    ...
    return didSomething;
}
```


