---
layout: post
title: Service启动过程学习笔记（二）——进程内绑定Service组件
date: 2016-12-31 22:53:58 +0800
categories: Android学习笔记
tags: Service启动过程
toc: true
comments: true
---
进程内绑定Service组件是以客户端调用bindService(...)为起点，该函数的原型为：
`boolean bindService(Intent service, ServiceConnection conn,  
            int flags);`
当成功绑定后，conn的onServiceConnected(...)会被调用，以便客户端可以获得Service的接口。<!-- more -->
接下来就以父类成员函数ContextWrapper::bindService(...)为起点开始分析。
# Step1 ContextWrapper::bindService(...)
``` java
// frameworks/base/core/java/android/context/ContextWrapper.java:602
public boolean bindService(Intent service, ServiceConnection conn,
        int flags) {
    return mBase.bindService(service, conn, flags);
}
```
其中mBase指向一个ContextImpl对象。
# Step2 ContextImpl::bindService(...)
``` java
// frameworks/base/core/java/android/app/ContextImpl.java:1283
    public boolean bindService(Intent service, ServiceConnection conn,
            int flags) {
        warnIfCallingFromSystemProcess();
        return bindServiceCommon(service, conn, flags, Process.myUserHandle());
    }
    ...
    private boolean bindServiceCommon(Intent service, ServiceConnection conn, int flags,
            UserHandle user) {
        IServiceConnection sd;
        ...
        if (mPackageInfo != null) {
            // getOuterContext()返回的Context对象指向调用方的Activity组件
            // mMainThread.getHandler()返回mMainThread.mH，用来向主线程消息队列发送消息
            // 🏁将conn封装成一个实现了IServiceConnection接口的Binder对象
            sd = mPackageInfo.getServiceDispatcher(conn, getOuterContext(),
                    mMainThread.getHandler(), flags);
        } else ...
        validateServiceIntent(service);
        try {
            IBinder token = getActivityToken();
            ...
            service.prepareToLeaveProcess();
            // 🏁Step5将sd及service（是个Intent对象）发送给ActivityManagerService，以便
            // 它将Service组件启动起来。此处调用的是ActivityManagerService代理对象
            // 的成员函数bindService(...)
            int res = ActivityManagerNative.getDefault().bindService(
                mMainThread.getApplicationThread(), getActivityToken(), service,
                service.resolveTypeIfNeeded(getContentResolver()),
                sd, flags, getOpPackageName(), user.getIdentifier());
            ...
            return res != 0;
        } catch (RemoteException e) ...
    }
```
# Step3 ContextImpl::getServiceDispatcher(...)
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:977
    public final IServiceConnection getServiceDispatcher(ServiceConnection c,
            Context context, Handler handler, int flags) {
        synchronized (mServices) {
            LoadedApk.ServiceDispatcher sd = null;
            // 每个绑定过Service的Activity都以ServiceConnection为key保存在HashMap
            // 中，该HashMap再以Activity::context为key保存在mServices中，即：
            // <Activity::Context, <ServiceConnection, Activity> >
            ArrayMap<ServiceConnection, LoadedApk.ServiceDispatcher> map = mServices.get(context);
            if (map != null) {
                sd = map.get(c);
            }
            if (sd == null) {
                sd = new ServiceDispatcher(c, context, handler, flags);
                if (map == null) {
                    map = new ArrayMap<ServiceConnection, LoadedApk.ServiceDispatcher>();
                    mServices.put(context, map);
                }
                map.put(c, sd);
            } else {
                sd.validate(context, handler);
            }
            return sd.getIServiceConnection(); // 🏁
        }
    }
```
# Step4 LoadedApk.ServiceDispatcher::getIServiceConnection()
sd的类型为LoadedApk.ServiceDispatcher，其getIServiceConnection()函数返回数据成员mIServiceConnection，该成员是在ServiceDispatcher的构造函数中创建的：
``` java
public final class LoadedApk {
...
// frameworks/base/core/java/android/app/LoadedApk.java:1049
    static final class ServiceDispatcher {
        private final ServiceDispatcher.InnerConnection mIServiceConnection;
        // 当客户端C绑定Service组件时，LoadedApk会为它创建一个ServiceDispatcher对象
        // 其mContext指向C的Activity组件，
        // 其mConnection指向C内部的serviceConnection对象，
        // 其mActivityThread指向C所在进程的主线程Handler对象，即ActivityThread::mH
        private final ServiceConnection mConnection; // 与mContext关联的ServiceConnection对象
        private final Context mContext;         // 指向Activity组件
        private final Handler mActivityThread;  // 与mContext关联的Handler对象

