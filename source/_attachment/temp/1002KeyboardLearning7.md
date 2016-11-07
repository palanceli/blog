---
layout: post
title: 键盘消息处理学习笔记（七）——创建新窗口在InputDispatcher更新的注册信息
date: 2016-10-03 20:09:28 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step3：
``` java
    // 如果当前活动窗口和正在启动的窗口不是同一个窗口，则当前焦点会发生改变
    if (focusChanged) {
        // 🏁把正在启动的窗口注册到InputDispatcher中，以便它可以将键盘事件分发给窗口
        mInputMonitor.setInputFocusLw(mCurrentFocus, false /*updateInputWindows*/);
    }
```
通过函数mInputMonitor.setInputFocusLw(...)，把当前活动窗口注册到InputDispatcher中，以便它可以将键盘事件分发给窗口，本文继续深入这个注册函数。
需要注意的是：该函数是应用程序创建Activi时，通过WindowSession代理向WindowManagerService发送跨进程请求时，WindowManagerService响应执行的代码，所以该段代码所在的进程空间是WindowManagerService所在的进程，而不是应用程序进程。
<!-- more -->

mInputMonitor在WindowManagerService的块中完成初始化：
``` java
// frameworks/base/services/core/java/com/android/server/wm/WindowManagerService.java:7550
    final InputMonitor mInputMonitor = new InputMonitor(this);
```
# Step1: InputMonitor::setInputFocusLw(...)
``` java
// frameworks/base/services/core/java/com/android/server/wm/InputMontor.java:398
    public void setInputFocusLw(WindowState newWindow, boolean updateInputWindows) {
        ... ...
        if (newWindow != mInputFocus) {
            ... ...
            // mInputFocus用来描述当前活动窗口
            mInputFocus = newWindow;
            setUpdateInputWindowsNeededLw();

            if (updateInputWindows) {
                // 🏁将mInputFocus注册到InputDispatcher
                updateInputWindowsLw(false /*force*/);  
            }
        }
    }
```

