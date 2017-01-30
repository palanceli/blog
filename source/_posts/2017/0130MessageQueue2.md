---
layout: post
title: Android应用消息队列（二）——创建消息队列
date: 2017-01-30 09:09:18 +0800
categories: Android学习笔记
tags: 消息队列
toc: true
comments: true
---
在[《细胞分裂——Android进程的启动》](http://palanceli.com/2017/01/29/2017/0129Process/#Step11-ActivityThread-main-…)的尾部，通过`Looper.prepareMainLooper()`创建消息泵之后，通过调用`Looper.loop()`进入消息循环。接下来就以此为起点进入学习。<!-- more -->
# Step1 Looper::loop()
``` java
// frameworks/base/core/java/android/os/Looper.java:122
public static void loop() {
    final Looper me = myLooper(); // 获取当前线程的消息队列
    ...
    final MessageQueue queue = me.mQueue;

    // Make sure the identity of this thread is that of the local process,
    // and keep track of what that identity token actually is.
    Binder.clearCallingIdentity();
    final long ident = Binder.clearCallingIdentity();

    for (;;) {
        Message msg = queue.next(); // 🏁might block
        ...
        msg.target.dispatchMessage(msg);
        ...
        // Make sure that during the course of dispatching the
        // identity of the thread wasn't corrupted.
        final long newIdent = Binder.clearCallingIdentity();
        ...
        msg.recycleUnchecked();
    }
}
```
# Step2 MessageQueue::next()
``` java
// frameworks/base/core/java/android/os/MessageQueue.java:307
Message next() {
    ...
    // 用来保存注册到消息队列中的空闲消息处理器(IdleHandler)的个数，当消息队列
    // 没有新消息需要处理时，不是马上进入睡眠等待状态，而是先调用已注册的IdleHandler
    // 对象的queueIdle(...)函数，以便有机会进行空闲处理。
    int pendingIdleHandlerCount = -1; // -1 only during first iteration

    // 若没有新消息待处理，线程睡眠等待的时间。
    // 0表示不要进入睡眠等待状态；-1表示若无新消息，则永久睡眠等待
    int nextPollTimeoutMillis = 0; 
    for (;;) {
        if (nextPollTimeoutMillis != 0) {
            Binder.flushPendingCommands();
        }
        // 🏁检查线程消息队列是否有新消息，首次不进入睡眠等待
        nativePollOnce(ptr, nextPollTimeoutMillis);
        // mMessages描述当前线程需要处理的消息，nativePollOnce(...)会给mMessages
        // 完成赋值
        synchronized (this) {
            // Try to retrieve the next message.  Return if found.
            final long now = SystemClock.uptimeMillis();
            Message prevMsg = null;
            Message msg = mMessages;
            ...
            if (msg != null) {
                if (now < msg.when) {
                    // Next message is not ready.  Set a timeout to wake up when it is ready.
                    // 计算下次调用nativePollOnce(...)的时间
                    nextPollTimeoutMillis = (int) Math.min(msg.when - now, Integer.MAX_VALUE);
                } else {
                    ...
                        mMessages = msg.next;
                    ...
                    msg.next = null;
                    ...
                    return msg;
                }
            } else {
                // No more messages. 没有消息处理，则睡眠等待
                nextPollTimeoutMillis = -1;
            }
            ...
        }

        // Run the idle handlers.
        // We only ever reach this code block during the first iteration.
        for (int i = 0; i < pendingIdleHandlerCount; i++) {
            final IdleHandler idler = mPendingIdleHandlers[i];
            mPendingIdleHandlers[i] = null; // release the reference to the handler

            boolean keep = false;
            try {
                keep = idler.queueIdle();
            } catch (Throwable t) ...

            if (!keep) {
                synchronized (this) {
                    mIdleHandlers.remove(idler);
                }
            }
        }

        // Reset the idle handler count to 0 so we do not run them again.
        pendingIdleHandlerCount = 0;

        // While calling an idle handler, a new message could have been delivered
        // so go back and look again for a pending message without waiting.
        nextPollTimeoutMillis = 0;
    }
}
```
# Step3 MessageQueue::nativePollOnce(...)
这是一个JNI函数，它对应的Native层函数如下：
``` c
// frameworks/base/core/jni/android_os_MessageQueue.cpp:188
static void android_os_MessageQueue_nativePollOnce(JNIEnv* env, jobject obj,
        jlong ptr, jint timeoutMillis) {
    NativeMessageQueue* nativeMessageQueue = reinterpret_cast<NativeMessageQueue*>(ptr);
    nativeMessageQueue->pollOnce(env, obj, timeoutMillis);
}
```
# Step4 NativeMessageQueue::pollOnce(...)
``` c
// frameworks/base/core/jni/android_os_MessageQueue.cpp:107
void NativeMessageQueue::pollOnce(JNIEnv* env, jobject pollObj, int timeoutMillis) {
    ...
    mLooper->pollOnce(timeoutMillis);
    ...
}
```
# Step5 Looper::pollOnce(...)
``` c
// system/core/libutils/Looper.cpp:184
int Looper::pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData) {
    int result = 0;
    for (;;) {
        ...
        if (result != 0) { 
            ...
            return result; // 如果有新消息处理，则返回
        }

        result = pollInner(timeoutMillis); // 循环检查是否有新消息要处理
    }
}
```
# Step6 Looper::pollInner(...)
在[《Android应用消息队列（一）——创建消息队列》之Step5](http://localhost:4000/2017/01/29/2017/0129MessageQueue1/#Step5-NativeMessageQueue-NativeMessageQueue)中，在Native层创建mLooper对象，在其构造函数里创建了事件对象mWakeEventFd、epoll实例mEpollFd，并将mWakeEventFd注册到mEpollFd，此处开始等待mEpollFd：
``` c
// system/core/libutils/Looper.cpp:220
int Looper::pollInner(int timeoutMillis) {
...
    // Poll.
    int result = POLL_WAKE;
    mResponses.clear();
    mResponseIndex = 0;

    // We are about to idle.
    mPolling = true;

    struct epoll_event eventItems[EPOLL_MAX_EVENTS];
    int eventCount = epoll_wait(mEpollFd, eventItems, EPOLL_MAX_EVENTS, timeoutMillis);
    ...
    for (int i = 0; i < eventCount; i++) {
        int fd = eventItems[i].data.fd;
        uint32_t epollEvents = eventItems[i].events;
        if (fd == mWakeEventFd) { 
            if (epollEvents & EPOLLIN) {
                awoken(); // 如果是mWakeEventFd的EPOLLIN事件，则读出数据
            } else ...
        } else { // 如果是mWakeEventFd以外的epoll事件，则缓存requestIndex到mResponse
            ssize_t requestIndex = mRequests.indexOfKey(fd);
            if (requestIndex >= 0) {
                int events = 0;
                if (epollEvents & EPOLLIN) events |= EVENT_INPUT;
                if (epollEvents & EPOLLOUT) events |= EVENT_OUTPUT;
                if (epollEvents & EPOLLERR) events |= EVENT_ERROR;
                if (epollEvents & EPOLLHUP) events |= EVENT_HANGUP;
                pushResponse(events, mRequests.valueAt(requestIndex));
            } else ...
        }
    }
Done: ;
    ...
    // Invoke all response callbacks.
    // 遍历前面缓存到mResponse中的request，调用保存在其中的callback，这些
    // 函数通常为业务层逻辑，因此以callback的形式保存（注册）到机制层
    for (size_t i = 0; i < mResponses.size(); i++) {
        Response& response = mResponses.editItemAt(i);
        if (response.request.ident == POLL_CALLBACK) {
            int fd = response.request.fd;
            int events = response.events;
            void* data = response.request.data;
...
            // Invoke the callback.  Note that the file descriptor may be closed by
            // the callback (and potentially even reused) before the function returns so
            // we need to be a little careful when removing the file descriptor afterwards.
            int callbackResult = response.request.callback->handleEvent(fd, events, data);
            if (callbackResult == 0) {
                removeFd(fd, response.request.seq);
            }

            // Clear the callback reference in the response structure promptly because we
            // will not clear the response vector itself until the next poll.
            response.request.callback.clear();
            result = POLL_CALLBACK;
        }
    }
    return result;
}
```
# 总结
创建消息队列的调用过程如下：
![创建消息队列的调用过程](0130MessageQueue2/img1.png)