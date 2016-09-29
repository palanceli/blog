---
layout: post
title: 用Shell脚本完成基本统计
date: 2016-09-28 23:50:13 +0800
categories: 随笔笔记
tags: Shell
toc: true
comments: true
---
读了Android源码的envsetup.sh之后，才知道Shell脚本真是个强大的工具！以前跟着做前端的同事学了点三脚猫功夫，可是以后每次用的时候都要重复查一些用法，这里不打算系统地讲Shell脚本，那需要一本书的厚度。我只记录自己常用的命令，至少以后不用一再搜索了。我使用shell脚本最多的就是日志统计，用的比较多的命令是cut、grep、awk，读完envsetup.sh之后，我认为应该扩大自己掌握的范围，能给日常统计工作带来极大便利。最主要的好处就是轻便、快。

# cut

