---
title: 输入法文件存储占用尺寸调查
date:   2016-09-10 14:40:21 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
# 了解各输入法的文件分布情况
直接使用du命令，即可把所有文件的尺寸打印出来。首先来看/data/app
<!-- more -->
``` bash
$ du -ack /data/app/com.sohu.inputmethod.sogou-1
20704   ./com.sohu.inputmethod.sogou-1/base.apk
16  ./com.sohu.inputmethod.sogou-1/lib/arm/libsogouupdcore.so
28  ./com.sohu.inputmethod.sogou-1/lib/arm/libweibosdkcore.so
... ...
$ du -ack /data/app/com.baidu.input-1
$ du -ack /data/app/com.iflytek.inputmethod-1
```
-a 是显示每个文件的大小
-c 是显示文件夹的总和
-k 是以k为单位输出

然后再看/data/data
``` bash
$ du -ack /data/data/com.sohu.inputmethod.sogou
$ du -ack /data/data/com.iflytek.inputmethod
$ du -ack /data/data/com.baidu.input
```
把结果导入到excel里，并以空格、Tab符、/作为分隔符。

