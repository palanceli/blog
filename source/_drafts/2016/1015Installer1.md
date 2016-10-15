---
layout: post
title: Android App安装过程笔记
date: 2016-10-15 15:14:42 +0800
categories: Android
tags: 安装过程
toc: true
comments: true
---
在Android下安装一个APP时，PackageManagerService会解析该APP的AndroidManifest.xml文件，以便获取它的安装信息，同时为该APP分配Linux用户ID和Linux用户组ID。

PackageManagerService是在SystemService启动的时候由该进程启动起来的：
<!-- more -->
``` java
// frameworks/base/services/java/com/android/server/SystemServer.java:366
public final class SystemServer {
... ...
    public static void main(String[] args) {    // 入口函数
        new SystemServer().run();
    }
    private void run() {
        ... ... 
        try { 
            startBootstrapServices();           // :268
            ... ...
        } catch (Throwable ex) {
            ... ...
        }
    }
    private void startBootstrapServices() {
    ... ...
    // Start the package manager.
    Slog.i(TAG, "Package Manager");             // :365
    mPackageManagerService = PackageManagerService.main(mSystemContext, installer,
            mFactoryTestMode != FactoryTest.FACTORY_TEST_OFF, mOnlyCore);
    mFirstBoot = mPackageManagerService.isFirstBoot();
    mPackageManager = mSystemContext.getPackageManager();
    ... ...
} 
```
PackageManagerService在启动过程中会对系统中的应用程序进行安装，因此可以它的main函数作为起点。
# PackageManagerService.main(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:1765
public static PackageManagerService main(Context context, Installer installer,
        boolean factoryTest, boolean onlyCore) {
    PackageManagerService m = new PackageManagerService(context, installer,
            factoryTest, onlyCore);
    ServiceManager.addService("package", m);
    return m;
}
```

