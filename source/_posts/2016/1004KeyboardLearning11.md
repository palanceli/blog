---
layout: post
title: 键盘消息处理学习笔记（十一）
date: 2016-10-04 18:49:17 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接《键盘消息处理学习笔记（十）》当InputDispatcher被InputReader唤醒后，启动键盘事件分发流程，最终会把分发数据写入活动窗口注册进来的socket描述符，完成事件分发。这会导致应用程序的主线程Looper被唤醒，并且调用与该描述符关联的回调函数。
<!-- more -->
先回顾一下当初是如何在应用程序主线程Looper中注册InputChannel的吧，参见《键盘消息处理学习笔记（八）》的Step5：
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:145
void NativeInputEventReceiver::setFdEvents(int events) {
    if (mFdEvents != events) {
        mFdEvents = events;
        int fd = mInputConsumer.getChannel()->getFd();
        if (events) { // 为真
            mMessageQueue->getLooper()->addFd(fd, 0, events, this, NULL);
        } else {
            mMessageQueue->getLooper()->removeFd(fd);
        }
    }
}
```
mInputConsumer.getChannel()->getFd()返回ViewRootImpl::mInputChannel->getFd()，即Client端的InputChannel的socket描述符。需要注意addFd(...)的第四个参数是一个回调函数，其实是一个有回调接口的对象。参见《键盘消息处理学习笔记（四）》之[Looper::pollInner(...)](http://localhost:4000/2016/10/02/2016/1002KeyboardLearning4/#Looper-pollInner-…)，当Looper被唤醒后，如果注册的描述符有回调接口，则调用其handleEvent(...)函数。本文就以NativeInputEventReceiver::handleEvent(...)函数为起点，来看该事件如何被应用程序窗口处理。

# Step1: NativeInputEventReceiver::handleEvent(...)
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:157
int NativeInputEventReceiver::handleEvent(int receiveFd, int events, void* data) {
    ... ...
    if (events & ALOOPER_EVENT_INPUT) {
        JNIEnv* env = AndroidRuntime::getJNIEnv();
        status_t status = consumeEvents(env, false /*consumeBatches*/, -1, 
                                        NULL); // 🏁
        mMessageQueue->raiseAndClearException(env, "handleReceiveCallback");
        return status == OK || status == NO_MEMORY ? 1 : 0;
    }
    ... ...
    return 1;
}
```

