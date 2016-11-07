---
layout: post
title: 键盘消息处理学习笔记（三）——InputDispatcherThread和InputReaderThread两个线程函数
date: 2016-10-02 10:14:36 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
InputDispatcherThread和InputReaderThread都继承自Thread，先来看一下该类的基本框架：
``` c++
// system/core/libutils/Threads.cpp:675
status_t Thread::run(const char* name, int32_t priority, size_t stack)
{
    ... ...
        res = createThreadEtc(_threadLoop,
                this, name, priority, stack, &mThread); // 调用线程函数_threadLoop
    ... ...
}

int Thread::_threadLoop(void* user)
{
    ... ...
    sp<Thread> strong(self->mHoldSelf);
    ... ...
    do {
        bool result;
        ... ...
            result = self->threadLoop();    // 循环调用线程函数threadLoop()
        ... ...
    } while(strong != 0);

    return 0;
}
```

在[《键盘消息处理学习笔记（二）](http://http://palanceli.com/2016/10/01/2016/1001KeyboardLearning2/)中，InputManagerService的启动最终落实到了InputDispatcherThread和InputReaderThread的启动，这两个线程启动后就是不断调用自己的线程函数threadLoop()，接下来就深入到这两个线程的线程函数中。
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
    {   // 执行一次消息分发
        ... ...
        // 如果有缓存的命令要执行，则执行，并返回true；否则，返回false
        if (!haveCommandsLocked()) {    
            // 🏁执行一次分发，在《键盘消息处理学习笔记（十）中深入讨论
            dispatchOnceInnerLocked(&nextWakeupTime);
        }

        // 如果前面执行了缓存命令，则让nextWakeupTime置为最短，以便pollOnce(...)
        // 不再休眠。因为在执行缓存命令期间，系统可能会发生了新的键盘事件
        if (runCommandsLockedInterruptible()) {
            nextWakeupTime = LONG_LONG_MIN;
        }
    }

    // 进入休眠，等待消息，最长等待timeoutMillis毫秒
    nsecs_t currentTime = now();
    int timeoutMillis = toMillisecondTimeoutDelay(currentTime, nextWakeupTime);
    mLooper->pollOnce(timeoutMillis);   // 
}
```
函数mLooper->pollOnce(...)详见[《键盘消息处理学习笔记（四）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning4/)，它等待从Looper消息泵中获取通知，最多等待timeoutMillis毫秒，如果超时则返回。
mLooper是在InputDispatcher的构造函数中创建的：
``` c++
InputDispatcher::InputDispatcher(const sp<InputDispatcherPolicyInterface>& policy) : ... {
    mLooper = new Looper(false);
    ... ...
}
```

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
    size_t count = mEventHub->getEvents(timeoutMillis, mEventBuffer, 
                            EVENT_BUFFER_SIZE);    // 🏁获取键盘事件
    ... ...
        if (count) {
            // 🏁 处理键盘事件，将在《键盘消息处理学习笔记（九）》中讨论
            processEventsLocked(mEventBuffer, count); 
        }
    ... ...
}
```
mEventHub是在NativeInputManager构造函数里创建，并通过mInputManager一路传递给InputReader。参见《键盘消息处理学习笔记（一）》的[总结](http://palanceli.com/2016/10/01/2016/0904KeyboardLearning1/#总结)可以复习这部分内容。键盘事件的处理后面讨论，在深入讨论EventHub::getEvents(...)函数之前，先来看一下EventHub的创建：
``` c++
// frameworks/native/services/inputflinger/EventHub.cpp:184
EventHub::EventHub(void) :
        mBuiltInKeyboardId(NO_BUILT_IN_KEYBOARD), mNextDeviceId(1), mControllerNumbers(),
        mOpeningDevices(0), mClosingDevices(0),
        mNeedToSendFinishedDeviceScan(false),
        mNeedToReopenDevices(false), mNeedToScanDevices(true),
        mPendingEventCount(0), mPendingEventIndex(0), mPendingINotify(false) {
    acquire_wake_lock(PARTIAL_WAKE_LOCK, WAKE_LOCK_ID);

    mEpollFd = epoll_create(EPOLL_SIZE_HINT);
    ... ...
    mINotifyFd = inotify_init(); // 创建inotify实例
    // 监控DEVICE_PATH即/dev/input目录，当系统新增或删除一个输入设备时，该目录就会变化
    int result = inotify_add_watch(mINotifyFd, DEVICE_PATH, IN_DELETE | IN_CREATE);
    ... ...

    struct epoll_event eventItem;
    memset(&eventItem, 0, sizeof(eventItem));
    eventItem.events = EPOLLIN;
    eventItem.data.u32 = EPOLL_ID_INOTIFY;
    // DEVICE_PATH发生变化，mINotifyFd就会收到通知
    result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mINotifyFd, &eventItem);
    ... ...

    int wakeFds[2];
    result = pipe(wakeFds);
    ... ...

    mWakeReadPipeFd = wakeFds[0];
    mWakeWritePipeFd = wakeFds[1];

    result = fcntl(mWakeReadPipeFd, F_SETFL, O_NONBLOCK);
    ... ...
    result = fcntl(mWakeWritePipeFd, F_SETFL, O_NONBLOCK);
    ... ...

    eventItem.data.u32 = EPOLL_ID_WAKE;
    result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mWakeReadPipeFd, &eventItem);
    ... ...
}
```
构造函数中，除了创建inotify监听输入设备的增删外，还构造了epoll机制。
接下来深入讨论获取键盘事件的EventHub::getEvents(...)函数。
## Step3: EventHub::getEvents(...)
``` c++
// frameworks/native/services/inputflinger/EventHub.cpp:721
// buffer和bufferSize返回获取到的键盘事件及个数
size_t EventHub::getEvents(int timeoutMillis, RawEvent* buffer, size_t bufferSize) {
    ... ...
    struct input_event readBuffer[bufferSize];

    RawEvent* event = buffer;
    size_t capacity = bufferSize;
    bool awoken = false;
    for (;;) {
        nsecs_t now = systemTime(SYSTEM_TIME_MONOTONIC);
        ... ...
        // Report any devices that had last been added/removed.
        // 把“要删除键盘设备”的信息封装成键盘事件
        while (mClosingDevices) {
            Device* device = mClosingDevices;
            ... ...
            mClosingDevices = device->next;
            event->when = now;
            event->deviceId = device->id == mBuiltInKeyboardId ? BUILT_IN_KEYBOARD_ID : device->id;
            event->type = DEVICE_REMOVED;
            event += 1;
            delete device;
            mNeedToSendFinishedDeviceScan = true;
            if (--capacity == 0) {
                break;
            }
        }
        ... ...
        // 把“要打开键盘设备”的信息封装成键盘事件
        while (mOpeningDevices != NULL) {
            Device* device = mOpeningDevices;
            ... ...
            mOpeningDevices = device->next;
            event->when = now;
            event->deviceId = device->id == mBuiltInKeyboardId ? 0 : device->id;
            event->type = DEVICE_ADDED;
            event += 1;
            mNeedToSendFinishedDeviceScan = true;
            if (--capacity == 0) {
                break;
            }
        }
        ... ...
        // Grab the next input event.
        // mPendingEventItems是一个epoll_event数组，其中每个元素代表一个输入设备
        bool deviceChanged = false;
        while (mPendingEventIndex < mPendingEventCount) {
            const struct epoll_event& eventItem = mPendingEventItems[mPendingEventIndex++];
            ... ...
            if (eventItem.data.u32 == EPOLL_ID_WAKE) {// 默认监控Fd发生信号
                if (eventItem.events & EPOLLIN) {
                    ... ...
                    awoken = true;  // 这会跳出大循环，让函数返回
                    char buffer[16];
                    ssize_t nRead;
                    do {            // 清空数据
                        nRead = read(mWakeReadPipeFd, buffer, sizeof(buffer));
                    } while ((nRead == -1 && errno == EINTR) || nRead == sizeof(buffer));
                } else ... ...
                continue;
            }
            // 键盘设备发生了IO事件
            ssize_t deviceIndex = mDevices.indexOfKey(eventItem.data.u32);
            ... ...
            Device* device = mDevices.valueAt(deviceIndex);
            if (eventItem.events & EPOLLIN) {
                // 正常应该读出若干个input_event结构体
                int32_t readSize = read(device->fd, readBuffer,
                        sizeof(struct input_event) * capacity);
                if (readSize == 0 || (readSize < 0 && errno == ENODEV)) {
                    // Device was removed before INotify noticed.
                    ... ...
                } else if (readSize < 0) {
                    ... ...
                } else if ((readSize % sizeof(struct input_event)) != 0) {
                    ... ...
                } else {
                    int32_t deviceId = device->id == mBuiltInKeyboardId ? 0 : device->id;

                    size_t count = size_t(readSize) / sizeof(struct input_event);
                    for (size_t i = 0; i < count; i++) {
                        struct input_event& iev = readBuffer[i];
                        ... ...
                        if (device->timestampOverrideSec || device->timestampOverrideUsec) {
                            iev.time.tv_sec = device->timestampOverrideSec;
                            iev.time.tv_usec = device->timestampOverrideUsec;
                            if (iev.type == EV_SYN && iev.code == SYN_REPORT) {
                                device->timestampOverrideSec = 0;
                                device->timestampOverrideUsec = 0;
                            }
                            ... ...
                        }
                        // 把从设备独到的数据写入buffer，返回给调用者
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
        // 如果mWakeReadPipeFd被通知或者(注册Fd被通知且读出了数据)，则终止循环
        if (event != buffer || awoken) {
            break;
        }
        ... ...
        int pollResult = epoll_wait(mEpollFd, mPendingEventItems, EPOLL_MAX_EVENTS, timeoutMillis);
        ... ...
    }

    // All done, return the number of events we read.
    return event - buffer;
}
```
在进入getEvents(...)函数之前，需要先看[《键盘消息处理学习笔记（四）》，这个函数虽然很长，确是一段很模式化的写法，InputDispatcher的线程函数也是这种模式，只是比InputReader断点。它的主要任务就是监控mWakeReadPipeFd以及注册的Fd，如果发生键盘IO事件，就把具体的数据读出来，返回给调用者。否则就一直执行阻塞式监听。
# 总结
到此可以先小小地总结一下了。InputManagerService启动后，创建了两个线程：InputReaderThread和InputDispatcherThread，前者用于监听输入设备的IO事件，后者等待IO事件发生，负责分发。当键盘IO事件发生后，InputReaderThread被唤醒，它对这些事件完成封装，然后唤醒InputDispatcherThread线程，把事件分发给目标窗口。