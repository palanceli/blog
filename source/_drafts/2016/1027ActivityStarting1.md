---
layout: post
title: Activity启动过程学习笔记（一）
date: 2016-10-27 22:36:58 +0800
categories: Android
tags: Activity启动过程
toc: true
comments: true
---
# 找到Launcher启动app的入口点
当在桌面上点击一个应用程序图标时，Luancher响应点击消息，会调用Launcher::onClick(...)。
<!-- more -->
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2458
    public void onClick(View v) {
        ... ...
        Object tag = v.getTag();
        if (tag instanceof ShortcutInfo) {
            onClickAppShortcut(v);
        } else if (tag instanceof FolderInfo) { ... } 
        else ...
    }

// :2591
    protected void onClickAppShortcut(final View v) {
        ... ...
        // Start activities
        startAppShortcutOrInfoActivity(v);
        ... ...
    }
// :2647
    @Thunk void startAppShortcutOrInfoActivity(View v) {
        Object tag = v.getTag();
        ... ...
        boolean success = startActivitySafely(v, intent, tag);
        ... ...
    }
```
接下来以`Launcher::startActivitySafely(...)`为起点进入app启动的分析。
# Step1 Launcher::startActivitySafely(...)
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2938
    public boolean startActivitySafely(View v, Intent intent, Object tag) {
        boolean success = false;
        ... ...
        try {
            success = startActivity(v, intent, tag);  // 🏁
        } catch (ActivityNotFoundException e) { ... }
        return success;
    }
```
其中参数intent中包含Activity组建的信息：
```
action="android.intent.action.MAIN"
category="android.instent.category.LAUNCHER"
cmp="palance.li.activity.MainActivity"
```
这些信息来自应用程序的AndroidManifest.xml文件，是在应用程序安装的时候由PackageManagerService解析并保存的。
# Step2 Launcher::startActivity(...)
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2871
    private boolean startActivity(View v, Intent intent, Object tag) {
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            ... ...
            if (user == null || user.equals(UserHandleCompat.myUserHandle())) {
                // Could be launching some bookkeeping activity
                startActivity(intent, optsBundle); // 🏁
            } else {...}
            return true;
        } catch (SecurityException e) { ... }
        return false;
    }
```
Launcher继承自Activity，这个`startActivity(...)`就来自该父类。
# Step3 Activity::startActivity(...)
``` java
// frameworks/base/core/java/android/app/Activity.java:4207
    public void startActivity(Intent intent, @Nullable Bundle options) {
        if (options != null) {
            startActivityForResult(intent, -1, options);
        } else {
            // Note we want to go through this call for compatibility with
            // applications that may have overridden the method.
            startActivityForResult(intent, -1); // 🏁
        }
    }
```
# Step4 Activity::startActivityForResult(...)
``` java
// frameworks/base/core/java/android/app/Activity.java:4555
    @Override
    public void startActivityForResult(
            String who, Intent intent, int requestCode, @Nullable Bundle options) {
        ... ...
        // Instrumentation  用来监控应用和系统之间的交互操作。
        // mMainThread  描述应用程序进程，Android应用的每个进程都会保存这个成员变量。
        // mMainThread.getApplicationThread()  返回Launcher所在进程的
        //   ApplicationThread对象。
        // mToken  指向ActivityManagerService中类型为ActivityRecord的Binder对象，
        //  每个已启动的Activity组件在ActivityManagerService都维护一个对应的
        //  ActivityRecord对象，用来维护对应Activity组件的运行状态及信息。
        Instrumentation.ActivityResult ar =
            mInstrumentation.execStartActivity(
                this, mMainThread.getApplicationThread(), mToken, who,
                intent, requestCode, options); // 🏁
        ... ...
    }
```
# Step5 Instrumentation::execStartActivity(...)
``` java
// frameworks/base/core/java/android/app/Instrumentation.java:1481
    public ActivityResult execStartActivity(
            Context who, IBinder contextThread, IBinder token, Activity target,
            Intent intent, int requestCode, Bundle options) {
        ... ...
        try {
            ... ...
            // ActivityManagerNative.getDefault()  返回ActivityManagerService
            //   的代理对象。
            int result = ActivityManagerNative.getDefault()
                .startActivity(whoThread, who.getBasePackageName(), intent,
                        intent.resolveTypeIfNeeded(who.getContentResolver()),
                        token, target != null ? target.mEmbeddedID : null,
                        requestCode, 0, null, options); // 🏁
            ... ...
        } catch (RemoteException e) { ... }
        return null;
    }
