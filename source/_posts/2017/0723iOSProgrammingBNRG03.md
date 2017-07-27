---
layout: post
title: 《iOS Programming BNRG》笔记三
date: 2017-07-23 23:00:00 +0800
categories: iOS Programming
tags: BNRG笔记
toc: true
comments: true
---
![base ui](0723iOSProgrammingBNRG03/img01.png)
第三章构造了一个这样的界面，并添加约束。本章运用的知识差不多在第一章就介绍过了。
<!-- more -->

# 1 构造UI
## 1.1 点和像素之间的关系是什么？
在第111页提到：
``` objc
override func viewDidLoad() {
super.viewDidLoad()
let firstFrame = CGRect(x: 160, y:240, width: 100, height: 150)
let firstView = UIView(frame: firstFrame)
firstView.backgroundColor = UIColor.blue
view.addSubview(firstView)
}
```
这段代码对应的UI界面如下：
![base ui](0723iOSProgrammingBNRG03/img02.png)
但此处的单位不是像素而是点，点是一个相对单位，在不同的设备上对应的像素数不同。<font color =red>那么对应关系是什么呢？</font>