        ...
        private static class InnerConnection extends IServiceConnection.Stub {
            final WeakReference<LoadedApk.ServiceDispatcher> mDispatcher;

            InnerConnection(LoadedApk.ServiceDispatcher sd) {
                mDispatcher = new WeakReference<LoadedApk.ServiceDispatcher>(sd);
            }
            ...
        }
...
// :1085
        ServiceDispatcher(ServiceConnection conn,
                Context context, Handler activityThread, int flags) {
            mIServiceConnection = new InnerConnection(this);
            ...
        }
...
// :1130
        IServiceConnection getIServiceConnection() {
            return mIServiceConnection;
        }
```
# Step5 ActivityManagerProxy::bindService(...)
``` java 
// frameworks/base/core/java/android/app/ActivityManagerNative.java:2619
class ActivityManagerProxy implements IActivityManager
{
...
// frameworks/base/core/java/android/app/ActivityManagerNative.java:3740
    public int bindService(IApplicationThread caller, IBinder token,
            Intent service, String resolvedType, IServiceConnection connection,
            int flags,  String callingPackage, int userId) throws RemoteException {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        data.writeStrongBinder(caller != null ? caller.asBinder() : null);
        data.writeStrongBinder(token);
        service.writeToParcel(data, 0);
        data.writeString(resolvedType);
        data.writeStrongBinder(connection.asBinder());
        data.writeInt(flags);
        data.writeString(callingPackage);
        data.writeInt(userId);
        mRemote.transact(BIND_SERVICE_TRANSACTION, data, reply, 0);
        reply.readException();
        int res = reply.readInt();
        data.recycle();
        reply.recycle();
        return res;
    }
...
}
```
此处通过代理对象向ActivityManagerService发送类型为BIND_SERVICE_TRANSACTION的请求，以上步骤均在客户端完成，接下来转入ActivityManagerService中执行。
# Step6 ActivityManagerService::bindService(...)
``` java
public final class ActivityManagerService extends ActivityManagerNative
...
    final ActiveServices mServices;
...
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:15973
    public int bindService(IApplicationThread caller, IBinder token, Intent service,
            String resolvedType, IServiceConnection connection, int flags, String callingPackage,
            int userId) throws TransactionTooLargeException {
        ...
        synchronized(this) {
            return mServices.bindServiceLocked(caller, token, service,
                    resolvedType, connection, flags, callingPackage, userId);
        }
    }
```
# Step7 ActiveServices::bindServiceLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:697
    int bindServiceLocked(IApplicationThread caller, IBinder token, Intent service,
            String resolvedType, IServiceConnection connection, int flags,
            String callingPackage, int userId) throws TransactionTooLargeException {
        ...
        // 得到请求service操作的进程
        final ProcessRecord callerApp = mAm.getRecordForAppLocked(caller);
        ...
        ActivityRecord activity = null;
        if (token != null) { // 得到请求service操作的activity
            activity = ActivityRecord.isInStackLocked(token);
            ...
        }
        ...
        ServiceLookupResult res =
            retrieveServiceLocked(service, resolvedType, callingPackage,
                    Binder.getCallingPid(), Binder.getCallingUid(), userId, true, callerFg);
        ...
        ServiceRecord s = res.record; // 得到即将被绑定的service组件

        ...
            // 一个service组件可能被同一个进程中多个Activity组件使用同一个
            // InnerConnection对象来绑定。因此ServiceRecord对象可能会对应多个
            // ConnectionRecord对象，他们被保存在一个列表中，该列表被保存在
            // ServiceRecord::connection所描述的HashMap中

            // 🏁
            AppBindRecord b = s.retrieveAppBindingLocked(service, callerApp);
            // 用这些数据组织成一个ConnectionRecord对象c，表示activity组件通过参数
            // connection绑定了s，且activity试运行在callerApp进程中的
            ConnectionRecord c = new ConnectionRecord(b, activity,
                    connection, flags, clientLabel, clientIntent);
            // connection是一个InnerConnection代理对象，此处获得其IBinder接口
            IBinder binder = connection.asBinder();
            // 查找是否存在以binder为key的列表
            ArrayList<ConnectionRecord> clist = s.connections.get(binder);
            if (clist == null) {
                clist = new ArrayList<ConnectionRecord>();
                s.connections.put(binder, clist); // 以binder为key保存
            }
            // 表示activity通过参数connection绑定了s所描述的Service组件
            clist.add(c);
            b.connections.add(c);
            ...
            if ((flags&Context.BIND_AUTO_CREATE) != 0) {
                ...
                // 🏁Step9启动service
                if (bringUpServiceLocked(s, service.getFlags(), callerFg, false) != null) {...}
            }
        ...
        return 1;
    }
```
# Step8 ServiceRecord::retrieveAppBindingLocked(...)
ServiceRecord::bindings中记录了绑定了此Service的所有进程对象，形式为：
<FilterComparison, IntentBindRecord>
``` java
final class ServiceRecord extends Binder {
...
    final ArrayMap<Intent.FilterComparison, IntentBindRecord> bindings
            = new ArrayMap<Intent.FilterComparison, IntentBindRecord>();
                            // All active bindings to the service.
...
// frameworks/base/services/core.java/com/android/server/am/ServiceRecord.java:363
    public AppBindRecord retrieveAppBindingLocked(Intent intent,
            ProcessRecord app) {
        // 根据intent创建FilterComparison对象
        Intent.FilterComparison filter = new Intent.FilterComparison(intent);
        IntentBindRecord i = bindings.get(filter); // 此key是否对应内容
        if (i == null) { // 如果不存在则创建
            i = new IntentBindRecord(this, filter);
            bindings.put(filter, i);
        }
        AppBindRecord a = i.apps.get(app); // 是否存在AppBindRecord对象
        if (a != null) { // 如果存在说明该进程已经绑定过intent描述的Service组件
            return a;    // 直接返回
        }               // 如果不存在，则创建后再返回
        a = new AppBindRecord(this, i, app);
        i.apps.put(app, a);
        return a;
    }
```
# Step9 ActiveServices::bringUpServiceLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1371
    private final String bringUpServiceLocked(ServiceRecord r, int intentFlags, boolean execInFg,
            boolean whileRestarting) throws TransactionTooLargeException {
        ...
        // 获得service的android:process属性
        final String procName = r.processName; 
        ProcessRecord app;

        if (!isolated) {
            app = mAm.getProcessRecordLocked(procName, r.appInfo.uid, false);
            ...
            // Service指定的进程已存在
            if (app != null && app.thread != null) {
                try {
                    app.addPackage(r.appInfo.packageName, r.appInfo.versionCode, mAm.mProcessStats);
                    realStartServiceLocked(r, app, execInFg);
                    return null;
                } ...
            }
        } else ...
        return null;
    }
```
# Step10 ActiveServices::realStartServiceLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1501
    private final void realStartServiceLocked(ServiceRecord r,
            ProcessRecord app, boolean execInFg) throws RemoteException {
        ...
        r.app = app;
        ...
        // 表示r是在app所描述的进程中启动的
        final boolean newService = app.services.add(r);
        ...
        boolean created = false;
        try {
            ...
            // 🏁 app.thread是一个类型为ApplicationThreadProxy的Binder代理对象，
            // 它指向app所在进程中的ApplicationThread对象。继续请求启动service。
            app.thread.scheduleCreateService(r, r.serviceInfo,
                    mAm.compatibilityInfoForPackageLocked(r.serviceInfo.applicationInfo),
                    app.repProcState);
            ...
        } catch (DeadObjectException e) ...
        // 🏁Step15将service组件和调用者activity组件连接起来
        requestServiceBindingsLocked(r, execInFg);

        ...
    }
```
# Step11 ApplicationThreadProxy.scheduleCreateService(...)
可参见[Service启动过程学习笔记（一）之Step16](http://palanceli.com/2016/11/21/2016/1121ServiceStarting1/#Step16-ApplicationThreadProxy-scheduleCreateService-…)
它向客户端所在进程发送一个SCHEDULE_CREATE_SERVICE_TRANSACTION请求。以上步骤都是在ActivityManagerService中执行，接下来将转入客户端。
# Step12 ActivityThread::scheduleCreateService(…)
# Step13 ActivityThread::handleMessage(…)
# Step14 ActivityThread::handleCreateService(…)
从Step12 到Step14可参见[Service启动过程学习笔记（一）之Step17~19](http://palanceli.com/2016/11/21/2016/1121ServiceStarting1/#Step17-ActivityThread-scheduleCreateService-…)
之后便是执行客户端service的onCreate函数。

# Step15 ActiveServices::requestServiceBindingsLocked(...)
承接Step11。
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1491
    // 参数r描述已经启动起来的service组件
    private final void requestServiceBindingsLocked(ServiceRecord r, boolean execInFg)
            throws TransactionTooLargeException {
        // 在其bindings中保存了一系列IntentBindRecord对象，用来描述被绑定service的进程
        for (int i=r.bindings.size()-1; i>=0; i--) {
            IntentBindRecord ibr = r.bindings.valueAt(i);
            if (!requestServiceBindingLocked(r, ibr, execInFg, false)) {
                break;
            }
        }
    }
```
# Step16 ActiveServices::requestServiceBindingLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:1165
    private final boolean requestServiceBindingLocked(ServiceRecord r, IntentBindRecord i,
            boolean execInFg, boolean rebind) throws TransactionTooLargeException {
        ...
        // 是否要将r重新绑定到i中
        if ((!i.requested || rebind) && i.apps.size() > 0) {
            try {
                ...
                // 再讲r绑定到i之前，首先要获得这个service组件内部的binder本地对象，
                // 以便进程可以通过它来获得要绑定的service组件的访问接口
                r.app.thread.scheduleBindService(r, i.intent.getIntent(), rebind,
                        r.app.repProcState);// 🏁请求r返回其内部的binder本地对象
                // 表示i已经接收到r返回的binder本地对象，以免以后重复请求
                if (!rebind) { 
                    i.requested = true;
                }
                i.hasBound = true;
                i.doRebind = false;
            } catch (TransactionTooLargeException e) ...
        }
        return true;
    }
```
# Step17 ApplicationThreadProxy::scheduleBindService(...)
``` java
// frameworks/base/core/java/android/app/ApplicationThreadNative.java:937
    public final void scheduleBindService(IBinder token, Intent intent, boolean rebind,
            int processState) throws RemoteException {
        Parcel data = Parcel.obtain();
        data.writeInterfaceToken(IApplicationThread.descriptor);
        data.writeStrongBinder(token);
        intent.writeToParcel(data, 0);
        data.writeInt(rebind ? 1 : 0);
        data.writeInt(processState);
        mRemote.transact(SCHEDULE_BIND_SERVICE_TRANSACTION, data, null,
                IBinder.FLAG_ONEWAY);
        data.recycle();
    }
```
此处向客户端进程发送一个类型为SCHEDULE_BIND_SERVICE_TRANSACTION的进程间通信请求。以上步骤是在AvtivityManagerService中执行的，接下来将转入客户端执行。
# Step18 ApplicationThread::scheduleBindService(...)
``` java
// frameworks/base/core/java/android/app/ActivityThread.java:729
        public final void scheduleBindService(IBinder token, Intent intent,
                boolean rebind, int processState) {
            updateProcessState(processState, false);
            // 将token的service组件信息封装成BinderServiceData对象
            BindServiceData s = new BindServiceData();
            s.token = token; 
            s.intent = intent;
            s.rebind = rebind;

            ...
            sendMessage(H.BIND_SERVICE, s);
        }
```
# Step19 ApplicationThread::handleMessage(...)
``` java
        public void handleMessage(Message msg) {
...
// frameworks/base/core/java/android/app/ActivityThread.java:1430
                case BIND_SERVICE:
                    ...
                    handleBindService((BindServiceData)msg.obj);
                    ...
                    break;
...
```
# Step20 ApplicationThread::handleBindService(...)
``` java
// frameworks/base/core/java/android/app/ActivityThread.java:2894
    private void handleBindService(BindServiceData data) {
        // data.token指向Binder代理对象，指向ServiceRecord对象，当service组件
        // 和客户端在同一进程时，此对象即位于客户端的service组件。前面Step14中，
        // Service组件在客户端进程启动后，会将自己保存在ActivityThread::mService
        // 中，并以data.token为key，此处将它取出。
        Service s = mServices.get(data.token);
        ...
        if (s != null) {
            try {
                ...
                try {
                    if (!data.rebind) {
                        // 调用service的onBind(...)获得其内部的Binder本地对象
                        IBinder binder = s.onBind(data.intent);
                        // 🏁将此对象传递给ActivityManagerService
                        ActivityManagerNative.getDefault().publishService(
                                data.token, data.intent, binder);
                    } else ...
                } ...
            } ...
        }
    }
```
# Step21 ActivityManagerProxy::publishService(...)
``` java
// frameworks/base/core/java/android/app/ApplicationThreadNative.java:3775
    public void publishService(IBinder token,
            Intent intent, IBinder service) throws RemoteException {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        data.writeStrongBinder(token);
        intent.writeToParcel(data, 0);
        data.writeStrongBinder(service);
        mRemote.transact(PUBLISH_SERVICE_TRANSACTION, data, reply, 0);
        reply.readException();
        data.recycle();
        reply.recycle();
    }
```
向ActivityManagerService发送一个类型为PUBLISH_SERVICE_TRANSACTION的进程间通信请求。以上是在客户端中执行，接下来将转入ActivityManagerService中。
# Step22 ActivityManagerService::publishService(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:15999
    // token描述客户端请求绑定的service组件
    // 客户端通过intent向ActivityManagerService请求绑定service组件
    // service指向service组件内部的一个binder本地对象
   public void publishService(IBinder token, Intent intent, IBinder service) {
        ...
        synchronized(this) {
            ...
            mServices.publishServiceLocked((ServiceRecord)token, intent, service);
        }
    }
```
# Step23 ActiveServices::publishServiceLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActiveServices.java:867
    void publishServiceLocked(ServiceRecord r, Intent intent, IBinder service) {
        final long origId = Binder.clearCallingIdentity();
        try {
            ...
            if (r != null) {
                Intent.FilterComparison filter
                        = new Intent.FilterComparison(intent);
                IntentBindRecord b = r.bindings.get(filter);
                // b.received描述r是否已经将其内部的binder本地对象传递给
                // ActivitManagerService了
                if (b != null && !b.received) {
                    b.binder = service;
                    b.requested = true;
                    b.received = true;
                    // 每个需要绑定r的Activity组件都使用一个ConnectionRecord对象
                    // 来描述。不同的Activity可能会使用相同的InnerConnection对象
                    // 来绑定Service组件，因此ActivityManagerService会把这些使用
                    // 相同InnerConnection对象的ConnectionRecord对象放到同一个列
                    // 表中。此处获得此列表
                    for (int conni=r.connections.size()-1; conni>=0; conni--) {
                        ArrayList<ConnectionRecord> clist = r.connections.valueAt(conni);
                        for (int i=0; i<clist.size(); i++) {
                            ConnectionRecord c = clist.get(i);
                            ...
                            try {
                                // conn引用了InnerConnection的Binder本地对象，该
                                // 对象用来连接一个Service组件和一个Activity组件。
                                // 此处调用客户端所使用的一个InnerConnection对象
                                // 的成员函数connected(...)来连接service组件。    
                                c.conn.connected(r.name, service);
                            } catch (Exception e) ...
                        }
                    }
                }
                ...
            }
        } ...
    }
```
以上步骤是在ActivityManagerService中执行的，接下来将转入客户端程序。
# Step24 LoadedApk::ServiceDispatcher::connected(...)
``` java
public final class LoadedApk {
...
// frameworks/base/core/java/android/app/LoadedApk.java:1048
    static final class ServiceDispatcher {
        ...
        private static class InnerConnection extends IServiceConnection.Stub {
            ...
            public void connected(ComponentName name, IBinder service) throws RemoteException {
                LoadedApk.ServiceDispatcher sd = mDispatcher.get();
                if (sd != null) {
                    sd.connected(name, service);
                }
            }
        }
```
# Step26 LoadedApk::ServiceDispatcher::connected(...)
``` java
public final class LoadedApk {
...    
    static final class ServiceDispatcher {
... 
// frameworks/base/core/java/android/app/LoadedApk.java:1146
        public void connected(ComponentName name, IBinder service) {
            if (mActivityThread != null) {
                // 封装成RunConnection消息，并将此消息发送到客户端主线程消息队列。
                // 该消息最终在RunConnection::run中被处理。
                mActivityThread.post(new RunConnection(name, service, 0));
            } else ...
        }
```
ServiceDispatcher::mActivityThread指向与调用端Activity相关联的Handler对象，用来向调用端的主线程消息队列发送消息。
# Setp27 LoadedApk::ServiceDispatcher::RunConnection::run()
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:1231
        private final class RunConnection implements Runnable {
            RunConnection(ComponentName name, IBinder service, int command) {
                mName = name;
                mService = service;
                mCommand = command;
            }

            public void run() {
                if (mCommand == 0) {
                    doConnected(mName, mService); // 🏁
                } else ...
            }
```
# Step28 LoadedApk::ServiceDispatcher::
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:1175
        public void doConnected(ComponentName name, IBinder service) {
            ...
            // If there is a new service, it is now connected.
            if (service != null) {
                // mConnection指向客户端内部成员变量serviceConnection所描述的
                // service对象，因此此处实际调用了客户端的serviceConnection的
                // 成员函数onServiceConnected(...)以便将service所描述的本地
                // binder对象传递给客户端。
                mConnection.onServiceConnected(name, service);
            }
        }
```
客户端获得了service组件的访问接口之后，就可以直接使用该接口请求服务了。

