---
layout: post
title: Service启动过程学习笔记（一）
date: 2016-11-21 23:59:58 +0800
categories: Android
tags: Service启动过程
toc: true
comments: true
---
当客户端通过startService(...)启动Service组件时，它调用的是ContextWrapper::startService(...)，接下来就以此函数为起点学习Service组件的启动。<!-- more -->
# Step1 ContextWrapper::startService(...)
``` java
public class ContextWrapper extends Context {
    Context mBase;  // mBase实际指向一个ContextImpl对象，用来描述所运行的上下文环境
... ...
// frameworks/base/core/java/android/content/ContextWrapper.java:580
    public ComponentName startService(Intent service) {
        return mBase.startService(service); // 🏁
    }
... ...
}
```
# Step2 ContextImpl::startService(...)
``` java
// frameworks/base/core/java/android/app/ContextImpl.java:1220
    public ComponentName startService(Intent service) {
        ... 
        return startServiceCommon(service, mUser); // 🏁
    }

// frameworks/base/core/java/android/app/ContextImpl.java:1236
    private ComponentName startServiceCommon(Intent service, UserHandle user) {
        try {
            validateServiceIntent(service);
            service.prepareToLeaveProcess();
            ComponentName cn = ActivityManagerNative.getDefault().startService(
                mMainThread.getApplicationThread(), service, 
                service.resolveTypeIfNeeded(
                            getContentResolver()), getOpPackageName(), 
                            user.getIdentifier());
            ...
            return cn;
        } catch (RemoteException e) { ... }
    }
```