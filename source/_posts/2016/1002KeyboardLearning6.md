---
layout: post
title: 键盘消息处理学习笔记（六）
date: 2016-10-02 23:35:08 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step3。通过函数mInputManager.registerInputChannel(...)，把Server端InputChannel注册到InputManager，本文继续深入这个注册函数。
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

    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);    // 将指针还原为NativeInputManager类型

    sp<InputChannel> inputChannel = android_view_InputChannel_getInputChannel(env,
            inputChannelObj);   // 把java层的InputChannel转换为C++层InputChannel
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
