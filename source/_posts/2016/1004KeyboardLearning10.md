---
layout: post
title: 键盘消息处理学习笔记（十）
date: 2016-10-04 13:04:17 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接《键盘消息处理学习笔记（三）》之[InputDispatcherThread的启动](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning3/#InputDispatcherThread的启动)。
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:4530
bool InputDispatcherThread::threadLoop() {
    mDispatcher->dispatchOnce();
    return true;
}
// frameworks/native/services/inputflinger/InputDispatcher.cpp:230
void InputDispatcher::dispatchOnce() {
    ... ...
    dispatchOnceInnerLocked(&nextWakeupTime); // 🏁
    ... ...
    nsecs_t currentTime = now();
    int timeoutMillis = toMillisecondTimeoutDelay(currentTime, nextWakeupTime);
    mLooper->pollOnce(timeoutMillis);   // 等待消息
}
```
当mLooper->pollOnce(timeoutMillis)被InputReader唤醒后，dispatchOnce(...)将返回，threadLoop()也返回，进入`thread::_threadLoop(...)`大循环，再调用
`InputDispatcherThread::threadLoop()` -> 
`InputDispatcher::dispatchOnce()` -> 
`InputDispatcher::dispatchOnceInnerLocked(...)`
进入事件分发。接下来就以InputDispatcher::dispatchOnceInnerLocked(...)为起点进入讨论。
<!-- more -->
# Step1: InputDispatcher::dispatchOnceInnerLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:255
// nextWakeupTime是个传出参数，描述InputDispatcher处理下一个键盘事件的最迟时间
void InputDispatcher::dispatchOnceInnerLocked(nsecs_t* nextWakeupTime) {
    nsecs_t currentTime = now();
    ... ...
    // Optimize latency of app switches.
    // Essentially we start a short timeout when an app switch key (HOME / ENDCALL) has
    // been pressed.  When it expires, we preempt dispatch and drop all other pending events.
    // 通常我们会给应用程序切换（通过HOME键或结束通话键）留一小段超时时间，
    // 如果时间过期，则需要立刻分发或者丢掉未完成的事件。
    bool isAppSwitchDue = mAppSwitchDueTime <= currentTime;
    if (mAppSwitchDueTime < *nextWakeupTime) { // 如果过期，把超时时间传出去，以便上层立即处理
        *nextWakeupTime = mAppSwitchDueTime;
    }

    // Ready to start a new event.
    // If we don't already have a pending event, go grab one.
    // mPendingEvent指向上一个需要奋发的键盘事件，如果为空，表明上次已经成功分发
    if (! mPendingEvent) {
        // mInboundQueue维护着待分发的键盘事件队列
        if (mInboundQueue.isEmpty()) {
            ... ...

            // Synthesize a key repeat if appropriate.
            // mKeyRepeatState描述当前重复键盘按键情况
            if (mKeyRepeatState.lastKeyEntry) { 
                // 如果某个按键一直被按着没送，则需要在这里合成一个键盘事件
                // 如果当前时间到了下次处理时间，则合成
                if (currentTime >= mKeyRepeatState.nextRepeatTime) {
                    mPendingEvent = synthesizeKeyRepeatLocked(currentTime);
                } else {
                    if (mKeyRepeatState.nextRepeatTime < *nextWakeupTime) {
                        *nextWakeupTime = mKeyRepeatState.nextRepeatTime;
                    }
                }
            }

            // Nothing to do if there is no pending event.
            if (!mPendingEvent) { // 如果待处理队列为空，且不需要合成，则返回
                return;
            }
        } else {
            // Inbound queue has at least one entry.
            // 队列非空，则从头部取出元素，保存到mPendingEvent
            mPendingEvent = mInboundQueue.dequeueAtHead();
            traceInboundQueueLengthLocked();
        }
        ... ...
    }
    ... ...
    switch (mPendingEvent->type) {
    ... ...
    case EventEntry::TYPE_KEY: {
        KeyEntry* typedEntry = static_cast<KeyEntry*>(mPendingEvent);
        if (isAppSwitchDue) {   // 需要处理app切换
            // 当前要分发的键盘事件是否就是前面发生的与app切换相关的事件，如果是
            // 将mAppSwitchDueTime置为LONG_LONG_MAX表示该事件已得到处理
            if (isAppSwitchKeyEventLocked(typedEntry)) { 
                resetPendingAppSwitchLocked(true);
                isAppSwitchDue = false;
            } ... ...
        }
        ... ...
        done = dispatchKeyLocked(currentTime, typedEntry, &dropReason, nextWakeupTime); // 🏁继续完成分发，如果成功分发则返回true
        break;
    }
    ... ...
    if (done) { // 如果成功分发， 将mPendingEvent置为空，并立即进入下一轮分发
        ... ...
        releasePendingEventLocked();
        *nextWakeupTime = LONG_LONG_MIN;  // force next poll to wake up immediately
    }
}
```

# Step2: InputDispatcher::dispatchKeyLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:714
bool InputDispatcher::dispatchKeyLocked(nsecs_t currentTime, KeyEntry* entry,
        DropReason* dropReason, nsecs_t* nextWakeupTime) {
    ... ...

    // Identify targets.
    // 🏁Step3将当前活动窗口mFocusedWindow封装成InputTarget对象，保存到inputTargets中
    Vector<InputTarget> inputTargets;
    int32_t injectionResult = findFocusedWindowTargetsLocked(currentTime,
            entry, inputTargets, nextWakeupTime);
    ... ...

    // Dispatch the key.
    // 🏁Step4将键盘事件分发给当前的活动窗口
    dispatchEventLocked(currentTime, entry, inputTargets);
    return true;
}
```

# Step3: InputDispatcher::findFocusedWindowTargetsLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:1072
int32_t InputDispatcher::findFocusedWindowTargetsLocked(nsecs_t currentTime,
        const EventEntry* entry, Vector<InputTarget>& inputTargets, nsecs_t* nextWakeupTime) {
    int32_t injectionResult;
    String8 reason;

    // If there is no currently focused window and no focused application
    // then drop the event.
    if (mFocusedWindowHandle == NULL) {
        // 如果InputManagerService还没有把当前活动窗口注册到InputDispatcher中，
        // entry所描述的键盘事件分发失败
        if (mFocusedApplicationHandle != NULL) {
            ... ...
            goto Unresponsive;
        }
        ... ...
        goto Failed;
    }

    // Check permissions.
    // 如果键盘事件由应用程序注入进来，而非硬件产生，
    // 检查该应用程序是否有权限向当前活动窗口注入键盘事件，如果没有则分发失败
    if (! checkInjectionPermission(mFocusedWindowHandle, entry->injectionState)) {
        injectionResult = INPUT_EVENT_INJECTION_PERMISSION_DENIED;
        goto Failed;
    }

    // Check whether the window is ready for more input.
    // 应用程序是否已经处理完上次分发给他的键盘事件，如果没有则分发失败
    reason = checkWindowReadyForMoreInputLocked(currentTime,
            mFocusedWindowHandle, entry, "focused");
    if (!reason.isEmpty()) {
        injectionResult = handleTargetsNotReadyLocked(currentTime, entry,
                mFocusedApplicationHandle, mFocusedWindowHandle, nextWakeupTime, reason.string());
        goto Unresponsive;
    }

    // Success!  Output targets.
    injectionResult = INPUT_EVENT_INJECTION_SUCCEEDED;
    addWindowTargetLocked(mFocusedWindowHandle,
            InputTarget::FLAG_FOREGROUND | InputTarget::FLAG_DISPATCH_AS_IS, BitSet32(0),
            inputTargets); // 把当前的活动窗口封装成InputTarget，保存到inputTargets中
    ... ...
    return injectionResult;
}
```
InputDispatcher::addWindowTargetLocked(...)函数很简单，向inputTargets中添加一个元素，并编辑：
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:1565
void InputDispatcher::addWindowTargetLocked(const sp<InputWindowHandle>& windowHandle,
        int32_t targetFlags, BitSet32 pointerIds, Vector<InputTarget>& inputTargets) {
    inputTargets.push();

    const InputWindowInfo* windowInfo = windowHandle->getInfo();
    InputTarget& target = inputTargets.editTop();
    // 这是最重要的一步，windowInfo是当前活动窗口，
    // 它的成员变量inputChannel用来描述Server端InputChannel
    target.inputChannel = windowInfo->inputChannel;
    target.flags = targetFlags;
    target.xOffset = - windowInfo->frameLeft;
    target.yOffset = - windowInfo->frameTop;
    target.scaleFactor = windowInfo->scaleFactor;
    target.pointerIds = pointerIds;
}
```
回到Step2中，完成了inputTargets的封装，继续把键盘事件分发给活动窗口。
# Step4: InputDispatcher::dispatchEventLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:921
void InputDispatcher::dispatchEventLocked(nsecs_t currentTime,
        EventEntry* eventEntry, const Vector<InputTarget>& inputTargets) {
... ...
    // 系统需要接收键盘事件的窗口都保存在inputTargets中，
    // 对于向InputManagerService注册过Connection的窗口，依次向他们分发键盘事件
    for (size_t i = 0; i < inputTargets.size(); i++) {
        const InputTarget& inputTarget = inputTargets.itemAt(i);

        // 从mConnectionsByFd中根据关键字找到Connection对象
        ssize_t connectionIndex = getConnectionIndexLocked(inputTarget.inputChannel); 
        if (connectionIndex >= 0) { // 注册过Connection的窗口，找到其Connection对象
            sp<Connection> connection = mConnectionsByFd.valueAt(connectionIndex);
            prepareDispatchCycleLocked(currentTime, connection, eventEntry, 
                &inputTarget);  // 🏁
        } ... ...
    }
}
```
回顾《键盘消息处理学习笔记（六）》之[Step4](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning6/#Step4-InputDispatcher-registerInputChannel-…)，Server端的InputChannel是以描述符为关键字保存到InputDispatcher::mConnectionsByFd中的，value被封装成了Connection对象的形式。

# Step5: InputDispatcher::prepareDispatchCycleLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:1773
void InputDispatcher::prepareDispatchCycleLocked(nsecs_t currentTime,
        const sp<Connection>& connection, EventEntry* eventEntry, const InputTarget* inputTarget) {
... ...

    // Not splitting.  Enqueue dispatch entries for the event as is.
    enqueueDispatchEntriesLocked(currentTime, connection, eventEntry, 
        inputTarget); // 🏁
}
```
# Step6: InputDispatcher::enqueueDispatchEntriesLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:1821
// 每一个Connection对象内部都有一个待分发的键盘事件队列outboundQueue，用于依次
// 分发给与之关联的窗口。只有上一个键盘事件被目标窗口处理完成后，才能继续分发下一个。
void InputDispatcher::enqueueDispatchEntriesLocked(nsecs_t currentTime,
        const sp<Connection>& connection, EventEntry* eventEntry, const InputTarget* inputTarget) {
    bool wasEmpty = connection->outboundQueue.isEmpty();

    // Enqueue dispatch entries for the requested modes.
    // 这一坨只有一个调用会生效
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_HOVER_EXIT);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_OUTSIDE);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_HOVER_ENTER);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_IS);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_SLIPPERY_EXIT);
    enqueueDispatchEntryLocked(connection, eventEntry, inputTarget,
            InputTarget::FLAG_DISPATCH_AS_SLIPPERY_ENTER);

    // If the outbound queue was previously empty, start the dispatch cycle going.
    // 如果之前队列为空，本次进队后非空，则可以将分发继续向窗口推进，
    // 否则说明上一次分发还没被处理完，本次分发不能马上进行
    if (wasEmpty && !connection->outboundQueue.isEmpty()) {
        startDispatchCycleLocked(currentTime, connection);  // 🏁
    }
}

void InputDispatcher::enqueueDispatchEntryLocked(
        const sp<Connection>& connection, EventEntry* eventEntry, const InputTarget* inputTarget,
        int32_t dispatchMode) {
    int32_t inputTargetFlags = inputTarget->flags;
    if (!(inputTargetFlags & dispatchMode)) {
        return; // 如果和要求的模式不匹配则直接退出
    }
    inputTargetFlags = (inputTargetFlags & ~InputTarget::FLAG_DISPATCH_MASK) | dispatchMode;

    // This is a new event.
    // Enqueue a new dispatch entry onto the outbound queue for this connection.
    DispatchEntry* dispatchEntry = new DispatchEntry(eventEntry, // increments ref
            inputTargetFlags, inputTarget->xOffset, inputTarget->yOffset,
            inputTarget->scaleFactor);

    // Apply target flags and update the connection's input state.
    switch (eventEntry->type) {
    case EventEntry::TYPE_KEY: {
        KeyEntry* keyEntry = static_cast<KeyEntry*>(eventEntry);
        dispatchEntry->resolvedAction = keyEntry->action;
        dispatchEntry->resolvedFlags = keyEntry->flags;
        ... ...
        break;
    }
    ... ...
    }
    ... ...
    // Enqueue the dispatch entry.将待分发的键盘事件入队
    connection->outboundQueue.enqueueAtTail(dispatchEntry);
    traceOutboundQueueLengthLocked(connection);
}
```
# Step7: InputDispatcher::startDispatchCycleLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputDispatcher.cpp:1932
void InputDispatcher::startDispatchCycleLocked(nsecs_t currentTime,
        const sp<Connection>& connection) {
... ...
    while (connection->status == Connection::STATUS_NORMAL
            && !connection->outboundQueue.isEmpty()) {
        DispatchEntry* dispatchEntry = connection->outboundQueue.head;
        dispatchEntry->deliveryTime = currentTime;

        // Publish the event.
        status_t status;
        EventEntry* eventEntry = dispatchEntry->eventEntry;
        switch (eventEntry->type) {
        case EventEntry::TYPE_KEY: {
            KeyEntry* keyEntry = static_cast<KeyEntry*>(eventEntry);

            // Publish the key event.
            status = connection->inputPublisher.publishKeyEvent(dispatchEntry->seq,
                    keyEntry->deviceId, keyEntry->source,
                    dispatchEntry->resolvedAction, dispatchEntry->resolvedFlags,
                    keyEntry->keyCode, keyEntry->scanCode,
                    keyEntry->metaState, keyEntry->repeatCount, keyEntry->downTime,
                    keyEntry->eventTime);   // 🏁
            break;
        }

        ... ...

        // Check the result.
        if (status) {
            if (status == WOULD_BLOCK) {
                if (connection->waitQueue.isEmpty()) {
                    ... ...
                    abortBrokenDispatchCycleLocked(currentTime, connection, true /*notify*/);
                } else {
                    // Pipe is full and we are waiting for the app to finish process some events
                    // before sending more events to it.
                    ... ...
                    connection->inputPublisherBlocked = true;
                }
            } else {
                ... ...
                abortBrokenDispatchCycleLocked(currentTime, connection, true /*notify*/);
            }
            return;
        }

        // Re-enqueue the event on the wait queue.
        connection->outboundQueue.dequeue(dispatchEntry);
        traceOutboundQueueLengthLocked(connection);
        connection->waitQueue.enqueueAtTail(dispatchEntry);
        traceWaitQueueLengthLocked(connection);
    }
}
```
# Step8: InputPublisher::publishKeyEvent(...)
``` c++
// frameworks/native/libs/input/InputTransport.cpp:243
status_t InputPublisher::publishKeyEvent(
        uint32_t seq,
        int32_t deviceId,
        int32_t source,
        int32_t action,
        int32_t flags,
        int32_t keyCode,
        int32_t scanCode,
        int32_t metaState,
        int32_t repeatCount,
        nsecs_t downTime,
        nsecs_t eventTime) {
        ... ...
    InputMessage msg;
    msg.header.type = InputMessage::TYPE_KEY;
    msg.body.key.seq = seq;
    msg.body.key.deviceId = deviceId;
    msg.body.key.source = source;
    msg.body.key.action = action;
    msg.body.key.flags = flags;
    msg.body.key.keyCode = keyCode;
    msg.body.key.scanCode = scanCode;
    msg.body.key.metaState = metaState;
    msg.body.key.repeatCount = repeatCount;
    msg.body.key.downTime = downTime;
    msg.body.key.eventTime = eventTime;
    return mChannel->sendMessage(&msg); // 🏁
}
```
# Step9: InputChannel::sendMessage(...)
``` c++
//frameworks/native/libs/input/InputTransport.cpp:152
status_t InputChannel::sendMessage(const InputMessage* msg) {
    size_t msgLength = msg->size();
    ssize_t nWrite;
    do {
        nWrite = ::send(mFd, msg, msgLength, MSG_DONTWAIT | MSG_NOSIGNAL);
    } while (nWrite == -1 && errno == EINTR);
    ... ...
    return OK;
}
```
此处的mFd来自需要接收键盘事件的应用窗口所保留的Server端的InputChannel，在《键盘消息处理学习笔记（八）》的[Step5](http://palanceli.com/2016/10/03/2016/1002KeyboardLearning8/#Step5-NativeInputEventReceiver-setFdEvents-…)中，该描述符被添加到了线程Looper中，并指定了回调函数：
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:145
void NativeInputEventReceiver::setFdEvents(int events) {
    ... ...
    mMessageQueue->getLooper()->addFd(fd, 0, events, this, NULL);
    ... ...
}
```
NativeInputEventReceiver继承自LooperCallback:
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:50
class NativeInputEventReceiver : public LooperCallback {
... ...
};
```
于是，当线程Looper监听到该描述符有内容写入后，将调用回调函数体NativeInputEventReceiver::handleEvent(...)。