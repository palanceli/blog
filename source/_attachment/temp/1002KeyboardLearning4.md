---
layout: post
title: 键盘消息处理学习笔记（四）——Looper机制
date: 2016-10-02 11:30:41 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
在[《键盘消息处理学习笔记（三）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning3/)中，InputSispatcher::dispatchOnce()函数里，消息的等待落到了Looper::pollOnce(...)函数中，本文就来专门研究一下Looper这个类。该类可以用来监控一组文件描述符的事件，当任意一个它所维护的文件描述符有新消息时，将被唤醒，否则就一直等待。

<!-- more -->
# Looper的构造函数
``` cpp
// system/core/libutils/Looper.cpp:71
Looper::Looper(bool allowNonCallbacks) :
        mAllowNonCallbacks(allowNonCallbacks), mSendingMessage(false),
        mPolling(false), mEpollFd(-1), mEpollRebuildRequired(false),
        mNextRequestSeq(0), mResponseIndex(0), mNextMessageUptime(LLONG_MAX) {
    mWakeEventFd = eventfd(0, EFD_NONBLOCK);
    ... ...
    rebuildEpollLocked();
}
```
函数eventfd()创建一个事件对象的描述符，该对象可以用于事件的等待/通知机制。其原型如下：
``` cpp
#include <sys/eventfd.h>
int eventfd(unsigned int initval, int flags);
```
该对象在内核维护着一个计数器，初始值为initval。它有两个函数：
* ssize_t write(int fd, const void* buf, size_t count)
从buf中取出8字节的整型值，加到计数器上。如果计数器的值达到0xfffffffffffffffe就会阻塞，直到被read。
* ssize_t read(int fd, void* buf, size_t count)
读取计数器的值。如果计数器的值不为0，则读取成功返回该值；如果为0，非阻塞模式时直接返回失败，并把error置为EINVAL，阻塞模式则一直阻塞到计数器非0。

mWakeEventFd正是这样一种对象，Looper默认生成这么一个eventfd对象，Looper::pollOnce(...)等待该对象被写入内容，一旦被写入，Looper::pollOnce(...)函数就会返回。这就是组成消息泵的重要部件——消息的发送者发出消息后向mWakeEventFd写入内容，Looper::pollOnce(...)被唤醒，然后执行消息处理，处理完成后再次睡眠等待，直到下次再发来消息。Android应用程序的消息处理就采用了这种模式。

Looper也支持多个描述符的同时监听，可以通过Looper::addFd(...)添加多个描述符，Looper使用一个数组mRequests保存这些描述符。任何一个描述符被写入数据，Looper::pollOnce(...)都会被唤醒，Android应用程序键盘消息处理就采用了这种模式。

## Looper::rebuildEpollLocked()
``` cpp
void Looper::rebuildEpollLocked() {
    ... ...

    // Allocate the new epoll instance and register the wake pipe.
    // 创建一个epoll实例，该实例可以监控一组已注册的描述符，任何一个描述符发生了
    // 写入，对该epoll实例的wait都会返回，否则会一直阻塞
    mEpollFd = epoll_create(EPOLL_SIZE_HINT);
    ... ...

    struct epoll_event eventItem;
    memset(& eventItem, 0, sizeof(epoll_event)); // zero out unused members of data field union
    eventItem.events = EPOLLIN;
    eventItem.data.fd = mWakeEventFd;
    // mWakeEventFd注册到mEpollFd中，成为默认被监控的描述符
    int result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mWakeEventFd, & eventItem);
    ... ...

    for (size_t i = 0; i < mRequests.size(); i++) {
        const Request& request = mRequests.valueAt(i);
        struct epoll_event eventItem;
        request.initEventItem(&eventItem);

        int epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, request.fd, & eventItem);
        ... ...
    }
}
```
# Looper::addFd(...)
``` cpp
int Looper::addFd(int fd, int ident, int events, 
            const sp<LooperCallback>& callback, void* data) {
    ... ...
        Request request;
        request.fd = fd;
        request.ident = ident;
        request.events = events;
        request.seq = mNextRequestSeq++;
        request.callback = callback;
        request.data = data;
        ... ...
        struct epoll_event eventItem;
        request.initEventItem(&eventItem);
            // 注册描述符
            int epollResult = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, fd, & eventItem);
            ... ...
            mRequests.add(fd, request); // 保存到mRequests数组
    ... ...
    return 1;
}
```

