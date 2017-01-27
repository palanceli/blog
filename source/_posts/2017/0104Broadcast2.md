---
layout: post
title: 广播机制学习笔记（二）——Broadcast的发送
date: 2017-01-01 22:23:45 +0800
categories: Android
tags: 广播机制
toc: true
comments: true
---
广播的发送始于客户端对sendBroadcast(...)的调用，该函数继承自ContextWrapper::sendBroadcast(...)。
<!-- more -->
# Step1 ContextWrapper::sendBroadcast(...)
``` java
// frameworks/base/core/java/android/app/ContextImpl.java:395
    public void sendBroadcast(Intent intent) {
        mBase.sendBroadcast(intent);  // 🏁
    }
```
mBase的类型为ContextImpl。
# Step2 ContextImpl::Broadcast(...)
``` java
// frameworks/base/core/java/android/app/ContextImpl.java:762
    public void sendBroadcast(Intent intent) {
        ...
        String resolvedType = intent.resolveTypeIfNeeded(getContentResolver());
        try {
            intent.prepareToLeaveProcess();
            ActivityManagerNative.getDefault().broadcastIntent(
                    mMainThread.getApplicationThread(), intent, resolvedType, null,
                    Activity.RESULT_OK, null, null, null, AppOpsManager.OP_NONE, null, false, false,
                    getUserId()); // 🏁
        } catch ...
    }
```
# Step3 ActivityManagerProxy::broadcastIntent(...)
``` java
// frameworks/base/core/java/android/app/ActivityManagerNative.java:3033
    public int broadcastIntent(IApplicationThread caller,
            Intent intent, String resolvedType, IIntentReceiver resultTo,
            int resultCode, String resultData, Bundle map,
            String[] requiredPermissions, int appOp, Bundle options, boolean serialized,
            boolean sticky, int userId) throws RemoteException
    {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        data.writeStrongBinder(caller != null ? caller.asBinder() : null);
        intent.writeToParcel(data, 0);
        data.writeString(resolvedType);
        data.writeStrongBinder(resultTo != null ? resultTo.asBinder() : null);
        data.writeInt(resultCode);
        data.writeString(resultData);
        data.writeBundle(map);
        data.writeStringArray(requiredPermissions);
        data.writeInt(appOp);
        data.writeBundle(options);
        data.writeInt(serialized ? 1 : 0);
        data.writeInt(sticky ? 1 : 0);
        data.writeInt(userId);
        mRemote.transact(BROADCAST_INTENT_TRANSACTION, data, reply, 0);
        reply.readException();
        int res = reply.readInt();
        reply.recycle();
        data.recycle();
        return res;
    }
```
它向ActivityManagerService发送一个BROADCAST_INTENT_TRANSACTION请求，以上步骤是在客户端完成的，接下来将转入ActivityManagerService。
# Step4 ActivityManagerService::broadcastIntent(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:17001
    public final int broadcastIntent(IApplicationThread caller,
            Intent intent, String resolvedType, IIntentReceiver resultTo,
            int resultCode, String resultData, Bundle resultExtras,
            String[] requiredPermissions, int appOp, Bundle options,
            boolean serialized, boolean sticky, int userId) {
        ...
        synchronized(this) {
            intent = verifyBroadcastLocked(intent);

            final ProcessRecord callerApp = getRecordForAppLocked(caller);
            // 获得广播发送进程的身份
            final int callingPid = Binder.getCallingPid();
            final int callingUid = Binder.getCallingUid(); 
            final long origId = Binder.clearCallingIdentity();
            // 🏁处理intent描述的广播
            int res = broadcastIntentLocked(callerApp,
                    callerApp != null ? callerApp.info.packageName : null,
                    intent, resolvedType, resultTo, resultCode, resultData, resultExtras,
                    requiredPermissions, appOp, null, serialized, sticky,
                    callingPid, callingUid, userId);
            Binder.restoreCallingIdentity(origId);
            return res;
        }
    }
