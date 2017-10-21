---
layout: post
title: 《iOS Programming BNRG》笔记九
date: 2017-07-28 23:30:00 +0800
categories: iOS Programming
tags: iOS BNRG笔记
toc: true
comments: true
---
第九章简单介绍了调试技巧
<!-- more -->
# 1 调试技巧
## 1.1 记录当前文件名、函数名、行号的常量
``` objc
print("Method: \(#function) in file: \(#file) line: \(#line) called.")
```