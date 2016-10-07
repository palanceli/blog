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
        status_t status = consumeEvents(env, false /*consumeBatches*/, 
                                        -1, NULL); // 🏁
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
                // 见《键盘消息处理学习笔记（八）》Step1、2，这个指针
                // 实际指向的是一个WindowInputEventReceiver对象
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
                // WindowInputEventReceiver::dispatchInputEvent(...)函数
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
            // Receive a fresh message.
            status_t result = mChannel->receiveMessage(&mMsg);  // 🏁Step4
            ... ...

        switch (mMsg.header.type) {
        case InputMessage::TYPE_KEY: {
            KeyEvent* keyEvent = factory->createKeyEvent();
            if (!keyEvent) return NO_MEMORY;

            initializeKeyEvent(keyEvent, &mMsg); // 用读出的数据初始化KeyEvent对象
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
它读出的mMsg跟《键盘消息处理学习笔记（十）》之Step8刚好是相应的，前面是往里写，此处是读出来。然后把独处的数据封装成KeyEvent类型，赋给*outEvent，这会终止下一轮的while循环。
# Step4: InputChannel::receiveMessage(...)
``` c++
// frameworks/native/libs/input/InputTransport.cpp:188
status_t InputChannel::receiveMessage(InputMessage* msg) {
    ssize_t nRead;
    do {    // 非阻塞式接收
        nRead = ::recv(mFd, msg, sizeof(InputMessage), MSG_DONTWAIT); 
    } while (nRead == -1 && errno == EINTR);
    ... ...
    return OK;
}
```
注意在::recv第四个参数中使用了MSG_DONTWAIT标志，表明该读操作是个非阻塞的，如果当前没有数据可读，该函数立即返回EWOULDBLOCK错误。在本节的上下文中，该函数之所以被执行，是因为主线程Looper被该socketIO事件通知到而唤醒，说明一定是有数据可读的，因此，这里会返回OK，即0。

返回到Step3中，把读到的数据组织成KeyEvent对象，返回给输出参数。再回到Step2中，前半部分是读取键盘事件，后半部分是调用WindowInputEventReceiver::dispatcheInputEvent(...)函数处理该事件，该函数继承自InputEventReceiver：

# Step5: InputEventReceiver::dispatchInputEvent(...)
``` java
// frameworks/base/core/java/android/view/InputEventReceiver.java:183
    private void dispatchInputEvent(int seq, InputEvent event) {
        mSeqMap.put(event.getSequenceNumber(), seq);
        onInputEvent(event);    // 🏁
    }
```
onInputEvent(...)是一个虚函数，调用WidnowInputEventReceiver的版本：
# Step6: WindowInputEventReceiver::onInputEvent(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:6025
        public void onInputEvent(InputEvent event) {
            enqueueInputEvent(event, this, 0, true);    // 🏁
        }
```
enqueueInputEvent(...)即没有在WindowInputEventReceiver中，也没有在其父类InputEventReceiver中。WindowInputEventReceiver是定义在ViewRootImpl中的内部类，因此这个函数可以去ViewRootImpl中找：
# Step7: ViewRootImpl::enqueueInputEvent(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:5835
    void enqueueInputEvent(InputEvent event, InputEventReceiver receiver, 
                        int flags, boolean processImmediately) {
        // flags                0
        // processImmediately   true
        adjustInputEventForCompatibility(event);
        // 将event入队
        QueuedInputEvent q = obtainQueuedInputEvent(event, receiver, flags);
        ... ...
        mPendingInputEventCount += 1;
        ... ...
        if (processImmediately) {
            doProcessInputEvents();     // 🏁
        } else {
            scheduleProcessInputEvents();
        }
    }
```
# Step8: ViewRootImpl::doProcessInputEvents(...)
// frameworks/base/core/java/android/view/ViewRootImpl.java:5873
``` c++
    void doProcessInputEvents() {
        // Deliver all pending input events in the queue.
        while (mPendingInputEventHead != null) {
            ... ...
            deliverInputEvent(q);   // 🏁
        }

        // We are done processing all input events that we can process right now
        // so we can clear the pending flag immediately.
        if (mProcessInputEventsScheduled) {
            mProcessInputEventsScheduled = false;
            mHandler.removeMessages(MSG_PROCESS_INPUT_EVENTS);
        }
    }
```

# Step9: ViewRootImpl::deliverInputEvent(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:5908
    private void deliverInputEvent(QueuedInputEvent q) {
        Trace.asyncTraceBegin(Trace.TRACE_TAG_VIEW, "deliverInputEvent",
                q.mEvent.getSequenceNumber());
        if (mInputEventConsistencyVerifier != null) {
            mInputEventConsistencyVerifier.onInputEvent(q.mEvent, 0);
        }

        InputStage stage;
        if (q.shouldSendToSynthesizer()) { // 这里应该是处理合成键盘消息的分支
            stage = mSyntheticInputStage;
        } else {    // 显然不应该忽略输入法，所以stage = mFirstInputStage
            stage = q.shouldSkipIme() ? mFirstPostImeInputStage : mFirstInputStage;
        }

        if (stage != null) {
            stage.deliver(q);   // 🏁
        } else {
            finishInputEvent(q);
        }
    }
```
来看ViewRootImpl::setView(...)时对InputStage的初始化：
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:633

    // Set up the input pipeline.
    CharSequence counterSuffix = attrs.getTitle();
    mSyntheticInputStage = new SyntheticInputStage();
    InputStage viewPostImeStage = new ViewPostImeInputStage(
            mSyntheticInputStage);
    InputStage nativePostImeStage = new NativePostImeInputStage(
            viewPostImeStage, "aq:native-post-ime:" + counterSuffix);
    InputStage earlyPostImeStage = new EarlyPostImeInputStage(
            nativePostImeStage);
    InputStage imeStage = new ImeInputStage(earlyPostImeStage,
            "aq:ime:" + counterSuffix);
    InputStage viewPreImeStage = new ViewPreImeInputStage(imeStage);
    InputStage nativePreImeStage = new NativePreImeInputStage(
            viewPreImeStage, "aq:native-pre-ime:" + counterSuffix);

    mFirstInputStage = nativePreImeStage;
    mFirstPostImeInputStage = earlyPostImeStage;
    mPendingInputEventQueueLengthCounterName = "aq:pending:" + counterSuffix;
```
可以发现他们依次以前面的一个InputStage为参数，这是因为
`NativePreImeInputStage` -> `ViewPreImeInputStage` -> `ImeInputStage` ->`EarlyPostImeInputStage` -> `NativePostImeInputStage` -> `ViewPostImeInputStage` -> `SyntheticInputStage`
他们依次构成一个输入事件的处理链，如果本阶段对时间没有处理，则传递到下一个对象处理，知道事件被处理。

此处的stage应该被赋值为mFirstInputStage即NativePreInputStage。

# Step10: InputStage::deliver(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:3637
        public final void deliver(QueuedInputEvent q) {
            if ((q.mFlags & QueuedInputEvent.FLAG_FINISHED) != 0) {
                forward(q);
            } else if (shouldDropInputEvent(q)) {
                finish(q, false);
            } else {
                apply(q, onProcess(q)); // 🏁
            }
        }
```
由于时间还没完成，不会带上FLAG_FINISHED标志，正常案件消息不应该被抛弃，因此我们走apply(...)分支。第二个参数又是一个函数调用，先来看onProcess(...)
# Step11: NativePreImeInputStage::onProcess(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:3899
        protected int onProcess(QueuedInputEvent q) {
            if (mInputQueue != null && q.mEvent instanceof KeyEvent) {
                mInputQueue.sendInputEvent(q.mEvent, q, true, this); // 🏁
                return DEFER;
            }
            return FORWARD;
        }
```
# Step12: InputQueue::sendInputEvent(...)
``` java
// frameworks/base/core/java/android/view/InputQueue.java:91
    public void sendInputEvent(InputEvent e, Object token, boolean predispatch,
            FinishedInputEventCallback callback) {
        ActiveInputEvent event = obtainActiveInputEvent(token, callback);
        long id;
        if (e instanceof KeyEvent) { // 我们关注的是键盘消息
            id = nativeSendKeyEvent(mPtr, (KeyEvent) e, predispatch);//🏁
        } else {
            id = nativeSendMotionEvent(mPtr, (MotionEvent) e);
        }
        mActiveEventArray.put(id, event);
    }
```
# Step13 : nativeSendKeyEvent(...)
``` c++
// frameworks/base/core/jni/android_view_InputQueue.cpp:219
static jlong nativeSendKeyEvent(JNIEnv* env, jobject clazz, jlong ptr, jobject eventObj,
        jboolean predispatch) {
    InputQueue* queue = reinterpret_cast<InputQueue*>(ptr);
    KeyEvent* event = queue->createKeyEvent();
    status_t status = android_view_KeyEvent_toNative(env, eventObj, event);
    if (status) {
        queue->recycleInputEvent(event);
        jniThrowRuntimeException(env, "Could not read contents of KeyEvent object.");
        return -1;
    }

    if (predispatch) {
        event->setFlags(event->getFlags() | AKEY_EVENT_FLAG_PREDISPATCH);
    }

    queue->enqueueEvent(event);     // 把event放入mPendingEvents队列中
    return reinterpret_cast<jlong>(event);
}
```
再回到Step10中，NativePreInputStage没有apply(...)，找父类`AsyncInputStage::apply(...)`是有的。
# Step14: AsyncInputStage::apply(...)
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:3841
        protected void apply(QueuedInputEvent q, int result) {
            if (result == DEFER) {
                defer(q);   // 🏁
            } else {
                super.apply(q, result);
            }
        }

// frameworks/base/core/java/android/view/ViewRootImpl.java:3775
        protected void defer(QueuedInputEvent q) {
            q.mFlags |= QueuedInputEvent.FLAG_DEFERRED;
            enqueue(q);
        }

// frameworks/base/core/java/android/view/ViewRootImpl.java:3849
        private void enqueue(QueuedInputEvent q) {
            if (mQueueTail == null) {
                mQueueHead = q;
                mQueueTail = q;
            } else {
                mQueueTail.mNext = q;
                mQueueTail = q;
            }

            mQueueLength += 1;
            Trace.traceCounter(Trace.TRACE_TAG_INPUT, mTraceCounter, mQueueLength);
        }

```
