---
layout: post
title: 广播机制学习笔记（一）——BroadcastReceiver的注册
date: 2017-01-01 22:23:45 +0800
categories: Android学习笔记
tags: 广播机制
toc: true
comments: true
---
广播的使用分两个环节：注册和发送/接收。首先完成注册，才能接收到广播，接下来先研究注册环节。<!-- more -->

客户端通过调用registerReceiver(...)来将一个广播接收者注册到ActivityManagerService中，该函数来自ContextWrapper类。

# Step1 ContextWrapper::registerReceiver(...)

``` java
// frameworks/base/core/java/android/app/ContextImpl.java:1145
    public Intent registerReceiver(BroadcastReceiver receiver, IntentFilter filter) {
        return registerReceiver(receiver, filter, null, null);
    }

    public Intent registerReceiver(BroadcastReceiver receiver, IntentFilter filter,
            String broadcastPermission, Handler scheduler) {
        // getOuterContext()返回调用者所在的Activity组件
        return registerReceiverInternal(receiver, getUserId(),
                filter, broadcastPermission, scheduler, getOuterContext());
    }
    ...
    private Intent registerReceiverInternal(BroadcastReceiver receiver, int userId,
            IntentFilter filter, String broadcastPermission,
            Handler scheduler, Context context) {
        IIntentReceiver rd = null;
        if (receiver != null) {
            if (mPackageInfo != null && context != null) {
                if (scheduler == null) {
                    // mMainThread描述当前进程
                    // getHandler()返回Handler对象，用来向主线程消息队列发送消息
                    scheduler = mMainThread.getHandler();
                }
                // 🏁将receiver封装成实现了IIntentReceiver接口的Binder本地对象=>rd
                rd = mPackageInfo.getReceiverDispatcher(
                    receiver, context, scheduler,
                    mMainThread.getInstrumentation(), true);
            } ...
        }
        try { 
            // 🏁Step4 将rd及filter发送给ActivityManagerService，以便它将rd
            // 注册在其内部，并将filter描述的广播转发给他处理
            return ActivityManagerNative.getDefault().registerReceiver(
                    mMainThread.getApplicationThread(), mBasePackageName,
                    rd, filter, broadcastPermission, userId);
        } catch (RemoteException e) ...
    }
```
# Step2 LoadedApk::getReceiverDispatcher(...)
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:706
    public IIntentReceiver getReceiverDispatcher(BroadcastReceiver r,
            Context context, Handler handler,
            Instrumentation instrumentation, boolean registered) {
        synchronized (mReceivers) {
            LoadedApk.ReceiverDispatcher rd = null;
            ArrayMap<BroadcastReceiver, LoadedApk.ReceiverDispatcher> map = null;
            if (registered) {
                map = mReceivers.get(context);
                if (map != null) {
                    rd = map.get(r);
                }
            }
            if (rd == null) {
                // 保存注册它的Activity组件信息
                rd = new ReceiverDispatcher(r, context, handler,
                        instrumentation, registered);
                if (registered) {
                    if (map == null) { // 以context为key保存到mReceivers
                        map = new ArrayMap<BroadcastReceiver, LoadedApk.ReceiverDispatcher>();
                        mReceivers.put(context, map);
                    }
                    // 将被注册的广播接收者r与注册它的Activity组件rd关联起来
                    map.put(r, rd);
                }
            } else {
                rd.validate(context, handler);
            }
            rd.mForgotten = false;
            return rd.getIIntentReceiver(); // 🏁
        }
    }
```
# Step3 LoadedApk.ReceiverDispatcher::getIIntentReceiver()
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:80
public final class LoadedApk {
// :786
    static final class ReceiverDispatcher {
        // ④ 类型定义于此
        final static class InnerReceiver extends IIntentReceiver.Stub {
            final WeakReference<LoadedApk.ReceiverDispatcher> mDispatcher;
...
            InnerReceiver(LoadedApk.ReceiverDispatcher rd, boolean strong) {
                mDispatcher = new WeakReference<LoadedApk.ReceiverDispatcher>(rd);
                ...
            }
            ...
        }
    ...
// :827
    final IIntentReceiver.Stub mIIntentReceiver; // ②定义于此
    final BroadcastReceiver mReceiver; // 与该Activity组件关联的BroadcastReceiver
    final Context mContext;            // 指向调用者所在的Activity组件
    final Handler mActivityThread;     // 与该Activity组件关联的Handler对象
    ...
    ReceiverDispatcher(BroadcastReceiver receiver, Context context,
            Handler activityThread, Instrumentation instrumentation,
            boolean registered) {
        ...
        // ③在此处初始化
        mIIntentReceiver = new InnerReceiver(this, !registered);
        mReceiver = receiver;
        mContext = context;
        mActivityThread = activityThread;
        ...
    }
    ...
// :944
    IIntentReceiver getIIntentReceiver() {
        return mIIntentReceiver; // ① 返回值
    }
```
`LoadedApk.ReceiverDispatcher::getIIntentReceiver()`的返回值即`LoadedApk.ReceiverDispatcher::mIIntentReceiver`。该值的定义、初始化在代码中用①②③④标出。

