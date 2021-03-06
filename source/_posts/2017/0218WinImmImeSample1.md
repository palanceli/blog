---
layout: post
title: Windows下创建基于IMM的输入法
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
4. 有一系列扩展窗口
5. 执行特定的安装过程

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
关于这些函数的介绍，可以参见win2kddk，这个版本的DDK在Ntddk/src/ime/docs目录下有两份输入法开发文档，这也是为数不多的微软发布的输入法开发官方文档。我们只挑最必须的文件重点介绍。
## ImeInquire
该函数在输入法首次切出时被调用，负责处理输入法的初始化，它返回一个`IMEINFO`结构体以及输入法的UI窗体类名。这里的实现过程为：
``` c++
BOOL WINAPI ImeInquire(LPIMEINFO lpImeInfo, LPTSTR lpszUIClass, LPCTSTR lpszOptions)
{
  // 如果宿主进程为Winlogon，则直接退出
  if((DWORD_PTR)lpszOptions & IME_SYSINFO_WINLOGON )
    return FALSE;

  lpImeInfo->dwPrivateDataSize  = 0; //sizeof(t_uiExtra);

  lpImeInfo->fdwProperty  = IME_PROP_COMPLETE_ON_UNSELECT | 
    IME_PROP_SPECIAL_UI | IME_PROP_CANDLIST_START_FROM_1 |
    IME_PROP_UNICODE | IME_PROP_KBD_CHAR_FIRST;                 // 输入法属性

  lpImeInfo->fdwConversionCaps  = IME_CMODE_SYMBOL | 
    IME_CMODE_SOFTKBD | IME_CMODE_FULLSHAPE;                    // 转换模式
  lpImeInfo->fdwSentenceCaps    = IME_SMODE_NONE;               // 句子模式
  lpImeInfo->fdwUICaps          = UI_CAP_SOFTKBD| UI_CAP_2700;  // UI标记
  lpImeInfo->fdwSCSCaps         = 0x00000000;
  lpImeInfo->fdwSelectCaps      = 0x00000000;

  // 窗体类名
  _tcscpy_s(lpszUIClass, MAX_CLASSNAME_UI, UIWnd::GetUIWndClassName());

  return TRUE;
}
```
系统通过该函数返回的窗体类名创建输入法UI窗体。
## ImeProcessKey
每当产生一个按键操作，IMM会调用该函数，输入法根据按键预判断是否要处理，如果处理返回TRUE；否则返回FALSE。这里我们只处理字符A~Z以及回车、空格和ESC：
``` c++
BOOL WINAPI ImeProcessKey(HIMC hImc, UINT unVirtKey, DWORD unScanCode, CONST LPBYTE achKeyState)
{
  ImcHandle imcHandle(hImc);
  Comp* pComp = imcHandle.GetComp();
  LPTSTR szCompString = pComp->GetCompString();
  if (unVirtKey >= 0x41 && unVirtKey <= 0x5A) {
    return TRUE;    // 从A到Z
  }
  if (_tcslen(szCompString) > 0 &&(unVirtKey == VK_RETURN || unVirtKey == VK_SPACE || unVirtKey == VK_ESCAPE)) {
    return TRUE;  // 当有写作串且当前按键为回车、空格或ESC
  }
  return FALSE;
}
```
## ImeToAsciiEx
如果经过上一步的输入法预判断，需要处理，IMM则继续调用该函数进入处理逻辑；如果不需要处理，则不会调用该函数，而是直接把按键以WM_KEYDOWN/WM_KEYUP的形式发给应用程序。这里的处理分三个步骤：
1. 处理按键，通常要追加当前的输入内容进入写作串；
2. 完成转换，这是输入法最核心的部分，根据写作串里的拼音转成汉字；
3. 完成界面的更新，只需要组装相应的消息到lpdwTransBuf指向的数组中，IMM会把这些消息发送给输入法UI窗口，由UI窗口继续完成界面的处理。
``` c++
UINT WINAPI ImeToAsciiEx(UINT unKey, UINT unScanCode, CONST LPBYTE achKeyState, LPDWORD lpdwTransBuf, UINT fuState, HIMC hImc)
{ 
  
  ImcHandle imcHandle(hImc);
  Comp* pComp = imcHandle.GetComp();
  LPTSTR szCompString = pComp->GetCompString();
  COMPOSITIONSTRING& compCore = pComp->GetCore();
  size_t ccOriginCompLen = _tcslen(szCompString);

  if (HIWORD(unKey) >= 'a' && HIWORD(unKey) <= 'z') {
    TCHAR szKey[2] = { HIWORD(unKey), 0 };
    _tcscat_s(szCompString, Comp::c_MaxCompString, szKey);  // 将字符追加到写作串
    compCore.dwCompStrLen = (DWORD)_tcslen(szCompString);
  }

  const DWORD dwBufLen = *lpdwTransBuf;
  lpdwTransBuf += sizeof(size_t) / sizeof(DWORD);
  UINT cMsg = 0;
  LPTRANSMSG lpTransMsg = (LPTRANSMSG)lpdwTransBuf;
  if(ccOriginCompLen == 0){  // 没有写作串
    if(HIWORD(unKey) >= 'a' && HIWORD(unKey) <= 'z'){
      lpTransMsg[0].message = WM_IME_STARTCOMPOSITION;  // 打开写作窗
      lpTransMsg[0].wParam = 0;
      lpTransMsg[0].lParam = 0;
      cMsg++;

      lpTransMsg[1].message = WM_IME_COMPOSITION; // 更新写作窗
      lpTransMsg[1].wParam = 0;
      lpTransMsg[1].lParam = GCS_COMPSTR | GCS_CURSORPOS | GCS_COMPATTR;
      cMsg++;

      lpTransMsg[2].message = WM_IME_NOTIFY;      // 打开候选窗
      lpTransMsg[2].wParam = IMN_OPENCANDIDATE;
      lpTransMsg[2].lParam = 1;
      cMsg++;

      lpTransMsg[3].message = WM_IME_NOTIFY;      // 更新候选窗
      lpTransMsg[3].wParam = IMN_CHANGECANDIDATE;
      lpTransMsg[3].lParam = 1;
      cMsg++;
      return cMsg;
    }
  }else{ // _tcslen(szCompString) > 0     // 有写作串
    if(HIWORD(unKey) >= 'a' && HIWORD(unKey) <= 'z'){
      // 更新写作窗
      ...
      // 更新候选窗
      ...
      return cMsg;
    }else if(HIWORD(unKey) == VK_RETURN || HIWORD(unKey) == VK_SPACE){ // 回车或空格
      LPTSTR szResultString = pComp->GetResultString();
      _tcscpy_s(szResultString, Comp::c_MaxResultString, szCompString); // 将写作串拷入结果串
      compCore.dwResultStrLen = (DWORD)_tcslen(szResultString);
      memset(szCompString, 0, sizeof(TCHAR) * Comp::c_MaxCompString);   // 清空写作串
      compCore.dwCompStrLen = 0;
      // 更新写作窗
      ...
      // 关闭写作窗
      ...
      // 关闭候选窗
      ...
      return cMsg;
    }else if(HIWORD(unKey) == VK_ESCAPE){ // ESC
      memset(szCompString, 0, sizeof(TCHAR) * Comp::c_MaxCompString);
      compCore.dwCompStrLen = 0;
      // 更新写作窗
      ...
      // 关闭写作窗
      ...
      // 关闭候选窗
      ...
      return cMsg;
    }
  }
  return cMsg;
}
```
以上就是输入法最最关键的三个导出函数，即使一个丰满的输入法，主要逻辑也是在这几个函数中，尤其是`ImeProcessKey`和`ImeToAsciiEx`中。
** 特别注意 **
在DDK的`immdev.h`中定义的数据类型`LPTRANSMSGLIST`是错误的，它定义缓冲区长度`TRANSMSGLIST::uMsgCount`的类型为UINT，其实该字段的长度在32位和64位系统下不一样，32位下是4字节，64位下是8字节。因此在上面代码中有：
```c++
lpdwTransBuf += sizeof(size_t) / sizeof(DWORD);
```

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
输入法UI窗体和普通自定义窗体最不同之处在于窗体的创建，自定义窗体要通过调用`CreateWindow(...)`函数来完成创建，但输入法UI窗体则是由系统负责创建的。该函数的第一个参数要传入窗体类名，系统怎么知道窗体类名的呢？前面已经讲过：在导出函数`ImeInquire`那里。

