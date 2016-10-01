---
layout: post
title: 键盘消息处理学习笔记（二）
date: 2016-10-01 22:28:50 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
# 启动
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