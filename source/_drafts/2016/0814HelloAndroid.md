---
title: 驱动->HAL->frameworks->app
date:   2016-08-15 00:51:21 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
跟着《Android系统源代码情景分析》第2章，我想把从`驱动层`到`硬件抽象层`到`frameworks层`再到`应用层`各层的工作完整地做一遍、调一遍。之前已经有了一些积累，我希望在Android最新的源码上，并且使用AndroidStudio能编译、调试得到每一层。按照我下一步计划，接下来将深入研究键盘消息处理机制，希望在开展这一步工作之前，能够对Android的格局有更进一步的理解，对AndroidStudio的使用能够更娴熟。

首先我会按照《Android系统源代码情景分析》，在命令行下，自下而上把各层工作跑一遍。尔后再从上到下，逐步把各层工作切换到AndroidStudio上来。计划用两周时间搞定。代码就放在[palanceli/androidex/hello-android](https://github.com/palanceli/androidex/tree/master/hello-android)下。
<!-- more -->
# 驱动层
androidex的文件结构如下：
```
├──android-6.0.1_r11           // Android源码
├──androidex
   ├──setup.sh                 // 调用每个子项目的setup.sh，完成初始化工作
   ├──hello-android
   │  └──hello-android-driver
   │     ├──hello-android.c
   │     ├──hello-android.h
   │     ├──Kconfig
   │     ├──Makefile
   │     └──setup.sh           
   ├──... ...
   └──
```
脚本`androidex/hell-android/hello-android-driver/setup.sh`创建
软链`kernel/goldfish/drivers/hello-android`指向
`androidex/hell-android/hello-android-driver/`。
执行`androidex/setup.sh`完成初始化。
这么做的目的是让Android源码和我的代码分离开，我的代码全都集中在androidex下，可以完整地提交到GitHub上去。随Android源码编译的需要，androidex散落到源码树中，建个软链就确保源码树下总能访问到最新androidex了。