```
# Step6 ActivityManagerProxy::startActivity(...)
``` java
// frameworks/base/core/java/android/app/ActivityManagerNative.java:2631
    public int startActivity(IApplicationThread caller, String callingPackage, Intent intent,
            String resolvedType, IBinder resultTo, String resultWho, int requestCode,
            int startFlags, ProfilerInfo profilerInfo, Bundle options) throws RemoteException {
        Parcel data = Parcel.obtain();
        Parcel reply = Parcel.obtain();
        data.writeInterfaceToken(IActivityManager.descriptor);
        // caller指向Launcher对应的ApplicationThread对象。
        data.writeStrongBinder(caller != null ? caller.asBinder() : null);
        data.writeString(callingPackage);
        // intent 包含了即将启动的Activity组件的信息。
        intent.writeToParcel(data, 0);
        data.writeString(resolvedType);
        // resultTo 指向ActivityManagerService内的ActivityRecord对象，它保存了
        //   Launcher的详细信息。
        data.writeStrongBinder(resultTo);
        ... ...
        mRemote.transact(START_ACTIVITY_TRANSACTION, data, reply, 0);
        ... ...
        return result;
    }
```
它想ActivityManagerService发送了START_ACTIVITY_TRANSACTION的进程间通信请求。

** 以上的步骤都是在Launcher中执行，接下来将转入ActivityManagerService。**
# Setp7 ActivityManagerService::startActivity(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:3849
    public final int startActivity(IApplicationThread caller, String callingPackage,
            Intent intent, String resolvedType, IBinder resultTo, String resultWho, int requestCode,
            int startFlags, ProfilerInfo profilerInfo, Bundle options) {
        return startActivityAsUser(caller, callingPackage, intent, resolvedType, resultTo,
            resultWho, requestCode, startFlags, profilerInfo, options,
            UserHandle.getCallingUserId()); // 🏁
    }
```
# Step8 ActivityManagerService::startActivityAsUser(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java:3858
    public final int startActivityAsUser(IApplicationThread caller, String callingPackage,
            Intent intent, String resolvedType, IBinder resultTo, String resultWho, int requestCode,
            int startFlags, ProfilerInfo profilerInfo, Bundle options, int userId) {
        ... ...
        // 🏁
        // mStackSupervisor类型为ActivityStackSupervisor，描述一个Activity组件堆栈
        return mStackSupervisor.startActivityMayWait(caller, -1, callingPackage, intent,
                resolvedType, null, null, resultTo, resultWho, requestCode, startFlags,
                profilerInfo, null, null, options, false, userId, null, null);
    }
```
# Step9 ActivityStackSupervisor::startActivityMayWait(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStackSupervisor.java:925
    final int startActivityMayWait(IApplicationThread caller, int callingUid,
            String callingPackage, Intent intent, String resolvedType,
            IVoiceInteractionSession voiceSession, IVoiceInteractor voiceInteractor,
            IBinder resultTo, String resultWho, int requestCode, int startFlags,
            ProfilerInfo profilerInfo, WaitResult outResult, Configuration config,
            Bundle options, boolean ignoreTargetSecurity, int userId,
            IActivityContainer iContainer, TaskRecord inTask) {
        ... ...
        boolean componentSpecified = intent.getComponent() != null;

        // Don't modify the client's object!
        intent = new Intent(intent);

        // 解析intent内容，获得启动Activity组件的信息
        ActivityInfo aInfo =
                resolveActivity(intent, resolvedType, startFlags, profilerInfo, userId);
        ... ...
        synchronized (mService) {
            ... ...
            int res = startActivityLocked(caller, intent, resolvedType, aInfo,
                    voiceSession, voiceInteractor, resultTo, resultWho,
                    requestCode, callingPid, callingUid, callingPackage,
                    realCallingPid, realCallingUid, startFlags, options, ignoreTargetSecurity,
                    componentSpecified, null, container, inTask); // 🏁
            ... ...
            return res;
        }
    }
```
# Step10 ActivityStackSupervisor::startActivityMayWait(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStackSupervisor.java:1399
    final int startActivityLocked(IApplicationThread caller,
            Intent intent, String resolvedType, ActivityInfo aInfo,
            IVoiceInteractionSession voiceSession, IVoiceInteractor voiceInteractor,
            IBinder resultTo, String resultWho, int requestCode,
            int callingPid, int callingUid, String callingPackage,
            int realCallingPid, int realCallingUid, int startFlags, Bundle options,
            boolean ignoreTargetSecurity, boolean componentSpecified, ActivityRecord[] outActivity,
            ActivityContainer container, TaskRecord inTask) {
        int err = ActivityManager.START_SUCCESS;

        ProcessRecord callerApp = null;
        if (caller != null) {
            // callerApp指向Launcher组件所在的应用程序进程
            callerApp = mService.getRecordForAppLocked(caller);
            if (callerApp != null) {
                callingPid = callerApp.pid;
                callingUid = callerApp.info.uid;
            } else { ... }
        }
        ... ...
        ActivityRecord sourceRecord = null;
        ActivityRecord resultRecord = null;
        if (resultTo != null) {
            // resultTo指向Launcher在ActivityManagerService中的ActivityRecord
            // 代理对象， sourceRecord得到该代理对象在本地的ActivityRecord对象
            sourceRecord = isInAnyStackLocked(resultTo);
            ... ...
            if (sourceRecord != null) {
                if (requestCode >= 0 && !sourceRecord.finishing) {
                    resultRecord = sourceRecord;
                }
            }
        }
        ... ...
        // 创建即将启动的Activity组件
        ActivityRecord r = new ActivityRecord(mService, callerApp, callingUid, callingPackage,
                intent, resolvedType, aInfo, mService.mConfiguration, resultRecord, resultWho,
                requestCode, componentSpecified, voiceSession != null, this, container, options);
        if (outActivity != null) {
            outActivity[0] = r;
        }
        ... ...
        err = startActivityUncheckedLocked(r, sourceRecord, voiceSession, voiceInteractor,
                startFlags, true, options, inTask); // 🏁
        ... ...
        return err;
    }
