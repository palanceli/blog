---
layout: post
title: Input Method Kit（译）
date: 2017-03-06 20:53:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
>Develop input methods and manage communication with client applications, candidates windows, and input method modes.

（本文来自[《Input Method Kit API Reference》](https://developer.apple.com/reference/inputmethodkit)）
Input Method Kit用于开发输入法，并管理与客户端应用之间通讯，管理候选窗口和输入模式等。<!-- more -->

>Overview
The Input Method Kit, introduced in OS X v10.5, provides a streamlined programming interface that lets you develop input methods with far less code than older Mac programming interfaces. It is fully integrated with the Text Services Manager. The Input Method Kit allows 32-bit applications to work with 64-bit applications.
The Input Method Kit provides classes and protocols for managing communication with client applications, candidates windows, and input method modes. Input methods supply text from a conversion engine (written in any language, such as C, C++, Objective-C, Python, and so on), key bindings and optional event handling, and information about your input method in an extended Info.plist file. You also have the option to provide menu items that support input-method-specific commands or preferences settings.

# 概要
OSX 自10.5引入了IMK，该框架提供了输入法开发的原型接口，与老版本的mac相比，这套接口大大简化了输入法的开发工作量。该框架与文字服务管理器充分整合，使得32位和64位应用程序和输入法之间可以无缝合作。

IMK提供了类和协议来支持输入法与客户端应用间的通讯，管理候选窗和输入模式等。输入法从转换引擎提供转换后的文字（该引擎可以用C，C++，Objective-C，Python等编写），还会提供键盘绑定、可选的事件处理、通过一个扩展的Info.plist文件提供更多输入法信息。还可以通过菜单项支持输入法的特殊命令或偏好设置。

接下来看IMK涉及的类、协议和其它数据结构。

# IMKCandidates
>The IMKCandidates class presents candidates to users and notifies the appropriate IMKInputController object when the user selects a candidate. Candidates are alternate characters for a given input sequence. The IMKCandidates class supports using a candidates window in your input method; using IMKCandidates is optional. Not all input methods require them.

IMKCandidates类用来表示候选并在用户选择了一个候选后，会提示对应的[IMKInputController](#IMKInputController)对象。候选是对已经输入的文字序列转换后的结果。IMKCandidates类支持在你的输入法中使用一个候选窗口来展现内容。该类的使用是可选的，不是所有输入法都需要它。

# IMKInputController
> The IMKInputController class provides a base class for custom input controller classes. The IMKServer class, which is allocated in the main function of an input method, creates an input controller object for each input session created by a client application. For every input session there is a corresponding IMKInputController object.

IMKInputController为用户自定义的输入控制器提供一个基类。由[IMKServer为](#IMKServer)每个输入会话创建输入控制器，IMKServer通常在main函数的开头创建，输入会话则由客户端应用负责创建。对于每个输入会话都会有一个对应的输入控制器即IMKInputController对象。

# IMKServer
> The IMKServer class manages client connections to your input method. When you write the main function for your input method, you create an IMKServer object. You should never need to override this class.

IMKServer类管理客户端与输入法的连接。应当在main函数中创建IMKServer对象，永远不要修改该类，不要从它派生子类。

# IMKMouseHandling
> The IMKMouseHandling protocol defines methods that your input method can implement to handle mouse events.

这是一个协议，它定义了输入法可以实现的鼠标处理事件。

# IMKServerInput
> IMKServerInput is an informal protocol that defines methods for receiving text events. This is intentionally not a formal protocol because there are three ways to receive events. An input method chooses one of the following approaches and implements the appropriate methods:

这是一个协议，它定义了处理文本事件的方法。这不是一个正式协议，因为有三种方式来处理事件，输入法选择其中之一来实现对应方法。

# IMKStateSetting
> The IMKStateSetting protocol defines methods for setting or accessing values that indicate the state of an input method.

这是一个协议，它定义了设置输入法状态的方法。

# NSObject
> The root class of most Objective-C class hierarchies, from which subclasses inherit a basic interface to the runtime system and the ability to behave as Objective-C objects.

这是Objective-C派生体系的根类，从该类可以继承系统对象的基本接口以及OC对象的基本能力。

