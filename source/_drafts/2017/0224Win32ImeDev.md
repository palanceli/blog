---
layout: post
title: Win32 多语言输入法的开发（译）
date: 2017-02-25 00:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
本文介绍如何为Windows95, 98, NT/2000开发一款输入法。本文是对《Win32 多语言输入法API》的补充。<!-- more -->

# 概览
>Beginning with Windows 95 and Windows NT® 4.0, Input Method Editors (IMEs) are provided as a dynamic-link library (DLL), in contrast to the IMEs for the Windows 3.1 Far East Edition. Each IME runs as one of the multilingual keyboard layouts. In comparison to the Windows 3.1 IME, the new Win32 Multilingual Input Method Manager (IMM) and Input Method Editor (IME) architecture provide the following advantages:
Run as a component of the multilingual environment
Offer multiple Input Contexts for each application task
Keep one active IME per each application thread
Give information to the application through message looping (no message order broken)
Offer strong support for both IME-aware and IME-unaware applications

>To fully utilize these advantages, an application needs to support the new Win32 IMM/IME application interface.
In order to maintain maximum compatibility with existing Windows 95 and Windows NT 4.0 IMEs, Windows 98 and Windows 2000 have not changed significantly in design. However, new features have been added in order to provide better system integration and to support more intelligent IMEs.

>Note
IME developers must use the immdev.h in DDK, which is a superset of the imm.h in the SDK or other development tools.

Windows在Win95和Win NT4.0开始以动态链接库（DLL）的形式来提供输入法。每个输入法都作为多语言键盘布局的其中一种独立运行，相比之前的Windows版本，新的Win32多语言输入法管理器（IMM）和输入法编辑器（IME）在架构上有如下优点：
* 作为多语言环境下的一个组件独立运行
* 对于每个应用程序都提供了多个输入上下文
* 每个应用程序的线程都有一个活动的输入法
* 通过消息循环想应用程序提供信息
* 对于IME-aware和IME-unaware类型的应用程序都提供了强有力的支持

为了充分利用这些特性，应用程序需要支持新的Win32 IMM/IME应用接口。

为了保持向前的最大兼容，Win98和Win2000在设计上尽管没有做太大的变动，但新特性还是被加入到系统中，以确保系统可以配备更智能的输入法。

**注意**
输入法开发必须使用DDK中的immdev.h，该头文件是SDK中imm.h的超集。

# Win98和Win2000的IMM/IME
>The Windows 98 and Windows 2000 IMM/IME architecture retains the Windows 95 and Windows NT 4.0 design. However, some changes have been made in order to support intelligent IME development and integration of the IME with Windows. These changes include:
    New IME functions that allow applications to communicate with the IMM/IME. These include:
ImmAssociateContextEx
ImmDisableIME
ImmGetImeMenuItems
    New functions that allow the IME to communicate with IMM and applications. These include: 
ImmRequestMessage
ImeGetImeMenuItems
    Supporting reconversion
This is a new IME feature that allows you to reconvert a string that has already been inserted into the application’s document. This function will help intelligent IMEs to get more information about the converted result and improve conversion accuracy and performance. This feature requires that the application and the IME cooperate.
    Adding IME menu items to the Context menu of the System Pen icon 
This new feature provides a way for an IME to insert its own menu items into the Context menu of the System Pen icon in the system bar and in applications.
    New bits and flags for the IME
The following new bits support new conversion modes:
IME_CMODE_FIXED
IME_SMODE_CONVERSATION
IME_PROP_COMPLETE_ON_UNSELECT
    Edit control enhancement for the IME
Through two new edit control messages, EM_SETIMESTATUS and EM_GETIMESTATUS, applications can manage IME status for edit controls.
    Changing IME Pen Icon and Tooltips
Through three new messages, INDICM_SETIMEICON, INDICM_SETIMETOOLTIPS, and INDICM_REMOVEDEFAULTMENUITEMS, IME can change the system Pen Icon and Tooltips in the system task bar.
    Two new IMR messages
IMR_QUERYCHARPOSITION and IMR_DOCUMENTFEED help the IME and application to communicate position and document information. 

>64-bit compliant
Two new structures (TRANSMSG and TRANSMSGLIST) are added into IMM32. They are used by INPUTCONTEXT and ImeToAsciiEx to receive IME translated message. 

>IME_PROP_ACCEPT_WIDE_VKEY
This new property is added into Windows 2000 so IME can handle the injected Unicode by SendInput API. ImeProcessKey and ImeToAsciiEx APIs are updated to  handle injected Unicode as well. The injected Unicode can be used by application and handwriting programs to put Unicode strings into input queue. 

Win98和Win2000的IMM/IME架构保留了Win95和Win NT4.0的设计。但是在新的Windows版本中还是引入了一些新变化，这使得支持更智能的输入法开发并将其整合到Windows系统中成为可能。这些变化包括：
* 新的输入法函数，他们允许应用程序与IMM/IME进行通讯，这些函数包括：
    - ImmAssociateContextEx
    - ImmDisableIME
    - ImmGetImeMenuItems
* 允许IME和IMM以及应用程序通讯的新函数，这些函数包括：
    - ImmRequestMessage
    - ImmGetImeMenuItems
* 支持转换恢复。允许已经上屏的字符串恢复成原始字符串，这是输入法的新特性。该函数将帮助智能输入法获得更多关于转换结果的信息，有助于改善转换的精度和性能。该特性需要应用程序和输入法的共同配合。
* 向系统笔形图标的上下文菜单中添加输入法菜单项。该新特性为输入法提供了一种向系统笔形图标的上下文菜单添加菜单项的方法。
* 输入法新的标志位。下面新添加的标志位将支持新的转换模式：
    - IME_CMODE_FIXED
    - IME_SMODE_CONVERSATION
    - IME_PROP_COMPLETE_ON_UNSELECT
* 输入法编辑控制的改进。通过`EM_SETIMESTATUS`和`EM_GETIMESTATUS`两个消息，应用程序可以参与输入法的编辑控制。
* 修改系统笔形图标和提示文字。通过`INDICM_SETIMEICON`、`INDICM_SETIMETOOLTIPS`和`INDICM_REMOVEDEFAULTMENUITEMS`，输入法可以改变系统任务栏的笔形图标和提示文字。
* 两个新IMR消息。`IMR_QUERYCHARPOSITION`和`IMR_DOCUMENTFEED`帮助输入法和应用程序之间沟通位置信息和文档信息。
* 64位兼容。两个新的结构体（`TRANSMSG`和`TRANSMSGLIST`）被加入到IMM32中。他们被`INPUTCONTEXT`和`ImeToAsciiEx`函数使用，以获取输入法的转换消息。
* `IME_PROP_ACCEPT_WIDE_VKEY` 该属性被添加到Win2000中，这样输入法就可以处理由`SendInput`发出的注入字符。`ImeProcessKey`和`ImeToAsciiEx`函数也支持处理这类注入字符了。应用程序或手写程序可以使用注入字符将字符串发送到输入队列中。

# Win32 IME 结构体
>A new Win32 IME has to provide two components. One is the IME Conversion Interface and the other is the IME User Interface. The IME Conversion Interface is provided as a set of functions that are exported from the IME module. These functions are called by the IMM. The IME User Interface is provided in the form of windows. These windows receive messages and provide the user interface for the IME.