```
# Step11 ActivityStackSupervisor::startActivityUncheckedLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStackSupervisor.java:1828
    final int startActivityUncheckedLocked(final ActivityRecord r, ActivityRecord sourceRecord,
            IVoiceInteractionSession voiceSession, IVoiceInteractor voiceInteractor, int startFlags,
            boolean doResume, Bundle options, TaskRecord inTask) {
        final Intent intent = r.intent;
        final int callingUid = r.launchedFromUid;
        ... ...
        int launchFlags = intent.getFlags();
        ... ...
        // 记录即将启动的Activity是否由用户手动启动。如果是，需要向源Activity发送用户离开通知
        mUserLeaving = (launchFlags & Intent.FLAG_ACTIVITY_NO_USER_ACTION) == 0;
        ... ...
        boolean addingToTask = false;
        ... ...
        boolean newTask = false;
        boolean keepCurTransition = false;

        TaskRecord taskToAffiliate = launchTaskBehind && sourceRecord != null ?
                sourceRecord.task : null;

        // 需要创建新任务
        if (r.resultTo == null && inTask == null && !addingToTask
                && (launchFlags & Intent.FLAG_ACTIVITY_NEW_TASK) != 0) {
            newTask = true;
            targetStack = computeStackFocus(r, newTask);
            targetStack.moveToFront("startingNewTask");

            if (reuseTask == null) {
                r.setTask(targetStack.createTaskRecord(getNextTaskId(),
                        newTaskInfo != null ? newTaskInfo : r.info,
                        newTaskIntent != null ? newTaskIntent : intent,
                        voiceSession, voiceInteractor, !launchTaskBehind /* toTop */),
                        taskToAffiliate);
                ... ...
            } else {
                r.setTask(reuseTask, taskToAffiliate);
            }
            ... ...
        } else if (sourceRecord != null) { ... } 
        else if (inTask != null) { ... } 
        else { ... }
        ... ...
        targetStack.startActivityLocked(r, newTask, doResume, keepCurTransition, options); // 🏁
        ... ...
        return ActivityManager.START_SUCCESS;
    }
```
默认情况下目标Activity组件和源组件应该运行在同一个任务中，如果启动标志的FLAG_ACTIVITY_NEW_TASK置为1，且源组件不需要知道目标的运行结果，ActivityManagerService就会将目标组件运行在另一个任务中。组件属性android:taskAffinity描述它的专属任务，当ActivityManagerService决定要将目标组件运行在不同任务中时，ActivityManagerService就会检查目标组建的专属任务是否存在，如果存在就在该专属任务中运行，否则先创建该专属任务。

targetStack的类型为ActivityStack。
# Step12 ActivityStack::startActivityLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStack.java:2074
    final void startActivityLocked(ActivityRecord r, boolean newTask,
            boolean doResume, boolean keepCurTransition, Bundle options) {
        TaskRecord rTask = r.task;
        final int taskId = rTask.taskId;
        // 将目标Activity保存到组件堆栈顶端
        if (!r.mLaunchTaskBehind && (taskForIdLocked(taskId) == null || newTask)) {
            // Last activity in task had been removed or ActivityManagerService is reusing task.
            // Insert or replace.
            // Might not even be in.
            insertTaskAtTop(rTask, r);
            mWindowManager.moveTaskToTop(taskId);
        }
        ... ...
        task = r.task;
        ... ...
        task.addActivityToTop(r);
        task.setFrontOfTask();
        ... ...
        if (doResume) {
            // 将组件堆栈顶端的组件激活
            mStackSupervisor.resumeTopActivitiesLocked(this, r, options);
        }
    }