# Looper::pollOnce(...)
前面注册了若干描述符，函数pollOnce(timeoutMillis)则用来等待这些描述符，最长等待timeoutMillis毫秒。等待期间，任何一个描述符发生读写事件，则该函数立刻返回。
``` cpp
// system/core/include/utils/Looper.h
class Looper : public RefBase {
... ...
// : 263
    int pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData);
    inline int pollOnce(int timeoutMillis) {
        return pollOnce(timeoutMillis, NULL, NULL, NULL); // 🏁
    }
... ...
};

// system/core/libutils/Looper.cpp:184
int Looper::pollOnce(int timeoutMillis, int* outFd, int* outEvents, void** outData) {
    int result = 0;
    for (;;) {
... ...
        if (result != 0) {
... ...
            return result;
        }

        result = pollInner(timeoutMillis); // 🏁
    }
}
```
该函数不断调用pollInner(...)查询是否有新消息需要处理。如果有，pollInner(...)返回非0，跳出循环。

## Looper::pollInner(...)
``` cpp
// system/core/libutils/Looper.cpp:220
int Looper::pollInner(int timeoutMillis) {
    ... ...
    struct epoll_event eventItems[EPOLL_MAX_EVENTS];
    // 阻塞，等待在这里，直到有写入事件
    int eventCount = epoll_wait(mEpollFd, eventItems, EPOLL_MAX_EVENTS, timeoutMillis);
    ... ...
    // 检查是哪一个描述符发生了读写事件
    for (int i = 0; i < eventCount; i++) {
        int fd = eventItems[i].data.fd;
        uint32_t epollEvents = eventItems[i].events;
        if (fd == mWakeEventFd) {
            if (epollEvents & EPOLLIN) {
                awoken();   // 🏁把mWakeEventFd中的数据读出，以清空缓存
            } 
            ... ...
        } else {
            ssize_t requestIndex = mRequests.indexOfKey(fd);
            if (requestIndex >= 0) {
                int events = 0;
                if (epollEvents & EPOLLIN) events |= EVENT_INPUT;
                if (epollEvents & EPOLLOUT) events |= EVENT_OUTPUT;
                if (epollEvents & EPOLLERR) events |= EVENT_ERROR;
                if (epollEvents & EPOLLHUP) events |= EVENT_HANGUP;
                pushResponse(events, mRequests.valueAt(requestIndex));
            } 
            ... ...
        }
    }
Done: ;
... ...
    // Invoke all response callbacks.
    // 如果通过addFd(...)注册的描述符还有附加的callback，则依次执行
    for (size_t i = 0; i < mResponses.size(); i++) {
        Response& response = mResponses.editItemAt(i);
        if (response.request.ident == POLL_CALLBACK) {
            int fd = response.request.fd;
            int events = response.events;
            void* data = response.request.data;
... ...
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
... ...
    return result;
}
```
如下面介绍，Looper::awoken()只不过把mWakeEventFd中的数据读出，具体是什么数据其实并不需要关心，因为mWakeEventFd的作用只是当一个信号灯，数据写入会让信号灯亮，亮了以后要做什么则是业务层的职责了。mWakeEventFd只负责等待灯亮后，放行业务层来处理。

而mRequests中的描述符被写入，则不应该在这里读出数据，因为这些描述符是业务层创建、维护，只是注册到Looper中，利用了Looper阻塞、等待的机制，一旦信号灯亮，Looper会把这些描述符交给业务层处理。

这就好比学校传达室的大爷，他自己定个闹钟，到点了，他会去敲学校的钟，告诉大家要上课了，当然敲钟之前他会自己把闹钟按掉。这就是mWakeEventFd机制。
此外，他还会帮大家代收快递，这也相当于是等待的过程。一旦来了快递，他会通知收件人过来取件，而不会自己把包裹处理掉，这就是通过addFd(...)添加进来的描述符的机制。

在`Done:`后面还有一大坨代码是更高级的机制：每个通过addFd(...)添加进来的描述符还可以指定一个回调函数，每次有信号发生时，先执行该回调，再通知业务层。这就好比我们提前跟传达室的大爷打好招呼，如果有人找我，先把他请到休息室，茶水招待上，再通知我过来接待。

## Looper::awoken()
``` cpp
// system/core/libutils/Looper.cpp:418
void Looper::awoken() {
    ... ...
    uint64_t counter;
    TEMP_FAILURE_RETRY(read(mWakeEventFd, &counter, sizeof(uint64_t)));
}
```
`TEMP_FAILURE_RETRY`的定义为
``` cpp
#define TEMP_FAILURE_RETRY(expression) \  
  (__extension__\  
   ({ long int __result;\  
       do __result = (long int)(expression);\  
       while(__result == -1L&& errno == EINTR);\  
       __result;})\  
#endif  
```
直到读出一个正数才返回。

