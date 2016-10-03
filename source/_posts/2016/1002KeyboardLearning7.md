---
layout: post
title: 键盘消息处理学习笔记（七）
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
        // 🏁把正在启动的窗口注册到InputDispatcher中，以便InputDispatcher可以将键盘事件分发给它
        mInputMonitor.setInputFocusLw(mCurrentFocus, false /*updateInputWindows*/);
    }
```
通过函数mInputMonitor.setInputFocusLw(...)，把当前活动窗口注册到InputDispatcher中，以便InputDispatcher可以将键盘分发给它，本文继续深入这个注册函数。
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

            mInputFocus = newWindow;                    // 当前的活动窗口
            setUpdateInputWindowsNeededLw();

            if (updateInputWindows) {
                updateInputWindowsLw(false /*force*/);  // 🏁
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
        final int numDisplays = mService.mDisplayContents.size();
        for (int displayNdx = 0; displayNdx < numDisplays; ++displayNdx) {
            WindowList windows = mService.mDisplayContents.valueAt(displayNdx).getWindowList();
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
                addInputWindowHandleLw(inputWindowHandle, child, flags, type, isVisible, hasFocus,
                        hasWallpaper);
            }
        }

        // Send windows to native code.
        mService.mInputManager.setInputWindows(mInputWindowHandles); // 🏁

        // Clear the list in preparation for the next round.
        clearInputWindowHandlesLw();

        ... ...
    }
```
此处应该是把所有需要接收键盘事件的应用窗口都添加到mInputWindowHandles中了。mInputWindowHandles是一个InputWindowHandle数组，函数`addInputWindowHandleLw`把第一个参数添加到该数组中，待mService.mInputManager.setInputWindows(...)函数将该数组注册到InputDispatcher中。<font color='red'>这段代码的疑问比较多，比如mService.mDisplayContents是什么？被省略的代码也调用了addInputWindowHandleLw(...)，为什么要添加？这些问题暂时搁置，后面再研究。</font>先进入InputManagerService::setInputWindows(...)。
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

    mInputManager->getDispatcher()->setInputWindows(windowHandles);     // 🏁
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
        mWindowHandles = inputWindowHandles;

        sp<InputWindowHandle> newFocusedWindowHandle;
        bool foundHoveredWindow = false;
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
                sp<InputChannel> focusedInputChannel = mFocusedWindowHandle->getInputChannel();
                if (focusedInputChannel != NULL) {
                    CancelationOptions options(CancelationOptions::CANCEL_NON_POINTER_EVENTS,
                            "focus left window");
                    synthesizeCancelationEventsForInputChannelLocked(
                            focusedInputChannel, options);
                }
            }
... ...
            mFocusedWindowHandle = newFocusedWindowHandle;
        }
        // 从for循环到这里，找到当前新的活动窗口

        for (size_t d = 0; d < mTouchStatesByDisplay.size(); d++) {
            TouchState& state = mTouchStatesByDisplay.editValueAt(d);
            for (size_t i = 0; i < state.windows.size(); i++) {
                TouchedWindow& touchedWindow = state.windows.editItemAt(i);
                if (!hasWindowHandleLocked(touchedWindow.windowHandle)) {
... ...
                    sp<InputChannel> touchedInputChannel =
                            touchedWindow.windowHandle->getInputChannel();
                    if (touchedInputChannel != NULL) {
                        CancelationOptions options(CancelationOptions::CANCEL_POINTER_EVENTS,
                                "touched window was removed");
                        synthesizeCancelationEventsForInputChannelLocked(
                                touchedInputChannel, options);
                    }
                    state.windows.removeAt(i--);
                }
            }
        }

        // Release information for windows that are no longer present.
        // This ensures that unused input channels are released promptly.
        // Otherwise, they might stick around until the window handle is destroyed
        // which might not happen until the next GC.
        for (size_t i = 0; i < oldWindowHandles.size(); i++) {
            const sp<InputWindowHandle>& oldWindowHandle = oldWindowHandles.itemAt(i);
            if (!hasWindowHandleLocked(oldWindowHandle)) {
... ...
                oldWindowHandle->releaseInfo();
            }
        }
    ... ...

    // Wake up poll loop since it may need to make new input dispatching choices.
    mLooper->wake();
}
```
在《Android系统源码情景分析》中就没有把这一小节看得很明白，费这么大劲只是为了记录当前活动窗口？而且Android6的代码多了一坨对Hover窗口的处理，不知道具体目的是什么。先不管，往后看。