## 窗体函数
窗体函数中要注意：不要让WM_IME_xxx类的消息交给`DefWindowProc`函数来处理，因为它会把这类消息再交给输入法窗口，这会导致死循环。对于不处理的WM_IME_xxx消息，返回0即可。

与普通用户窗体的不同之处在于他要处理一系列的WM_IME_xxx消息，以响应来自`ImeToAsciiEx`的消息——显示或隐藏写作窗、候选窗、状态栏以及更新它们。本文我们先不着急引入这些窗口，你会看到当敲字母键的时候没有反应，而实际上输入法把这些字母“吃掉”了，再按空格或回车会一次上屏，按ESC则清空“吃掉”的字母，进入重新输入的状态。

# 扩展窗口
扩展窗口包括写作窗、候选窗、状态栏等。这些窗口需要具备一些共同的特征：
1. 关于窗体类风格，需要指定CS_IME标记。但我觉得其实只有输入法UI窗口用该风格，其余的扩展窗口应该不用，因为它们的创建是由开发者创建的。
2. 在创建输入法窗体的时候，**必须**指定窗体风格为**WS_DISABLED**。这是因为输入法窗体不能接受输入焦点，否则就又会激活输入法，输入逻辑就嵌套了。
3. 这些窗口可以在输入法UI窗口的WM_CREATE函数中完成注册和创建。
4. 这些窗口里要现实的内容需要作为IMCC在IMC中创建。IMC中有一些默认的IMCC是不需要在此创建的，比如：
``` c++
typedef struct tagINPUTCONTEXT { 
  ...
  HIMCC   hCompStr; 
  HIMCC   hCandInfo; 
  HIMCC   hGuideLine; 
  HIMCC   hPrivate; 
  ...
} INPUTCONTEXT, *PINPUTCONTEXT, NEAR *NPINPUTCONTEXT, FAR *LPINPUTCONTEXT; 
```
在`ImeSelect`函数中首次获得IMC，你可以尝试获得这些IMCC的尺寸，发现是非0的，说明这些IMCC已经存在了。但是为了适配自己的业务逻辑，我在`ImeSelect`中初始化IMC，调用`ImmReSizeIMCC(m_pContext->hCompStr, sizeof(Comp));`，用自己的Comp类替换掉了原先的hCompStr。

# 安装
输入法的安装要做两件事：1、将ime文件拷贝到Windows/System32目录下；2、调用`ImmInstallIME`注册该输入法。
需要注意，在64位机器下，应该为32位和64位生成两份ime文件，这样在64位和32位的应用程序里才能分别切出对应的输入法。64位ime文件放在Windows/System32下，32位放在Windows/SysWOW64下。 

通常这些活是由NSIS脚本干的，此处我写了一个ImeInstall程序来做，注意：因为要往Windows/System32下写文件，该程序必须具备管理员权限，因此在CMake文件中添加如下链接选项：
``` CMake
SET_TARGET_PROPERTIES(ImeInstaller PROPERTIES LINK_FLAGS "/level='requireAdministrator' /uiAccess='false'")
```

> 本文代码已提交至[WinImmImeSample-MiniIme](https://github.com/palanceli/WinImmImeSample)