# Looper::wake()
``` cpp
// system/core/libutils/Looper.cpp:404
void Looper::wake() {
 ... ...
    uint64_t inc = 1;
    ssize_t nWrite = TEMP_FAILURE_RETRY(write(mWakeEventFd, &inc, sizeof(uint64_t)));
    ... ...
}
```
显然Looper构造了一个完整的消息泵逻辑，poll系列的函数从该泵中获取信号，如果没有信号则一直等待；wake()函数负责向该泵发送信号。

# 关于epoll
epoll在Looper中以及键盘消息处理机制中都有被使用，这里简单描述一下它的原理和使用方法。epoll是用来替代select，但和select相比，它不会随着监听fd数目的增长而降低效率。epoll的接口很简单，共三个函数。
## int epoll_create(int size)
创建一个epoll句柄，size用来告诉内核这个监听的数目一共有多大。需要注意，当创建好epoll句柄后，它会占用一个fd值，在linux下如果查看/proc/进程id/fd/，是能够看到这个fd的，所以在使用完epoll后，必须调用close()关闭，否则可能导致fd被耗尽。

## int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event)
epoll的事件注册函数。第一个参数是epoll_create()的返回值，第二个参数表示动作，用三个宏来表示：
EPOLL_CTL_ADD：注册新的fd到epfd中；
EPOLL_CTL_MOD：修改已经注册的fd的监听事件；
EPOLL_CTL_DEL：从epfd中删除一个fd；
第三个参数是需要监听的fd，第四个参数是告诉内核需要监听什么事，struct epoll_event结构如下：
``` cpp
typedef union epoll_data {
    void *ptr;
    int fd;
    __uint32_t u32;
    __uint64_t u64;
} epoll_data_t;

struct epoll_event {
    __uint32_t events; /* Epoll events */
    epoll_data_t data; /* User data variable */
};
```
events可以是以下几个宏的集合：
EPOLLIN ：表示对应的文件描述符可以读（包括对端SOCKET正常关闭）；
EPOLLOUT：表示对应的文件描述符可以写；
EPOLLPRI：表示对应的文件描述符有紧急的数据可读（这里应该表示有带外数据到来）；
EPOLLERR：表示对应的文件描述符发生错误；
EPOLLHUP：表示对应的文件描述符被挂断；
EPOLLET： 将EPOLL设为边缘触发(Edge Triggered)模式，这是相对于水平触发(Level Triggered)来说的。
EPOLLONESHOT：只监听一次事件，当监听完这次事件之后，如果还需要继续监听这个socket的话，需要再次把这个socket加入到EPOLL队列里

## int epoll_wait(int epfd, struct epoll_event * events, int maxevents, int timeout)
等待事件的产生。参数events用来从内核得到事件的集合，maxevents表示events有多大，这个 maxevents的值不能大于创建epoll_create()时的size，参数timeout是超时时间（毫秒，0会立即返回，-1将永久阻塞）。该函数返回需要处理的事件数目，如返回0表示已超时。

## epoll的使用模式
几乎所有的epoll程序都是用如下框架：
``` cpp
for( ; ; ) { 
    nfds=epoll_wait(epfd, events, maxevents, timeoutMilliSec); 

    for(i=0;i<nfds;++i){ //处理所发生的所有事件
        if(events[i].data.fd==listenfd){    // 监听事件
            connfd = accept(listenfd,(sockaddr *)&clientaddr, &clilen); 
            ev.data.fd = connfd;            // 设置用于读操作的文件描述符 
            ev.events = EPOLLIN | EPOLLET;  // 设置用于注测的读操作事件 
            epoll_ctl(epfd,EPOLL_CTL_ADD,connfd,&ev); // 注册ev事件 
       }else if(events[i].events&EPOLLIN){  // 读事件
            if ( (sockfd = events[i].data.fd) < 0) 
                continue; 
            read(sockfd, line, MAXLINE);

            ev.data.fd = sockfd;            // 设置用于写操作的文件描述符 
            ev.events = EPOLLOUT | EPOLLET; // 设置用于注测的写操作事件 
            epoll_ctl(epfd, EPOLL_CTL_MOD, sockfd, &ev); //修改sockfd上要处理的事件为EPOLLOUT 
       }else if(events[i].events&EPOLLOUT){ // 写事件
            sockfd = events[i].data.fd; 
            write(sockfd, line, n);

            ev.data.fd=sockfd;              //设置用于读操作的文件描述符 
            ev.events=EPOLLIN | EPOLLET;    //设置用于注册的读操作事件 
            epoll_ctl(epfd,EPOLL_CTL_MOD,sockfd,&ev); //修改sockfd上要处理的事件为EPOLIN 
        } 
     } 
  } 
```