# Step4 ActivityManagerProxy::registerReceiver(...)
回到Step1中ContextWrapper::registerReceiverInternal(...)，在创建完IIntentReceiver对象rd后，调用ActivityManagerNative.getDefault().registerReceiver(...)继续完成注册。ActivityManagerNative.getDefault()返回的是ActivityManagerService的本地代理对象。
``` java
// frameworks/base/core/java/android/app/ActivityManagerNative.java:2998
    public Intent registerReceiver(IApplicationThread caller, String packageName,
            IIntentReceiver receiver,
            IntentFilter filter, String perm, int userId) throws RemoteException
    {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        data.writeStrongBinder(caller != null ? caller.asBinder() : null);
        data.writeString(packageName);
        data.writeStrongBinder(receiver != null ? receiver.asBinder() : null);
        filter.writeToParcel(data, 0);
        data.writeString(perm);
        data.writeInt(userId);
        mRemote.transact(REGISTER_RECEIVER_TRANSACTION, data, reply, 0);
        reply.readException();
        Intent intent = null;
        int haveIntent = reply.readInt();
        if (haveIntent != 0) {
            intent = Intent.CREATOR.createFromParcel(reply);
        }
        reply.recycle();
        data.recycle();
        return intent;
    }
```
此处向ActivityManagerService发送一个REGISTER_RECEIVER_TRANSACTION请求，以上都是在客户端进程中执行的，接下来将转入ActivityManagerService中执行。

# ActivityManagerService::registerReceiver(...)
``` java
// frameworks/base/core/java/com/android/server/am/ActivityManagerService.java:16208
    public Intent registerReceiver(IApplicationThread caller, String callerPackage,
            IIntentReceiver receiver, IntentFilter filter, String permission, int userId) {
        ...
        synchronized(this) {
            if (caller != null) {
                // 描述正在祖册BroadcastReceiver的Activity组件所在的进程
                callerApp = getRecordForAppLocked(caller);
                ...
            } 
            ...
        }

        ArrayList<Intent> allSticky = null;
        if (stickyIntents != null) {
            final ContentResolver resolver = mContext.getContentResolver();
            // Look for any matching sticky broadcasts...
            for (int i = 0, N = stickyIntents.size(); i < N; i++) {
                Intent intent = stickyIntents.get(i);
                // If intent has scheme "content", it will need to acccess
                // provider that needs to lock mProviderMap in ActivityThread
                // and also it may need to wait application response, so we
                // cannot lock ActivityManagerService here.
                if (filter.match(resolver, intent, true, TAG) >= 0) {
                    if (allSticky == null) {
                        allSticky = new ArrayList<Intent>();
                    }
                    allSticky.add(intent);
                }
            }
        }

    // Activity组件注册一个BroadcastReceiver并不是将该Reciever注册到
    // ActivityManagerService中，而是注册与他关联的InnerReceiver对象。
    // ActivityManagerService接收到广播时，会根据该广播类型在内部找到对应的
    // InnerReceiver对象，再根据此对象将广播发送给对应的BroadcastReceiver

    // 在ActivityManagerService中使用BroadcastFilter来描述广播接收者，
    // BroadcastFilter是根据InnerReceiver对象和要接收到的广播类型而创建出来。
    // 在一个进程的不同Activity可能使用同一个InnerReceiver来注册不同的广播接收者，
    // ActivityManagerService使用一个ReceiverList来保存这些使用了相同InnserReceiver
    // 对象来注册的广播接收者，并以他们所使用的InnerReceiver为key。

        // 如果ActivityManagerService内部存在与filter对应的黏性广播，则将allSticky
        // 中第一个黏性广播取出来
        // The first sticky in the list is returned directly back to the client.
        Intent sticky = allSticky != null ? allSticky.get(0) : null;
        ...
        if (receiver == null) {
            return sticky;
        }

        synchronized (this) {
            ...
            ReceiverList rl = mRegisteredReceivers.get(receiver.asBinder());
            if (rl == null) {
                rl = new ReceiverList(this, callerApp, callingPid, callingUid,
                        userId, receiver);
                ...
                mRegisteredReceivers.put(receiver.asBinder(), rl);
            } else ...
            // 描述正在注册的广播接收者
            BroadcastFilter bf = new BroadcastFilter(filter, rl, callerPackage,
                    permission, callingUid, userId);
            rl.add(bf);
            ...
            mReceiverResolver.addFilter(bf);
            // 以后ActivityManagerService接收到广播时，就可以在mReceiverResolver中
            // 找到对应的广播接收者了
            ...
            return sticky;
        }
    }
```
黏性广播被发送到ActivityManagerService之后会被一直保存，直到下次再接收到另一个同类型的黏性广播为止。一个Activity组件在向ActivityManagerService注册接收某一种类型的广播时，如果其内部恰好保存有该类型的黏性广播，就会将此黏性广播返回给Activity，以便他知道系统上次发出的他所感兴趣的广播内容。可以通过ContextWrapper::sendStickyBroadcast(...)发送一个黏性广播。

到此，BroadcastReceiver的注册过程就走完了，接下来继续研究广播的发送过程。
