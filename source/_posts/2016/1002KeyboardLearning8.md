---
layout: post
title: 键盘消息处理学习笔记（八）注册Client端InputChannel
date: 2016-10-03 22:01:23 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step1：
``` java
// 🏁将mInputChannel注册到正在启动的Activity所在进程的主线程中
mInputEventReceiver = new WindowInputEventReceiver(mInputChannel,
                            Looper.myLooper());
```
mInputChannel是在ViewRootImpl::setView(...)中创建的Client端InputChannel，并且被transferTo到InputDispatcher创建的Client端InputChannel。
通过构造WindowInputEventReceiver，将该InputChannel注册到正在启动的Activity所在主线程中，本文继续深入WindowInputEventReceiver。

在深入讨论之前，先抛出我的一个疑问：在ViewRootImpl::setView(...)函数中，相互连接的InputChannel对是在WindowManagerService进程中创建的，通过函数`mWindowSession.addToDisplay(...)`在远程完成，函数返回后mInputChannel中保存的是WindowManagerService中创建的socket描述符，在本地是不能直接使用的，接下来的注册又用到了mInputChannel，号称要把它注册到正在启动的Activity中，这不会有危险吗？
<!-- more -->

# Step1: WindowInputEventReceiver的构造函数
``` java
// frameworks/base/core/java/android/view/ViewRootImpl.java:6018
    final class WindowInputEventReceiver extends InputEventReceiver {
    ... ...
        /// inputChannel    ViewRootImpl::mInputChannel
        public WindowInputEventReceiver(InputChannel inputChannel, Looper looper) {
            super(inputChannel, looper);    // 🏁
        }
```

# Step2: InputEventReceiver的构造函数
``` java
// frameworks/base/core/java/android/view/InputEventReceiver.java:60
    // inputChannel     ViewRootImpl::mInputChannel
    public InputEventReceiver(InputChannel inputChannel, Looper looper) {
        ... ...
        mInputChannel = inputChannel;
        mMessageQueue = looper.getQueue();
        mReceiverPtr = nativeInit(new WeakReference<InputEventReceiver>(this),
                inputChannel, mMessageQueue);   // 🏁

        mCloseGuard.open("dispose");
    }
```

# Step3: nativeInit(...)
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:333
static jlong nativeInit(JNIEnv* env, jclass clazz, jobject receiverWeak,
        jobject inputChannelObj, jobject messageQueueObj) {
    // 把java层对象转成c++层
    sp<InputChannel> inputChannel = android_view_InputChannel_getInputChannel(
                                                        env, inputChannelObj);
    ... ...
    sp<MessageQueue> messageQueue = android_os_MessageQueue_getMessageQueue(
                                                        env, messageQueueObj);
    ... ...

    sp<NativeInputEventReceiver> receiver = new NativeInputEventReceiver(env,
                                    receiverWeak, inputChannel, messageQueue);
    status_t status = receiver->initialize(); // 🏁
    ... ...

    receiver->incStrong(gInputEventReceiverClassInfo.clazz); // retain a reference for the object
    return reinterpret_cast<jlong>(receiver.get());
}

// :89
// inputChannel     Client端InputChannel
NativeInputEventReceiver::NativeInputEventReceiver(JNIEnv* env,
        jobject receiverWeak, const sp<InputChannel>& inputChannel,
        const sp<MessageQueue>& messageQueue) :
        mReceiverWeakGlobal(env->NewGlobalRef(receiverWeak)),
        mInputConsumer(inputChannel), mMessageQueue(messageQueue),
        mBatchedInputEventPending(false), mFdEvents(0) {
    ... ...
}
```
由于后面会用到，来看mInputConsumer的构造函数：
``` c++
// frameworks/native/libs/input/InputTransport.cpp:376
InputConsumer::InputConsumer(const sp<InputChannel>& channel) :
        mResampleTouch(isTouchResamplingEnabled()),
        mChannel(channel), mMsgDeferred(false) {
}
```
mChannel的类型为InputChannel：
``` c++
// frameworks/native/libs/input/InputTransport.h:138
class InputChannel : public RefBase {
... ...
    InputChannel(const String8& name, int fd);

... ...
    inline int getFd() const { return mFd; }
```

# Step4: NativeInputEventReceiver::initialize()
``` c++
// frameworks/base/core/jni/android_view_InputEventReceiver.cpp:105
status_t NativeInputEventReceiver::initialize() {
    setFdEvents(ALOOPER_EVENT_INPUT); // 🏁
    return OK;
}
```
`ALOOPER_EVENT_INPUT`定义在frameworks/native/include/android/looper.h中：
``` c++
enum {
    /**
     * The file descriptor is available for read operations.
     */
    ALOOPER_EVENT_INPUT = 1 << 0,
    ... ...
}；
```

# Step5: NativeInputEventReceiver::setFdEvents(...)
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
根据Step3的分析，mInputConsumer.getChannel()->getFd()返回ViewRootImpl::mInputChannel->getFd()，即Client端的InputChannel的socket描述符。

mMessageQueue->getLooper()是从Step2中一路传进来，其实就是主线程的Looper，相当于是个线程全局变量，独一份。

# 总结
所谓“将mInputChannel注册到正在启动的Activity所在进程的主线程中”的含义很简单，就是向主线程注册活动窗口的InputChannel的socket，让主线程Looper监听该socket。通过该socket，InputManagerService的InputDispatcher就可以将键盘事件分发到应用程序。
至此，舞台已经搭建完成，发条上满了弦，多米诺骨牌也都已摆放就绪，就等着一个按键被敲击，触发一系列的连锁反应了。接下来看键盘消息怎么在这个舞台上流转和处理。

不过前面我的存疑一直没有得到解决：<font color='red'>这个socket是在WindowManagerService中创建的，描述符跨进程传递是没意义的。我猜测一定是在某个环节，系统做了合法的转换，所以这个存疑暂时还得先搁置，不影响大局。</font>