# Step2: InputMonitor::updateInputWindowsLw(...)
``` java
// frameworks/base/services/core/java/com/android/server/wm/InputMontor.java:229
    public void updateInputWindowsLw(boolean force) {
        ... ...
        mUpdateInputWindowsNeeded = false;
        ... ...
        // Add all windows on the default display.
        // mDisplayContents中保存了所有的显示设备
        final int numDisplays = mService.mDisplayContents.size();
        for (int displayNdx = 0; displayNdx < numDisplays; ++displayNdx) {
            WindowList windows = mService.mDisplayContents.valueAt(displayNdx).getWindowList();
            // windows中保存了所有需要接收键盘事件的窗口
            for (int winNdx = windows.size() - 1; winNdx >= 0; --winNdx) {
                final WindowState child = windows.get(winNdx);
                final InputChannel inputChannel = child.mInputChannel;
                final InputWindowHandle inputWindowHandle = child.mInputWindowHandle;
                ... ...
                if (addInputConsumerHandle
                        && inputWindowHandle.layer <= mService.mInputConsumer.mWindowHandle.layer) {
                    addInputWindowHandleLw(mService.mInputConsumer.mWindowHandle);
                    addInputConsumerHandle = false;
                }
                ... ...
                // 遍历所有现实设备下所有需要接收键盘事件的窗口，把他们添加到
                // mInputWindowHandles中
                addInputWindowHandleLw(inputWindowHandle, child, flags, type, isVisible, hasFocus,
                        hasWallpaper);
            }
        }

        // Send windows to native code.
        // 🏁把mInputWindowHandles中的窗口重新注册到InputDispatcher中
        mService.mInputManager.setInputWindows(mInputWindowHandles); 

        // Clear the list in preparation for the next round.
        clearInputWindowHandlesLw();
        ... ...
    }
```
InputMonitor::mService的类型为WindowManagerService。
此处把所有需要接收键盘事件的应用窗口都添加到mInputWindowHandles中了。mInputWindowHandles是一个InputWindowHandle数组，函数`addInputWindowHandleLw`把参数所代表的窗口添加到该数组中。InputManagerService::setInputWindows(...)负责把这些窗口重新注册到InputDispatcher中，以便InputDispatcher知道哪些窗口需要接收键盘事件，那个窗口是当前活动窗口。
# Step3: InputManagerService::setInputWindows(...)
``` java
// frameworks/base/services/core/java/com/android/server/input/InputManagerService.java:1249
    public void setInputWindows(InputWindowHandle[] windowHandles) {
        nativeSetInputWindows(mPtr, windowHandles);     // 🏁
    }
```
# Step4: nativeSetInputWindows(...)
``` c++
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:1232
static void nativeSetInputWindows(JNIEnv* env, jclass /* clazz */,
        jlong ptr, jobjectArray windowHandleObjArray) {
    NativeInputManager* im = reinterpret_cast<NativeInputManager*>(ptr);

    im->setInputWindows(env, windowHandleObjArray);     // 🏁
}
```
# Step5: NativeInputManager::setInputWindows(...)
``` c++
// frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:662
void NativeInputManager::setInputWindows(JNIEnv* env, 
                    jobjectArray windowHandleObjArray) {
    Vector<sp<InputWindowHandle> > windowHandles;

    // 将java层的InputWindowHandle对象转成C++层对象，并保存到windowHandles
    if (windowHandleObjArray) {
        jsize length = env->GetArrayLength(windowHandleObjArray);
        for (jsize i = 0; i < length; i++) {
            jobject windowHandleObj = env->GetObjectArrayElement(windowHandleObjArray, i);
            if (! windowHandleObj) {
                break; // found null element indicating end of used portion of the array
            }

            sp<InputWindowHandle> windowHandle =
                    android_server_InputWindowHandle_getHandle(env, windowHandleObj);
            if (windowHandle != NULL) {
                windowHandles.push(windowHandle);
            }
            env->DeleteLocalRef(windowHandleObj);
        }
    }
    // 🏁前面把JAVA对象们转换成C++对象，然后在C++层执行注册操作
    mInputManager->getDispatcher()->setInputWindows(windowHandles);     
    ... ...
}
```
# Step6: InputDispatcher::setInputWindows(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:2822
void InputDispatcher::setInputWindows(const Vector<sp<InputWindowHandle> >&
                                        inputWindowHandles) {
... ...
        Vector<sp<InputWindowHandle> > oldWindowHandles = mWindowHandles;
        mWindowHandles = inputWindowHandles; // 重新保存所有需要接收键盘事件的窗口

        sp<InputWindowHandle> newFocusedWindowHandle;
        bool foundHoveredWindow = false;
        // 重新检查一遍，把不需要接收键盘事件的窗口删除，顺便获得当前焦点窗口
        for (size_t i = 0; i < mWindowHandles.size(); i++) {
            const sp<InputWindowHandle>& windowHandle = mWindowHandles.itemAt(i);
            if (!windowHandle->updateInfo() || windowHandle->getInputChannel() == NULL) {
                mWindowHandles.removeAt(i--);
                continue;
            }
            if (windowHandle->getInfo()->hasFocus) {
                newFocusedWindowHandle = windowHandle;
            }
            if (windowHandle == mLastHoverWindowHandle) {
                foundHoveredWindow = true;
            }
        }

        if (!foundHoveredWindow) {
            mLastHoverWindowHandle = NULL;
        }

        if (mFocusedWindowHandle != newFocusedWindowHandle) {
            if (mFocusedWindowHandle != NULL) {
            ... ...
            mFocusedWindowHandle = newFocusedWindowHandle;
        }
        // ↑从for循环到这里，收集到所有需要接收键盘事件的应用窗口并找到当前新的活动窗口
    ... ...
    // Wake up poll loop since it may need to make new input dispatching choices.
    mLooper->wake();
}
```
费这么大劲，只是为了把当前所有需要接收键盘事件的窗口重新记录一遍，同时也重新记录当前活动窗口的信息。而且Android6的代码多了一坨对Hover窗口的处理，不知道具体目的是什么。先不管，往后看。
# 总结
这段代码是在系统中有新的Activity创建时被调用的，以后如果研究Activity的启动过程应该还会遇到。这里遇到的疑问比较多：为什么每创建一个新Activity，都要让InputDispatcher更新一遍系统中所有接收键盘事件的窗口信息？没有更便捷的方式么？这让Activity的启动成本挺高的，而且这段在键盘消息处理机制中起了什么作用呢？
我猜测应该就是InputDispatcher保留了系统所有需要接收键盘事件的应用程序窗口列表，以及知道当前的活动窗口是谁。InputDispatcher的主要职责就是分发键盘事件，未来当它需要履行该指责的时候，就可以根据这张列表决定事件分发的目的地。
