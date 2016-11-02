---
layout: post
title: 热补丁之AndFix
date: 2016-11-01 22:50:58 +0800
categories: Android
tags: 热补丁
toc: true
comments: true
---
# AndFix的使用
Andfix是阿里巴巴的开源项目，完成热补丁的功能。来[alibaba/AndFix](https://github.com/alibaba/AndFix)可以下到源代码，先来把这个东西跑起来。测试app的代码树结构如下：<!-- more -->
```
HelloAndroid
├──AndroidManifest.xml
├──Android.mk
├──src
│  └──palance/li/hello
│     └──HelloAndroid.java
└──res
   ├──layout
   │  └──main.xml
   ├──values
   │  └──strings.xml
   └──drawable
      └──icon.png 
```
运行起来如下：
![测试app被patch前](1101AndFix/img01.png)

