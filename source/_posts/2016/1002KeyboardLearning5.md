---
layout: post
title: 键盘消息处理学习笔记（五）——InputChannel的创建
date: 2016-10-02 21:17:38 +0800
categories: Android学习笔记
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
本文的起点是ViewRootImpl的setView(...)函数，先不管Android系统中它和Activity之间的关系，只需要知道它是Activity创建的必经之路。本文的目标是探索InputChannel的创建过程，等这个过程捋顺了，以后再探索窗体的创建过程。
<!-- more -->
# Step1: ViewRootImpl::setView(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:447
    public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView) {
        ... ...
                mView = view;
                ... ...
                mAdded = true;
                ... ...
                    mInputChannel = new InputChannel();
                ... ...
                    // 🏁将正在启动的应用程序窗口添加到WindowManagerService中
                    res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes,
                            getHostVisibility(), mDisplay.getDisplayId(),
                            mAttachInfo.mContentInsets, mAttachInfo.mStableInsets,
                            mAttachInfo.mOutsets, mInputChannel);
                ... ...
                if (view instanceof RootViewSurfaceTaker) {
                    mInputQueueCallback =
                        ((RootViewSurfaceTaker)view).willYouTakeTheInputQueue();
                }
                if (mInputChannel != null) {
                    if (mInputQueueCallback != null) {
                        mInputQueue = new InputQueue();
                        mInputQueueCallback.onInputQueueCreated(mInputQueue);
                    }
                    // 🏁将mInputChannel注册到正在启动的Activity所在进程的主线程中
                    // 在《键盘消息处理学习笔记（八）》中深入讨论
                    mInputEventReceiver = new WindowInputEventReceiver(mInputChannel,
                            Looper.myLooper());
                }
                ... ...
    }
```
mWindowSession是在ViewRootImpl的构造函数中创建的：
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:358
    public ViewRootImpl(Context context, Display display) {
        mContext = context;
        mWindowSession = WindowManagerGlobal.getWindowSession();
        ... ...
    } 
```
WindowManagerGlobal.getWindowSession()是一个单例工厂方法：
``` java
// frameworks/base/core/java/android/view/WindowManagerGlobal.java:148
    public static IWindowSession getWindowSession() {
        synchronized (WindowManagerGlobal.class) {
            if (sWindowSession == null) {
                ... ...
                    InputMethodManager imm = InputMethodManager.getInstance();
                    // 获得WindowManagerService的代理对象
                    IWindowManager windowManager = getWindowManagerService();
                    // 获得session的代理对象，并保存到静态变量sWindowsSession
                    sWindowSession = windowManager.openSession(
                            new IWindowSessionCallback.Stub() {
                                @Override
                                public void onAnimatorScaleChanged(float scale) {
                                    ValueAnimator.setDurationScale(scale);
                                }
                            },
                            imm.getClient(), imm.getInputContext());
                ... ...
            }
            return sWindowSession;
        }
    }
```
sWindowSession是一个静态变量，getWindowManagerService()返回的是WindowManagerService的代理对象，通过它的openSession(...)得到的当然也是WindowSession的代理对象。
> 注意，由于它们都是Binder代理对象，以后对他们的调用都是跨进程的请求，实际执行是在WindowManagerService所在的进程中完成。
> Binder是Android下一个神奇的机制，它弱化了进程之间的边界。在我的《Binder学习笔记》和《深度探索Binder》系列中有深入的讨论。

回到ViewRootImpl::setView(...)中，它调用mWindowSession.addToDisplay(...)向运行在WindowManagerService中的一个Session发送进程间通信请求，将正在启动的应用程序窗口添加到WindowManagerService中。

# Step2: Session::addToDisplay(...)
接下来的代码就是在WindowManagerService进程内完成的了。
``` java
// frameworks/base/services/core/java/com/android/server/wm/Session.java:69
    // outInputChannel  ViewRootImpl::mInputChannel
    // window           ViewRootImpl::mWindow
    public int addToDisplay(IWindow window, int seq, WindowManager.LayoutParams attrs,
            int viewVisibility, int displayId, Rect outContentInsets, Rect outStableInsets,
            Rect outOutsets, InputChannel outInputChannel) {
        return mService.addWindow(this, window, seq, attrs, viewVisibility, displayId,
                outContentInsets, outStableInsets, outOutsets, outInputChannel);
    }
```
其中mService类型为WindowManagerService。