```
# Step5 ActivityManagerService::broadcastIntentLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:16497
    private final int broadcastIntentLocked(ProcessRecord callerApp,
            String callerPackage, Intent intent, String resolvedType,
            IIntentReceiver resultTo, int resultCode, String resultData,
            Bundle resultExtras, String[] requiredPermissions, int appOp, Bundle options,
            boolean ordered, boolean sticky, int callingPid, int callingUid, int userId) {
        intent = new Intent(intent);
        ...
        final String action = intent.getAction();
        ...
        // Add to the sticky list if requested.

        // 如果是粘性广播，需要将它保存下来，以便后面注册接收此种类型广播的
        // BroadcastReceiver可以获得此广播
        if (sticky) {
            ...
            // 所有类型相同的黏性广播都保存在一个列表中，这些列表又保存在mStickBroadcasts
            // 中，并以广播类型为关键字。
            // 先根据广播类型找到匹配的广播列表
            ArrayMap<String, ArrayList<Intent>> stickies = mStickyBroadcasts.get(userId);
            if (stickies == null) {
                stickies = new ArrayMap<>();
                mStickyBroadcasts.put(userId, stickies);
            }
            ArrayList<Intent> list = stickies.get(intent.getAction());
            if (list == null) {
                list = new ArrayList<>();
                stickies.put(intent.getAction(), list);
            }
            // 再从广播列表中找到与intent一致的广播
            final int stickiesCount = list.size();
            int i;
            for (i = 0; i < stickiesCount; i++) {
                // 查找是否存在于intent一致的广播
                if (intent.filterEquals(list.get(i))) {
                    // This sticky already exists, replace it.
                    list.set(i, new Intent(intent));
                    break;
                }
            }
            if (i >= stickiesCount) {
                list.add(new Intent(intent));
            }
        }

        int[] users;
        if (userId == UserHandle.USER_ALL) {
            // Caller wants broadcast to go to all started users.
            users = mStartedUserArray;
        } else {
            // Caller wants broadcast to go to one specific user.
            users = new int[] {userId};
        }

        // Figure out who all will receive this broadcast.
        List receivers = null;  // 保存静态注册的接收者
        List<BroadcastFilter> registeredReceivers = null; // 保存动态注册的接收者
        // Need to resolve the intent to interested receivers...
        if ((intent.getFlags()&Intent.FLAG_RECEIVER_REGISTERED_ONLY)
                 == 0) {
            receivers = collectReceiverComponents(intent, resolvedType, callingUid, users);
        }
        if (intent.getComponent() == null) {
            if (userId == UserHandle.USER_ALL && callingUid == Process.SHELL_UID) {
                // Query one target user at a time, excluding shell-restricted users
                UserManagerService ums = getUserManagerLocked();
                for (int i = 0; i < users.length; i++) {
                    if (ums.hasUserRestriction(
                            UserManager.DISALLOW_DEBUGGING_FEATURES, users[i])) {
                        continue;
                    }
                    List<BroadcastFilter> registeredReceiversForUser =
                            mReceiverResolver.queryIntent(intent,
                                    resolvedType, false, users[i]);
                    if (registeredReceivers == null) {
                        registeredReceivers = registeredReceiversForUser;
                    } else if (registeredReceiversForUser != null) {
                        registeredReceivers.addAll(registeredReceiversForUser);
                    }
                }
            } else {
                registeredReceivers = mReceiverResolver.queryIntent(intent,
                        resolvedType, false, userId);
            }
        }

        // 上次接收的广播还未来得及转发给接收者
        final boolean replacePending =
                (intent.getFlags()&Intent.FLAG_RECEIVER_REPLACE_PENDING) != 0;
        ...
        int NR = registeredReceivers != null ? registeredReceivers.size() : 0;
        // 当前发送的广播是无序广播 && 存在动态注册的接收者
        if (!ordered && NR > 0) {
            // If we are not serializing this broadcast, then send the
            // registered receivers separately so they don't wait for the
            // components to be launched.
            // 将intent描述的广播转发给目标接收者，由此可见动态注册的广播要比静态注册的
            // 优先收到无序广播
            final BroadcastQueue queue = broadcastQueueForIntent(intent);
            // r用来描述ActivityManagerService要执行的广播转发任务
            BroadcastRecord r = new BroadcastRecord(queue, intent, callerApp,
                    callerPackage, callingPid, callingUid, resolvedType, requiredPermissions,
                    appOp, brOptions, registeredReceivers, resultTo, resultCode, resultData,
                    resultExtras, ordered, sticky, false, userId);
            ...
            final boolean replaced = replacePending && queue.replaceParallelBroadcastLocked(r);
            // 如果没有需要替换的广播，则将r插入无序广播调度队列；如果有，则不再重复插入
            if (!replaced) { 
                queue.enqueueParallelBroadcastLocked(r);
                queue.scheduleBroadcastsLocked(); // 🏁重新调度队列中的广播转发任务
            }
            // 此时，对于无序广播，已将intent所描述的广播转发给那些动态注册的接收者
            registeredReceivers = null;
            NR = 0;
        }

        // 无论ActivityManagerService当前接收到的是无序广播还是有序广播，都会将
        // 该广播及目标接收者封装成转发任务，并添加到有序广播调度队列中。
        // mOrderedBroadcasts描述有序广播调度队列，其中每个转发任务的目标接收者都是按照
        // 优先级由高到低排列的。
        // Merge into one list.
        int ir = 0;
        // 合并动态注册和静态注册的目标接收者，按照优先级从高到低排列，存放到receivers
        if (receivers != null) {
            ...
            int NT = receivers != null ? receivers.size() : 0;
            int it = 0;
            ResolveInfo curt = null;
            BroadcastFilter curr = null;
            while (it < NT && ir < NR) {
                if (curt == null) {
                    curt = (ResolveInfo)receivers.get(it);
                }
                if (curr == null) {
                    curr = registeredReceivers.get(ir);
                }
                if (curr.getPriority() >= curt.priority) {
                    // Insert this broadcast record into the final list.
                    receivers.add(it, curr);
                    ir++;
                    curr = null;
                    it++;
                    NT++;
                } else {
                    // Skip to the next ResolveInfo in the final list.
                    it++;
                    curt = null;
                }
            }
        }
        while (ir < NR) {
            if (receivers == null) {
                receivers = new ArrayList();
            }
            receivers.add(registeredReceivers.get(ir));
            ir++;
        }

        if ((receivers != null && receivers.size() > 0)
                || resultTo != null) {
            BroadcastQueue queue = broadcastQueueForIntent(intent);
            BroadcastRecord r = new BroadcastRecord(queue, intent, callerApp,
                    callerPackage, callingPid, callingUid, resolvedType,
                    requiredPermissions, appOp, brOptions, receivers, resultTo, resultCode,
                    resultData, resultExtras, ordered, sticky, false, userId);
            ...
            boolean replaced = replacePending && queue.replaceOrderedBroadcastLocked(r);
            if (!replaced) {
                queue.enqueueOrderedBroadcastLocked(r);
                queue.scheduleBroadcastsLocked();
            }
        }
        // 至此，ActivityManagerService就找到intent所描述的目标接收者，并分别将他们
        // 保存在内部无序广播调度队列mParallelBroadcasts和有序广播队列
        // mOrderedBroadcasts中
        return ActivityManager.BROADCAST_SUCCESS;
    }
```
由此可见，无论对于有序还是无序广播，都会把目标接收者保存到mOrderedBroadcasts中，对于无序广播，会再保存到mParallelBroadcasts中。

