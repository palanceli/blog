---
layout: post
title: 键盘消息处理学习笔记（一）
date: 2016-09-04 14:18:02 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
最近一个礼拜把《Android源码情景分析》之键盘消息处理机制的内容学习了一遍，感觉相比Binder要简单好多，而且有了智能指针和Binder的基础，学习键盘消息处理几乎没有什么障碍了。不过Android2.x和Android6之间的差异巨大，完全掌握最新的Android键盘消息处理机制还有很长的路要走。如Binder系列，我还是打算分两个个板块来记录Android键盘消息处理机制的探索：1、学习笔记；2、深度探索。“学习笔记”主要记录初次学习中遇到的所有细节问题，目前我对键盘消息处理也仅处于“身在此山中”的状态，每个知识点都有些印象，但不成体系。完成学习笔记之后，我会再来回顾一遍，用自己的理解把它们讲出来，这就是“深度探索”系列的任务了。
<!-- more -->

# InputManagerService的启动和创建
键盘消息处理机制的源头在InputManagerService，因此从它的启动搞起。在Android6中，InputManagerService是在SystemServer中直接被启动的，如下：
``` java
// frameworks/base/services/java/com/android/server/SystemServer.java:167
public final class SystemServer {
... ...
    public static void main(String[] args) {    // 入口函数
        new SystemServer().run();
    }

    private void run() {
        ... ... 
        try {       // :270
            ... ...
            startOtherServices();               // 启动一批Services
        } catch (Throwable ex) {
            ... ...
        }
    }
    private void startOtherServices() {
        try{
            ... ... // :497
            inputManager = new InputManagerService(context);
            ... ...
            wm = WindowManagerService.main(context, inputManager,
                    mFactoryTestMode != FactoryTest.FACTORY_TEST_LOW_LEVEL,
                    !mFirstBoot, mOnlyCore);
            ServiceManager.addService(Context.WINDOW_SERVICE, wm);
            ServiceManager.addService(Context.INPUT_SERVICE, inputManager);

            mActivityManagerService.setWindowManager(wm);

            inputManager.setWindowManagerCallbacks(wm.getInputMonitor());
            inputManager.start();
        } catch (RuntimeException e) {
            ... ...
        }

```
这跟《源码分析》有些差异，在Android2.3中InputManager是在WindowManagerService中被创建和启动的。
## 创建
接下来看InputManagerService在创建过程中都做了什么：

<a name="InputManagerService__InputManagerService"></a>
``` java
// frameworks/base/services/core/java/com/android/server/input/InputManagerService.java

public class InputManagerService extends IInputManager.Stub
        implements Watchdog.Monitor {
    ... ...
    // :278
    public InputManagerService(Context context) {
        ... ...
        mPtr = nativeInit(this, mContext, mHandler.getLooper().getQueue());
        ... ...
    }
    ... ...
}
```
InputManagerService::mPtr是函数nativeInit(...)的返回值，继续看该函数返回的是一个NativeInputManager对象：
``` java
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp
// :1035
static jlong nativeInit(JNIEnv* env, jclass /* clazz */,
        jobject serviceObj, jobject contextObj, jobject messageQueueObj) {
    ... ...
    NativeInputManager* im = new NativeInputManager(contextObj, serviceObj,
            messageQueue->getLooper());
    im->incStrong(0);
    return reinterpret_cast<jlong>(im);
}
```
<a name="NativeInputManager__NativeInputManager"></a>
``` java
// :288
NativeInputManager::NativeInputManager(jobject contextObj,
        jobject serviceObj, const sp<Looper>& looper) :
        mLooper(looper), mInteractive(true) {
    ... ...
    sp<EventHub> eventHub = new EventHub();
    mInputManager = new InputManager(eventHub, this, this);
}

// frameworks/native/services/inputflinger/InputManager.cpp
// :27
InputManager::InputManager(
        const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& readerPolicy,
        const sp<InputDispatcherPolicyInterface>& dispatcherPolicy) {
    mDispatcher = new InputDispatcher(dispatcherPolicy);
    mReader = new InputReader(eventHub, readerPolicy, mDispatcher);
    initialize();
}

// :48
void InputManager::initialize() {
    mReaderThread = new InputReaderThread(mReader);
    mDispatcherThread = new InputDispatcherThread(mDispatcher);
}

// frameworks/native/services/inputflinger/InputDispatcher.cpp:202
InputDispatcher::InputDispatcher(const sp<InputDispatcherPolicyInterface>& policy) :
    mPolicy(policy),
    mPendingEvent(NULL), mLastDropReason(DROP_REASON_NOT_DROPPED),
    mAppSwitchSawKeyDown(false), mAppSwitchDueTime(LONG_LONG_MAX),
    mNextUnblockedEvent(NULL),
    mDispatchEnabled(false), mDispatchFrozen(false), mInputFilterEnabled(false),
    mInputTargetWaitCause(INPUT_TARGET_WAIT_CAUSE_NONE) {
    mLooper = new Looper(false);
    ... ...
}

// frameworks/native/services/inputflinger/InputReader.cpp:249
InputReader::InputReader(const sp<EventHubInterface>& eventHub,
        const sp<InputReaderPolicyInterface>& policy,
        const sp<InputListenerInterface>& listener) :
        mContext(this), mEventHub(eventHub), mPolicy(policy),
        mGlobalMetaState(0), mGeneration(1),
        mDisableVirtualKeysTimeout(LLONG_MIN), mNextTimeout(LLONG_MAX),
        mConfigurationChangesToRefresh(0) {
    mQueuedListener = new QueuedInputListener(listener);

    { // acquire lock
        AutoMutex _l(mLock);

        refreshConfigurationLocked(0);
        updateGlobalMetaStateLocked();
    } // release lock
}
```
总结一下：InputManagerService的创建包含：
* 构造NativeInputManager
* 构造EventHub
* 构造InputManager
* 构造InputDispatcher
* 构造InputReader
* 构造InputReaderThread
* 构造InputDispatcherThread
* 构造Looper
* 构造QueuedInputListener

## 启动
InputManagerService的启动是由[SystemServer::startOtherServices()](#InputManagerService的启动和创建)中的
`inputManager.start()`
引爆：
``` java
// frameworks/base/services/core/java/com/android/server/input/InputService.java

public class InputManagerService extends IInputManager.Stub
        implements Watchdog.Monitor {
        ... ...
    // :299
    public void start() {
        ... ...
        nativeStart(mPtr);
        ... ...
    }
    ... ...
}

// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp
// :1049
static void nativeStart(JNIEnv* env, jclass /* clazz */, jlong ptr) {
    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);

    status_t result = im->getInputManager()->start();
    ... ...
}
```
参数im来自InputManagerService::mPtr，在[InputManagerService的构造函数](#InputManagerService__InputManagerService)中已有分析，它是一个NativeInputManager对象。
它的getInputManager()返回成员变量mInputManager：
``` c++
class NativeInputManager : public virtual RefBase,
    public virtual InputReaderPolicyInterface,
    public virtual InputDispatcherPolicyInterface,
    public virtual PointerControllerPolicyInterface {
    ... ...
    inline sp<InputManager> getInputManager() const { return mInputManager; }
};
```
在[NativeInputManager的构造函数](#NativeInputManager__NativeInputManager)中，mInputManager是新创建的InputManager对象。

<font color="red">待续...</font>