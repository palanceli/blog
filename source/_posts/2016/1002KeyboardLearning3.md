---
layout: post
title: 键盘消息处理学习笔记（三）
date: 2016-10-02 10:14:36 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
在[《键盘消息处理学习笔记（二）](http://http://palanceli.com/2016/10/01/2016/1001KeyboardLearning2/)中，InputManagerService的启动最终落实到了InputDispatcherThread和InputReaderThread的的启动上来，它们的启动本质上是调用各自的线程函数。接下来就深入到这两个线程的线程函数。
<!-- more -->
# InputDispatcherThread的启动
## Step1: InputDispatcherThread::threadLoop()
``` cpp
// frameworks/native/services/inputflinger/InputDispatcher.cpp:4530
bool InputDispatcherThread::threadLoop() {
    mDispatcher->dispatchOnce();    // 🏁
    return true;
}
```
在[InputManagerService的创建过程](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/)中，Step6创建InputReaderThread和InputDispatcherThread的时候会分别传入InputReader和InputDispatcher。此处的mDispatcher正是在那里传入的InputDispatcher参数。

## Step2: InputDispatcher::dispatchOnce()
``` cpp
// frameworks/native/services/inputflinger/InputDispatcher.cpp:230
void InputDispatcher::dispatchOnce() {
    nsecs_t nextWakeupTime = LONG_LONG_MAX;
    { // acquire lock
        AutoMutex _l(mLock);
        mDispatcherIsAliveCondition.broadcast();

        // Run a dispatch loop if there are no pending commands.
        // The dispatch loop might enqueue commands to run afterwards.
        if (!haveCommandsLocked()) {
            dispatchOnceInnerLocked(&nextWakeupTime);   // 🏁《键盘消息处理学习笔记（十）中深入讨论
        }

        // Run all pending commands if there are any.
        // If any commands were run then force the next poll to wake up immediately.
        if (runCommandsLockedInterruptible()) {
            nextWakeupTime = LONG_LONG_MIN;
        }
    } // release lock

    // Wait for callback or timeout or wake.  (make sure we round up, not down)
    nsecs_t currentTime = now();
    int timeoutMillis = toMillisecondTimeoutDelay(currentTime, nextWakeupTime);
    mLooper->pollOnce(timeoutMillis);   // 等待消息
}
```
第3~19行执行一次消息分发，然后在第22~24行调用pollOnce(...)进入休眠。
在第10行中检查如果没有缓存的命令要执行，则调用函数`dispatchOnceInnerLocked(...)`完成一次分发，该函数后面再讨论。
第10行检查如果有缓存的命令，则执行并返回true，在第11行就会给nextWakeupTime置为LONG_LONG_MIN，这使得pollOnce(...)不再休眠，因为在执行缓存命令期间，系统可能会发生了新的键盘事件。
函数mLooper->pollOnce(...)详见[《键盘消息处理学习笔记（四）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning4/)，它等待从Looper消息泵中获取通知，最多等待timeoutMillis毫秒，如果超时则返回。

# InputReaderThread的启动
## Step1: InputReaderThread::threadLoop()
``` cpp
// frameworks/native/services/inputflinger/InputReader.cpp:912
bool InputReaderThread::threadLoop() {
    mReader->loopOnce();    // 🏁
    return true;
}
```
## Step2: InputReader::loopOnce()
``` cpp
// frameworks/native/services/inputflinger/InputReader.cpp:272
void InputReader::loopOnce() {
    ... ...
    int32_t timeoutMillis;
    ... ...
    size_t count = mEventHub->getEvents(timeoutMillis, mEventBuffer, EVENT_BUFFER_SIZE);    // 🏁
    ... ...

        if (count) {
            // 🏁 处理键盘事件，将在《键盘消息处理学习笔记（九）》中讨论
            processEventsLocked(mEventBuffer, count); 
        }
    ... ...
}
```
该函数调用mEventHub->getEvents(...)来获取键盘事件，调用processEventsLocked(...)处理键盘事件。mEventHub是在NativeInputManager构造函数里创建，并通过mInputManager一路传递给InputReader。可以把InputManagerService的创建过程修正如下：
![InputManagerService的创建过程](1002KeyboardLearning3/img01.png)
相关对象之间的关系修正如下：
![InputManagerService相关对象之间的关系](1002KeyboardLearning3/img02.png)

键盘事件的处理以后再讨论，接下来深入到获取键盘事件的EventHub::getEvents(...)函数。
## Step3: EventHub::getEvents(...)
``` cpp
// frameworks/native/services/inputflinger/EventHub.cpp:721
size_t EventHub::getEvents(int timeoutMillis, RawEvent* buffer, size_t bufferSize) {
    ... ...
    struct input_event readBuffer[bufferSize];

    RawEvent* event = buffer;
    size_t capacity = bufferSize;
    bool awoken = false;
    for (;;) {
        nsecs_t now = systemTime(SYSTEM_TIME_MONOTONIC);
        ... ...
        // Grab the next input event.
        bool deviceChanged = false;
        // 遍历收到通知的输入设备
        while (mPendingEventIndex < mPendingEventCount) {   
            const struct epoll_event& eventItem = mPendingEventItems[mPendingEventIndex++];
            ... ...
            ssize_t deviceIndex = mDevices.indexOfKey(eventItem.data.u32);
            ... ...
            Device* device = mDevices.valueAt(deviceIndex);
            if (eventItem.events & EPOLLIN) {
                // 从收到通知的输入设备中读取IO事件
                int32_t readSize = read(device->fd, readBuffer,
                        sizeof(struct input_event) * capacity);
                ... ...
                 {
                    int32_t deviceId = device->id == mBuiltInKeyboardId ? 0 : device->id;

                    size_t count = size_t(readSize) / sizeof(struct input_event);
                    for (size_t i = 0; i < count; i++) {
                        struct input_event& iev = readBuffer[i];
                        ... ...
                        event->deviceId = deviceId;
                        event->type = iev.type;
                        event->code = iev.code;
                        event->value = iev.value;
                        event += 1;
                        capacity -= 1;
                    }
                    if (capacity == 0) {
                        // The result buffer is full.  Reset the pending event index
                        // so we will try to read the device again on the next iteration.
                        mPendingEventIndex -= 1;
                        break;
                    }
                }
            } ... ...
        }
        ... ...
        // Return now if we have collected any events or if we were explicitly awoken.
        if (event != buffer || awoken) {
            break;
        }
        ... ...
        mPendingEventIndex = 0;
        ... ...
        // 监听所有输入设备
        int pollResult = epoll_wait(mEpollFd, mPendingEventItems, EPOLL_MAX_EVENTS, timeoutMillis);
        ... ...
        mPendingEventCount = size_t(pollResult);
    }

    // All done, return the number of events we read.
    return event - buffer;
}
```
在进入getEvents(...)函数之前，需要先看[《键盘消息处理学习笔记（四）》之“epoll的使用模式”](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning4/#epoll的使用模式)。
mPendingEventItems是一个epoll_event数组，其中的每一个元素代表一个输入设备描述符。getEvents(...)函数监听所有打开的输入设备，如果有设备发生了IO事件，则依次从这些设备中读取IO事件。IO事件使用input_event结构体来描述，getEvents(...)将读取出来的IO事件写入到参数buffer中，返回读取到的IO事件的个数。
