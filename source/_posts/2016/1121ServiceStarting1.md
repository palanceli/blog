---
layout: post
title: Service启动过程学习笔记（一）——跨进程启动Service组件
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
    // 由此可见，当进程启动完成后，ActivityManagerService会优先处理Activity组件然后
    // 再处理Service组件，这是因为前者需要用户交互，后者不需要。
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
        try { // 检查保存在mPendingService中的service组件是否需要在app中启动
            for (int i=0; i<mPendingServices.size(); i++) {
                // 如果需要启动，从mPendingService中取出并删除
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
# Step15 ActiveServices::realStartServiceLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1501
    private final void realStartServiceLocked(ServiceRecord r,
            ProcessRecord app, boolean execInFg) throws RemoteException {
        ...
        r.app = app;
        ...
        try {
            ...
            // app.thread是类型为ApplicationThreadProxy的Binder代理对象
            // 请求新进程将r所描述的service组件启动起来
            app.thread.scheduleCreateService(r, r.serviceInfo,
                    mAm.compatibilityInfoForPackageLocked(r.serviceInfo.applicationInfo),
                    app.repProcState);
            ...
        } catch ...
        ...
    }
```
# Step16 ApplicationThreadProxy::scheduleCreateService(...)
``` java
public abstract class ApplicationThreadNative extends Binder
        implements IApplicationThread {
// frameworks/base/core/java/android/app/ApplicationThreadNative.java:919
    public final void scheduleCreateService(IBinder token, ServiceInfo info,
            CompatibilityInfo compatInfo, int processState) throws RemoteException {
        Parcel data = Parcel.obtain();
        data.writeInterfaceToken(IApplicationThread.descriptor);
        data.writeStrongBinder(token);
        info.writeToParcel(data, 0);
        compatInfo.writeToParcel(data, 0);
        data.writeInt(processState);
        try {
            // 向新建进程发送SCHEDULE_CREATE_SERVICE_TRANSACTION请求
            mRemote.transact(SCHEDULE_CREATE_SERVICE_TRANSACTION, data, null,
                    IBinder.FLAG_ONEWAY);
        } catch (TransactionTooLargeException e) ...
        data.recycle();
    }
...
}
```
以上步骤是在ActivityManagerService中进行，接下来转入新建进程中。
# Step17 ActivityThread::scheduleCreateService(...)
``` java
public final class ActivityThread {
    private class ApplicationThread extends ApplicationThreadNative {
...
// frameworks/base/core/java/android/app/ApplicationThreadNative.java:718
    public final void scheduleCreateService(IBinder token,
            ServiceInfo info, CompatibilityInfo compatInfo, int processState) {
        updateProcessState(processState, false);
        CreateServiceData s = new CreateServiceData();
        s.token = token;
        s.info = info;
        s.compatInfo = compatInfo;

        sendMessage(H.CREATE_SERVICE, s);
    }
    ...
    }
    ...
}
```
此处把“要启动Service组件”信息封装成一个CreateServiceData对象，再通过sendMessage发送到消息队列，可参考[Activity启动过程学习笔记（二）之Step39](http://palanceli.com/2016/10/27/2016/1027ActivityStarting2/#Step39-ActivityThread-scheduleLaunchActivity-…)

# Step18 ActivityThread::handleMessage(…)
``` java
// frameworks/base/core/java/android/app/ActivityThread.java:1335
    public void handleMessage(Message msg) {
        ... ...
        switch (msg.what) {
            ...
            case CREATE_SERVICE:
                ...
                handleCreateService((CreateServiceData)msg.obj);
                ...
                break;
        ...
    }...
}
```
# Step19 ActivityThread::handleCreateService(...)
``` java
public final class ActivityThread {
...
// frameworks/base/core/java/android/app/ActivityThread.java:2849
    private void handleCreateService(CreateServiceData data) {
        ...
        // 描述即将启动的Service组件所在的应用程序的LoadedApk对象，
        // 通过它可以访问应用程序的资源
        LoadedApk packageInfo = getPackageInfoNoCheck(
                data.info.applicationInfo, data.compatInfo);
        Service service = null;
        try {
            // 获得类加载器
            java.lang.ClassLoader cl = packageInfo.getClassLoader();
            // 将data所描述的Service组件加载到内存
            service = (Service) cl.loadClass(data.info.name).newInstance();
        } catch (Exception e) ...
        }

        try {
            ...
            // context作为service运行的上下文环境，通过它可以访问到特定的
            // 应用程序资源，及启动其他应用程序组件
            ContextImpl context = ContextImpl.createAppContext(this, packageInfo);
            context.setOuterContext(service);

            // 描述service所属的应用程序
            Application app = packageInfo.makeApplication(false, mInstrumentation);
            // 初始化service对象
            service.attach(context, this, data.info.name, data.token, app,
                    ActivityManagerNative.getDefault());
            service.onCreate(); // 调用它的onCreate()成员函数
            // 以token为关键字，把service保存在ActivityThread::mServices中
            mServices.put(data.token, service); 
            try {
                ActivityManagerNative.getDefault().serviceDoneExecuting(
                        data.token, SERVICE_DONE_EXECUTING_ANON, 0, 0);
            } catch (RemoteException e) ...
        } catch (Exception e) ...
    }
```
至此，Service的启动过程就分析完了。它和Activity的启动过程非常相似。
那天老板问我Android下的Activity和Service如果类比到Windows下的概念，有没有可比物，我的回答是Window。Android弱化了进程的概念以及进程之间的边缘。程序员接触到的是四大组件，这些组件是进程创建后，根据manifest描述再创建的对象，组件的创建和销毁均由进程在其生命周期内完成。Windows下也一样，进程创建后通过CreateWindow(...)创建窗体，窗体销毁后进程可能还在。
Android通过Binder机制弱化了进程之间的边缘，启动其它组件、发送数据可能是跨进程的，但在实现层面上和进程内没有差别，这和Windows就有差别了，首先Windows没有类似Binder的支持，稍微有点相似的是窗体消息，可以跨进程拿到窗体句柄，并发送消息，但并非所有消息都支持进程间发送。
