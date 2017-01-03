---
layout: post
title: 广播机制学习笔记（一）
date: 2017-01-01 22:23:45 +0800
categories: Android
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
