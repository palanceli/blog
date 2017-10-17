---
layout: post
title: 《Android Programming BNRG》笔记四
date: 2016-10-16 22:00:00 +0800
categories: Android Programming
tags: BNRG笔记
toc: true
comments: true
---
本章介绍了Android编程时常用的调试方法，本章没有太多要记录的笔记，简单写几笔吧。
本章要点：
- 分析Exception和调用栈信息
- 使用log+Exception打印log和调用栈信息
- 断点调试
- Android Lint
<!-- more -->
# 开启Android Lint
Android Lint是Android Studio自带的静态代码分析工具，点击菜单 Analyze > Inspect Code...即可启动。

# 当Android Studio出现一些和资源相关奇怪错误的解决办法
有时候当添加或删除资源文件时，Android Studio会报一些奇怪的错误，在确认确实代码没问题时，可以试试下面的方法。
- R.java可能还没有为某个资源生成代码，找到这个资源所在xml文件，重新保存，这会触发R.java重新为它生成代码。
- Build > Clean Project会触发Android Studio重建项目
- 如果修改了build.gradle，需要更新项目的构建设置，具体步骤是Tools > Android > Sync Project with Gradle Files。
- 运行Android Lint。