---
layout: post
title: macOS下基于IMK的输入法（二）——处理流程
date: 2017-03-23 23:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
[前文](http://palanceli.com/2017/03/05/2017/0305macOSIMKSample1/)分析了基于IMK输入法的创建步骤，本文将分析对按键的处理流程和规范。[《Input Method Kit（译）》](http://palanceli.com/2017/03/06/2017/0306InputMethodKit/#IMKServerInput)中提到IMKServerInput对按键的处理模式有三种：键盘绑定，仅处理文本数据，处理所有事件。<!-- more -->
# 键盘绑定
> 系统把每一个键盘按下事件映射到到输入法的一个方法。如果成功（找到此映射方法），系统调用didCommandBySelector:client:，否则（没有找到该方法）调用inputText:client:。针对此方式，你应当实现inputText(_:client:) 和didCommand(by:client:)两个方法。

以上是苹果官方文档的描述，可以做个实验来观察这两个方法的调用流程：
``` obj-c
#import "IMKSampleController.h"

@implementation IMKSampleController
// 该方法接收来自客户程序的按键输入，InputMethodKit会把按键事件转换成NSString发送给本方法。
//返回YES表明输入法要处理，系统将不再把按键继续发送给应用程序；否则返回NO
-(BOOL)inputText:(NSString*)string client:(id)sender
{
  NSLog(@"%@", string);
  return NO;
}

-(BOOL)didCommandBySelector:(SEL)aSelector client:(id)sender
{
  // 如果输入法要处理该事件，则返回YES，否则返回NO
  NSLog(@"didCommandBySelector:%@", NSStringFromSelector(aSelector));
  return NO;
}
@end
```
切出输入法，按下`a`、`b`、`c`，可以在控制台看到如下输出：
```
默认  12:33:25.769423 +0800 IMKSample a
默认  12:33:33.385260 +0800 IMKSample b
默认  12:33:33.385260 +0800 IMKSample c
```
按下`Backspace`、`回车`、`Tab`以及上下左右键，看到如下输出：
```
默认  12:33:36.319315 +0800 IMKSample didCommandBySelector:deleteBackward:
默认  12:33:27.258984 +0800 IMKSample didCommandBySelector:insertNewline:
默认  12:33:45.027618 +0800 IMKSample didCommandBySelector:insertTab:
默认  12:36:20.385862 +0800 IMKSample didCommandBySelector:moveUp:
默认  12:36:21.633254 +0800 IMKSample didCommandBySelector:moveDown:
默认  12:36:21.063002 +0800 IMKSample didCommandBySelector:moveLeft:
默认  12:36:22.083668 +0800 IMKSample didCommandBySelector:moveRight:
```
可以得出**结论：**
1. 当按下字符键，将调用`input​Text:​client:​`并传入按下的字符
2. 当按下控制键，将调用`did​Command​By​Selector:​client:​`并传入该控制键对应的函数选择器

在两个函数中，如果输入法要处理该字符/控制键，则返回YES，该按键就不在传递给应用程序；否则返回NO，同时按键被发送到应用程序。

## 实现方法
假设要实现的输入法逻辑是：对于可显示字符暂时缓存起来，通过回车或空格上屏。实现方法：在`input​Text:​client:​`中缓存空格以外的字符，以及空格完成上屏；在`did​Command​By​Selector:​client:​`中处理回车完成上屏。

