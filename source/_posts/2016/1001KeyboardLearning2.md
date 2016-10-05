---
layout: post
title: 键盘消息处理学习笔记（二）
date: 2016-10-01 22:28:50 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
在《键盘消息处理学习笔记（一）》中讨论了InputManagerService的创建。在[Step1中](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/#Step1-InputManagerService的创建)，完成InputManagerService创建之后，调用其start()函数，完成启动。本文就以该start()函数为起点进入启动过程的探索。
<!-- more -->
# Step1: InputManagerService::start()
``` java
// frameworks/base/services/core/java/com/android/server/input/InputService.java
public class InputManagerService extends IInputManager.Stub
        implements Watchdog.Monitor {
        ... ...
    // :299
    public void start() {
        ... ...
        nativeStart(mPtr);  // 🏁
        ... ...
    }
    ... ...
}
```
参见[InputManagerService相关对象关系图](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/img02.png)可知，mPtr是NativeInputManager对象的指针，是在InputManagerService创建过程的Step4中创建的。

# Step2: nativeStart(...)
``` cpp
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:1049
static void nativeStart(JNIEnv* env, jclass /* clazz */, jlong ptr) {
    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);

    status_t result = im->getInputManager()->start(); // 🏁
    ... ...
}
```
NativeInputManager::getInputManager()返回成员变量mInputManager，类型为InputManager。该对象是在[InputManagerService的创建过程Step4中](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/#Step4-NativeInputManager-NativeInputManager-…)被创建出来的。
``` c++
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp: 184
class NativeInputManager : public virtual RefBase,
    public virtual InputReaderPolicyInterface,
    public virtual InputDispatcherPolicyInterface,
    public virtual PointerControllerPolicyInterface {
    ... ...
    inline sp<InputManager> getInputManager() const { return mInputManager; }
};
```

# Step3: InputManager::start()
``` cpp
// frameworks/native/servies/inputflinger/InputManager.cpp:53
status_t InputManager::start() {
    status_t result = mDispatcherThread->run("InputDispatcher", 
                                    PRIORITY_URGENT_DISPLAY);  // 🏁《键盘消息处理笔记（三）》中讨论
    ... ...

    result = mReaderThread->run("InputReader", 
                                PRIORITY_URGENT_DISPLAY);  // 🏁《键盘消息处理笔记（三）》中讨论
    ... ...
}
```
mDispatcherThread和mReaderThread是InputManager在构造时创建的两个线程对象。他们均继承自Thread，当run(...)被调用时，实际进入了各自的线程函数threadLoop(...)。

# 总结
InputManagerService的启动过程如下：
![InputManagerService的启动过程](1001KeyboardLearning2/img01.png)
所以接下来就需要深入到InputDispatcherThread和InputReaderThread两个线程函数里去了。