# Step2: NativeInputEventReceiver::consumeEvents(...)
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:217
status_t NativeInputEventReceiver::consumeEvents(JNIEnv* env,
        bool consumeBatches, nsecs_t frameTime, bool* outConsumedBatch) {
        // consumeBatches   false
        // frameTime        -1
        // outConsumedBatch NULL
    ... ...
    ScopedLocalRef<jobject> receiverObj(env, NULL);
    bool skipCallbacks = false;
    for (;;) {
        uint32_t seq;
        InputEvent* inputEvent;
        // 🏁Step3: 将InputDispatcher分发过来的键盘事件读取到inputEvent
        status_t status = mInputConsumer.consume(&mInputEventFactory,
                consumeBatches, frameTime, &seq, &inputEvent);
        ... ...
        if (!skipCallbacks) { // 为真
            // 前面读取到了合法数据，接下来在窗口消息组织合适的分发函数，完成分发
            if (!receiverObj.get()) {
                // 此处得到的是java层InputEventReceiver的弱引用指针
                // 见《键盘消息处理学习笔记（八）》Step2
                receiverObj.reset(jniGetReferent(env, mReceiverWeakGlobal));
                ... ...
            }

            jobject inputEventObj;
            switch (inputEvent->getType()) {
            case AINPUT_EVENT_TYPE_KEY:
                ... ...
                // 把C++层InputEvent对象转成Java层InputEvent对象
                inputEventObj = android_view_KeyEvent_fromNative(env,
                        static_cast<KeyEvent*>(inputEvent));
                break;
            ... ...
            }

            if (inputEventObj) {
                ... ...
                // 🏁Step5:调用java层
                // InputEventReceiver::dispatchInputEvent(...)函数
                env->CallVoidMethod(receiverObj.get(),
                        gInputEventReceiverClassInfo.dispatchInputEvent, seq, inputEventObj);
                if (env->ExceptionCheck()) {
                    ... ...
                    skipCallbacks = true;
                }
                env->DeleteLocalRef(inputEventObj);
            } else {
                ... ...
                skipCallbacks = true;
            }
        }

        if (skipCallbacks) {
            mInputConsumer.sendFinishedSignal(seq, false);
        }
    }
}
```
# Step3: InputConsumer::consume(...)
``` c++
// frameworks/native/libs/input/InputTransport.cpp:399
// 从InputChannel读出数据，返回到outEvent
status_t InputConsumer::consume(InputEventFactoryInterface* factory,
        bool consumeBatches, nsecs_t frameTime, uint32_t* outSeq, InputEvent** outEvent) {
        // consumeBatches   false
        // frameTime        -1
    ... ...
    *outSeq = 0;
    *outEvent = NULL;

    // Fetch the next input message.
    // Loop until an event can be returned or no additional events are received.
    while (!*outEvent) {
        ... ...
            // 此处应该对照《键盘消息处理学习笔记（十）》之Step8
            status_t result = mChannel->receiveMessage(&mMsg); // 🏁
            ... ...
        switch (mMsg.header.type) {
        case InputMessage::TYPE_KEY: {
            KeyEvent* keyEvent = factory->createKeyEvent();
            if (!keyEvent) return NO_MEMORY;
            // 用读出的数据初始化KeyEvent对象
            initializeKeyEvent(keyEvent, &mMsg);  
            *outSeq = mMsg.body.key.seq;
            *outEvent = keyEvent;
            ... ...
            break;
        }
        ... ...
    }
    return OK;
}

status_t InputConsumer::consume(InputEventFactoryInterface* factory,
        bool consumeBatches, nsecs_t frameTime, uint32_t* outSeq, InputEvent** outEvent) {
        ... ...
    *outSeq = 0;
    *outEvent = NULL;

    // Fetch the next input message.
    // Loop until an event can be returned or no additional events are received.
    while (!*outEvent) {
        ... ...
            // Receive a fresh message.
            status_t result = mChannel->receiveMessage(&mMsg);
            if (result) {
                // Consume the next batched event unless batches are being held for later.
                if (consumeBatches || result != WOULD_BLOCK) {
                    result = consumeBatch(factory, frameTime, outSeq, outEvent);
                    if (*outEvent) {
                        ... ...
                        break;
                    }
                }
                return result;
            }
        ... ...
        switch (mMsg.header.type) {
        case InputMessage::TYPE_KEY: {
            KeyEvent* keyEvent = factory->createKeyEvent();
            if (!keyEvent) return NO_MEMORY;

            initializeKeyEvent(keyEvent, &mMsg);
            *outSeq = mMsg.body.key.seq;
            *outEvent = keyEvent;
            ... ...
            break;
        }

        ... ...
    }
    return OK;
}

```
# Step4: InputChannel::receiveMessage(...)
``` c++
// frameworks/native/libs/input/InputTransport.cpp:188
status_t InputChannel::receiveMessage(InputMessage* msg) {
    ssize_t nRead;
    do {
        nRead = ::recv(mFd, msg, sizeof(InputMessage), MSG_DONTWAIT);
    } while (nRead == -1 && errno == EINTR);

    if (nRead < 0) {
        int error = errno;
        ... ...
        if (error == EAGAIN || error == EWOULDBLOCK) {
            return WOULD_BLOCK;
        }
        ... ...
        return -error;
    }
    ... ...
    return OK;  // system/core/include/utils/Errors.h 中定义为0
}
status_t InputChannel::receiveMessage(InputMessage* msg) {
    ssize_t nRead;
    do {    // 非阻塞式接收
        nRead = ::recv(mFd, msg, sizeof(InputMessage), MSG_DONTWAIT); 
    } while (nRead == -1 && errno == EINTR);

    if (nRead < 0) {
        int error = errno;
        ... ...
        if (error == EAGAIN || error == EWOULDBLOCK) {
            return WOULD_BLOCK;
        }
        if (error == EPIPE || error == ENOTCONN || error == ECONNREFUSED) {
            return DEAD_OBJECT;
        }
        return -error;
    }

    if (nRead == 0) { // check for EOF
        ... ...
        return DEAD_OBJECT;
    }

    if (!msg->isValid(nRead)) {
        ... ...
        return BAD_VALUE;
    }
    ... ...
    return OK;
}

```
# Step5: InputEventReceiver::dispatchInputEvent(...)
``` java
// frameworks/base/core/java/android/view/InputEventReceiver.java:183
    private void dispatchInputEvent(int seq, InputEvent event) {
        mSeqMap.put(event.getSequenceNumber(), seq);
        onInputEvent(event);
    }
```
# Step6: InputEventReceiver::onInputEvent(...)
``` java
// frameworks/base/core/java/android/view/InputEventReceiver.java:116
    public void onInputEvent(InputEvent event) {
        finishInputEvent(event, false);
    }
```
# Step7: InputEventReceiver::finishInputEvent(...)
``` java
// frameworks/base/core/java/android/view/InputEventReceiver.java:139
    public final void finishInputEvent(InputEvent event, boolean handled) {
        ... ...
        if (mReceiverPtr == 0) {
            ... ...
        } else {
            int index = mSeqMap.indexOfKey(event.getSequenceNumber());
            if (index < 0) {
                ... ...
            } else {
                int seq = mSeqMap.valueAt(index);
                mSeqMap.removeAt(index);
                nativeFinishInputEvent(mReceiverPtr, seq, handled);
            }
        }
        event.recycleIfNeededAfterDispatch();
    }
```
# Step8: nativeFinishInputEvent(...)
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:369
``` c++
static void nativeFinishInputEvent(JNIEnv* env, jclass clazz, jlong receiverPtr,
        jint seq, jboolean handled) {
    sp<NativeInputEventReceiver> receiver =
            reinterpret_cast<NativeInputEventReceiver*>(receiverPtr);
    status_t status = receiver->finishInputEvent(seq, handled);
    if (status && status != DEAD_OBJECT) {
        String8 message;
        message.appendFormat("Failed to finish input event.  status=%d", status);
        jniThrowRuntimeException(env, message.string());
    }
}
```