# Step6 BroadcastQueue::scheduleBroadcastsLocked()
``` java
// frameworks/base/services/core/java/com/android/server/am/BroadcastQueue.java
public final class BroadcastQueue {
...
// :155
    final BroadcastHandler mHandler;
...
// :346
// 成员变量mBroadcastsScheduled描述ActivityManagerService是否已经向它所在线程消息队列
// 发送了类型为BROADCAST_INTENT_MSG的消息。ActivityManagerService就是通过该消息来调度
// 两个队列中的广播。
    public void scheduleBroadcastsLocked() {
        ...
        // ActivityManagerService所在线程消息队列中已经存在BROADCAST_INTENT_MSG消息了
        if (mBroadcastsScheduled) {
            return;
        }
        mHandler.sendMessage(mHandler.obtainMessage(BROADCAST_INTENT_MSG, this));
        mBroadcastsScheduled = true;
    }
```
mBroadcastsScheduled的类型为BroadcastHandler。
# Step7 BroadcastHandler::handleMessage(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/BroadcastQueue.java:163
    public void handleMessage(Message msg) {
        switch (msg.what) {
            case BROADCAST_INTENT_MSG: {
                ...
                processNextBroadcast(true);  // 🏁
            } break;
            ...
        }
    }

```
# Step8 BroadcastQueue::processNextBroadcast(...)
``` java 
// frameworks/base/services/core/java/com/android/server/am/BroadcastQueue.java:639
    final void processNextBroadcast(boolean fromMsg) {
        synchronized(mService) {
            BroadcastRecord r;
            ...
            // 表示前面发送到ActivityManagerService的BROADCAST_INTENT_MSG已被处理
            if (fromMsg) { 
                mBroadcastsScheduled = false;
            }

            // First, deliver any non-serialized broadcasts right away.
            // 将保存在无序队列mParallelBroadcasts中的转发任务发送给接收者
            while (mParallelBroadcasts.size() > 0) {
                r = mParallelBroadcasts.remove(0); // 遍历
                ...
                final int N = r.receivers.size();
                ...
                // 将他所描述的无序广播发送给每一个接收者
                for (int i=0; i<N; i++) {
                    Object target = r.receivers.get(i);
                    ...
                    // 🏁
                    deliverToRegisteredReceiverLocked(r, (BroadcastFilter)target, false);
                }
                ...
            }
            // 继续处理保存在有序队列mOrderedBroadcasts中的广播
            // 有序队列mOrderedBroadcast描述的目标接收者有可能是静态注册，此时可能尚未
            // 被启动，因此ActivityManagerService将广播发送给他们处理时，首先要将它们
            // 启动起来
            // Now take care of the next serialized one...

            // If we are waiting for a process to come up to handle the next
            // broadcast, then do nothing at this point.  Just in case, we
            // check that the process we're waiting for still exists.
            // mPendingBroadcast描述正在等待静态注册的目标接收者启动起来的广播转发任务
            if (mPendingBroadcast != null) { // 检查目标接收者所在进程是否启动
                ...
                boolean isDead;
                synchronized (mService.mPidsSelfLocked) {
                    ProcessRecord proc = mService.mPidsSelfLocked.get(mPendingBroadcast.curApp.pid);
                    isDead = proc == null || proc.crashing;
                }
                if (!isDead) { // 如果进程正在启动，则ActivityManagerService继续等待
                    // It's still alive, so keep waiting
                    return;
                } else {        // 否则准备向目标进程发送一个广播
                    ...
                    mPendingBroadcast.state = BroadcastRecord.IDLE;
                    mPendingBroadcast.nextReceiver = mPendingBroadcastRecvIndex;
                    mPendingBroadcast = null;
                }

            }

            boolean looped = false;
            
            do {
                if (mOrderedBroadcasts.size() == 0) {
                    ...
                    return;
                }
                r = mOrderedBroadcasts.get(0); // 遍历有序队列
                boolean forceReceive = false;

                ...
                // 得到r的目标接收者的个数
                int numReceivers = (r.receivers != null) ? r.receivers.size() : 0;
                // 检查前一个接收者是否在规定时间内处理完成上一个有序广播
                if (mService.mProcessesReady && r.dispatchTime > 0) {
                    long now = SystemClock.uptimeMillis();
                    // ActivityManagerService在处理广播任务时，会将当前时间记录在
                    // r.dispatchTime中，如果该广播不能在
                    // (2*BROADCAST_TIMEOUT*numReceivers)毫秒处理完
                    if ((numReceivers > 0) &&
                            (now > r.dispatchTime + (2*mTimeoutPeriod*numReceivers))) {
                        ...
                        // 强制结束
                        broadcastTimeoutLocked(false); // forcibly finish this broadcast
                        // 下面两行赋值表示要继续处理有序队列
                        forceReceive = true;
                        r.state = BroadcastRecord.IDLE;
                    }
                }

                // 检查r是否正在处理中，如果是，则等待处理完成后在转发给下一个目标接收者
                // 因此直接返回
                if (r.state != BroadcastRecord.IDLE) {
                    ...
                    return;
                }
                // 如果r已经处理完成，或者被强制结束
                if (r.receivers == null || r.nextReceiver >= numReceivers
                        || r.resultAbort || forceReceive) {
                    // No more receivers for this broadcast!  Send the final
                    // result if requested...
                    ...
                    // 删除前面发送到ActivityManagerService的
                    // BROADCAST_TIMEOUT_MSG消息
                    cancelBroadcastTimeoutLocked();
                    ...
                    // ... and on to the next...
                    ...
                    mOrderedBroadcasts.remove(0);
                    r = null;
                    ...
                    continue;
                }
            } while (r == null);

            // r.receivers保存广播r的目标接收者列表；r.nextReceiver保存下一个接收者序号
            // Get the next receiver...
            int recIdx = r.nextReceiver++;

            // Keep track of when this receiver started, and make sure there
            // is a timeout message pending to kill it if need be.
            // 表示有序广播r发送给下一个目标接收者处理的时间
            r.receiverTime = SystemClock.uptimeMillis();
            if (recIdx == 0) { // 说明广播r刚开始被处理，因此记录dispatchTime
                r.dispatchTime = r.receiverTime;
                ...
            }
            // 检查ActivityManagerService是否已经向它所在线程发送了
            // BROADCAST_TIMEOUT_MSG消息，如果还没发送，则发送，并指定它在
            // mTimeoutPeriod之后处理
            if (! mPendingBroadcastTimeoutMessage) {
                long timeoutTime = r.receiverTime + mTimeoutPeriod;
                ...
                setBroadcastTimeoutLocked(timeoutTime);
            }
            ...
            final Object nextReceiver = r.receivers.get(recIdx);

            if (nextReceiver instanceof BroadcastFilter) {// 说明是动态注册的
                // Simple case: this is a registered receiver who gets
                // a direct call.
                BroadcastFilter filter = (BroadcastFilter)nextReceiver;
                ...
                // 🏁 因为动态注册的接收者肯定已启动，直接发送即可
                deliverToRegisteredReceiverLocked(r, filter, r.ordered);
                // 检查如果是无序广播
                if (r.receiver == null || !r.ordered) {
                    // The receiver has already finished, so schedule to
                    // process the next one.
                    ...
                    // 表示无需等待它前一个接收者处理完成，就可以将该广播继续发送给
                    // 它下一个目标接收者
                    r.state = BroadcastRecord.IDLE; 
                    scheduleBroadcastsLocked();
                } ...
                return;
            }

            
            // Hard case: need to instantiate the receiver, possibly
            // starting its application process to host it.
            // 如果nextReceiver类型非BroadcastFilter，说明一定是ResoveInfo
            // 即静态注册，故可以强制转型
            ResolveInfo info =
                (ResolveInfo)nextReceiver;
            ...
            // 获取接收者的android:process属性，即进程名
            String targetProcess = info.activityInfo.processName;
            ...
            // 检查该进程是否已启动
            // Is this receiver's application already running?
            ProcessRecord app = mService.getProcessRecordLocked(targetProcess,
                    info.activityInfo.applicationInfo.uid, false);
            if (app != null && app.thread != null) {
                try { // 如果已经启动，则直接发送给它处理
                    ...
                    processCurBroadcastLocked(r, app);
                    return;
                } catch (RemoteException e) ...

                // If a dead object exception was thrown -- fall through to
                // restart the application.
            }

            ...
            // 先启动进程
            if ((r.curApp=mService.startProcessLocked(targetProcess,
                    info.activityInfo.applicationInfo, true,
                    r.intent.getFlags() | Intent.FLAG_FROM_BACKGROUND,
                    "broadcast", r.curComponent,
                    (r.intent.getFlags()&Intent.FLAG_RECEIVER_BOOT_UPGRADE) != 0, false, false))
                            == null) {
                ... // 如果启动失败，则结束对广播r的处理
                scheduleBroadcastsLocked();
                r.state = BroadcastRecord.IDLE;
                return;
            }
            // 表示正在等待广播r下一个目标接收者所在进程启动起来
            mPendingBroadcast = r;
            mPendingBroadcastRecvIndex = recIdx;
        }
    }