# Step3: WindowManagerService::addWindow(...)
``` java
// frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java:2353
    // outInputChannel  ViewRootImpl::mInputChannel
    // client           ViewRootImpl::mWindow
    public int addWindow(Session session, IWindow client, int seq,
            WindowManager.LayoutParams attrs, int viewVisibility, int displayId,
            Rect outContentInsets, Rect outStableInsets, Rect outOutsets,
            InputChannel outInputChannel) {
        ... ...
        WindowState attachedWindow = null;
        ... ...
        synchronized(mWindowMap) {
            ... ...
            // 描述正在启动的应用程序窗口
            WindowState win = new WindowState(this, session, client, token,
                    attachedWindow, appOp[0], seq, attrs, viewVisibility, displayContent);
            ... ...
            // 此句为真
            if (outInputChannel != null && (attrs.inputFeatures
                    & WindowManager.LayoutParams.INPUT_FEATURE_NO_INPUT_CHANNEL) == 0) {    
                String name = win.makeInputChannelName();
                // 🏁创建一对InputChannel
                InputChannel[] inputChannels = InputChannel.openInputChannelPair(name);
                // server端InputChannel     
                win.setInputChannel(inputChannels[0]);

                // client端InputChannel，用inputChannels[1]初始化outInputChannel
                // 即：将outInputChannel的C++层指针指向inputChannels[1]
                inputChannels[1].transferTo(outInputChannel);
                // 🏁把server端InputChannel注册到InputManager
                // 详见《键盘消息处理学习笔记（六）》
                mInputManager.registerInputChannel(win.mInputChannel, win.mInputWindowHandle);
            }
            ... ...
            // client即ViewRootImpl::mWindow，是正在创建的窗口的代理对象
            // 以该代理的IBinder接口为key，保存WindowState对象
            mWindowMap.put(client.asBinder(), win);
            ... ...
            if (type == TYPE_INPUT_METHOD) {
                ... ...
            } else if (type == TYPE_INPUT_METHOD_DIALOG) {
                ... ...
            } else { // 如果正在创建的窗口不是与输入法相关的窗口
                // 将正在创建的WindowState保存在mWindows所描述的窗口列表中
                addWindowToListInOrderLocked(win, true);
                ... ...
            }
            ... ...

            boolean focusChanged = false;
            if (win.canReceiveKeys()) { // 可以接收键盘事件
                // 将正在创建的窗口作为当前活动窗口，即把win保存在mCurrentFocus中
                focusChanged = updateFocusedWindowLocked(UPDATE_FOCUS_WILL_ASSIGN_LAYERS,
                        false /*updateInputWindows*/);
                ... ...
            }
            ... ...
            // 如果当前活动窗口和正在启动的窗口不是同一个窗口，则当前焦点会发生改变
            if (focusChanged) {
                // 🏁把正在启动的窗口注册到InputDispatcher中，以便它可以将键盘
                // 事件分发给窗口，在《键盘消息处理学习笔记（七）》中详细讨论
                mInputMonitor.setInputFocusLw(mCurrentFocus, false /*updateInputWindows*/);
            }
            ... ...
        }
        ... ...
    }
```
关于`inputChannels[1].transferTo(outInputChannel);`这句，后面还会关注，我们先把它背后做了什么得出个结论放在这：
``` java
// frameworks/base/core/java/android/view/InputChannel.java:121
// 让outParameter的mPtr指向this，让this的mPtr废掉
    public void transferTo(InputChannel outParameter) {
        ... ...
        nativeTransferTo(outParameter);
    }
```
``` c++
// frameworks/base/core/jni/android_view_InputChannel.cpp:178
// 让otherObj的mPtr指向obj，让obj的mPtr指向空
static void android_view_InputChannel_nativeTransferTo(JNIEnv* env, 
        jobject obj, jobject otherObj) {
    ... ...
    NativeInputChannel* nativeInputChannel =
            android_view_InputChannel_getNativeInputChannel(env, obj);
    android_view_InputChannel_setNativeInputChannel(env, otherObj, nativeInputChannel);
    android_view_InputChannel_setNativeInputChannel(env, obj, NULL);
}
```
``` c++
// frameworks/base/core/jni/android_view_InputChannel.cpp:90
// 让inputChannelObj.mPtr指向nativeInputChannel.mPtr
static void android_view_InputChannel_setNativeInputChannel(JNIEnv* env, 
        jobject inputChannelObj, NativeInputChannel* nativeInputChannel) {
    env->SetLongField(inputChannelObj, gInputChannelClassInfo.mPtr,
             reinterpret_cast<jlong>(nativeInputChannel));
}
```
综上所述，
`inputChannels[1].transferTo(outInputChannel)`
的含义就是让outInputChannel“变成”inputChannels[1]，所谓“变成”是指令其C++层实体对象指向后者。跟C++的引用很像：
`InputChannel& outInputChannel = inputChannels[1];`

