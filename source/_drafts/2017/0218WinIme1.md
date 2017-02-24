---
layout: post
title: Windows下创建基于IMM的输入法1——最小要求
date: 2017-02-18 23:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
基于IMM框架的输入法是一个按照系统要求导出十几个函数的DLL文件，这十几个导出函数的原型定义于imm.h文件，系统定义了它们的调用时机，比如切出输入法、按键处理等。接下来就从最核心的要求开始，逐步分析基于IMM的输入法实现步骤。
<!-- more -->
要确保输入法能运转起来，需要具备四个条件：
1. 是一个DLL文件
2. 依照imm.h导出十几个函数
3. 有一个UI窗口
4. 执行特定的安装过程

能最小化运转不代表能正常交互，只是技术路径上跑通了。像一个完备的输入法那样正常交互起来还要具备写作窗、候选窗，还要处理从拼音到汉字、词的转化。本节先介绍最小化运转的实现细节。

# DLL文件
1. 要在`DllMain`的`DLL_PROCESS_ATTACH`分支下注册UI窗体类，系统IMM框架会负责创建该窗体，并通过向该窗体发消息让输入法知道什么时候该显示/隐藏写作窗，什么时候该显示/隐藏候选窗。关于UI窗口在下文还有详细介绍。
2. 要在资源文件（*.rc）中设置几个key:
`FILEOS` = `0x4L`
`FILETYPE` = `VFT_DRV`
`FILESUBTYPE` = `VFT2_DRV_INPUTMETHOD`
`Block Header` = `中文（简体，中国）（0x0404b0）` 选择Language为`Chinese（Simplified PRC）`即为此设置。
3. 包含一个icon图标，该图标用于在系统语言栏显示创建的输入法。

# 导出函数
## 引入`imm.h`文件
这些函数原型定义在`imm.h`，需要注意该文件有两份定义，一份来自DDK，一份来自SDK。开发输入法时应使用DDK版本。这个文件，在不同的Windows DDK版本中命名发生过变化，最早是`imm.h`，在win2kDDK的某个版本中就变成了`immdev.h`，后来的Windows DDK一直沿用`immdev.h`。

使用`imm.h`会导致和SDK版本重名，确实不方便。这要求包含该文件的时候必须这么写：
``` c++
# define NOIME
#include <windows.h>
#include "imm.h"
#define _DDKIMM_H_
...
```
`windows.h`必须写在`imm.h`前面，因为`imm.h`依赖`windows.h`，可是在`windows.h`中又包含了SDK版本的`imm.h`：
``` c++
// windows.h
...
#ifndef NOIME
#include <imm.h>
#endif
...
```
因此，我们在`#include <windows.h>`前必须先定义`NOIME`，让windows.h中的imm.h无效。
如果使用`immdev.h`，则不存在头文件命名冲突的问题。不过我在编写输入法时，还是使用老版本的`imm.h`，因为不确定使用`immdev.h`能否完全与老的Windows系统兼容。
## 定义十五个导出函数
关于这些函数的介绍，可以参见win2kddk，这个版本的DDK在Ntddk/src/ime/docs目录下有两份输入法开发文档，这也是为数不多的微软发布的输入法开发官方文档。下面是对这些函数的介绍。
### ImeInquire
该函数处理输入法的初始化，它返回一个`IMEINFO`结构体以及输入法的UI窗体类名。
``` c++
BOOL ImeInquire(
    LPIMEINFO lpIMEInfo,    // 指向IMEINFO结构体指针
    LPTSTR lpszWndClass,    // 输入法UI窗体的窗体类名
    DWORD dwSystemInfoFlags // 系统通过该值传入一些系统信息
   )
```
dwSystemInfoFlags是由一些标志位逻辑或而成，这些标志位的含义为：
* `dwSystemInfoFlags` 告诉输入法当前进程是Winlogon，由于还没有登录系统，此时输入法的处理应当非常小心，比如不允许修改输入法配置，因为配置可能是和Windows用户绑定的；比如绝对不允许调用打开系统explorer或者Common Dialog等操作，以防止通过输入法可以hack到系统。
* `IME_SYSINFO_WOW16` 告诉输入法当前进程是一个16位应用程序。

# UI窗口
## 概述
输入法可分为框架层和逻辑层，框架层定义了控制流、数据流的流转路径，以及控制类型。比如，当一个按键被按下，首先由导出函数ImeProcessKey、ImeToAsciiEx处理，之后再通过IMM消息通知UI窗口，这些都属于控制流。通知UI窗口的消息则属于控制类型，比如显示/隐藏写作窗、显示/隐藏候选窗。以上这些都是框架层的工作，而在业务层则负责处理具体收到显示/隐藏写作窗的时候怎么显示，显示在哪，等等。

通常我们能看到的输入法窗口都属于业务逻辑层的范畴，而不是框架层。它们都是UI窗口的子窗口，你可以根据自己业务逻辑的需要决定创建多少个子窗口，并决定怎么显示它们。

UI窗口是框架层和业务层的桥梁——框架层把消息发送给UI窗口，由它决定要不要告诉业务层的子窗体，也由它来控制要不要显示或隐藏这些窗体。

## 注册窗体类
既然是Windows窗体，必然包含注册窗体类、创建窗体、执行窗体函数这三个关键步骤。注册窗体类是在`DllMain`函数的`DLL_PROCESS_ATTACH`分支中完成，在`DLL_PROCESS_DETACH`分支完成注销窗体类。和普通的自定义窗体类不同在于`style`字段和`cbWndExtra`字段：
``` c++
void UIWnd::RegisterUIWndClass(HINSTANCE hInstance)
{
  WNDCLASSEX wc = { 0 };
  wc.cbSize = sizeof(WNDCLASSEX);
  wc.style = CS_IME;  // 注意1
  wc.lpfnWndProc = UIWndProc;
  wc.cbClsExtra = 0;
  wc.cbWndExtra = 2 * sizeof(LONG_PTR); // 注意2：系统要存放IMMGWL_IMC 和 IMMGWL_PRIVATE
  wc.hInstance = hInstance;
  wc.hCursor = NULL;
  wc.hIcon = NULL;
  wc.lpszMenuName = NULL;
  wc.lpszClassName = GetUIWndClassName();
  wc.hbrBackground = NULL;
  wc.hIconSm = NULL;
  ATOM atomUi = RegisterClassEx(&wc);
  mhInstance = hInstance;
}
```
## 创建窗体
输入法UI窗体和普通自定义窗体最不同之处在于窗体的创建，自定义窗体要通过调用`CreateWindow(...)`函数来完成创建，但输入法UI窗体则是由系统负责创建的。该函数的第一个参数要传入窗体类名，系统怎么知道窗体类名的呢？答案在导出函数`ImeInquire`那里，通过第二个参数输入法将UI窗体类名传给系统。

## 窗体函数
# 安装