```
假设广播r的下一个目标接收者是：(动态注册 || (静态注册 && 进程已经启动起来) )那么接下来就会调用deliverToRegisteredReceiverLocked(...)将广播转发给该接收者处理。

# Step9 BroadcastQueue::deliverToRegisteredReceiverLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/BroadcastQueue.java:465
    private void deliverToRegisteredReceiverLocked(BroadcastRecord r,
            BroadcastFilter filter, boolean ordered) {
        boolean skip = false;
        if (filter.requiredPermission != null) { // 需要检查发送者权限
            int perm = mService.checkComponentPermission(filter.requiredPermission,
                    r.callingPid, r.callingUid, -1, true);
            if (perm != PackageManager.PERMISSION_GRANTED) {
                ...
                skip = true;
            } ...
        }
        // 需要检查接收者权限
        if (!skip && r.requiredPermissions != null && r.requiredPermissions.length > 0) {
            for (int i = 0; i < r.requiredPermissions.length; i++) {
                String requiredPermission = r.requiredPermissions[i];
                int perm = mService.checkComponentPermission(requiredPermission,
                        filter.receiverList.pid, filter.receiverList.uid, -1, true);
                if (perm != PackageManager.PERMISSION_GRANTED) {
                    ...
                    skip = true;
                    break;
                }
                ...
            }
        }
        ...
        if (!skip) { // 成功通过了权限检查
            ...
            try {
                ...
                // 🏁将r转发给filter所描述的接收者
                performReceiveLocked(filter.receiverList.app, filter.receiverList.receiver,
                        new Intent(r.intent), r.resultCode, r.resultData,
                        r.resultExtras, r.ordered, r.initialSticky, r.userId);
                ...
            } catch (RemoteException e) ...
        }
    }
```
# Step10 BroadcastQueue::performReceiveLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/BroadcastQueue.java:445
private static void performReceiveLocked(ProcessRecord app, IIntentReceiver receiver,
    Intent intent, int resultCode, String data, Bundle extras,
    boolean ordered, boolean sticky, int sendingUser) throws RemoteException {
    // app描述目标接收者所在进程
    // receiver描述目标接收者
    // intent描述即将发送的广播
    // Send the intent to the receiver asynchronously using one-way binder calls.
    if (app != null) {
        if (app.thread != null) {
            // If we have an app thread, do the call through that so it is
            // correctly ordered with other one-way calls.
            // 🏁
            app.thread.scheduleRegisteredReceiver(receiver, intent, resultCode,
                    data, extras, ordered, sticky, sendingUser, app.repProcState);
        } else {
            // Application has died. Receiver doesn't exist.
            throw new RemoteException("app.thread must not be null");
        }
    } else {
        receiver.performReceive(intent, resultCode, data, extras, ordered,
                sticky, sendingUser);
    }
}
```
app.thread是引用了运行在该进程中的一个ApplicationThread对象的Binder代理对象，其类型为ApplicationThreadProxy。

# Step11 ApplicationThreadProxy::scheduleRegisteredReceiver(...)
``` java
// frameworks/base/core/java/android/app/ApplicationThreadNative.java:707
class ApplicationThreadProxy implements IApplicationThread {
...
// :1114
    public void scheduleRegisteredReceiver(IIntentReceiver receiver, Intent intent,
            int resultCode, String dataStr, Bundle extras, boolean ordered,
            boolean sticky, int sendingUser, int processState) throws RemoteException {
        Parcel data = Parcel.obtain();
        data.writeInterfaceToken(IApplicationThread.descriptor);
        data.writeStrongBinder(receiver.asBinder());
        intent.writeToParcel(data, 0);
        data.writeInt(resultCode);
        data.writeString(dataStr);
        data.writeBundle(extras);
        data.writeInt(ordered ? 1 : 0);
        data.writeInt(sticky ? 1 : 0);
        data.writeInt(sendingUser);
        data.writeInt(processState);
        mRemote.transact(SCHEDULE_REGISTERED_RECEIVER_TRANSACTION, data, null,
                IBinder.FLAG_ONEWAY);
        data.recycle();
    }
```
它向发送广播消息的应用程序发送SCHEDULE_REGISTERED_RECEIVER_TRANSACTION请求，接下来转入应用程序。

# Step12 ApplicationThread::scheduleRegisteredReceiver(...)
``` java
// frameworks/base/core/java/android/app/ActivityThread.java:150
public final class ActivityThread {
//:574
    private class ApplicationThread extends ApplicationThreadNative {
    ...
//:893
        public void scheduleRegisteredReceiver(IIntentReceiver receiver, Intent intent,
                int resultCode, String dataStr, Bundle extras, boolean ordered,
                boolean sticky, int sendingUser, int processState) throws RemoteException {
            updateProcessState(processState, false);
            // 🏁
            receiver.performReceive(intent, resultCode, dataStr, extras, ordered,
                    sticky, sendingUser);
        }
```
receiver指向一个InnerReceiver对象。
# Step13 InnerReceiver::performReceive(...)
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:786
static final class ReceiverDispatcher {

    final static class InnerReceiver extends IIntentReceiver.Stub {
        final WeakReference<LoadedApk.ReceiverDispatcher> mDispatcher;
        ...
        public void performReceive(Intent intent, int resultCode, String data,
                Bundle extras, boolean ordered, boolean sticky, int sendingUser) {
            LoadedApk.ReceiverDispatcher rd = mDispatcher.get();
            ...
            if (rd != null) {
                // 🏁
                rd.performReceive(intent, resultCode, data, extras,
                        ordered, sticky, sendingUser);
            } else ...
        }
    }
}
```
# Step14 ReceiverDispatcher::performReceive(...)
``` java
// frameworks/base/core/java/android/app/LoadedApk.java:786
    static final class ReceiverDispatcher {
    ...
//:956
        public void performReceive(Intent intent, int resultCode, String data,
                Bundle extras, boolean ordered, boolean sticky, int sendingUser) {
            ...
            // 将intent描述的广播封装成Args对象，并发送给主线程消息队列，该消息最终由
            // Args.run函数来处理
            Args args = new Args(intent, resultCode, data, extras, ordered,
                    sticky, sendingUser);
            if (!mActivityThread.post(args)) {
                ...
            }
        }
```
 # Step15 Args::run()
 ``` java
// frameworks/base/core/java/android/app/LoadedApk.java:786
static final class ReceiverDispatcher {
...
final BroadcastReceiver mReceiver; // 指向广播接收者
final boolean mRegistered; // 描述mReeiver是否已经注册到ActivityManagerService
...
//:837
 final class Args extends BroadcastReceiver.PendingResult implements Runnable {
    private Intent mCurIntent;      // 描述一个广播
    private final boolean mOrdered; // mCurOrdered是否为有序广播
//:850
    ...
    public void run() {
        final BroadcastReceiver receiver = mReceiver; 
        final boolean ordered = mOrdered;  
        ...
        final IActivityManager mgr = ActivityManagerNative.getDefault();
        final Intent intent = mCurIntent;
        ...
        try {
            ...
            receiver.onReceive(mContext, intent); // 到达接收者
        } catch (Exception e) ...
        
        if (receiver.getPendingResult() != null) {
            finish();
        }
        ...
    }
}
 ```
