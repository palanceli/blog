---
layout: post
title: 键盘消息处理学习笔记（十一）
date: 2016-10-04 18:49:17 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接《键盘消息处理学习笔记（十）》当InputDispatcher被InputReader唤醒后，启动键盘事件分发流程，最终会把分发数据写入活动窗口注册进来的socket描述符，完成事件分发。这会导致线程Looper继续被唤醒，并且调用与这些描述符关联的回调函数。回调函数为NativeInputEventReceiver::handleEvent(...)本文以该回调函数为起点，来看该事件如何被应用程序窗口处理。

<!-- more -->
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
    ... ...

    if (consumeBatches) {
        mBatchedInputEventPending = false;
    }
    if (outConsumedBatch) {
        *outConsumedBatch = false;
    }

    ScopedLocalRef<jobject> receiverObj(env, NULL);
    bool skipCallbacks = false;
    for (;;) {
        uint32_t seq;
        InputEvent* inputEvent;
        status_t status = mInputConsumer.consume(&mInputEventFactory,
                consumeBatches, frameTime, &seq, &inputEvent);
        if (status) {
            if (status == WOULD_BLOCK) {
                if (!skipCallbacks && !mBatchedInputEventPending
                        && mInputConsumer.hasPendingBatch()) {
                    // There is a pending batch.  Come back later.
                    if (!receiverObj.get()) {
                        receiverObj.reset(jniGetReferent(env, mReceiverWeakGlobal));
                        ... ...
                    }

                    mBatchedInputEventPending = true;
                    ... ...
                    env->CallVoidMethod(receiverObj.get(),
                            gInputEventReceiverClassInfo.dispatchBatchedInputEventPending);
                    if (env->ExceptionCheck()) {
                        ALOGE("Exception dispatching batched input events.");
                        mBatchedInputEventPending = false; // try again later
                    }
                }
                return OK;
            }
            ... ...
            return status;
        }
        assert(inputEvent);

        if (!skipCallbacks) {
            if (!receiverObj.get()) {
                receiverObj.reset(jniGetReferent(env, mReceiverWeakGlobal));
                ... ...
            }

            jobject inputEventObj;
            switch (inputEvent->getType()) {
            case AINPUT_EVENT_TYPE_KEY:
                ... ...
                inputEventObj = android_view_KeyEvent_fromNative(env,
                        static_cast<KeyEvent*>(inputEvent));
                break;

            case AINPUT_EVENT_TYPE_MOTION: {
                ... ...
                MotionEvent* motionEvent = static_cast<MotionEvent*>(inputEvent);
                if ((motionEvent->getAction() & AMOTION_EVENT_ACTION_MOVE) && outConsumedBatch) {
                    *outConsumedBatch = true;
                }
                inputEventObj = android_view_MotionEvent_obtainAsCopy(env, motionEvent);
                break;
            }

            default:
                assert(false); // InputConsumer should prevent this from ever happening
                inputEventObj = NULL;
            }

            if (inputEventObj) {
                ... ...
                env->CallVoidMethod(receiverObj.get(),
                        gInputEventReceiverClassInfo.dispatchInputEvent, seq, inputEventObj);
                if (env->ExceptionCheck()) {
                    ALOGE("Exception dispatching input event.");
                    skipCallbacks = true;
                }
                env->DeleteLocalRef(inputEventObj);
            } else {
                ALOGW("channel '%s' ~ Failed to obtain event object.", getInputChannelName());
                skipCallbacks = true;
            }
        }

        if (skipCallbacks) {
            mInputConsumer.sendFinishedSignal(seq, false);
        }
    }
}
```