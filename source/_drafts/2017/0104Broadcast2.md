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
# Step8 BroadcastQueue::::processNextBroadcast(...)
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
            while (mParallelBroadcasts.size() > 0) {
                r = mParallelBroadcasts.remove(0);
                r.dispatchTime = SystemClock.uptimeMillis();
                r.dispatchClockTime = System.currentTimeMillis();
                final int N = r.receivers.size();
                ...
                for (int i=0; i<N; i++) {
                    Object target = r.receivers.get(i);
                    ...
                    deliverToRegisteredReceiverLocked(r, (BroadcastFilter)target, false);
                }
                addBroadcastToHistoryLocked(r);
                ...
            }

            // Now take care of the next serialized one...

            // If we are waiting for a process to come up to handle the next
            // broadcast, then do nothing at this point.  Just in case, we
            // check that the process we're waiting for still exists.
            if (mPendingBroadcast != null) {
                ...

                boolean isDead;
                synchronized (mService.mPidsSelfLocked) {
                    ProcessRecord proc = mService.mPidsSelfLocked.get(mPendingBroadcast.curApp.pid);
                    isDead = proc == null || proc.crashing;
                }
                ...
            }

            boolean looped = false;
            
            do {
                if (mOrderedBroadcasts.size() == 0) {
                    // No more broadcasts pending, so all done!
                    mService.scheduleAppGcsLocked();
                    if (looped) {
                        // If we had finished the last ordered broadcast, then
                        // make sure all processes have correct oom and sched
                        // adjustments.
                        mService.updateOomAdjLocked();
                    }
                    return;
                }
                r = mOrderedBroadcasts.get(0);
                boolean forceReceive = false;

                // Ensure that even if something goes awry with the timeout
                // detection, we catch "hung" broadcasts here, discard them,
                // and continue to make progress.
                //
                // This is only done if the system is ready so that PRE_BOOT_COMPLETED
                // receivers don't get executed with timeouts. They're intended for
                // one time heavy lifting after system upgrades and can take
                // significant amounts of time.
                int numReceivers = (r.receivers != null) ? r.receivers.size() : 0;
                if (mService.mProcessesReady && r.dispatchTime > 0) {
                    long now = SystemClock.uptimeMillis();
                    if ((numReceivers > 0) &&
                            (now > r.dispatchTime + (2*mTimeoutPeriod*numReceivers))) {
                        ...
                        broadcastTimeoutLocked(false); // forcibly finish this broadcast
                        forceReceive = true;
                        r.state = BroadcastRecord.IDLE;
                    }
                }

                if (r.state != BroadcastRecord.IDLE) {
                    ...
                    return;
                }

                if (r.receivers == null || r.nextReceiver >= numReceivers
                        || r.resultAbort || forceReceive) {
                    // No more receivers for this broadcast!  Send the final
                    // result if requested...
                    if (r.resultTo != null) {
                        try {
                            ...
                            performReceiveLocked(r.callerApp, r.resultTo,
                                new Intent(r.intent), r.resultCode,
                                r.resultData, r.resultExtras, false, false, r.userId);
                            // Set this to null so that the reference
                            // (local and remote) isn't kept in the mBroadcastHistory.
                            r.resultTo = null;
                        } catch (RemoteException e) ...
                    }

                    ...
                    cancelBroadcastTimeoutLocked();

                    ...

                    // ... and on to the next...
                    addBroadcastToHistoryLocked(r);
                    mOrderedBroadcasts.remove(0);
                    r = null;
                    looped = true;
                    continue;
                }
            } while (r == null);

            // Get the next receiver...
            int recIdx = r.nextReceiver++;

            // Keep track of when this receiver started, and make sure there
            // is a timeout message pending to kill it if need be.
            r.receiverTime = SystemClock.uptimeMillis();
            if (recIdx == 0) {
                r.dispatchTime = r.receiverTime;
                r.dispatchClockTime = System.currentTimeMillis();
                ...
            }
            if (! mPendingBroadcastTimeoutMessage) {
                long timeoutTime = r.receiverTime + mTimeoutPeriod;
                ...
                setBroadcastTimeoutLocked(timeoutTime);
            }

            final BroadcastOptions brOptions = r.options;
            final Object nextReceiver = r.receivers.get(recIdx);

            if (nextReceiver instanceof BroadcastFilter) {
                // Simple case: this is a registered receiver who gets
                // a direct call.
                BroadcastFilter filter = (BroadcastFilter)nextReceiver;
                ...
                deliverToRegisteredReceiverLocked(r, filter, r.ordered);
                if (r.receiver == null || !r.ordered) {
                    // The receiver has already finished, so schedule to
                    // process the next one.
                    ...
                    r.state = BroadcastRecord.IDLE;
                    scheduleBroadcastsLocked();
                } else {
                    if (brOptions != null && brOptions.getTemporaryAppWhitelistDuration() > 0) {
                        scheduleTempWhitelistLocked(filter.owningUid,
                                brOptions.getTemporaryAppWhitelistDuration(), r);
                    }
                }
                return;
            }

            // Hard case: need to instantiate the receiver, possibly
            // starting its application process to host it.

            ResolveInfo info =
                (ResolveInfo)nextReceiver;
            ComponentName component = new ComponentName(
                    info.activityInfo.applicationInfo.packageName,
                    info.activityInfo.name);

            boolean skip = false;
            int perm = mService.checkComponentPermission(info.activityInfo.permission,
                    r.callingPid, r.callingUid, info.activityInfo.applicationInfo.uid,
                    info.activityInfo.exported);
            if (perm != PackageManager.PERMISSION_GRANTED) {
                if (!info.activityInfo.exported) {
                    ...
                } else ...
                skip = true;
            } else if (info.activityInfo.permission != null) {
                final int opCode = AppOpsManager.permissionToOpCode(info.activityInfo.permission);
                if (opCode != AppOpsManager.OP_NONE
                        && mService.mAppOpsService.noteOperation(opCode, r.callingUid,
                                r.callerPackage) != AppOpsManager.MODE_ALLOWED) {
                    ...
                    skip = true;
                }
            }
            if (!skip && info.activityInfo.applicationInfo.uid != Process.SYSTEM_UID &&
                r.requiredPermissions != null && r.requiredPermissions.length > 0) {
                for (int i = 0; i < r.requiredPermissions.length; i++) {
                    String requiredPermission = r.requiredPermissions[i];
                    try {
                        perm = AppGlobals.getPackageManager().
                                checkPermission(requiredPermission,
                                        info.activityInfo.applicationInfo.packageName,
                                        UserHandle
                                                .getUserId(info.activityInfo.applicationInfo.uid));
                    } catch (RemoteException e) ...
                    if (perm != PackageManager.PERMISSION_GRANTED) {
                        ...
                        skip = true;
                        break;
                    }
                    int appOp = AppOpsManager.permissionToOpCode(requiredPermission);
                    if (appOp != AppOpsManager.OP_NONE && appOp != r.appOp
                            && mService.mAppOpsService.noteOperation(appOp,
                            info.activityInfo.applicationInfo.uid, info.activityInfo.packageName)
                            != AppOpsManager.MODE_ALLOWED) {
                        ...
                        skip = true;
                        break;
                    }
                }
            }
            if (!skip && r.appOp != AppOpsManager.OP_NONE
                    && mService.mAppOpsService.noteOperation(r.appOp,
                    info.activityInfo.applicationInfo.uid, info.activityInfo.packageName)
                    != AppOpsManager.MODE_ALLOWED) {
                ...
                skip = true;
            }
            if (!skip) {
                skip = !mService.mIntentFirewall.checkBroadcast(r.intent, r.callingUid,
                        r.callingPid, r.resolvedType, info.activityInfo.applicationInfo.uid);
            }
            boolean isSingleton = false;
            try {
                isSingleton = mService.isSingleton(info.activityInfo.processName,
                        info.activityInfo.applicationInfo,
                        info.activityInfo.name, info.activityInfo.flags);
            } catch (SecurityException e) ...
            if ((info.activityInfo.flags&ActivityInfo.FLAG_SINGLE_USER) != 0) {
                if (ActivityManager.checkUidPermission(
                        android.Manifest.permission.INTERACT_ACROSS_USERS,
                        info.activityInfo.applicationInfo.uid)
                                != PackageManager.PERMISSION_GRANTED) {
                    Slog.w(TAG, "Permission Denial: Receiver " + component.flattenToShortString()
                            + " requests FLAG_SINGLE_USER, but app does not hold "
                            + android.Manifest.permission.INTERACT_ACROSS_USERS);
                    skip = true;
                }
            }
            if (r.curApp != null && r.curApp.crashing) {
                // If the target process is crashing, just skip it.
                ...
                skip = true;
            }
            if (!skip) {
                boolean isAvailable = false;
                try {
                    isAvailable = AppGlobals.getPackageManager().isPackageAvailable(
                            info.activityInfo.packageName,
                            UserHandle.getUserId(info.activityInfo.applicationInfo.uid));
                } catch (Exception e) ...
                if (!isAvailable) {
                    ...
                    skip = true;
                }
            }

            if (skip) {
                ...
                r.receiver = null;
                r.curFilter = null;
                r.state = BroadcastRecord.IDLE;
                scheduleBroadcastsLocked();
                return;
            }

            r.state = BroadcastRecord.APP_RECEIVE;
            String targetProcess = info.activityInfo.processName;
            r.curComponent = component;
            final int receiverUid = info.activityInfo.applicationInfo.uid;
            // If it's a singleton, it needs to be the same app or a special app
            if (r.callingUid != Process.SYSTEM_UID && isSingleton
                    && mService.isValidSingletonCall(r.callingUid, receiverUid)) {
                info.activityInfo = mService.getActivityInfoForUser(info.activityInfo, 0);
            }
            r.curReceiver = info.activityInfo;
            if (DEBUG_MU && r.callingUid > UserHandle.PER_USER_RANGE) {
                ...
            }

            if (brOptions != null && brOptions.getTemporaryAppWhitelistDuration() > 0) {
                scheduleTempWhitelistLocked(receiverUid,
                        brOptions.getTemporaryAppWhitelistDuration(), r);
            }

            // Broadcast is being executed, its package can't be stopped.
            try {
                AppGlobals.getPackageManager().setPackageStoppedState(
                        r.curComponent.getPackageName(), false, UserHandle.getUserId(r.callingUid));
            } catch (RemoteException e) ...

            // Is this receiver's application already running?
            ProcessRecord app = mService.getProcessRecordLocked(targetProcess,
                    info.activityInfo.applicationInfo.uid, false);
            if (app != null && app.thread != null) {
                try {
                    app.addPackage(info.activityInfo.packageName,
                            info.activityInfo.applicationInfo.versionCode, mService.mProcessStats);
                    processCurBroadcastLocked(r, app);
                    return;
                } catch (RemoteException e) ...

                // If a dead object exception was thrown -- fall through to
                // restart the application.
            }

            ...
            if ((r.curApp=mService.startProcessLocked(targetProcess,
                    info.activityInfo.applicationInfo, true,
                    r.intent.getFlags() | Intent.FLAG_FROM_BACKGROUND,
                    "broadcast", r.curComponent,
                    (r.intent.getFlags()&Intent.FLAG_RECEIVER_BOOT_UPGRADE) != 0, false, false))
                            == null) {
                // Ah, this recipient is unavailable.  Finish it if necessary,
                // and mark the broadcast record as ready for the next.
                ...
                logBroadcastReceiverDiscardLocked(r);
                finishReceiverLocked(r, r.resultCode, r.resultData,
                        r.resultExtras, r.resultAbort, false);
                scheduleBroadcastsLocked();
                r.state = BroadcastRecord.IDLE;
                return;
            }

            mPendingBroadcast = r;
            mPendingBroadcastRecvIndex = recIdx;
        }
    }
```