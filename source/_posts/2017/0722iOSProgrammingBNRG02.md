---
layout: post
title: 《iOS Programming BNRG》笔记二
date: 2017-07-22 23:00:00 +0800
categories: iOS Programming
tags: BNRG笔记
toc: true
comments: true
---
第二章概览了Swift的语法。更细节的可以参见[《The Swift Programming Language (Swift 4)》](https://developer.apple.com/library/content/documentation/Swift/Conceptual/Swift_Programming_Language/TheBasics.html#//apple_ref/doc/uid/TP40014097-CH5-ID309)。本节的要点有：
- 数据类型
- optional变量
- 字符串插值
<!-- more -->

# 1 数据类型
## 1.1 Swift的数据类型分三类：结构体，类和枚举
每种数据类型都有：
`属性` - 关联到类型的值
`构造器` - 初始化类的实例的代码
`实例方法` - 关联到类型的函数，可以被该类型的实例调用
`类方法` - 也叫静态方法，关联到类型的函数，可以被类型调用

Swift下一些基本的数据类型都是结构体，比如：
数字：Int, Float, Double
布尔：Bool
文本：String, Character
集合：Array<Element>, Dictionary<Key:Hashable, Value>, Set<Element:Hashable>

<font color=red>这种分类的依据是什么？他们之间有什么不同点？</font>

# 2 optional变量
## 2.1 什么是optional变量
optional表示该变量可能并没有保存任何值。
``` objc
var reading1: Float?
```
末尾的问号表示该变量是一个optional 变量：它可能指向一个实例，也可能指向nil。
``` objc
var x1: Float?
var x2: Float?
let avg = (x1 + x2) / 2    // 这么写法会导致编译错误，因为x1和x2是optional变量，需要展开
```
## 2.2 强制展开optional变量是不安全的
这么写不安全：
``` objc
let avg = (x1! + x2!) / 2
```
如果x1或x2为nil，会导致运行时错误。

## 2.3 optional binding解决安全展开的问题
使用 if-let语句，该方法被称作optional binding
``` objc
if let t1 = x1,
let t2 = x2 {
let avg = (t1 + t2) / 2
} else {
let errorString = "x1 or x2 is niil."
}
```

## 2.4 if-let的本质依然是if...else
``` objc
if let text = textField.text, !text.isEmpty { 
celsiusLabel.text = text
} else {
celsiusLabel.text = "???"
}
```
if 后面是一串Bool值
## 2.5 既没有缀?也没有缀!的变量是什么变量呢？
# 3. 字符串插值
``` objc
let qaDict = ["What is your name?": "Palance", "How old are you?": "36"]
for (question, answer) in qaDict {
    let msg = "Question is \(question), answer is \(answer)"
}
```
写在\(和)之间的内容会当做变量（也可以是函数），在运行时求值。

