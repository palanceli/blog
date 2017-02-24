---
layout: post
title: Win32 多语言输入法API（译）
date: 2017-02-25 00:26:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
> This documentation contains the application programming interface reference for Input Method Editor (IME)development. The following functions are intended to be used by the IME.

本文包含输入法开发的API手册，一款输入法的开发通常包含如下功能：<!-- more -->
# IMM UI函数

> Following are the Input Method Manager (IMM) functions that can be accessed from the UI window. They are also used by applications to change IME status.

下面列出的是输入法管理器（IMM）函数，这些函数通过UI窗口调用，应用程序也可以调用这些函数来改变输入法状态。
ImmGetCompositionWindow
ImmSetCompositionWindow
ImmGetCandidateWindow
ImmSetCandidateWindow
ImmGetCompositionString
ImmSetCompositionString
ImmGetCompositionFont
ImmSetCompositionFont
ImmGetNumCandidateList
ImmGetCandidateList
ImmGetGuideLine
ImmGetConversionStatus
ImmGetConversionList
ImmGetOpenStatus
ImmSetConversionStatus
ImmSetOpenStatus
ImmNotifyIME
ImmCreateSoftKeyboard
ImmDestroySoftkeyboard
ImmShowSoftKeyboard

> Please refer to the Input Method Editor (IME) functions in the Platform SDK for information about these functions.

可以在Platform SDK中可以找到这些输入法（IME）函数的信息。
# IMM支持函数
> The following topics contain IMM functions that support and are used by the IME.

下面介绍在输入法中使用的输入法管理器（IMM）函数。
## ImmGenerateMessage
> The IME uses the ImmGenerateMessage function to send messages to the hWnd of hIMC. The messages to be sent are stored in hMsgBuf of hIMC.

输入法使用ImmGenerateMessage函数向hIMC的hWnd发送消息。即将发送的消息被存储在hIMC的hMsgBuf中。
``` c++
BOOL WINAPI ImmGenerateMessage(HIMC hIMC)
```
>Parameters
hIMC
Input context handle containing hMsgBuf.
Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

** 参数 **
`hIMC`  包含hMsgBuf的输入上下文句柄
** 返回值 **
成功返回TRUE，否则返回FALSE。

> Comments
This is a general purpose function. Typically, an IME uses this function when it is notified about the context update through ImmNotifyIME from IMM. In this case, even if IME needs to provide messages to an application, there is no keystroke in the application’s message queue.
An IME User Interface should not use this function when it only wants to update the UI appearance. The IME User Interface should have been updated when the IME is informed about the updated Input Context. It is recommended that you use this function from the IME only when the IME changes the Input Context without any keystroke given and needs to inform an application of the change.

** 注释 **
这是一个通用函数，当输入法收到来自IMM的ImmNotifyIme通知而需要更新上下文时，输入法将调用该函数。在本例中，即使输入法需要向应用程序提供消息，在应用程序消息队列中依然没有击键消息。
输入法用户界面如果只想更新UI界面时，不应该使用该函数。