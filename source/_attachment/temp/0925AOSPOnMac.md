---
layout: post
title: 解决macOSX10.12.SDK下编译Android Open Source Project出错的问题
date: 2016-09-25 20:44:05 +0800
categories: 环境、配置
tags: Android
toc: true
comments: true
---
最近macOS的XCode升级之后，Android源码就编译通不过了，报告syscall已经被废弃：
```
system/core/libcutils/threads.c:38:10: error: 'syscall' is deprecated: first deprecated in OS X 10.12 - syscall(2) is unsupported; please switch to a supported interface. For SYS_kdebug_trace use kdebug_signpost(). [-Werror,-Wdeprecated-declarations]
  return syscall(SYS_thread_selfid);
         ^
host C: libcutils <= system/core/libcutils/iosched_policy.c
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.12.sdk/usr/include/unistd.h:733:6: note: 'syscall' has been explicitly marked deprecated here
int      syscall(int, ...); 
```
<!-- more -->

看到这个报错都快哭了，我搜了一下，AOSP里有大量的syscall调用，从源码处解决是不现实的。都怪我手欠，看到升级提示，就同意了，而且几台mac都升级了😭。去Android官网以及Google搜索，都没有搜到相关的解决办法，估计是刚出的问题，遇到的人比较少。我不确认AndroidN是否支持macOS10.12.SDK，重新下载新的源码又需要很长时间，还有很多事情要做，不想在源码编译上再浪费时间了。最后我决定试一把用老的SDK编译，貌似可以解决问题。

去到/Applications/XCode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs，发现MacOSX10.11.sdk已经被删除，只剩下MacOSX10.12.sdk，所以首先要去下载10.11的SDK。可以去[MacOSX-SDKs](https://github.com/phracker/MacOSX-SDKs)下载MacOSX10.11.sdk，解压拷贝到/Applications/XCode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs。为了避免下次升级的时候再被删除，可以放到~/Document/MacOSX10.11.sdk，再给它创建一个软链接：
``` bash
$ ln -s ~/Document/MacOSX10.11.sdk /Applications/XCode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk
```

然后确保AOSP源码下build/core/combo/mac_version.mk文件中
`mac_sdk_versions_supported :=  10.9 10.10 10.11`
后面不要写10.12。

再编译就正常了。
