---
layout: post
title: 键盘消息处理学习笔记（九）
date: 2016-10-03 23:17:40 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
再回过头来看《键盘消息处理学习笔记（三）》中[InputReaderThread的启动](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning3/#InputReaderThread的启动)。Step3中`mEventHub->getEvents(...)`从所有输入设备读取一轮IO事件，如果有IO事件发生，该函数中的循环就会中断，函数返回到Step2中的`InputReader::loopOnce()`，接着由`InputReader::processEventsLocked(...)`来处理这些IO事件。本文以该函数为起点研究键盘事件的处理。
<!-- more -->
``` c++
// frameworks/native/services/inputflinger/InputReader.cpp:272
void InputReader::loopOnce() {
    ... ...
    int32_t timeoutMillis;
    ... ...
    size_t count = mEventHub->getEvents(timeoutMillis, mEventBuffer, EVENT_BUFFER_SIZE);    // 从所有输入设备读取一轮IO事件，保存到mEventBuffer
    ... ...
        if (count) {
            processEventsLocked(mEventBuffer, count); // 🏁
        }
    ... ...
}
```
# Step1: InputReader::processEventsLocked(...)
``` c++
// frameworks/native/services/inputflinger/InputReader.cpp:336
void InputReader::processEventsLocked(const RawEvent* rawEvents, size_t count) {
    for (const RawEvent* rawEvent = rawEvents; count;) {
        int32_t type = rawEvent->type;
        // 扫描rawEvent之后连续出现且和rawEvent->deviceId相同的，非设备增删查的事件个数
        size_t batchSize = 1;
        if (type < EventHubInterface::FIRST_SYNTHETIC_EVENT) {
            int32_t deviceId = rawEvent->deviceId;
            while (batchSize < count) {
                if (rawEvent[batchSize].type >= EventHubInterface::FIRST_SYNTHETIC_EVENT
                        || rawEvent[batchSize].deviceId != deviceId) {
                    break;
                }
                batchSize += 1;
            }
... ...
            // 🏁批量处理这些IO事件
            processEventsForDeviceLocked(deviceId, rawEvent, batchSize);
        } else {
            // 处理设备的增、删、查请求
            switch (rawEvent->type) {
            case EventHubInterface::DEVICE_ADDED:
                addDeviceLocked(rawEvent->when, rawEvent->deviceId);
                break;
            case EventHubInterface::DEVICE_REMOVED:
                removeDeviceLocked(rawEvent->when, rawEvent->deviceId);
                break;
            case EventHubInterface::FINISHED_DEVICE_SCAN:
                handleConfigurationChangedLocked(rawEvent->when);
                break;
            default:
                ALOG_ASSERT(false); // can't happen
                break;
            }
        }
        count -= batchSize;
        rawEvent += batchSize;
    }
}
```
