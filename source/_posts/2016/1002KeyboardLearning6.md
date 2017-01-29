---
layout: post
title: 键盘消息处理学习笔记（六）——注册Server端InputChannel
date: 2016-10-02 23:35:08 +0800
categories: Android学习笔记
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接[《键盘消息处理学习笔记（五）》之Step3](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/#Step3-WindowManagerService-addWindow-…)，在创建一对互联的InputChannel之后，通过函数mInputManager.registerInputChannel(...)，把Server端InputChannel注册到InputManager，本文继续深入这个注册函数。
<!-- more -->
# Step1: InputManagerService::registerInputChannel(...)
``` java
// frameworks/base/services/core/java/com/android/server/input/InputManagerService.java:481
    public void registerInputChannel(InputChannel inputChannel,
            InputWindowHandle inputWindowHandle) {
        ... ...
        nativeRegisterInputChannel(mPtr, inputChannel, inputWindowHandle, false); // 🏁
    }
```
在[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step3中，传入regisgetInputChannel函数的第一个参数正是刚刚创建的Server端InputChannel：
``` java
mInputManager.registerInputChannel(win.mInputChannel, win.mInputWindowHandle);
```
在《键盘消息处理学习笔记（一）》的[对象关系图中](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/img02.png)可以看到InputManagerService::mPtr是指向NativeInputManager对象的指针。

# Step2: nativeRegisterInputChannel(...)
``` c++
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:1142
// inputChannelObj     Server端InputChannel
static void nativeRegisterInputChannel(JNIEnv* env, jclass /* clazz */,
        jlong ptr, jobject inputChannelObj, jobject inputWindowHandleObj, 
        jboolean monitor) {

    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);    
    // 把java层的InputChannel转换为C++层InputChannel
    sp<InputChannel> inputChannel = android_view_InputChannel_getInputChannel(env, inputChannelObj);   
    ... ...
    sp<InputWindowHandle> inputWindowHandle =
            android_server_InputWindowHandle_getHandle(env, inputWindowHandleObj);

    status_t status = im->registerInputChannel(
            env, inputChannel, inputWindowHandle, monitor);     // 🏁
    ... ...
    if (! monitor) {
        android_view_InputChannel_setDisposeCallback(env, inputChannelObj,
                handleInputChannelDisposed, im);
    }
}
```

# Step3: NativeInputManager.registerInputChannel(...)
``` c++
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:377
// inputChannel     Server端InputChannel
status_t NativeInputManager::registerInputChannel(JNIEnv* /* env */,
        const sp<InputChannel>& inputChannel,
        const sp<InputWindowHandle>& inputWindowHandle, bool monitor) {
    return mInputManager->getDispatcher()->registerInputChannel(
            inputChannel, inputWindowHandle, monitor);
}
```
参见《键盘消息处理学习笔记（一）》的[对象关系图](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/img02.png)mInputManager->getDispatcher()返回其mDispatcher成员，其类型是InputDispatcher。

# Step4: InputDispatcher::registerInputChannel(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:3311
status_t InputDispatcher::registerInputChannel(const sp<InputChannel>& inputChannel,
        const sp<InputWindowHandle>& inputWindowHandle, bool monitor) {
        ... ...
        // 如果inputChannel已经注册过了，则返回错误
        if (getConnectionIndexLocked(inputChannel) >= 0) {
            ... ...
            return BAD_VALUE;
        }

        sp<Connection> connection = new Connection(inputChannel, inputWindowHandle, monitor);

        int fd = inputChannel->getFd();     // Server端的scoket描述符
        // 以fd为关键字，保存inputChannel对应的Connection对象
        mConnectionsByFd.add(fd, connection);
        ... ...
        // 把fd注册到mLooper，当fd收到数据时，mLooper将被唤醒
        mLooper->addFd(fd, 0, ALOOPER_EVENT_INPUT, handleReceiveCallback, this);
    ... ...
    return OK;
}
```
回顾一下inputChannel是在[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step6中，通过InputChannel::openInputChannelPair(...)创建的：
``` c++
    String8 serverChannelName = name;
    serverChannelName.append(" (server)");
    outServerChannel = new InputChannel(serverChannelName, sockets[0]);
    String8 clientChannelName = name;
    clientChannelName.append(" (client)");
    outClientChannel = new InputChannel(clientChannelName, sockets[1]);
    return OK;
```
在构造函数中传入的第二个参数正是fd，它是Server端和Client端相互连接的一对socket中Server端的描述符：
``` c++
// frameworks/native/include/input/InputTransport.h:143
class InputChannel : public RefBase {

    InputChannel(const String8& name, int fd);
    ... ...
    InputChannel(const String8& name, int fd);
    ... ...
};
```
# 总结
本节和上一节是个关键，我初次学习的时候也是在这里首先晕掉的，因为Binder机制模糊了进程的边界，这给操作带来了很大便利，却也给理解蒙上一层迷雾，一不留神就搞不清楚当前是在哪个进程空间。

当一个窗体创建时，它会向WindowManagerService发送请求，要求WindowManagerService为之创建一对用socket实现的InputChannel。本节把其中一个（Server端的）InputChannel的socket描述符注册到InputManagerService的InputDispatcher线程的mLooper中。
还记得在《键盘消息处理学习笔记（三）》中[InputDispatcherThreader的启动](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning3/#InputDispatcherThread的启动)一节我们探讨过的，当时这个线程通过`mLooper->pollOnce(...)`等待在了默认描述符mWakeEventFd处。结合本节的内容，**系统每创建一个可以接收键盘事件的Activity，就会向InputManagerService的InputDispatcher线程的mLooper注册一个InputChannel，以便纳入InputManagerService的监控。**“Server端Channel”的命名也是因此而来。具体怎么个用法，我们后面再探索。

----
# 疑问一：InputChannel如何能跨进程传输？
此处我还有个疑问：Binder为进程间通信提供了便利，可是细想这里面是有大坑的，比如socket对是在WindowManagerService进程中创建的，这个描述符显然不能跨进程使用；再如Binder只能在进程间传递与进程无关的数据，与进程相关的比如抽象数据类型，如果要传递，必须转成与进程无关才可以。而《键盘消息处理学习笔记（五）》中，ViewRootImpl::setView(...)开头便是：
``` java
public void setView(View view, WindowManager.LayoutParams attrs, View panelParentView) {
    ... ...
    mInputChannel = new InputChannel();
    ... ...
    // 把本地对象通过Binder代理传给mWindowSession
    res = mWindowSession.addToDisplay(mWindow, mSeq, mWindowAttributes,
            getHostVisibility(), mDisplay.getDisplayId(),
            mAttachInfo.mContentInsets, mAttachInfo.mStableInsets,
            mAttachInfo.mOutsets, mInputChannel);
    ... ...
}
```
它把一个本地对象传给了WindowSession的Binder代理，这是什么思想感情呢？

在查看InputChannel的定义时我找到了这个问题的答案：
``` java
// frameworks/base/core/java/android/view/InputChannel.java:30
public final class InputChannel implements Parcelable {
    ... ...
        @Override
    public void writeToParcel(Parcel out, int flags) {
        ... ...
        nativeWriteToParcel(out);
        ... ...
    }
}
```
Parcelable很眼熟，是的，在Binder中用于将一个本地对象“拍扁”的工具，“拍扁”后的对象即可用于进程间传递。派生自Parcelable，说明InputChannel可以用于进程间传递。这个类的Java层定义没有什么数据成员，只有一个指向jni层的指针，说明它的定义全在c++层，再看它的“拍扁”接口`writeToParcel(...)`也定义在jni层。

先看看c++层InputChannel的定义，也只有两个数据成员，名称和描述符：
``` c++
// frameworks/native/include/input/InputTransport.h:138
class InputChannel : public RefBase {
    ... ...
    String8 mName;
    int mFd;
};
```
再来看它的“拍扁”逻辑：
``` c++
// frameworks/base/core/jni/android_view_InputChannel.cpp:222
static void android_view_InputChannel_nativeWriteToParcel(JNIEnv* env, jobject obj,
        jobject parcelObj) {
    ... ...
    sp<InputChannel> inputChannel = nativeInputChannel->getInputChannel();

    parcel->writeInt32(1);
    parcel->writeString8(inputChannel->getName());
    parcel->writeDupFileDescriptor(inputChannel->getFd());
    ... ...
}
```
不过是把名字和文件描述符传了出去，到了对端再根据这些数据组装成本地对象，这就解答了InputChannel如何跨进程传输的问题。
不过疑云并没有彻底散去：这个只有在本地才有效的文件描述符传到对端有什么意义呢？在本节中，还没有遇到跨进程使用描述符的情况（相信不可能遇到），因为两个互联的socket是在WindowManagerService中创建，本节中又交给InputManagerService中的InputDispatcherThreader线程等待，他们都在同一个进程空间，这当然没什么问题。可是把InputChannel在进程间传来传去的，只是在物理意义上消除了进程间的界限，在逻辑上关系上却始终要注意“这个描述符是在哪里创建的，我能不能使用”，我感觉这是比C++的内存泄漏更大的陷阱呢？
好吧，疑云先驱散到这里，我觉得更多的得往后继续推进才能获得解答。