```
mStackSupervisor的类型为ActivityStackSupervisor。
# Step13 ActivityStackSupervisor::resumeTopActivitiesLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStackSupervisor.java:2727
    boolean resumeTopActivitiesLocked(ActivityStack targetStack, ActivityRecord target,
            Bundle targetOptions) {
        if (targetStack == null) {
            targetStack = mFocusedStack;
        }
        // Do targetStack first.
        boolean result = false;
        if (isFrontStack(targetStack)) {
            result = targetStack.resumeTopActivityLocked(target, targetOptions);
        }

        for (int displayNdx = mActivityDisplays.size() - 1; displayNdx >= 0; --displayNdx) {
            final ArrayList<ActivityStack> stacks = mActivityDisplays.valueAt(displayNdx).mStacks;
            for (int stackNdx = stacks.size() - 1; stackNdx >= 0; --stackNdx) {
                final ActivityStack stack = stacks.get(stackNdx);
                if (stack == targetStack) {
                    // Already started above.
                    continue;
                }
                if (isFrontStack(stack)) {
                    stack.resumeTopActivityLocked(null);
                }
            }
        }
        return result;
    }
```
# Step14 ActivityStack::resumeTopActivityLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStack.java:1540
    final boolean resumeTopActivityLocked(ActivityRecord prev, Bundle options) {
        ... ...
        boolean result = false;
        ... ...
            result = resumeTopActivityInnerLocked(prev, options);
        ... ...
        return result;
    }
```
# Step15 ActivityStack::resumeTopActivityInnerLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStack.java:1561
    private boolean resumeTopActivityInnerLocked(ActivityRecord prev, Bundle options) {
        ... ...
        // 取得堆栈顶端的Activity组件
        final ActivityRecord next = topRunningActivityLocked(null);

        // Remember how we'll process this pause/resume situation, and ensure
        // that the state is reset however we wind up proceeding.
        final boolean userLeaving = mStackSupervisor.mUserLeaving;
        mStackSupervisor.mUserLeaving = false;
        ... ...
        // 即将启动的组件也是当前的活动组件，则啥也不做，退出
        if (mResumedActivity == next && next.state == ActivityState.RESUMED &&
                    mStackSupervisor.allResumedActivitiesComplete()) {
            ... ...
            return false;
        }
        ... ...
        // 即将休眠 且 即将启动的组件刚刚被中止，则直接退
        if (mService.isSleepingOrShuttingDown()
                && mLastPausedActivity == next
                && mStackSupervisor.allPausedActivitiesComplete()) {
            ... ...
        if (mResumedActivity != null) {
            ... ...
            pausing |= startPausingLocked(userLeaving, false, true, dontWaitForPause);
        }
        ... ...
        return true;
    }
```
ActivityStack中三个成员变量：
mResumedActivity：描述当前活动的Activity组件
mLastPausedActivity：描述刚刚被终止的Activity组件
mPausingActivity：描述正在被中止的Activity组件

# Step16 ActivityStack::startPausingLocked(...)
``` java
// frameworks/base/services/core/java/com/android/server/am/ActivityStack.java:1561
    final boolean startPausingLocked(boolean userLeaving, boolean uiSleeping, boolean resuming,
            boolean dontWait) {
        ... ...
        ActivityRecord prev = mResumedActivity;
        ... ...
        mResumedActivity = null;
        mPausingActivity = prev;
        mLastPausedActivity = prev;
        mLastNoHistoryActivity = (prev.intent.getFlags() & Intent.FLAG_ACTIVITY_NO_HISTORY) != 0
                || (prev.info.flags & ActivityInfo.FLAG_NO_HISTORY) != 0 ? prev : null;
        prev.state = ActivityState.PAUSING;
        ... ...
        if (prev.app != null && prev.app.thread != null) {
           ... ...
            try {
                ... ...
                prev.app.thread.schedulePauseActivity(prev.appToken, prev.finishing,
                        userLeaving, prev.configChangeFlags, dontWait);
            } catch (Exception e) { ... }
        } else { ... }
        ... ...
        if (mPausingActivity != null) {
            ... ...
            if (dontWait) { ... } 
            else {
                ... ...
                Message msg = mHandler.obtainMessage(PAUSE_TIMEOUT_MSG);
                msg.obj = prev;
                prev.pauseTime = SystemClock.uptimeMillis();
                mHandler.sendMessageDelayed(msg, PAUSE_TIMEOUT);
                ... ...
                return true;
            }

        } else { ... }
    }
```