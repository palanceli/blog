---
layout: post
title: 《iOS Programming BNRG》笔记八
date: 2017-07-28 23:00:00 +0800
categories: iOS Programming
tags: BNRG笔记
toc: true
comments: true
---
第八章实现了一些简单的动画。本章要点：
- animate函数的使用
<!-- more -->

# 1. 闭包
## 1.1 什么是闭包
闭包就是一个代码块，可以参数或者返回值的形式被传递。

## 1.2 声明、定义、使用闭包的形式
声明格式：
``` objc
(arguments) -> returnType
```
定义格式：
``` objc
{ (arguments) -> returnType in
// code
}
```
其中arguments是参数列表，returnType是返回值类型，in是关键字，在code处写要执行的代码

使用：
``` objc
let animation = {()->Void in
    self.labelA.alpha = 1
}	// 定义闭包，并赋值给变量animation

UIView.animate(withDuration: 0.5, animations: animation)
```
对于参数和返回均为空的闭包，也可以写作：
``` objc
UIView.animate(withDuration: 0.5, animations: {self.lableA.alpha = 1})
```
# 2. 动效函数
## 2.1 怎么实现渐现/渐隐动画
## 2.2 怎么实现飞入/飞出动画

class func animate(withDuration duration: TimeInterval, animations: () -> Void)
使用见1.2，问题：它定义了到多少秒后界面长什么样，那么中间的变化过程是怎么定义的呢？