# Step4: InputChannel::openInputChannelPair(...)
``` java
// frameworks/base/core/java/android/view/InputChannel.java:86
    public static InputChannel[] openInputChannelPair(String name) {
        ... ...
        return nativeOpenInputChannelPair(name);
    }
```
# Step5: nativeOpenInputChannelPair(...)
``` cpp
// frameworks/base/core/jni/android_view_InputChannel.cpp:123
static jobjectArray android_view_InputChannel_nativeOpenInputChannelPair(JNIEnv* env,
        jclass clazz, jstring nameObj) {
    const char* nameChars = env->GetStringUTFChars(nameObj, NULL);
    String8 name(nameChars);
    env->ReleaseStringUTFChars(nameObj, nameChars);

    sp<InputChannel> serverChannel;
    sp<InputChannel> clientChannel;
    // 🏁创建一个server端InputChannel和一个client端InputChannel
    status_t result = InputChannel::openInputChannelPair(name, serverChannel, clientChannel);
    ... ...
    jobjectArray channelPair = env->NewObjectArray(2, gInputChannelClassInfo.clazz, NULL);
    ... ...
    // 把C++层的InputChannel对象封装成java层InputChannel对象
    jobject serverChannelObj = android_view_InputChannel_createInputChannel(env,
            new NativeInputChannel(serverChannel));
    ... ...
    // 把C++层的InputChannel对象封装成java层InputChannel对象
    jobject clientChannelObj = android_view_InputChannel_createInputChannel(env,
            new NativeInputChannel(clientChannel));
    ... ...
    // 将两个对象保存到数组channelPair，返回给调用者
    env->SetObjectArrayElement(channelPair, 0, serverChannelObj);
    env->SetObjectArrayElement(channelPair, 1, clientChannelObj);
    return channelPair;
}
```
# Step6: InputChannel::openInputChannelPair(...)
``` cpp
// frameworks/native/libs/input/InputTransport.cpp: 124
status_t InputChannel::openInputChannelPair(const String8& name,
        sp<InputChannel>& outServerChannel, sp<InputChannel>& outClientChannel) {
    int sockets[2];
    // 创建一对匿名的相互连接的socket，成功返回0
    if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sockets)) {
        ... ...
    }

    int bufferSize = SOCKET_BUFFER_SIZE;
    setsockopt(sockets[0], SOL_SOCKET, SO_SNDBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[0], SOL_SOCKET, SO_RCVBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[1], SOL_SOCKET, SO_SNDBUF, &bufferSize, sizeof(bufferSize));
    setsockopt(sockets[1], SOL_SOCKET, SO_RCVBUF, &bufferSize, sizeof(bufferSize));

    String8 serverChannelName = name;
    serverChannelName.append(" (server)");
    outServerChannel = new InputChannel(serverChannelName, sockets[0]);

    String8 clientChannelName = name;
    clientChannelName.append(" (client)");
    outClientChannel = new InputChannel(clientChannelName, sockets[1]);
    return OK;
}
```
Server端的InputChannel和Client端的InputChannel实际上是两个相互连接的socket。

# 总结
窗体在创建的时候会向WindowManagerService发送跨进程请求，将自己添加到WindowManagerService中。WindowManagerService收到请求后会创建一对相互连接的InputChannel，一个用于Server端，一个用于Client端，这一对互联的InputChannel是通过socket来实现的。
