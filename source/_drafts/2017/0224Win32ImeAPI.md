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
> ** Parameters **
hIMC
Input context handle containing hMsgBuf.
** Return Values **
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
** Comments **
This is a general purpose function. Typically, an IME uses this function when it is notified about the context update through ImmNotifyIME from IMM. In this case, even if IME needs to provide messages to an application, there is no keystroke in the application’s message queue.
An IME User Interface should not use this function when it only wants to update the UI appearance. The IME User Interface should have been updated when the IME is informed about the updated Input Context. It is recommended that you use this function from the IME only when the IME changes the Input Context without any keystroke given and needs to inform an application of the change.

** 参数 **
`hIMC`  包含hMsgBuf的输入上下文句柄
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 注释 **
这是一个通用函数，当输入法收到来自IMM的ImmNotifyIme通知而需要更新上下文时，输入法将调用该函数。在本例中，即使输入法需要向用程序发送消息，在应用程序消息队列中依然没有击键消息。
输入法用户界面如果只想更新UI界面时，不应该使用该函数。当输入法被通知到更新输入上下文时，输入法的用户界面应当已经被刷新了才对。建议仅当不是按键引起的输入上下文变化，且需要通知应用程序时，才使用该函数。

## ImmRequestMessage
> The ImmRequestMessage function is used to send a WM_IME_REQUEST message to the application. 

ImmRequestMessage 函数用来向应用程序发送一个WM_IME_REQUESY消息。
``` c++    
LRESULT WINAPI ImmRequestMessage(
    HIMC hIMC,
    WPARAM wParam,
    LPARAM lParam
   )

```
>Parameters
hIMC
Target input context handle.
wParam
wParam for the WM_IME_REQUEST message.
lParam
lParam for the WM_IME_REQUEST message.

>Return Values
The return value is the return value of the WM_IME_REQUEST message.
Comments
This function is new for Windows® 98 and Window 2000, and is used by the IME to send a WM_IME_REQUEST message to the application. The IME may want to obtain some guidelines from the application in defining the position of the candidate or composition window. But in an IME fully aware (true in-line) application, the application usually does not set the composition window position. When the IME makes a request to the application, it receives the WM_IME_REQUEST message. The IME should make a request to the application by calling the ImmRequestMessage function and not by calling SendMessage
The following is a list of submessages that the IME can send to applications through the ImmRequestMessage function:
IMR_COMPOSITIONWINOW
IMR_CANDIDATEWINDOW
IMR_COMPOSITIONFONT
IMR_RECONVERTSTRING
IMR_CONFIRMRECONVERTSTRING
IMR_QUERYCHARPOSITION
IMR_DOCUMENTFEED

>Please refer to the Input Method Editor (IME) functions in the Platform SDK for information about these messages.

** 参数 **
`hIMC` 目标输入上下文句柄
`wParam` WM_IME_REQUEST消息的wParam参数
`lParam` WM_IME_REQUEST消息的lParam参数
** 返回值 **
该函数返回WM_IME_REQUEST消息处理的返回值。
** 注释 **
该函数是在Win98/Win2000引入的，输入法使用它想应用程序发送WM_IME_REQUEST消息。输入法在确定写作窗和候选窗位置时需要从应用程序获取一些辅助信息。但在输入法为fully aware类（即in-line）模式的应用程序中，应用程序通常不需要设置写作窗。当输入法向应用程序发送请求，应用程序将收到一个WM_IME_REQUEST消息。输入法应当调用ImmRequestMessage函数向应用程序发送WM_IME_REQUEST消息，而不要通过SendMessage函数。下面是输入法通过ImmRequestMessage函数能向应用程序发送的子消息：
IMR_COMPOSITIONWINOW
IMR_CANDIDATEWINDOW
IMR_COMPOSITIONFONT
IMR_RECONVERTSTRING
IMR_CONFIRMRECONVERTSTRING
IMR_QUERYCHARPOSITION
IMR_DOCUMENTFEED
这些消息的具体信息可参见Platform SDK中的输入法函数。

# HIMC和HIMCC管理函数
> The following topics contain the HIMC and HIMCC management functions.

下面主题包含HIMC和HIMCC管理函数。
## ImmLockImc
> The ImmLockIMC function increases the lock count for the IMC. When the IME needs to see the INPUTCONTEXT structure, it calls this function to get the pointer of the INPUTCONTEXT structure.

ImmLockIMC函数将IMC的持有锁加一。输入法调用该函数获取指向INPUTCONTEXT结构体的指针。
``` c++
LPINPUTCONTEXT WINAPI ImmLockIMC(HIMC hIMC)
```
> Parameters
hIMC
Input context handle.

>Return Values
If the function is successful, it returns a pointer to the INPUTCONTEXT structure. Otherwise, it returns NULL.

** 参数 **
`hIMC` 输入上下文句柄
** 返回值 ** 成功返回指向INPUTCONTEXT结构体的指针，失败返回NULL。

## ImmUnlockIMC
> The ImmUnlockIMC function decrements the lock count for the IMC.

ImmUnlockIMC函数将IMC的持有锁减一。
``` c++
BOOL WINAPI ImmUnlockIMC(HIMC hIMC)
```
> Parameters
hIMC
Input context handle.

> Return Values
If the lock count of the IMC is decremeted to zero, the return value is FALSE. Otherwise, the return value is TRUE.

** 参数 **
`hIMC` 输入法上下文句柄
** 返回值 ** 
如果IMC的持有锁减到0，返回FALSE，否则返回TRUE。

## ImmGetIMCLockCount
> The ImmGetIMCLockCount is used to get the lock count of the IMC.

ImmGetIMCLockCount函数用来获取IMC的持有锁锁定次数。
``` c++
HIMCC WINAPI ImmGetIMCLockCount(HIMC hIMC)
```
>Parameters
hIMC
Input context handle

>Return Values
If the function is successful, the return value is the lock count of the IMC. Otherwise, the return value is NULL.

** 参数 **
`hIMC` 输入法上下文句柄
** 返回值 **
成功返回IMC持有锁的锁定次数，失败返回NULL。

## ImmCreateIMCC
> The ImmCreateIMCC function creates a new component as a member of the IMC.

ImmCreateIMCC函数为IMC创建一个新组件。
``` c++
HIMCC WINAPI ImmCreateIMCC(DWORD dwSize)
```
>Parameters
dwSize
Size of the new IMC component.

>Return Values
If the function is successful, the return value is the IMC component handle (HIMCC). Otherwise, the return value is NULL.
Comments
The IMC component created by this function is initialized as zero.

** 参数 **
`dwSize` IMC新组件的尺寸
** 返回值 **
成功返回IMC新组建的句柄（HIMCC），否则返回NULL。

## ImmDestroyIMCC
>The ImmDestroyIMCC function is used by the IME to destroy the IMC component that was created as a member of the IMC.

ImmDestroyIMCC函数用来销毁IMC组件。
``` c++
HIMCC WINAPI ImmDestroyIMCC(HIMCC hIMCC)
```
>Parameters
hIMCC
Handle of the IMC component.

>Return Values
If the function is successful, the return value is NULL. Otherwise, the return value is equal to the HIMCC.

** 参数 **
`hIMCC` 待销毁的IMC组件的句柄。
** 返回值 **
成功返回NULL，否则返回HIMCC。

## ImmLockIMCC
>The ImmLockIMCC function is used by the IME to get the pointer for the IMC component that was created as a member of the IMC. The ImmLockIMC function increases the lock count for the IMCC.

输入法使用ImmLockIMCC函数获取IMC组件的指针，该函数还会令IMCC的持有锁加一。
``` c++
LPVOID WINAPI ImmLockIMCC(HIMCC hIMCC)
```
>Parameters
hIMCC
Handle of the IMC component.

>Return Values
If the function is successful, the return value is the pointer for the IMC component. Otherwise, the return value is NULL.

** 参数 **
`hIMCC` IMC组件的句柄。
** 返回值 **
成功返回执行IMC组件的指针，失败返回NULL。

## ImmUnlockIMCC
>The ImmUnlockIMC function decrements the lock count for the IMCC.

ImmUnlockIMC函数将IMCC的持有锁减一。
``` c++
BOOL WINAPI ImmUnlockIMCC(HIMCC hIMCC)
```
>Parameters
hIMCC
Handle of the IMC component.

>Return Values
If the lock count of the IMCC is decremeted to zero, the return value is FALSE. Otherwise, the return value is TRUE.

** 参数**
`hIMCC` IMC组件句柄
** 返回值 **
如果IMCC持有锁被减至0，返回FALSE，否则返回TRUE。

##ImmReSizeIMCC
> The ImmReSizeIMCC function changes the size of the component.

ImmReSizeIMCC函数修改组件的尺寸。
``` c++
HIMCC WINAPI ImmReSizeIMCC(
    HIMCC hIMCC,
    DWORD dwSize
   )
```
>Parameters
hIMCC
Handle of the IMC component.
dwSize
New size of the IMC component.

>Return Values
If the function is successful, the return value is the new HIMCC. Otherwise, the return value is NULL.

** 参数**
`hIMCC` IMC组件句柄
** 返回值 **
成功返回新的HIMCC，否则返回NULL。

## ImmGetIMCCSize
>The ImmGetIMCCLockCount function is used to get the size of the IMCC.

ImmGetIMCCLockCount返回IMCC的尺寸。
``` c++
DWORD WINAPI ImmGetIMCCSize( HIMCC hIMCC)
```
>Parameters
hIMCC
Handle of the IMC component.

>Return Values
Size of the IMCC.

** 参数**
`hIMCC` IMC组件句柄
** 返回值 **
返回IMCC的尺寸。

## ImmGetIMCCLockCount
>The ImmGetIMCCLockCount function is used to get the lock count of the IMCC.

ImmGetIMCCLockCount函数返回IMCC持有锁锁定的次数。
``` c++
DWORD WINAPI ImmGetIMCCLockCount(HIMCC hIMCC)
```
>Parameters
hIMCC
Handle of the IMC component.

>Return Values
If the function is successful, the return value is the lock count of the IMCC. Otherwise, the return value is zero.

** 参数**
`hIMCC` IMC组件句柄
** 返回值 **
成功返回IMCC持有锁锁定的次数，否则返回0。

# 输入法热键及相关函数
>The IME hot key is used for changing the IME input mode and for switching the IME. The IME hot key used to switch directly to an IME is called a direct switching hot key.
The direct switching hot key ranges from IME_HOTKEY_DSWITCH_FIRST to IME_HOTKEY_DSWITCH_LAST. It is registered by an IME or Control Panel when the IME or an end user wants such a hot key. The IME hot key is effective in all IMEs, regardless which IME is active.
There are several predefined hot key functionalities in the IMM. The IMM itself provides the functionality (different handling routines) of those hot key functions. Every hot key funtionality has a different hot key ID in IMM and each ID has its own functionality according to the specific requirements of each country. Note that an application cannot add another predefined hot key ID into the system.
Following are the predefined hot key identifiers.

输入法热键用于改变输入法模式以及切换输入法。直接用于切至某一输入法的热键被称作“直接切换热键”。
“直接切换热键”的范围可由`IME_HOTKEY_DSWITCH_FIRST` 到 `IME_HOTKEY_DSWITCH_LAST`。可以通过输入法来注册该热键，也可以由用户通过系统控制面板注册。一旦注册了输入法热键，不论当前输入法是谁，该热键始终有效。
IMM中还有几个预先定义的热键功能。每个热键功能在IMM中都有一个不同的热键ID，每个ID根据每个国家语言指定的需求都有它独有的功能。注意：输入法不能向系统添加额外的预定义热键ID。
下面就是预定义的热键ID：
IME_CHOTKEY_IME_NONIME_TOGGLE
Hot key for Simplified Chinese Edition. This hot key toggles between the IME and non-IME.
IME_CHOTKEY_SHAPE_TOGGLE
Hot key for Simplified Chinese Edition. This hot key toggles the shape conversion mode of the IME.
IME_CHOTKEY_SYMBOL_TOGGLE
Hot key for Simplified Chinese Edition. This hot key toggles the symbol conversion mode of the IME. The symbol mode indicates that the user can input Chinese punctuation and symbols (full shape characters) by mapping it to the punctuation and symbol keystrokes of the keyboard.
IME_JHOTKEY_CLOSE_OPEN
Hot key for Japanese Edition. This hot key toggles between closed and opened.
IME_THOTKEY_IME_NONIME_TOGGLE
Hot key for (Traditional) Chinese Edition. This hot key toggles between the IME and non-IME.
IME_THOTKEY_SHAPE_TOGGLE
Hot key for (Traditional) Chinese Edition. This hot key toggles the shape conversion mode of the IME.
IME_THOTKEY_SYMBOL_TOGGLE
Hot key for (Traditional) Chinese Edition. This hot key toggles the symbol conversion mode of the IME.
* `IME_CHOTKEY_IME_NONIME_TOGGLE` 
简体中文热键，用于在有输入法和无输入法之间切换。
* `IME_CHOTKEY_SHAPE_TOGGLE` 
简体中文热键，用于切换全半角。
* `IME_CHOTKEY_SYMBOL_TOGGLE` 
简体中文热键。用于在符号模式之间切换。符号模式是指当用户按下符号键时，是否可以输入中文标点和符号（全角符号）。
* `IME_JHOTKEY_CLOSE_OPEN` 
日文热键。用于切换开-闭状态。
* `IME_THOTKEY_IME_NONIME_TOGGLE` 
繁体中文热键。用于在有输入法和无输入法之间切换。
* `IME_THOTKEY_SHAPE_TOGGLE` 
繁体中文热键。用于在全半角之间切换。
* `IME_THOTKEY_SYMBOL_TOGGLE` 
繁体中文热键。用于切换符号模式。
>The other kind of hot key is the IME private hot key, but there is no functionality for this kind of hot key. It is just a placeholder for a hot key value. An IME can get this value by calling ImmGetHotKey. If an IME supports this functionality for one hot key ID, it will perform the functionality every time it finds this key input.
Following are the currently defined private IME hot key IDs.

还有一种热键是输入法的私有热键，对于这类热键IMM没有提供相关功能。它仅仅是一个热键占位符。输入法可以调用ImmGetHotKey来获得该值。如果输入法支持该热键ID对应的功能，它会在每次检测到按键被按下时执行相关功能。
下面是目前定义的输入法私有热键ID：
IME_ITHOTKEY_RESEND_RESULSTR
Hot key for (Traditional) Chinese Edition. This hot key should trigger the IME to resend the previous result string to the application. If the IME detects that this hot key is pressed, it needs to resend the previous result string to this application.
IME_ITHOTKEY_PREVIOUS_COMPOSITION
Hot key for (Traditional) Chinese Edition. This hot key should trigger the IME to bring up the previous composition string to the application.
IME_ITHOTKEY_UISTYLE_TOGGLE
Hot key for (Traditional) Chinese Edition. This hot key should trigger the IME UI to toggle the UI style between caret-related UI and the caret-unrelated UI.
IME_ITHOTKEY_RECONVERTSTRING
Hot key for (Traditional) Chinese Edition. This hot key should trigger the IME to make a reconversion. This is a new ID for Windows 98 and Windows 2000.

* `IME_ITHOTKEY_RESEND_RESULSTR`
繁体中文热键。该键触发输入法向应用程序重新发送前一个结果串。
* `IME_ITHOTKEY_PREVIOUS_COMPOSITION`
繁体中文热键。该热键触发输入法向应用程序发出前一个写作串。
* `IME_ITHOTKEY_UISTYLE_TOGGLE`
繁体中文热键。该热键触发输入法UI风格在光标相关模式和光标无关模式间切换。
* `IME_ITHOTKEY_RECONVERTSTRING`
繁体中文热键。该热键触发输入法做重新转换。该ID是在Win98/Win2000引入的。

## ImmGetHotKey
>The ImmGetHotKey function gets the value of the IME hot key.

ImmGetHotKey函数获取输入法热键的值。
``` c++
BOOL WINAPI ImmGetHotKey(
    DWORD dwHotKeyID,
    LPUINT lpuModifiers,
    LPUINT lpuVKey,
    LPHKL lphKL
   )
```
>Parameters
dwHotKeyID
Hot key identifier.
lpuModifiers
Combination keys with the hot key. It includes ALT (MOD_ALT), CTRL (MOD_CONTROL), SHIFT (MOD_SHIFT), left-hand side (MOD_LEFT), and right-hand side (MOD_RIGHT).
The key up flag (MOD_ON_KEYUP) indicates that the hot key is effective when the key is up. The modifier ignore flag (MOD_IGNORE_ALL_MODIFIER) indicates that the combination of modifiers is ignored in hot key matching.
lpuVKey
Virtual key code of this hot key.
lphKL
HKL of the IME. If the return value of this parameter is not NULL, this hot key can switch to the IME with this HKL.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
Comments
This function is called by the Control Panel.

** 参数 **
`dwHotKeyID` 热键ID
`lpuModifiers` 热键组合键，包含ALT(MOD_ALT)，CTRL(MOD_CONTROL)，SHIFT(MOD_SHIFT)，左侧(MOD_LEFT)和右侧(MOD_RIGHT)。
按键抬起标志(MOD_ON_KEYUP)表示按键抬起时有效。修饰忽略标记(MOD_IGNORE_ALL_MODIFIER)表示修饰组合键会在热键匹配时被忽略掉。
`lpuVKey`热键的虚拟键盘码
`lphKL`输入法的HKL（Keyboard Layout Handle，用来标识一个输入法），如果该值返回非空，该热键可以切换到HKL所表示的输入法。
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 注释 ** 
该函数由控制面板调用。

## ImmSetHotKey
>The ImmSetHotKey function sets the value of the IME hot key.

ImmSetHotKey函数用于设置输入法热键。
``` c++
BOOL WINAPI ImmSetHotKey(
    DWORD dwHotKeyID,
    UINT uModifiers,
    UINT uVKey,
    hKL hKL
   )
```
>Parameters
dwHotKeyID
Hot key identifier.
uModifiers
Combination keys with the hot key. It includes ALT (MOD_ALT), CTRL (MOD_CONTROL), SHIFT (MOD_SHIFT), left-hand side (MOD_LEFT), and right-hand side (MOD_RIGHT).
The key up flag (MOD_ON_KEYUP) indicates that the hot key is effective when the key is up. The modifier ignore flag (MOD_IGNORE_ALL_MODIFIER) indicates that the combination of modifiers is ignored in hot key matching.
uVKey
Virtual key code of this hot key.
hKL
HKL of the IME. If this parameter is specified, this hot key can switch to the IME with this HKL.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
Comments
This function is called by the Control Panel. For a key that does not indicate a specific keyboard hand side, the uModifiers should specify both sides (MOD_LEFT|MODE_RIGHT).

** 参数 **
`dwHotKeyID` 热键ID
`lpuModifiers` 热键组合键，包含ALT(MOD_ALT)，CTRL(MOD_CONTROL)，SHIFT(MOD_SHIFT)，左侧(MOD_LEFT)和右侧(MOD_RIGHT)。
按键抬起标志(MOD_ON_KEYUP)表示按键抬起时有效。修饰忽略标记(MOD_IGNORE_ALL_MODIFIER)表示修饰组合键会在热键匹配时被忽略掉。
`uVKey`热键的虚拟键盘码
`hKL`输入法的HKL（Keyboard Layout Handle，用来标识一个输入法），如果该值返回非空，该热键可以切换到HKL所表示的输入法。
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 注释 ** 
该函数由控制面板调用。对于一个没有特殊指明左手侧或右手侧的按键，uModifiers应当带有MOD_LEFT|MOD_RIGHT标记。

# IMM软键盘函数
>The following topics contain the IMM functions that are used by the IME to manipulate the soft keyboard.

下面的主题将包含软键盘控制函数。

## ImmCreateSoftKeyboard
>The ImmCreateSoftKeyboard function creates one type of soft keyboard window.

ImmCreateSoftKeyboard函数创建一种软键盘窗口。
``` c++
HWND WINAPI ImmCreateSoftKeyboard(
    UINT uType,
    UINT hOwner,
    int x,
    int y
   )
```
>Parameters
uType
Specifies the type of the soft keyboard.
Utype
Description

>SOFTKEYBOARD_TYPE_T1
Type T1 soft keyboard. This kind of soft keyboard should be updated by IMC_SETSOFTKBDDATA.
SOFTKEYBOARD_TYPE_C1
Type C1 soft keyboard. This kind of soft keyboard should be updated by IMC_SETSOFTKBDDATA with two sets of 256-word array data. The first set is for nonshift state, and the second is for shift state.

>hOwner
Specifies the owner of the soft keyboard. It must be the UI window.
x
Specifies the initial horizontal position of the soft keyboard.
y
Specifies the initial vertical position of the soft keyboard.

>Return Values
This function returns the window handle of the soft keyboard.

** 参数 **
`uType` 指定软键盘的类型。其取值范围如下：
* `SOFTKEYBOARD_TYPE_T1` T1型软键盘，这类软键盘应当使用IMC_SETSOFTKBDDATA来更新。
* `SOFTKEYBOARD_TYPE_C1` C1型软键盘，这类软键盘应当使用附带两套256word数组的IMC_SETSOFTKBDDATA来更新。第一套用于表示无shift的状态，第二套用于表示有shift的状态。
`hOwner` 指定软键盘的归属，必须是UI窗体
`x` 指定软键盘初始x轴坐标
`y` 制定软键盘初始y轴坐标
** 返回值 **
返回软键盘的窗体句柄

## ImmDestroySoftKeyboard
>The ImmDestroySoftKeyboard function destroys the soft keyboard window.

该函数用于销毁软键盘。
``` c++
BOOL WINAPI ImmDestroySoftKeyboard(HWND hSoftKbdWnd)
```
>Parameters
hSoftKbdWnd
Window handle of the soft keyboard to destroy.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

** 参数 **
`hSoftKbdWnd` 待销毁的软键盘窗体句柄
** 返回值 **
成功返回TRUE，失败返回FALSE。

## ImmShowSoftKeyboard
>The ImmShowSoftKeyboard function shows or hides the given soft keyboard.

该函数显示或隐藏软键盘。
``` c++
BOOL WINAPI ImmShowSoftKeyboard(
    HWND hSoftKbdWnd,
    int nCmdShow
   )
```
>Parameters
hSoftKbdWnd
Window handle of the soft keyboard.
nCmdShow
Shows the state of the window. The following values are provided.
NcmdShow
Meaning

>SW_HIDE
Hides the soft keyboard.
SW_SHOWNOACTIVATE
Displays the soft keyboard

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

** 参数 **
`hSoftKbdWnd` 软键盘窗体句柄
`nCmdShow` 窗口的显示/隐藏状态，可以使用如下值来制定：
* `SW_HIDE` 隐藏软键盘
* `SW_SHOWNOACTIVATE` 显示软键盘
** 返回值 **
成功返回TRUE，失败返回FALSE。

# 消息
>The following topics contain the messages that the UI window receives.

下面讨论输入法UI窗体接收的消息。
>WM_IME_SETCONTEXT
The WM_IME_SETCONTEXT message is sent to an application when a window of the application is being activated. If the application does not have an application IME window, the application has to pass this message to the DefWindowProc and should return the return value of the DefWindowProc. If the application has an application IME window, the application should call ImmIsUIMessage.
WM_IME_SETCONTEXT
fSet= (BOOL) wParam; 
lISCBits = lParam; 
Parameters
fSet
fSet is TRUE when the Input Context becomes active for the application. When it is FALSE, the Input Context becomes inactive for the application.
lISCBits
lISCBits consists of the following bit combinations.
Value
Description

>ISC_SHOWUICOMPOSITIONWINDOW
Shows the composition window.
ISC_SHOWUIGUIDWINDOW
Shows the guide window.
ISC_SHOWUICANDIDATEWINDOW
Shows the candidate window of Index 0.
(ISC_SHOWUICANDIDATEWINDOW << 1)
Shows the candidate window of Index 1.
(ISC_SHOWUICANDIDATEWINDOW << 2)
Shows the candidate window of Index 2.
(ISC_SHOWUICANDIDATEWINDOW << 3)
Shows the candidate window of Index 3.

>Return Values
The return value is the return value of DefWindowProc or ImmIsUIMessage.
Comments
After an application calls DefWindowProc( or ImmIsUIMessage with WM_IME_SETCONTEXT, the UI window receives WM_IME_SETCONTEXT. If the bit is on, the UI window shows the composition, guide, or candidate window as the bit status of lParam.
If an application draws the composition window by itself, the UI window does not need to show its composition window. The application then has to clear the ISC_SHOWUICOMPOSITIONWINDOW bit of lParam and call DefWindowProc or ImmIsUIMessage with it.

## WM_IME_SETCONTEXT
当应用程序窗体被激活时，它将收到该消息。如果应用程序没有输入法窗口，它应当把该消息传递个`DefWindowProc`函数处理并返回该函数的返回值；如果应用程序有输入法窗体，它应调用`ImmIsUIMessage`。
** 参数 **
`wParam` fSet=(BOOL)wParam，应用程序被激活是时为TRUE；否则为FALSE。
`lParam` IISCBits，该值是如下值的组合：
* `ISC_SHOWUICOMPOSITIONWINDOW` 显示写作窗
* `ISC_SHOWUIGUIDWINDOW` 显示向导窗
* `ISC_SHOWUICANDIDATEWINDOW` 显示第0个候选窗
* `(ISC_SHOWUICANDIDATEWINDOW << 1)` 显示第1个候选窗
* `(ISC_SHOWUICANDIDATEWINDOW << 2)` 显示第2个候选窗
* `(ISC_SHOWUICANDIDATEWINDOW << 3)` 显示第3个候选窗

** 返回值 **
返回`DefWindowProc`或`ImmIsUUIMessage`的返回值。
** 注释 **
应用程序调用传入WM_IME_SETCONTEXT的`DefWindowProc`（或`ImmIsUIMessage`）函数后，输入法UI窗口会接收到WM_IME_SETCONTEXT消息。如果对应的标记为为ON，UI窗口将负责显示写作窗、向导窗或候选窗。
如果应用程序自己负责绘制写作窗，UI窗口就不需要显示写作窗口了。由应用程序负责清除`ISC_SHOWUICOMPOSITIONWINDOW`标记，并调用`DefWindowProc`或`ImmIsUIMessage`函数。

>WM_IME_CONTROL
The WM_IME_CONTROL message is a group of sub messages used to control the IME User Interface. An application uses this message to interact with the IME window created by the application.
WM_IME_CONTROL
wSubMessage= wParam;
lpData = (LPVOID) lParam;
Parameters
wSubMessage
Submessage value.
LpData
Dependent on each wSubMessage. 

>The following topics contain the submessages classified by the wSubMessage value.
Except for IMC_GETSOFTKBDSUBTYPE, IMC_SETSOFTKBDSUBTYPE, IMC_SETSOFTKBDDATA, IMC_GETSOFTKBDFONT, IMC_SETSOFTKBDFONT, IMC_GETSOFTKBDPOS and IMC_SETSOFTKBDPOS, it is recommended that applications use IMM APIs instead of the IMC messages to communicate with the IME window. 

## WM_IME_CONTROL
该消息是若干子消息的组合，用于控制输入法界面展现。应用程序使用该消息与输入法窗体通讯。
** 参数 **
`wParam` wSubMessage，子消息的值
`lParam` lpData=(LPVOID)lParam，根据每个wSubMessage有不同含义

下面讨论wSubMessage的不同取值。注意：除了IMC_GETSOFTKBDSUBTYPE, IMC_SETSOFTKBDSUBTYPE, IMC_SETSOFTKBDDATA, IMC_GETSOFTKBDFONT, IMC_SETSOFTKBDFONT, IMC_GETSOFTKBDPOS and IMC_SETSOFTKBDPOS这些消息外，建议应用程序在与输入法窗体通讯的时候使用IMM函数而不是IMC消息。

>IMC_GETCANDIDATEPOS
The IMC_GETCANDIDATEPOS message is sent by an application to the IME window to get the position of the candidate window. The IME can adjust the position of a candidate window in respect to the screen boundary. In addition, an application can obtain the real position of a candidate window to determine whether to move it to another position.
WM_IME_CONTROL
wSubMessage= IMC_GETCANDIDATEPOS;
lpCANDIDATENFORM = (LPCANDIDATEFORM) lParam;
Parameters
lpCANDIDATENFORM 
Buffer to retrieve the position of the candidate window.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
In return, the IME will fill the CANDIDATEFORM pointed to by lpCANDIDATENFORM with the client coordinates of the application’s focus window. The UI window receives this message. An application should specify lpCANIDATEFORM->dwIndex to 0 ~ 3 to obtain a different candidate window position. (For example, index 0 is a top-level candidate window.)

### IMC_GETCANDIDATEPOS
应用程序向输入法窗口发送该消息获得候选窗的位置。输入法可以根据屏幕边界调整候选窗位置，应用程序可以获得候选窗位置并决定要不要把它挪到别的地儿。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage = IMC_GETCANDIDATEPOS
lpCANDIDATEFORM = (LPCANDIDATEFORM)lParam
```
    ** 参数 **
    `lpCANDIDATEFORM` 获取候选窗体位置的Buffer。
    ** 返回值 **
    成功返回0，否则返回非0.
    ** 说明 **
    输入法会在该消息返回时填充lpCANDIDATEFORM结构体，将应用程序焦点窗口的基于客户端坐标系的候选窗坐标填入该结构体。UI窗口获得该消息。应用程序应当指定`lpCANDIDATEFORM->dwIndex`为0到3来获得不同的候选窗位置。

>IMC_GETCOMPOSITONFONT
The IMC_GETCOMPOSITONFONT message is sent by an application to the IME window to obtain the font to use in displaying intermediate characters in the composition window.
WM_IME_CONTROL
wSubMessage= IMC_GETCOMPOSITIONFONT;
lpLogFont= (LPLOGFONT) lParam;
Parameters
lpLogFont
Buffer to retrieve the LOGFONT.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The UI window does not receive this message.

### IMC_GETCOMPOSITONFONT
应用程序向IME窗体发送该消息来获得显示写作串的字体。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage = IMC_GETCOMPOSITIONFONT
lpLogFont = (LPLOGFONT)lParam
```
** 参数 **
`lpLogFont`
获得LOGFONT的Buffer。
** 返回值 **
成功返回0，否则返回非0。
** 说明 **
UI窗体不会收到该消息。

>IMC_GETCOMPOSITONWINDOW
The IMC_GETCOMPOSITONWINDOW message is sent by an application to the IME window to get the position of the composition window. An IME can adjust the position of a composition window, and an application can obtain the real position of composition window to determine whether to move it to another position.
WM_IME_CONTROL
wSubMessage= IMC_GETCOMPOSITIONWINDOW;
lpCOMPOSITIONFORM = (LPCOMPOSITIONFORM) lParam;
Parameters
lpCOMPOSITIONFORM
Buffer to retrieve the position of the composition window.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
In return, the IME will fill the CANDIDATEFORM pointed to by lpCANDIDATENFORM with the client coordinates of the application’s focus window. The UI window receives this message.

### IMC_GETCOMPOSITONWINDOW
应用程序向输入法窗口发送该消息获得写作窗的位置。输入法可以自主调整写作窗位置，应用程序可以获得该位置并决定要不要调整此位置。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage = IMC_GETCOMPOSITIONWINDOW;
lpCOMPOSITIONFORM = (LPCOMPOSITIONFORM) lParam;
```
** 参数 **
`lpCOMPOSITIONFORM`
获得写作窗位置的Buffer。
** 返回值 **
成功返回0，否则返回非0。
** 说明 **
输入法负责填充lpCOMPOSITIONFORM指向的结构体，并将应用程序焦点窗口的基于客户端坐标系的位置填入该结构体。UI窗体会接收到该消息。


>IMC_GETSOFTKBDFONT
The IMC_GETSOFTKBDFONT message is sent by the IME to the soft keyboard window to obtain the font to use for character display in the soft keyboard window.
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDFONT;
lpLogFont= (LPLOGFONT) lParam;
Parameters
lpLogFont
Buffer to retrieve the LOGFONT.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.

### IMC_GETSOFTKBDFONT
输入法向软键盘窗口发送该消息来获得软键盘窗口的字体。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDFONT;
lpLogFont= (LPLOGFONT) lParam;
```
** 参数 **
`lpLogFont`
获得LOGFONT的Buffer。
** 返回值 **
成功返回0，否则返回非0。

>IMC_GETSOFTKBDPOS
The IMC_GETSOFTKBDPOS message is sent by an IME to the soft keyboard window to obtain the position of the soft keyboard window.
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDPOS;
lParam = 0;
Parameters
lParam
Not used.

>Return Values
The return value specifies a POINTS structure that contains the x and y coordinates of the position of the soft keyboard window, in screen coordinates.
Comments
The POINTS structure has the following form:
typedef struct tagPOINTS { /* pts */
SHORT x;
SHORT y;
} POINTS;

### IMC_GETSOFTKBDPOS
输入法向软键盘窗体发送该消息来获得软键盘窗体的位置。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDPOS;
lParam = 0;
```

** 返回值 **
返回一个POINTS结构体，其x、y分别表示软键盘窗体基于屏幕坐标系的位置。
** 说明 **
POINTS结构体形式如下：
``` c++
typedef struct tagPOINTS { /* pts */
SHORT x;
SHORT y;
} POINTS;
```

>IMC_GETSOFTKBDSUBTYPE
The IMC_GETSOFTKBDSUBTYPE message is sent by an IME to the soft keyboard window to obtain the subtype of the soft keyboard window set by IMC_SETSOFTKBDSUBTYPE.
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDSUBTYPE;
lParam = 0;
Parameters
lParam
Not used.

>Return Values
The return value is the subtype of the soft keyboard set by IMC_SETSOFTKBDSUBTYPE. A return value of -1 indicates failure.

### IMC_GETSOFTKBDSUBTYPE
输入法向软键盘窗体发送该消息来获得软键盘子类型，该子类型是通过IMC_SETSOFTKBDSUBTYPE消息设定的。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_GETSOFTKBDSUBTYPE;
lParam = 0;
```
** 返回值 **
返回软键盘的子类型，失败返回-1。

>IMC_GETSTATUSWINDOWPOS
The IMC_GETSTATUSWINDOWPOS message is sent by an application to the IME window to get the position of the status window.
WM_IME_CONTROL
wSubMessage= IMC_GETSTATUSWINDOWPOS;
lParam = 0;
Parameters
lParam
Not used.

>Return Values
The return value specifies a POINTS structure that contains the x and y coordinates of the position of the status window, in screen coordinates.
Comments
The POINTS structure has the following form:
typedef struct tagPOINTS { /* pts */
SHORT x;
SHORT y;
} POINTS;
 
>Comments
The UI window receives the message.

### IMC_GETSTATUSWINDOWPOS
应用程序向输入法窗口发送该消息来获得状态栏的位置。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_GETSTATUSWINDOWPOS;
lParam = 0;
```
** 返回值 **
返回一个POINTS结构体，其包含的x、y表示状态栏基于屏幕坐标系的位置。

>IMC_SETCANDIDATEPOS
The IMC_SETCANDIDATEPOS message is sent by an application to the IME window to specify the display position of a candidate window. In particular, this applies to an application that displays composition characters by itself, but uses the IME UI to display candidates.
WM_IME_CONTROL
wSubMessage= IMC_SETCANDIDATEPOS;
lpCANDIDATEFORM= (LPCANDIDATEFORM) lParam;
Parameters
lpCANDIDATEFORM
Buffer includes the candidate window position information.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The UI window does not receive this message.

### IMC_SETCANDIDATEPOS
应用程序向输入法窗口发送该消息来指定候选窗的位置。该消息适用于应用程序自己显示写作窗，输入法负责显示候选窗的情况。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETCANDIDATEPOS;
lpCANDIDATEFORM= (LPCANDIDATEFORM) lParam;
```
** 参数 **
`lpCANDIDATEFORM` 候选窗口位置信息的Buffer
** 返回值 **
成功返回0，否则返回非0.
** 说明 **
UI窗口不接收该消息。

>IMC_SETCOMPOSITONFONT
The IMC_SETCOMPOSITONFONT message is sent by an application to the IME window to specify the font to use in displaying intermediate characters in the composition window.
WM_IME_CONTROL
wSubMessage= IMC_SETCOMPOSITIONFONT;
lpLogFont= (LPLOGFONT) lParam;
Parameters
lpLogFont
Buffer includes the LOGFONT data to set.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The UI window does not receive this message.

### IMC_SETCOMPOSITONFONT
应用程序向输入法窗体发送该消息来指定候选窗口使用的字体类型。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETCOMPOSITIONFONT;
lpLogFont= (LPLOGFONT) lParam;
```
** 参数 **
`lpLogFont` 指向LOGFONT的Buffer
** 返回值 **
成功返回0，否则返回非0.
** 说明 **
UI窗体不会接收该消息。

>IMC_SETCOMPOSITONWINDOW
The IMC_SETCOMPOSITONWINDOW message is sent by an application to the IME window to set the style of the composition window in the current active Input Context. Once an application sets the style, the IME user interface then follows the style specified in the Input Context.
WM_IME_CONTROL
wSubMessage= IMC_SETCOMPOSITIONWINDOW;
lpCOMPOSITIONFORM= (LPCOMPOSITIONFORM) lParam;
Parameters
lpCOMPOSITIONFORM 
COMPOSITIONFORM structure includes the new styles for the composition window.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The IME user interface uses a default style for the composition window that is equal to the CFS_POINT style. If an application has not specified a composition style in its Input Context, the IME user interface retrieves the current caret position and window client area when it opens the composition window (in client coordinates). The UI window does not receive this message.

### IMC_SETCOMPOSITONWINDOW
应用程序想输入法窗体发送该消息来设置当前活动的输入法写作窗风格。一旦应用程序设定了该窗口风格，输入法将会遵循它。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETCOMPOSITIONWINDOW;
lpCOMPOSITIONFORM= (LPCOMPOSITIONFORM) lParam;
```
** 参数 **
`lpCOMPOSITIONFORM` 设定写作窗新风格的COMPOSITIONFORM结构体
** 返回值 **
成功返回0，否则返回非0.
** 说明 **
输入法使用默认值（即CFS_POINT）来设定写作窗风格。如果应用程序不指定新的风格，输入法会在打开候选窗时获取当前光标位置和客户端窗体区域。UI窗口不接收此消息。

>IMC_SETSOFTKBDDATA
The IMC_SETSOFTKBDDATA message is sent by the IME to the soft keyboard window to specify the character code to use for displaying characters in the soft keyboard window.
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDDATA;
lpSoftKbdData= (LPSOFTKBDDATA) lParam;
Parameters
lpSoftKbdData 
Points to the buffer to specify the character code to use for displaying characters.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The UI window does not receive this message.

### IMC_SETSOFTKBDDATA
输入法向软键盘窗口发送该消息来指定软键盘要显示的字符码。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDDATA;
lpSoftKbdData= (LPSOFTKBDDATA) lParam;
```
** 参数 **
`lpSoftKbdData` 指定要显示的字符码的Buffer
** 返回值 **
成功返回0，否则返回非0.
** 说明 **
UI窗口不接收此消息。

>IMC_SETSOFTKBDSUBTYPE
The IMC_SETSOFTKBDSUBTYPE message is sent by the IME to the soft keyboard window to specify the subtype to use for displaying characters in the soft keyboard window. It also can be used for IME-specific purposes.
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDSUBTYPE;
lSubType= lParam;
Parameters
lSubType
Specifies the subtype to set.

>Return Values
The return value is the subtype. A return value of -1 indicates failure.
Comments
The UI window does not receive this message, and the SOFTKEYBOARD_TYPE_T1 does not use this information. The IME sends this message so the soft keyboard will not change the displayed reading characters. The IME can use the SOFTKEYBOARD_TYPE_T1 soft keyboard to define the meaning of this message and can obtain this data by using IMC_GETSOFTKBDSUBTYPE.

### IMC_SETSOFTKBDSUBTYPE
输入法想软键盘发送该消息来指定软键盘的子类。也可以用于输入法的特殊目的。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDSUBTYPE;
lSubType= lParam;
```
** 参数 **
`lSubType` 指定要显示的子类
** 返回值 **
成功返回子类型，失败返回-1。
** 说明 **
UI窗口不接收此消息，SOFTKEYBOARD_TYPE_T1不使用该信息。输入法发送该消息，软键盘不会改变已显示的字符。输入法可以使用SOFTKEYBOARD_TYPE_T1类型的软键盘来定义该消息的含义，可以使用IMC_GETSOFTKBDSUBTYPE来获取数据。

> IMC_SETSOFTKBDFONT
The IMC_SETSOFTKBDFONT message is sent by the IME to the soft keyboard window to specify the font to use in displaying characters in the soft keyboard window.
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDFONT;
lpLogFont= (LPLOGFONT)lParam;
Parameters
lpLogFont 
Points to the LOGFONT to be set.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The UI window does not receive this message.

### IMC_SETSOFTKBDFONT
输入法想软键盘窗口发送该校来指定软键盘的字体。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDFONT;
lpLogFont= (LPLOGFONT)lParam;
```
** 参数 **
`lpLogFont` 指向LOGFONT的指针。
** 返回值 **
成功返回0，否则返回非0。
** 说明 **
UI窗口不接收此消息。

>IMC_SETSOFTKBDPOS
The IMC_SETSOFTKBDPOS message is sent by the UI window to soft keyboard window to set the position of the soft keyboard window.
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDPOS;
ptsPt= (POINTS)lParam;
Parameters
ptsPt
Specifies a POINTS structure that contains the x and y coordinates of the position of the soft keyboard window, in screen coordinates.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The POINTS structure has the following form:
typedef struct tagPOINTS { /* pts */
SHORT x;
SHORT y;
} POINTS;

### IMC_SETSOFTKBDPOS
UI窗口向软键盘发送该消息来设置软键盘的位置。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETSOFTKBDPOS;
ptsPt= (POINTS)lParam;
```
** 参数 **
`ptsPt` 指向POINTS的指针，其x、y表示软键盘基于屏幕坐标系的位置。
** 返回值 **
成功返回0，否则返回非0。
 
>IMC_SETSTATUSWINDOWPOS
The IMC_SETSTATUSWINDOWPOS message is sent by an application to the IME window to set the position of the status window.
WM_IME_CONTROL
wSubMessage= IMC_SETSTATUSWINDOWPOS;
ptsPt= (POINTS)lParam;
Parameters
ptsPt
Specifies a POINTS structure that contains the x and y coordinates of the position of the status window, in screen coordinates.

>Return Values
If the message is successful, the return value is zero. Otherwise, the return value is nonzero.
Comments
The POINTS structure has the following form:
typedef struct tagPOINTS { /* pts */
SHORT x;
SHORT y;
} POINTS;
 
### IMC_SETSTATUSWINDOWPOS
应用程序向输入法窗体发送该消息来设置状态栏位置。消息形式为：
``` c++
WM_IME_CONTROL
wSubMessage= IMC_SETSTATUSWINDOWPOS;
ptsPt= (POINTS)lParam;
```
** 参数 **
`ptsPt` 指向POINTS的指针，其x、y表示状态栏基于屏幕坐标系的位置。
** 返回值 **
成功返回0，否则返回非0。

> WM_IME_COMPOSITION 
The WM_IME_COMPOSITION message is sent to an application when the IME composition status is changed (by the user). The message consists of two bytes of composition character. The IME user interface window changes its appearance when it processes this message. An application can call ImmGetCompositionString to obtain the new composition status.
WM_IME_COMPOSITION
wChar= wParam;
lAttribute= lParam;
Parameters
wChar
Consists of two bytes of DBCS character that is the latest change of composition character.
lAttribute
Contains the following flag combinations. Basically, the flag indicates how the composition string or character has changed. An application checks this to retrieve necessary information.
Value
Description

>GCR_ERRORSTR
Updates the error string.
GCR_INFORMATIONSTR
Updates the information string.
GCS_COMPATTR
Updates the attribute of the composition string.
GCS_COMPCLAUSE
Updates clause information of the composition string.
GCS_COMPREADATTR
Updates the attributes of the reading string of the current composition.
GCS_COMPREADCLAUSE
Updates the clause information of the reading string of the composition string.
GCS_COMPREADSTR
Updates the reading string of the current composition. 
GCS_COMPSTR
Updates the current composition string. 
GCS_CURSORPOS
Updates the cursor position in composition string.
GCS_DELTASTART
Updates the starting position of any changes in composition string.
GCS_RESULTCLAUSE
Updates clause information of the result string. 
GCS_RESULTREADCLAUSE
Updates clause information of the reading string. 
GCS_RESULTREADSTR
Updates the reading string. 
GCS_RESULTSTR
Updates the string of the composition result. 

>The following style bit values are provided for WM_IME_COMPOSITION.
Value
Description

>CS_INSERTCHAR
An IME specifies this value when wParam shows a composition character that should be inserted into the current insertion point. An application should display a composition character if it processes this bit flag.
CS_NOMOVECARET
An IME specifies this value when it does not want an application to move the caret position as a result of processing WM_IME_COMPOSITION. For example, if an IME specifies a combination of CS_INSERTCHAR and CS_NOMOVECARET, it means that an application should insert a character given by wParam to the current caret position, but should not move the caret. Subsequent WM_IME_COMPOSITION messages containing the GCS_RESULTSTR flag will replace this character.

>Return Values
None.
Comments
When an application wants to display composition characters by themselves, it should not pass this message to the application IME user interface window or to DefWindowProc. The DefWindowProc function processes this message to pass to the Default IME window. An IME should send this message to an application even when the IME only cancels the current composition. This message should also be used to notify an application or IME UI to erase the current composition string.
See Also
ImmGetCompositionString

## WM_IME_COMPOSITION
当舒服啊写作窗数据发生变化时，该消息会被发送给应用程序。该消息由写作串字符的两个字节组成。输入法处理该消息时会让窗口发生变化。应用程序可以调用`ImmGetCompositionString`来获得新的写作串。消息形式为：
``` c++
WM_IME_COMPOSITION
wChar= wParam;
lAttribute= lParam;
```
** 参数 **
`wChar` 最新写作串的DBCS字符的两个字节
`lAttribute` 该值为如下标记的组合，这些标记用来描述写作串如何发生变化。应用程序通过这些标记来获得必要的信息：
* `GCR_ERRORSTR` 更新错误串。
* `GCR_INFORMATIONSTR` 更新信息串。
* `GCS_COMPATTR` 更新写作串的属性。
* `GCS_COMPCLAUSE` 更新写作串的分句信息。
* `GCS_COMPREADATTR` 更新当前写作串的读入串属性。
* `GCS_COMPREADCLAUSE` 更新写作串的读入串分句信息。
* `GCS_COMPREADSTR` 更新当前写作串的读入串。
* `GCS_COMPSTR` 更新当前写作串。
* `GCS_CURSORPOS` 更新写作串中的光标位置。
* `GCS_DELTASTART` 更新写作串中发生变化的起始位置。
* `GCS_RESULTCLAUSE` 更新结果串的分句信息。
* `GCS_RESULTREADCLAUSE` 更新读入串的分句信息。
* `GCS_RESULTREADSTR` 更新读入串。
* `GCS_RESULTSTR` 更新写作串的结果串。

下面的风格位是由WM_IME_COMPOSITION提供：
* `CS_INSERTCHAR` 当wParam表明写作串应当被插入到当前插入位置时，输入法会指定该值。应用程序如果要处理该标记，就应当显示写作串。
* `CS_NOMOVECARET` 如果输入法不希望应用程序在处理WM_IME_COMPOSITION消息时移动光标位置，就会指定该值。例如，输入法指定`CS_INSERTCHAR|CS_NOMOVECARET`表明应用程序应当把wParam指定的字符插入到当前光标位置，但不应该移动光标。随后包含`GCS_RESULTSTR`标志`WM_IME_COMPOSITION`消息将替换该字符。

** 说明 **
如果应用程序希望自己显示写作串，则不应该把该消息传递给输入法窗口或者`DefWindowProc`来处理。`DefWindowProc`函数会将该消息传递给默认的输入法窗体。输入法应当把该消息发送给应用程序即使当输入法只是取消了当前写作窗。该消息还应当用来通知应用程序或输入法来擦除当前的写作窗。

>WM_IME_COMPOSITIONFULL
The WM_IME_COMPOSITIONFULL message is sent to an application when the IME user interface window cannot increase the size of the composition window. An application should specify how to display the IME UI window when it receives this message.
WM_IME_COMPOSITIONFULL
wParam = 0
lParam= 0
Parameters
wParam
Not used.
lParam
Not used.

>Return Values
None.
Comments
This message is a notification, which is sent to an application by the IME user interface window and not by the IME itself. The IME uses SendMEssage to send this notification.
See Also
IMC_SETCOMPOSITONWINDOW

## WM_IME_COMPOSITIONFULL
当输入法写作窗尺寸无法再扩大时，将此消息发送给应用程序。应用程序收到该消息时应当指定如何显示输入法UI窗口。消息形式为：
``` c++
WM_IME_COMPOSITIONFULL
wParam = 0
lParam= 0
```
** 说明 **
这个消息是由输入法的窗口而不是输入法本身发送给应用程序的，输入法使用`SendMessage`来发送该通知，还可参见`IMC_SETCOMPOSITONWINDOW`。

>WM_IME_ENDCOMPOSITION
The WM_IME_ENDCOMPOSITION message is sent to an application when the IME ends composition.
WM_IME_ENDCOMPOSITION
wParam = 0
lParam= 0
Parameters
wParam
Not used.
lParam
Not used.

>Return Values
None.
Comments
When an application wants to display composition characters by themselves, it should not pass this message to the application IME UI window or to DefWindowProc. DefWindowProc processes this message to pass it to the default IME window.

## WM_IME_ENDCOMPOSITION
当输入法要中止写作窗时，向应用程序发送该消息。消息形式为：
``` c++
WM_IME_ENDCOMPOSITION
wParam = 0
lParam= 0
```
** 说明 **
如果应用程序希望自己显示写作窗，它就不应该把该消息传递给输入法窗体或`DefWindowProc`函数。`DefWindowProc`函数会将此消息传递给默认输入法窗口。

>WM_IME_SELECT
The WM_IME_SELECT message is sent to the UI window when the system is about to change the current IME.
WM_IME_SELECT
fSelect= (BOOL)wParam;
hKL= lParam;
Parameters
fSelect
TRUE if the IME is newly selected. Otherwise, it is FALSE if the IME is unselected.
hKL
Input language handle of the IME. 

>Return Values
None.
Comments
The system IME class uses this message to create a new UI window and destroy an old UI window for an application or system. DefWindowProc processes this message to pass the information to the default IME window. The default IME window then sends this message to its UI window.

## WM_IME_SELECT
当系统要改变当前输入法时，会向输入法UI窗体发送此消息。消息形式为：
``` c++
WM_IME_SELECT
fSelect= (BOOL)wParam;
hKL= lParam;
```
** 参数 **
`fSelect` 如果输入法被选入为TRUE，如果输入法被选出为FALSE。
`hKL` 输入法的HKL。
** 说明 **
系统输入法类使用该消息来创建切入的输入法UI窗体，并销毁切出的输入法UI窗体。`DefWindowProc`函数会将此信息传递给默认输入法窗体来处理。默认输入法窗体再把该消息发送给它的子窗体。

>WM_IME_STARTCOMPOSITION
The WM_IME_STARTCOMPOSITION message is sent immediately before an IME generates a composition string as a result of a user’s keystroke. The UI window opens its composition window when it receives this message.
WM_IME_STARTCOMPOSITION
wParam = 0
lParam= 0
Parameters
wParam
Not used.
lParam
Not used.

>Return Values
None.
Comments
When an application wants to display composition characters by themselves, it should not pass this message to the application IME window or to DefWindowProc. The DefWindowProc function processes this message to pass it to the default IME window.

## WM_IME_STARTCOMPOSITION
当输入法为用户按键创建写作窗时，会收到该消息。UI窗口收到该消息时应当打开它的写作窗。消息形式为：
``` c++
WM_IME_STARTCOMPOSITION
wParam = 0
lParam= 0
```
** 说明 **
如果应用程序希望自己显示写作窗，它就不应该把该消息传递给输入法窗体或`DefWindowProc`。`DefWindowProc`会把该消息传递个默认输入法窗体。

>WM_IME_NOTIFY
The WM_IME_NOTIFY message is a group of submessages that notifies an application or UI window of the IME status. 
WM_IME_NOTIFY
wSubMessage= wParam; //submessage ID
lParam= lParam; // depends on the submessage
The following topics contain the submessages classified by the value of wSubMessage. 

## WM_IME_NOTIFY
该消息是通知应用程序或输入法UI窗口的若干子消息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage= wParam; //submessage ID
lParam= lParam; // depends on the submessage
```
下面讨论wSubMessage不同取值是的子消息。

>IMN_CLOSESTATUSWINDOW
The IMN_CLOSESTATUSWINDOW message is sent when an IME is about to close a status window. 
WM_IME_NOTIFY
wSubMessage = IMN_CLOSESTATUSWINDOW;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The UI window closes the status window when it receives this message.

### IMN_CLOSESTATUSWINDOW
当输入法要关闭状态栏时发送该消息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage= wParam; //submessage ID
lParam= lParam; // depends on the submessage
```
** 说明 **
当输入法UI窗体收到该消息时会隐藏状态栏。

>IMN_OPENSTATUSWINDOW
The IMN_OPENSTATUSWINDOW message is sent when an IME is about to create a status window. An application then processes this message and displays a system window for the IME itself.
An application can obtain information about the system window by calling the ImmGetConversionStatus function.
WM_IME_NOTIFY
wSubMessage = IMN_OPENSTATUSWINDOW;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The UI window creates a status window when it receives this message. 
See Also
ImmGetConversionStatus

### IMN_OPENSTATUSWINDOW
当输入法要显示状态栏时会发送该消息。应用程序处理该消息，并显示输入法的状态栏。应用程序可以通过调用`ImmGetConversionStatus`函数来获取系统窗口的信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_OPENSTATUSWINDOW;
lParam= 0;
```
** 说明 **
当输入法UI窗体收到该消息时会显示状态栏。还可参见`ImmGetConversionStatus`。

>IMN_OPENCANDIDATE
The IMN_OPENCANDIDATE message is sent when an IME is about to open a candidate window. An application then processes this message and calls ImmGetCandidateCount and ImmGetCandidateList to display the candidate window itself.
WM_IME_NOTIFY
wSubMessage = IMN_OPENCANDIDATE;
lCandidateList= lParam;
Parameters
lCandidateList
Shows which candidate list should be updated. For example, if bit 0 is 1, the first candidate list should be updated. If bit 31 is 1, the 32nd candidate list should be updated.

>Return Values
None.
Comments
The UI window creates a candidate window when it receives this message. 
See Also
ImmGetCandidateListCount, ImmGetCandidateList, WM_IME_CHANGECANDIDATE

### IMN_OPENCANDIDATE
当输入法要显示候选窗时会发送该消息。应用程序处理该消息并调用`ImmGetCandidateCount`和`ImmGetCandidateList`函数来显示候选窗。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_OPENCANDIDATE;
lCandidateList= lParam;
```
** 参数 **
`lCandidateList` 表明应当显示哪个候选列表。例如如果bit 0被置1，则第一个候选列表会被刷新；bit 31被置1，则第32个候选列表被刷新。
** 说明 **
输入法UI窗口会在收到该消息时创建候选窗。还可参见`ImmGetCandidateListCount`, `ImmGetCandidateList`, `WM_IME_CHANGECANDIDATE`。

>IMN_CHANGECANDIDATE
The IMN_CHANGECANDIDATE message is sent when an IME is about to change the content of a candidate window. An application then processes this message to display the candidate window itself.
WM_IME_NOTIFY
wSubMessage = IMN_CHANGECANDIDATE;
lCandidateList= lParam;
Parameters
lCandidateList
Shows which candidate list should be updated. For example, if bit 0 is 1, the first candidate list should be updated. If bit 31 is 1, the 32nd candidate list should be updated.

>Return Values
None.
Comments
The UI window redraws a candidate window when it receives this message. 
See Also
ImmGetCandidateCount, ImmGetCandidateList

### IMN_CHANGECANDIDATE
当输入法要改变候选窗内容时将发送该消息。应用程序处理该消息更新候选窗内容。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_CHANGECANDIDATE;
lCandidateList= lParam;
```
** 参数 **
`lCandidateList` 表明应当显示哪个候选列表。例如如果bit 0被置1，则第一个候选列表会被刷新；bit 31被置1，则第32个候选列表被刷新。
** 说明 **
输入法UI窗口会在收到该消息时重绘候选窗。还可参见`ImmGetCandidateCount`, `ImmGetCandidateList`。

>IMN_CLOSECANDIDATE
The IMN_CLOSECANDIDATE message is sent when an IME is about to close a candidate window. An application processes this message to obtain information about the end of candidate processing. 
WM_IME_NOTIFY
wSubMessage = IMN_CLOSECANDIDATE;
lCandidateList= lParam;
Parameters
lCandidateList
Shows which candidate list should be closed. For example, if bit 0 is 1, the first candidate list should be updated. If bit 31 is 1, the 32nd candidate list should be updated.

>Return Values
None.
Comments
The UI window destroys a candidate window when it receives this message.

### IMN_CLOSECANDIDATE
当输入法要关闭候选窗时发送该消息。应用程序通过接收该消息获得关闭候选窗的信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_CLOSECANDIDATE;
lCandidateList= lParam;
```
** 参数 **
`lCandidateList` 表明应当显示哪个候选列表。例如如果bit 0被置1，则第一个候选列表会被刷新；bit 31被置1，则第32个候选列表被刷新。
** 说明 **
输入法UI窗口会在收到该消息时销毁候选窗。

>IMN_SETCONVERSIONMODE
The IMN_SETCONVERSIONMODE message is sent when the conversion mode of the Input Context is updated. When the application or UI window receives this message, either one can call ImmGetConversionStatus to obtain information about the status window.
WM_IME_NOTIFY
wSubMessage = IMN_SETCONVERSIONMODE;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The UI window redraws the status window if the status window shows the conversion mode.

### IMN_SETCONVERSIONMODE
当输入上下文的转换模式发生变化时，会发送该消息。当应用程序或输入法UI窗口收到该消息后，可以调用函数`ImmGetConversionStatus`来获得状态栏信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETCONVERSIONMODE;
lParam= 0;
```
** 说明 **
如果输入法状态栏上显示转换模式，输入法UI窗口会在收到该消息时重绘状态栏。

>IMN_SETSENTENCEMODE
The IMN_SETSENTENCEMODE message is sent when the sentence mode of the Input Context is updated. When the application or UI window receives this message, either one can call ImmGetConversionStatus to obtain information about the status window.
WM_IME_NOTIFY
wSubMessage = IMN_SETSENTENCEMODE;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The UI window redraws the status window if the status window shows the sentence mode.

### IMN_SETSENTENCEMODE
当输入上下文的句子模式发生变化时，会发送该消息。当应用程序或输入法UI窗口收到该消息后，可以调用函数`ImmGetConversionStatus`来获得状态栏信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETSENTENCEMODE;
lParam= 0;
```
** 说明 **
如果输入法状态栏上显示句子模式，输入法UI窗口会在收到该消息时重绘状态栏。

>IMN_SETOPENSTATUS
The IMN_SETOPENSTATUS message is sent when the open status of the Input Context is updated. When the application or UI window receives this message, either one can call ImmGetOpenStatus to obtain information.
WM_IME_NOTIFY
wSubMessage = IMN_SETOPENSTATUS;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The UI window redraws the status window if the status window shows the open/close status.

### IMN_SETOPENSTATUS
如果输入上下文的开-闭状态发生变化时，会发送该消息。当应用程序或输入法UI窗口收到该消息后，可以调用函数`ImmGetOpenStatus`来获得状态栏信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETOPENSTATUS;
lParam= 0;
```
** 说明 **
如果输入法状态栏上显示开-闭状态，输入法UI窗口会在收到该消息时重绘状态栏。

>IMN_SETCANDIDATEPOS
The IMN_SETCANDIDATEPOS message is sent when an IME is about to move the candidate window. An application processes this message to obtain information about the end of candidate processing.
WM_IME_NOTIFY
wSubMessage = IMN_SETCANDIDATEPOS;
lCandidateList= lParam;
Parameters
lCandidateList
Shows which candidate list should be moved. For example, if bit 0 is 1, the first candidate list should be updated. If bit 31 is 1, the 32nd candidate list should be updated.

>Return Values
None.
Comments
The UI window moves a candidate window when it receives this message.

### IMN_SETCANDIDATEPOS
如果输入法要移动候选窗，会发送该消息。应用程序处理该消息来获得候选窗的移动信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETCANDIDATEPOS;
lCandidateList= lParam;
```
** 参数 **
`lCandidateList` 描述要移动的候选列表。例如bit 0置1表示第一个候选列表应该被更新；bit 31置1表示第32个候选列表应该被更新。
** 说明 **
输入法UI窗口接收到该消息后将移动候选窗。

>IMN_SETCOMPOSITIONFONT
The IMN_SETCOMPOSITIONFONT message is sent when the font of the Input Context is updated. When the application or UI window receives this message, either one can call ImmGetCompositionFont to obtain information about the composition font.
WM_IME_NOTIFY
wSubMessage = IMN_SETCOMPOSITIONFONT;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The composition component of the UI window uses the font information by calling ImmGetCompositionFont to draw the text of the composition string.

### IMN_SETCOMPOSITIONFONT
如果输入上下文的字体发生变化，会发送该消息。应用程序或UI窗口接收到高消息可以调用`ImmGetCompositionFont`来获得写作窗的字体。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETCOMPOSITIONFONT;
lParam= 0;
```
** 说明 **
输入法UI窗口的写作窗通过调用`ImmGetCompositionFont`来获取字体信息，用于绘制写作串。


>IMN_SETCOMPOSITIONWINDOW
The IMN_SETCOMPOSITIONWINDOW message is sent when the composition form of the Input Context is updated. When the UI window receives this message, the cfCompForm of the Input Context can be referenced to obtain the new conversion mode.
WM_IME_NOTIFY
wSubMessage = IMN_SETCOMPOSITIONWINDOW;
lParam= 0;
Parameters
lParam
Not used.

>Return Values
None.
Comments
The composition component of the UI window uses cfCompForm to show the composition window.

### IMN_SETCOMPOSITIONWINDOW
当输入上下文的写作串形式发生变化时，会发送该消息。当输入法UI窗体收到该消息，可以根据输入上下文的`cfCompForm`字段来获取新的转换模式。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SETCOMPOSITIONWINDOW;
lParam= 0;
```
** 说明 **
输入法UI窗口使用`cfCompForm`来控制写作窗的显示策略。

>IMN_GUIDELINE
The IMN_GUIDELINE message is sent when an IME is about to show an error or information. When the application or UI window receives this message, either one can call ImmGetGuideLine to obtain information about the guideline. 
WM_IME_NOTIFY
wSubMessage = IMN_GUIDELINE;
lParam= 0;
Parameters
lParam
Not used. Has to be zero.

>Return Values
None.
Comments
The UI window can create an information window when it receives this message and show the information string. 
See Also
ImmGetGuideLine, GUIDELINE structure

### IMN_GUIDELINE
当输入法要显示错误信息或一般信息时，会发送该消息。应用程序或UI窗口接收到该消息，可以调用`ImmGetGuideLine`函数来获取指导信息。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_GUIDELINE;
lParam= 0;
```
** 说明 **
输入法UI窗口在收到该消息时可以创建一个信息窗口来显示信息串。

>IMN_SOFTKBDDESTROYED
The IMN_SOFTKBDDESTROYED message is sent to the UI window when the soft keyboard is destroyed.
WM_IME_NOTIFY
wSubMessage = IMN_SOFTKBDDESTROYED;
lParam= 0;
Parameters
lParam
Not used. Has to be zero.

>Return Values
None.

### IMN_SOFTKBDDESTROYED
当销毁软键盘时，该消息被发送到UI窗口。消息形式为：
``` c++
WM_IME_NOTIFY
wSubMessage = IMN_SOFTKBDDESTROYED;
lParam= 0;
```

>WM_IME_KEYDOWN and WM_IME_KEYUP
The WM_IME_KEYDOWN and WM_IME_KEYUP messages are sent to an application when an IME needs to generate a WM_KEYDOWN or WM_KEYUP message. The value sent is the same as the original Windows WM_KEYDOWN and WM_KEYUP value (English version).
WM_IME_KEYDOWN / WM_IME_KEYUP
nVirtKey = (int) wParam; // virtual-key code 
lKeyData = lParam; // key data 
Parameters 
nVirtKey 
Value of wParam. Specifies the virtual key code of the nonsystem key. 
lKeyData 
Value of lParam. Specifies the repeat count, scan code, extended key flag, context code, previous key state flag, and transition state flag. It is the same as for the original Windows WM_KEYDOWN and WM_KEYUP messages

>Return Values
None.
Comments
An application can handle this message the same way as the WM_KEYDOWN and WM_KEYUP message. Otherwise, DefWindowProc processes this message to generate a WM_KEYDOWN or WM_KEYUP message with the same wParam and lParam parameters. This message is usually generated by the IME to maintain message order.

### WM_IME_KEYDOWN 和 WM_IME_KEYUP
当输入法需要产生一个WM_KEYDOWN或WM_KEYUP消息时，会向应用程序发送该消息。消息的值与Windows原始的WM_KEYDOWN和WM_KEYUP一致。消息形式为：
``` c++
WM_IME_KEYDOWN / WM_IME_KEYUP
nVirtKey = (int) wParam; // virtual-key code 
lKeyData = lParam; // key data 
```
** 参数 **
`nVirtKey` 指定非系统按键的虚拟键盘码
`lKeyData` 指定重复次数、扫描码、扩展标志、上下文码、前一次按键状态标志、转义状态标志。该值与Windows原始的WM_KEYDOWN和WM_KEYUP消息一致。
** 说明 **
应用程序可以像处理WM_KEYDOWN和WM_KEYUP那样处理该消息。`DefWindowProc`处理该消息时会产生一个同样wParam/lParam参数的WM_KEYDOWN或WM_KEYUP消息。该消息通常由输入法产生，以保持消息秩序。

>WM_IME_CHAR
The WM_IME_CHAR message is sent to an application when the IME gets a character of the conversion result. The value that is sent is similar to the original Windows WM_CHAR (English version). The difference is that wParam can include two bytes of character. 
WM_IME_CHAR
wCharCode = wParam;
lKeyData = lParam;
Parameters
wCharCode
Includes two bytes for an FE character. For NT Unicode application, it includes one Unicode character.
lKeyData
Same as the original Windows WM_CHAR (English Version). Following are the available bits and their description.
Value
Description

> 0 – 15
Repeat count. Since the first byte and second byte are continuous, this is always 1.
16 – 23
Scan Code. Scan code for a complete FE character.
24 – 28
Not used.
29
Context code.
31
Conversion state.


>Return Values
None.
Comments
If the application does not handle this message, the DefWindowProc function processes this message to generate WM_CHAR messages. If the application is not Unicode based and wCharCode includes 2 bytes of DBCS character, the DefWindowProc function will generate two WM_CHAR messages, each message containing 1 byte of the DBCS character. If the message just includes an SBCS character, DefWindowProc generates only one WM_CHAR message.

## WM_IME_CHAR
当输入法获得一个字符串换结果时，会发送该消息到应用程序。该消息的值与Windows原始的WM_CHAR保持一致，不同点在于wParam可以包含两个字节的字符。消息形式为：
``` c++
WM_IME_CHAR
wCharCode = wParam;
lKeyData = lParam;
```
** 参数 **
`wCharCode` 表示一个2字节的FE字符，对于NT Unicode应用程序，这是一个Unicode字符。
`lKeyData` 与Windows原始的WM_CHAR含义一致。下面是它不同位的含义：
* `0-15` 重复次数，通常为1
* `16-23` 扫描码
* `24-28` 保留未使用
* `29` 上下文码
* `31` 转换状态
** 说明 **
如果应用程序不处理该消息，`DefWindowProc`函数会产生一个WM_CHAR消息。如果应用程序不是基于Unicode的，wCharCode包含2字节的DBCS字符，`DefWindowProc`函数将产生2个WM_CHAR消息，每个消息包含1字节的DBCS字符。如果消息仅包含一个SBCS字符，则`DefWindowProc`仅产生1个WM_CHAR消息。

>VK_PROCESSKEY
The VK_PROCESSKEY message is sent to an application as a wParam of WM_KEYDOWN or WM_KEYUP. When this virtual key is generated, either the real virtual key is saved in the Input Context or the messages that were generated by IME are stored in the Input Context. The system either restores the real virtual key or posts the messages that are stored in the message buffer of the Input Context.
WM_KEYDOWN /WM_KEYUP
wParam = VK_PROCESSKEY;
lParam= 1;
Parameters
lParam
Must be 1.

## VK_PROCESSKEY
这其实是一个WM_KEYDOWN或WM_KEYUP消息，只是把wParam置为VK_PROCESSKEY。该虚拟消息产生时，要么虚拟键盘码会被保存到输入上下文中，要么有输入法产生的这个消息会被保存到输入上下文中。系统则要么恢复该虚拟键盘码，要么发送该消息。消息形式为：
``` c++
WM_KEYDOWN /WM_KEYUP
wParam = VK_PROCESSKEY;
lParam= 1;
```

>INDICM_SETIMEICON
This message is sent to the Indicator window when the IME wants to change the icon for System Pen icon. This message can be accepted when the selected hKL of the focused window is the same as the sender IME.
INDICM_SETIMEICON
nIconIndex = wParam;
hKL = lParam;
Parameters
nIconIdex
Index for the icon resource of the IME file. If this value is (-1), the Indicator restores the original icon provided by the system.
lKey
hKL that is the sender IME.

>Return Values
A nonzero value indicates failure. Otherwise, zero is returned.
Comments
Due to the internal design requirement in the task bar manager, the IME must use PostMessage for INDICM_xxx messages.

### INDICM_SETIMEICON
如果输入法要改变系统的笔形图标时，会发送该消息到输入法指示窗。当焦点窗口的输入法HKL和发送消息的输入法一致时，该消息才会被接受。消息形式为：
``` c++
INDICM_SETIMEICON
nIconIndex = wParam;
hKL = lParam;
```
** 参数 **
`nIconIdex` IME文件的资源中的icon序号，如果为-1，输入法指示器将恢复原始图标
`lKey` 发送方输入法的HKL
** 返回值 **
成功返回0，失败返回非0。
** 说明 **
处于任务栏管理器的内部需要，输入法必须使用`PostMessage`来发送`INDICM_xxx`消息。

>INDICM_SETIMETOOLTIPS
This message is sent to the Indicator window when the IME wants to change the Tooltip string for the System Pen icon. This message can be accepted when the selected hKL of the focused window is the same as the sender IME.
INDICM_SETIMETOOLTIPS
hAtom = wParam;
hKL = lParam;
Parameters
hAtom
Global ATOM value for the Tooltip string. If this value is (-1), the Indicator restores the original tips provided by the system.
lKey
hKL that is the sender IME.

>Return Values
A nonzero indicates failure. Otherwise, zero is returned.
Comments
Due to the internal design requirement in the task bar manager, the IME must use PostMessage for INDICM_xxx messages. The global ATOM must be retrieved by GlobalAddAtom or GlobalFindAtom.

### INDICM_SETIMETOOLTIPS
当输入法希望修改系统笔形图标的提示文字时，会发送该消息。当焦点窗口的输入法HKL和发送消息的输入法一致时，该消息才会被接受。消息形式为：
``` c++
INDICM_SETIMETOOLTIPS
hAtom = wParam;
hKL = lParam;
```
** 参数 **
`hAtom` 提示文字的全局ATOM值。如果该值为-1，输入法指示器将恢复原值。
`lKey` 发送方输入法的HKL
** 返回值 **
成功返回0，失败返回非0。
** 说明 **
处于任务栏管理器的内部需要，输入法必须使用`PostMessage`来发送`INDICM_xxx`消息。全局ATOM值必须通过`GlobalAddAtom`或`GlobalFindAtom`来获得。

>INDICM_REMOVEDEFAULTMENUITEMS
This message is sent to the Indicator window when the IME wants to remove the default menu items of the System Pen icon.
INDICM_REMOVEDEFAULTMENUITEMS
wValue = wParam;
hKL = lParam;
Parameters
wValue
wValue is a combination of the following bits.
Value
Description

>RDMI_LEFT
Removes the menu items of the left click menu.
RDMI_RIGHT
Removes the menu items of the right click menu.

>If wValue is zero, all default menu items are restored.
lKey
hKL that is the sender IME.

>Return Values
A nonzero indicates failure. Otherwise, zero is returned.
Comments
Due to the internal design requirement in the task bar manager, the IME must use PostMessage for INDICM_xxx messages. 

### INDICM_REMOVEDEFAULTMENUITEMS
当输入法要删除系统笔形图标的默认菜单时，会发送该消息。。消息形式为：
``` c++
INDICM_REMOVEDEFAULTMENUITEMS
wValue = wParam;
lKL = lParam;
```
** 参数 **
`wValue` 该值为如下位的组合：
* `RDMI_LEFT` 删除左键菜单
* `RDMI_RIGHT` 删除右键菜单
如果`wValue`为0，所有默认菜单将被恢复。
`lKey` 发送方输入法的HKL
** 返回值 **
成功返回0，失败返回非0。
** 说明 **
处于任务栏管理器的内部需要，输入法必须使用`PostMessage`来发送`INDICM_xxx`消息。全局ATOM值必须通过`GlobalAddAtom`或`GlobalFindAtom`来获得。

# 输入法界面函数
>IMEs are provided as dynamic-link libraries (DLLs). The Input Method Manager (IMM) should handle all installed IMEs. Because IMEs are changeable at run time without rebooting, the IMM will have a structure to maintain all the entry points of each IME.
The following topics contain all the common IME functions. These functions should not be called by an application directly.

输入法的IME文件实际是一个动态链接库（DLL）文件。输入法管理器（IMM）负责处理所有已安装的输入法。无需重启机器，输入法可以在运行时发生变化，IMM使用一个数据结构来保存每个输入法的所有入口。

下面就来介绍输入法的通用函数，这些函数应该只被IMM调用，而不应被应用程序直接调用。

> For Windows NT 4.0 and Windows 2000
BOOL
    ImeInquire(
    LPIMEINFO lpIMEInfo,
    LPTSTRlpszWndClass,
    DWORD dwSystemInfoFlags
   )
Parameters
lpIMEInfo
Pointer to the IME info structure.
lpszWndClass
Window class name that should be filled by the IME. This name is the IME’s UI class. 
dwSystemInfoFlags
Varying system information provided by the system. The following flags are provided.
Flag
Description
IME_SYSINFO_WINLOGON
Tells the IME that the client process is the Winlogon process. The IME should not allow users to configure the IME when this flag is specified.
IME_SYSINFO_WOW16
Tells the IME that the client process is a 16-bit application.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

## ImeInquire
``` c++
BOOL ImeInquire(
    LPIMEINFO lpIMEInfo,
    LPTSTR lpszWndClass,
    DWORD dwSystemInfoFlags
   )
```
** 参数 **
`lpIMEInfo` 指向IMEInfo结构体
`lpszWndClass` 输入法应通过此参数返回输入法UI窗体的窗体类名
`dwSystemInfoFlags` 系统通过此参数提供系统信息，这是一些标志位组合，可能的取值有：
* `IME_SYSINFO_WINLOGON` 告诉输入法当前宿主进程是Winlogon。此时应注意，输入法应禁止修改配置，这是因为大多数输入法配置如全/双拼，候选个数等都是与Windows用户绑定的，此时还未登录系统，也就没有对应的Windows用户。还要特别注意的是，不要让输入法有任何机会启动explorer进程，这会让用户不必登录而能访问系统文件。
* `IME_SYSINFO_WOW16` 告诉输入法当前宿主进程是一个16位应用。

** 返回值 **
成功返回TRUE，否则返回FALSE。

>ImeConversionList
The ImeConversionList function obtains a converted result list from another character or string.
DWORD
    IMEConversionList(
    HIMC hIMC,
    LPCTSTRlpSrc,
    LPCANDIDATELIST lpDst,
    DWORD dwBufLen,
    UINT uFlag
   )
Parameters
hIMC
Input context handle.
lpSrc
Character string to be converted.
lpDst
Pointer to the destination buffer.
dwBufLen
Length of the destination buffer.
uFlag
Currently can be one of the following three flags.
Flag
Description

>GCL_CONVERSION
Specifies the reading string to the lpSrc parameter. The IME returns the result string in the lpDst parameter.
GCL_REVERSECONVERSION
Specifies the result string in the lpSrc parameter. The IME returns the reading string in the lpDst parameter.
GCL_REVERSE_LENGTH
Specifies the result string in the lpSrc parameter. The IME returns the length that it can handle in GCL_REVERSECONVERSION. For example, an IME cannot convert a result string with a sentence period to a reading string. As a result, it returns the string length in bytes without the sentence period.

>Return Values
The return value is the number of bytes of the result string list.
Comments
This function is intended to be called by an application or an IME without generating IME-related messages. Therefore, an IME should not generate any IME-related messages in this function.

## ImeConversionList
该函数将一个字符串转换成结果串，并返回该结果串。
``` c++
DWORD IMEConversionList(
    HIMC hIMC,
    LPCTSTRlpSrc,
    LPCANDIDATELIST lpDst,
    DWORD dwBufLen,
    UINT uFlag
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`lpSrc` 待转换的字串
`lpDst` 指向目标buffer
`dwBufLen` 目标buffer的尺寸
`uFlag` 可由如下标志组合而成：
* `GCL_CONVERSION` 指定lpSrc中为读入串，输入法在lpDst中返回结果串。
* `GCL_REVERSECONVERSION` 指定lpSrc中为结果串，输入法在lpDst中返回读入串。
* `GCL_REVERSECONVERSION` 指定lpSrc中为结果串，输入法返回在`GCL_REVERSECONVERSION`可以处理的长度。比如，如果输入法无法转换一个结果串中的某个句段到阅读串，它将返回不包含词句段的阅读串长度。

** 返回值 **
返回结果串列表的字节数。
** 说明 **
应用程序或输入法调用该函数不会产生输入法相关的消息。因此输入法不应当在此函数中生成任何与输入法相关的消息。

>ImeConfigure
The ImeConfigure function provides a dialog box to use to request optional information for an IME.
BOOL
    ImeConfigure(
    HKL hKL,
    HWND hWnd,
    DWORD dwMode,
    LPVOID lpData
   )
Parameters
hKL
Input language handle of this IME.
hWnd
Parent window handle.
dwMode
Mode of dialog. The following flags are provided.
Flag
Description

>IME_CONFIG_GENERAL
Dialog for general purpose configuration. 
IME_CONFIG_REGWORD
Dialog for register word. 
IME_CONFIG_SELECTDICTIONARY
Dialog for selecting the IME dictionary. 

>lpData
Pointer to VOID, which will be a pointer to the REGISTERWORD structure only if dwMode==IME_CONFIG_REGISTERWORD. Otherwise, lpData should just be ignored.
This also can be NULL with the IME_CONFIG_REGISTER mode, if no initial string information is given.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
Comments
An IME checks lpData in the following way in the pseudo code.
if (dwmode != IME_CONFIG_REGISTERWORD)
    {
// Does original execution
    }
else if (IsBadReadPtr(lpdata, sizeof(REGISTERWORD))==FALSE)
    {
 
>if (IsBadStringPtr(PREGISTERWORD(lpdata)->lpReading, (UINT)-1)==FALSE)
    {
// Set the reading string to word registering dialogbox
    }
if (IsBadStringPtr(PREGISTERWORD(lpdata)->lpWord, (UINT)-1)==FALSE)
    {
// Set the word string to word registering dialogbox
    }
    }
 

## ImeConfigure
该函数会弹出一个用于修改输入法设置的对话框。
``` c++
BOOL ImeConfigure(
    HKL hKL,
    HWND hWnd,
    DWORD dwMode,
    LPVOID lpData
   )
```
** 参数 **
`hKL` 输入法的输入语言句柄（我称作键盘布局句柄，Keyboard Layout Handle）
`hWnd` 父窗体句柄
`dwMode` 对话框模式，可由如下标志组合而成：
* `ME_CONFIG_GENERAL` 通用目的对话框配置
* `IME_CONFIG_REGWORD` 针对注册字的对话框
* `IME_CONFIG_SELECTDICTIONARY` 选择输入法词典的对话框
`lpData` 仅当dwMode==IME_CONFIG_REGISTERWORD时为指向**REGISTERWORD**结构体的指针，其他情况下lpData应当被忽略；如果没有给出初始字串，该值也可以为NULL。
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 说明 **
输入法应当按照如下模式检查lpData：
``` c++
if (dwmode != IME_CONFIG_REGISTERWORD){
  // Does original execution
}else if (IsBadReadPtr(lpdata, sizeof(REGISTERWORD))==FALSE){
  if (IsBadStringPtr(PREGISTERWORD(lpdata)->lpReading, (UINT)-1)==FALSE){
    // Set the reading string to word registering dialogbox
  }
  if (IsBadStringPtr(PREGISTERWORD(lpdata)->lpWord, (UINT)-1)==FALSE){
    // Set the word string to word registering dialogbox
  }
}
```

>ImeDestroy
The ImeDestroy function terminates the IME itself. 
BOOL
    ImeDestroy(
    UINT uReserved
   )
Parameters
uReserved
Reserved. Currently, it should be zero. For this version, the IME should return FALSE if it is not zero.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

## ImeDestroy
该函数用于终止输入法。
``` c++
BOOL ImeDestroy(UINT uReserved)
```
** 参数 **
`uReserved` 保留字段，应当为0。如果不为0，输入法应返回FALSE
** 返回值 **
成功返回TRUE，否则返回FALSE。

>ImeEscape
The ImeEscape function allows an application to access capabilities of a particular IME not directly available though other IMM functions. This is necessary mainly for country-specific functions or private functions in the IME. 
LRESULT
    ImeEscape(
    HIMC hIMC,
    UINT uEscape,
    LPVOID lpData
   )
Parameters
hIMC
Input context handle
uEscape
Specifies the escape function to be performed.
lpData
Points to the data required for the specified escape.
The ImeEscape function supports the following escape functions.
uEscape
Meaning

>IME_ESC_QUERY _SUPPORT
Checks for implementation. If this escape is not implemented, the return value is zero.
IME_ESC_RESERVED_FIRST
Escape that is between IME_ESC_RESERVED_FIRST and IME_ESC_RESERVED_LAST is reserved by the system.
IME_ESC_RESERVED_LAST
Escape that is between IME_ESC_RESERVED_FIRST and IME_ESC_RESERVED_LAST is reserved by the system.
IME_ESC_PRIVATE_FIRST
Escape that is between IME_ESC_PRIVATE_FIRST and IME_ESC_PRIVATE_LAST is reserved for the IME. The IME can freely use these escape functions for its own purposes.
IME_ESC_PRIVATE_LAST
Escape that is between IME_ESC_PRIVATE_FIRST and IME_ESC_PRIVATE_LAST is reserved for the IME. The IME can freely use these escape functions for its own purposes. 
IME_ESC_SEQUENCE_TO_
INTERNAL
Escape that is Chinese specific. An application that wants to run under all Far East platforms should not use this. It is for the Chinese EUDC editor. The *(LPWORD)lpData is the sequence code, and the return value is the character code for this sequence code. Typically, the Chinese IME will encode its reading character codes into sequence 1 to n.
IME_ESC_GET_EUDC_
DICTIONARY
Escape that is Chinese specific. An application that wants to run under all Far East platforms should not use this. It is for the Chinese EUDC editor. On return from the function, the (LPTSTR)lpData is filled with the full path file name of the EUDC dictionary. The size of this buffer pointed by lpData should be greater or egual to MAX_PATH * sizeof(TCHAR). Note: Windows 95/98 and Windows NT 4.0 EUDC editor expect IMEs just use the buffer up to 80*sizeof(TCHAR).  
IME_ESC_SET_EUDC_
DICTIONARY
Sets the EUDC dictionary file. On input, the lpData parameter is the pointer to a null-terminated string specifying the full path. For use by the Chinese EUDC editor; do not use in other applications.
IME_ESC_MAX_KEY
Escape that is Chinese specific. An application that wants to run under all Far East platforms should not use this. It is for the Chinese EUDC editor. The return value is the maximum keystrokes for a EUDC character.
IME_ESC_IME_NAME
Escape that is Chinese specific. An application that wants to run under all Far East platforms should not use this. It is for the Chinese EUDC editor. On return from the function, the (LPTSTR) is the IME name to be displayed on the EUDC editor. The size of this buffer pointed to by lpData should be greater or equal to 16 * sizeof(TCHAR).
IME_ESC_SYNC_HOTKEY
Escape that is (Traditional) Chinese specific. An application that wants to run under all Far East platforms should not use this. It is for synchronizing between different IMEs. The input parameter *(LPDWORD)lpData is the IME private hot key ID. If this ID is zero, this IME should check every private hot key ID it concerns.
IME_ESC_HANJA_MODE
Escape that is Korean specific. An application that wants to run under all Far East platforms should not use this. It is for conversion from Hangeul to Hanja. The input parameter (LPSTR)lpData is filled with Hangeul characters that will be converted to Hanja and its null-terminated string. When an application wants to convert any Hangeul character to a Hanja character by using the same method as the Hanja conversion when the composition character is present, the application only needs to request this function. The IME will then set itself as the Hanja conversion mode.
IME_ESC_GETHELPFILENAME
Escape that is the name of the IME’s help file. On return from the function, the (LPTSTR)lpData is the full path file name of the IME’s help file. The path name should be less than MAX_PATH * sizeof(TCHAR). This is added to Windows 98 and Windows 2000. Note: Windows 98 expects the path length is less than 80 TCHARs. 
IME_ESC_PRIVATE_HOTKEY
lpdata points to a DWORD that contains the hot key ID (in the range of IME_HOTKEY_PRIVATE_FIRST and IME_HOTKEY_PRIVATE_LAST). After the system receives the hot key request within this range, the IMM will dispatch it to the IME using the ImeEscape function. Note: Windows® 95 does not support this escape.

>Return Values
If the function fails, the return value is zero. Otherwise, the return value depends on each escape function.
Comments
Parameter validation should be inside each escape function for robustness.
When uEscape is IME_ESC_QUERY _SUPPORT, lpData is the pointer to the variable that contains the IME escape value. Following is an example that can be used to determine if the current IME supports IME_ESC_GETHELPFILENAME.
DWORD dwEsc = IME_ESC_GETHELPFILENAME;
LRESULT lRet = ImmEscape(hKL, hIMC, IME_ESC_QUERYSUPPORT, (LPVOID)&dwEsc);
See Also
ImmEscape

## ImeEscape
该函数允许应用程序不必通过IMM函数而访问某些特定输入法的能力。对于某些特定国家语言的功能或者某些输入法的私有功能，这种能力是必要的。
``` c++
LRESULT ImeEscape(
    HIMC hIMC,
    UINT uEscape,
    LPVOID lpData
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`uEscape` 指定要执行的转义功能
`lpData` 指向特定转义功能需要的数据
该函数支持如下转移功能：
* `IME_ESC_QUERY _SUPPORT` 检查实现，如果该转移功能未实现，返回0
* `IME_ESC_RESERVED_FIRST` 转义定义在`IME_ESC_RESERVED_FIRST`和`IME_ESC_RESERVED_LAST`之间的系统保留功能
* `IME_ESC_RESERVED_LAST` 同上
* `IME_ESC_PRIVATE_FIRST` 转义定义在`IME_ESC_PRIVATE_FIRST`和`IME_ESC_PRIVATE_LAST`之间的输入法保留功能。输入法可以自由使用这些转义功能。
* `IME_ESC_PRIVATE_LAST` 同上
* `IME_ESC_SEQUENCE_TO_INTERNAL` 和中文有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能。这是为中文的EUDC准备的。lpData指向句子的编码，返回值则为该句子的符号码。例如，中文输入法会将读入字符串编码为1到n个句子。
* `IME_ESC_GET_EUDC_DICTIONARY` 和中文有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能。仅适用于中文EUDC。该函数在lpData中返回EUDC词典的路径名，需要注意lpData的尺寸应不小于`MAX_PATH * sizeof(TCHAR)`。
* `IME_ESC_SET_EUDC_DICTIONARY` 设置EUDC文件，lpData指向指定的文件路径。仅适用于中文EUDC。
* `IME_ESC_MAX_KEY` 和中文有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能。仅适用于中文EUDC。返回值为EUDC字符最大的按键次数。
* `IME_ESC_IME_NAME` 和中文有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能，仅适用于中文EUDC。函数会在lpData中返回输入法输入法名字，lpData的尺寸不小于`16 * sizeof(TCHAR)`。
* `IME_ESC_SYNC_HOTKEY` 和繁体中文有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能。用于同步不同输入法lpData是输入法的私有热键ID，如果该ID为0，输入法应当检查它关注的每个热键ID。
* `IME_ESC_HANJA_MODE` 和韩语有关的转义功能。如果应用程序系统运行在所有中东语言平台下，就不要使用该转义功能。用于从韩语到汉字的转换。lpData指向待转换的以0结尾的韩文。
* `IME_ESC_GETHELPFILENAME` 获取输入法的帮助文件。该函数会在lpData中返回输入法帮助文件的全路径名，lpData的大小不应小于`MAX_PATH * sizeof(TCHAR)`。
* `IME_ESC_PRIVATE_HOTKEY` lpData指向一个包含热键ID（范围从IME_HOTKEY_PRIVATE_FIRST到IME_HOTKEY_PRIVATE_LAST）的DWORD类型的数据。系统收到此范围内的热键请求后，IMM会使用ImeEscape函数将它发送给输入法。

** 返回值 **
失败返回0；否则根据每个转移功能返回不同的值。
** 说明 **
在每个转移功能内部要注意检查参数的有效性，以确保该函数健壮。

当`uEscape`为` IME_ESC_QUERY _SUPPORT`时，lpData指向包含输入法转义值的变量。下面是检查当前输入法是否支持`IME_ESC_GETHELPFILENAME`的代码例程：
``` c++
DWORD dwEsc = IME_ESC_GETHELPFILENAME;
LRESULT lRet = ImmEscape(hKL, hIMC, IME_ESC_QUERYSUPPORT, (LPVOID)&dwEsc);
```
** EUDC** ：end-user-defined characters即用户自造字。
还可参见ImmEscape。

>ImeSetActiveContext
The ImeSetActiveContext function notifies the current IME active Input Context.
BOOL
    ImeSetActiveContext(
    HIMC hIMC,
    BOOL fFlag
   )
Parameters
hIMC
Input context handle.
fFlag
Two flags are provided. TRUE indicates activated and FALSE indicates deactivated. 

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
Comments
The IME is informed by this function about a newly selected Input Context. The IME can carry out initialization, but it is not required.
See Also
ImeSetActiveContext

## ImeSetActiveContext
该函数通知当前输入法激活上下文。
``` c++
BOOL ImeSetActiveContext(
    HIMC hIMC,
    BOOL fFlag
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`hFlag` TRUE表示激活，FALSE表示deactivated。
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 说明 **
当输入法通过该函数收到被激活的通知，次数输入法可以执行一些初始化工作。
还可参见ImeSetActiveContext。

>ImeProcessKey
The ImeProcessKey function preprocesses all the keystrokes given through the IMM and returns TRUE if that key is necessary for the IME with a given Input Context.
BOOL
    ImeProcessKey(
    HIMC hIMC,
    UINT uVirKey,
    DWORD lParam,
    CONST LPBYTE lpbKeyState
   )
Parameters
hIMC
Input context handle
uVirKey
Virtual key to be processed.
lParam
lParam of key messages.
lpbKeyState
Points to a 256-byte array that contains the current keyboard state. The IME should not modify the content of the key state.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
Comments
The system decides whether the key is handled by IME or not by calling this function. If the function returns TRUE before the application gets the key message, the IME will handle the key. The system will then call the ImeToAsciiEx function. If this function returns FALSE, the system recognizes that the key will not be handled by the IME and the key message will be sent to the application.
For IMEs that support IME_PROP_ACCEPT_WIDE_VKEY on Windows 2000, ImeProcessKey will receive full 32 bit value for uVirKey, which is injected by using SendInput API through VK_PACKET. uVirKey will include 16-bit Unicode in hiword even the IME may be ANSI version. 
For IMEs that do not support IME_PROP_ACCEPT_WIDE_VKEY, Unicode IME's ImeProcessKey will receive VK_PACKET with zero'ed hiword. Unicode IME still can return TRUE so ImeToAsciiEx will be called with the injected Unicode. ANSI IME's ImeProcessKey will not receive anything. The injected Unicode will be discarded if the ANSI IME is open. If the ANSI IME is closed, the injected Unicode message will be posted to application's queue immediately.

## ImeProcessKey
该函数用于预处理经过IMM的所有按键，如果输入法要处理该按键，则返回TRUE，否则返回FALSE。
``` c++
BOOL ImeProcessKey(
    HIMC hIMC,
    UINT uVirKey,
    DWORD lParam,
    CONST LPBYTE lpbKeyState
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`uVirKey` 待处理的按键虚拟键盘码
`lpbKeyState` 指向一个256字节的数组，该数组包含键盘当前的状态。输入法不要改变该数组的内容。
** 返回值 **
成功返回TRUE，否则返回FALSE。
** 说明 **
系统通过调用该函数来决定是否要处理一个按键。如果该函数返回TRUE，输入法将会处理该按键，紧接着系统将调用`ImeToAsciiEx`函数。如果该函数返回FALSE，系统认为输入法不处理该按键，键盘消息将被发送给应用程序。

在Win2000下，对于支持IME_PROP_ACCEPT_WIDE_VKEY的输入法，ImeProcessKey将对uVirKey接收全32位值，该值是使用带VK_PACKET参数的SendInput函数注入的值。即使输入法是ANSI版本，uVirKey也会在高16位包含16位Unicode。

对于不支持IME_PROP_ACCEPT_WIDE_VKEY的输入法，Unicode版本的输入法的ImeProcessKey函数将接收高16位为0的VK_PACKET，Unicode版本的输入法依然返回TRUE，以便ImeToAsciiEx将被调用来处理该injected Unicode。ANSI版本的输入法的ImeProcessKey将不接受任何调用，即使输入法处于开启的状态，injected Unicode也会被抛弃，如果输入法关闭，该injected Unicode消息将立刻被发送给应用程序消息队列。

>NotifyIME
The NotifyIME function changes the status of the IME according to the given parameters.
BOOL
    NotifyIME(
    HIMC hIMC,
    DWORD dwAction,
    DWORD dwIndex,
    DWORD dwValue
   )
Parameters
hIMC
Input context handle.
dwAction
Following are the context items that an application can specify in the dwAction parameter.
Context Item
Description

>NI_OPENCANDIDATE 
Application has the IME open the candidate list. If the IME opens the candidate list, the IME sends a WM_IME_NOTIFY (subfunction is IMN_OPENCANDIDATE) message.

>dwIndex
Index of the candidate list to be opened.

>dwValue
Not used.
NI_CLOSECANDIDATE
Application has the IME close the candidate list. If the IME closes the candidate list, the IME sends a WM_IME_NOTIFY (subfunction is IMN_CLOSECANDIDATE) message.

>dwIndex
Index of the candidate list to be closed.

>dwValue
Not used.
NI_SELECTCANDIDATESTR
Application selects one of the candidates.

>dwIndex
Index of the candidate list to be selected.

>dwValue
Index of the candidate string in the selected candidate list.
NI_CHANGECANDIDATELIST
Application changes the currently selected candidate.

>dwIndex
Index of the candidate list to be selected.

>dwValue
Not used.
NI_SETCANDIDATE_PAGESTART
Application changes the page starting index of the candidate list.

>dwIndex
Index of the candidate list to be changed.

>dwValue
New page start index.
NI_SETCANDIDATE_PAGESIZE
Application changes the page size of the candidate list.

>dwIndex
Index of the candidate list to be changed.

>dwValue
New page size.
NI_CONTEXTUPDATED
Application or system updates the Input Context.

>dwIndex
When the value of dwValue is IMC_SETCONVERSIONMODE, dwIndex is the previous conversion mode.
When the value of dwValue is IMC_SETSENTENCEMODE, dwIndex is the previous sentence mode.
For any other dwValue, dwIndex is not used.

>dwValue
One of following values used by the WM_IME_CONTROL message:
IMC_SETCANDIDATEPOS
IMC_SETCOMPOSITIONFONT
IMC_SETCOMPOSITIONWINDOW
IMC_SETCONVERSIONMODE
IMC_SETSENTENCEMODE
IMC_SETOPENSTATUS
NI_COMPOSITIONSTR
Application changes the composition string. This action takes effect only when there is a composition string in the Input Context.

>dwIndex
The following values are provided for dwIndex:
CPS_COMPLETE
To determine the composition string as the result string.
CPS_CONVERT
To convert the composition string.
CPS_REVERT
To revert the composition string. The current composition string will be canceled and the unconverted string will be set as the composition string.
CPS_CANCEL 
To clear the composition string and set the status as no composition string.

>dwValue
Not used.

>dwIndex
Dependent on uAction.
dwValue
Dependent on uAction.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.
See Also
ImmNotifyIME

## NotifyIME
该函数会根据参数改变输入法状态。
``` c++
BOOL NotifyIME(
    HIMC hIMC,
    DWORD dwAction,
    DWORD dwIndex,
    DWORD dwValue
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`dwIndex`和`dwValue`将依赖`dwAction`的值
`dwAction` 应用程序可指定的上下文选项，下面是该值的取值范围：
* `NI_OPENCANDIDATE` 应用程序让输入法打开候选列表，如果输入法打开了候选列表，输入法会发送一个WM_IME_NOTIFY(子功能为IMN_OPENCANDIDATE)消息。此时`dwIndex`表示待打开的候选列表序号，`dwValue`未使用。
* `NI_CLOSECANDIDATE` 应用程序让输入法关闭候选列表，如果输入法关闭了候选列表，输入法发送一个WM_IME_NOTIFY（子功能为IMN_CLOSECANDIDATE）消息。此时`dwIndex`表示待关闭的候选列表序号，`dwValue`未使用。
* `NI_SELECTCANDIDATESTR` 应用程序选择一个候选。此时`dwIndex`表示被选中的候选序号；`dwValue`表示被选中的候选串。
* `NI_CHANGECANDIDATELIST` 应用程序修改当前选中的候选。此时`dwIndex`表示将被选择的候选序号；`dwValue`未使用。
* `NI_SETCANDIDATE_PAGESTART` 应用程序修改候选列表的起始页。此时`dwIndex`表示被修改的候选列表序号；`dwValue`表示新页中的起始序号。
* `NI_SETCANDIDATE_PAGESIZE` 应用程序修改候选列表的页数。此时`dwIndex`表示待修改的候选列表序号；`dwValue`表示新页尺寸。
* `NI_CONTEXTUPDATED` 应用程序或系统修改输入上下文。此时，
  - `dwIndex`的含义为：当`dwValue`为IMC_SETCONVERSIONMODE时`dwIndex`表示前一个转换模式；当`dwValue`为IMC_SETSENTENCEMODE时`dwIndex`表示前一个句子模式；其他情况`dwIndex`未使用
  - `dwValue`为WM_IME_CONTROL消息使用的如下值之一：
    IMC_SETCANDIDATEPOS
    IMC_SETCOMPOSITIONFONT
    IMC_SETCOMPOSITIONWINDOW
    IMC_SETCONVERSIONMODE
    IMC_SETSENTENCEMODE
    IMC_SETOPENSTATUS
* `NI_COMPOSITIONSTR` 应用程序修改写作串。该动作仅在输入上下文中有写作串时才会生效。此时，
  - `dwIndex`为如下值：
    CPS_COMPLETE 要把写作串转换成结果串。
    CPS_CONVERT 要转换写作串
    CPS_REVERT 要回复写作串。当前写作串将被取消，未转换的字串将被设置为写作串。
    CPS_CANCEL 要清除写作串，将输入法处于没有写作串的状态。
  - `dwValue`未使用

** 返回值  **
成功返回TRUE，否则返回FALSE。
还可参见ImmNotifyIME。

>ImeSelect
The ImeSelect function is used to initialize and uninitialize the IME private context.
BOOL
    ImeSelect(
    HIMC hIMC,
    BOOL fSelect
   )
Parameters
hIMC
Input context handle
fSelect
Two flags are provided. TRUE indicates initialize and FALSE indicates uninitialize (free resource). 

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

## ImeSelect
该函数用于初始化或者析构输入法的私有上下文。
``` c++
BOOL ImeSelect(
    HIMC hIMC,
    BOOL fSelect
   )
```
** 参数 **
`hIMC` 输入上下文句柄
`fSelect` TRUE表示初始化，FALSE表示析构。
** 返回值 **
成功返回TRUE，否则返回FALSE。

>ImeSetCompositionString
The ImeSetCompositionString function is used by an application to set the IME composition string structure with the data contained in the lpComp or lpRead parameters. The IME then generates a WM_IME_COMPOSITION message.
BOOL WINAPI
    ImeSetCompositionString(
    HIMC hIMC,
    DWORD dwIndex,
    LPCVOID lpComp,
    DWORD dwCompLen,
    LPCVOID lpRead,
    DWORD dwReadLen
   );
Parameters
hIMC
Input context handle. 
dwIndex
The following values are provided for dwIndex.
Value
Description

>SCS_SETSTR
Application sets the composition string, the reading string, or both. At least one of the lpComp and lpRead parameters must point to a valid string. If either string is too long, the IME truncates it.
SCS_CHANGEATTR
Application sets attributes for the composition string, the reading string, or both. At least one of the lpComp and lpRead parameters must point to a valid attribute array. 
SCS_CHANGECLAUSE
Application sets the clause information for the composition string, the reading string, or both. At least one of the lpComp and lpRead parameters must point to a valid clause information array.
SCS_QUERYRECONVERTSTRING
Application asks the IME to adjust its RECONERTSTRINGSTRUCTRE. If the application calls the ImeSetCompositionString function with this value, the IME adjusts the RECONVERTSTRING structure. The application can then pass the adjusted RECONVERTSTRING structure to this function with SCS_RECONVERTSTRING. The IME will not generate any WM_IMECOMPOSITION messages.
SCS_SETRECONVERTSTRING
Application asks the IME to reconvert the string contained in the RECONVERTSTRING structure.

>lpComp
Pointer to the buffer that contains the updated string. The type of string is determined by the value of dwIndex.
dwCompLen
Length of the buffer in bytes.
lpRead
Pointer to the buffer that contains the updated string. The type of string is determined by the value of dwIndex. If the value of dwIndex is SCS_SETRRECONVERTSTRING or SCS_QUERYRECONVERTSTRING, lpRead will be a pointer to the RECONVERTSTRING structure that contains the updated reading string. If the selected IME has the value SCS_CAP_MAKEREAD, this can be NULL.
dwReadLen
Length of the buffer in bytes.

>Comments
For Unicode, dwCompLen and dwReadLen specifies the length of the buffer in bytes, even if SCS_SETSTR is specified and the buffer contains a Unicode string. 
SCS_SETRECONVERTSTRING or SCS_QUERYRECONVERTSTRING can be used only for IMEs that have an SCS_CAP_SETRECONVERTSTRING property. This property can be retrieved by using the ImmGetProperty function.

## ImeSetCompositionString
应用程序构造lpComp或lpRead数据，使用该函数设置写作串。输入法随即收到一条WM_IME_COMPOSITION消息。
``` c++
BOOL WINAPI ImeSetCompositionString(
    HIMC hIMC,
    DWORD dwIndex,
    LPCVOID lpComp,
    DWORD dwCompLen,
    LPCVOID lpRead,
    DWORD dwReadLen
   );
```
** 参数 **
`hIMC` 输入上下文句柄
`dwIndex`可为如下值：
* `SCS_SETSTR` 应用程序设置写作串或读入串，或者两者都设。lpComp和lpRead两个参数至少要有一个指向合法字符串。如果任一字串超长，输入法将会截断它。
* `SCS_CHANGEATTR` 应用程序设置写作串或读入串的属性，或者两者都设。lpComp和lpRead两个参数至少要有一个指向合法字符串。
* `SCS_CHANGECLAUSE` 应用程序设置输入串或读入串的分句信息。lpComp和lpRead两个参数至少要有一个指向合法的分句信息数组。
* `SCS_QUERYRECONVERTSTRING` 应用程序让输入法调整它的RECONERTSTRINGSTRUCTRE。如果应用程序使用该值调用了`ImeSetCompositionString`函数，输入法将调整`RECONVERTSTRING`结构体。应用程序随即传入调整后的RECONVERTSTRING结构体给本函数，并传入参数`SCS_RECONVERTSTRING`。输入法将不产生任何WM_IMECOMPOSITION消息。
* `SCS_SETRECONVERTSTRING` 应用程序要求输入法重新转换包含在`RECONVERTSTRING`结构体中的字串。
`lpComp` 指向更新串的buffer。字串的类型由`dwIndex`决定。
`dwCompLen` buffer的字节数。
`lpRead` 指向更新串的buffer。字串的类型由`dwIndex`决定。如果`dwIndex`为`SCS_SETRRECONVERTSTRING` 或 `SCS_QUERYRECONVERTSTRING`，`lpRead`将是一个指向`RECONVERTSTRING`结构体的指针，该结构体包含更新的读入串。如果被选中的输入法为`SCS_CAP_MAKEREAD`，该值为NULL。
`dwReadLen` buffer的字节数。

** 说明 **
对于Unicode，`dwCompLen`和`dwReadLen`指定buffer的字节数，即使指定了`SCS_SETSTR`且buffer中包含Unicode字符。
`SCS_SETRECONVERTSTRING` 或 `SCS_QUERYRECONVERTSTRING` 仅适用于有`SCS_CAP_SETRECONVERTSTRING` 属性的输入法，可以通过函数`ImmGetProperty`来获得该属性。

> ImeToAsciiEx 
The ImeToAsciiEx function generates a conversion result through the IME conversion engine according to the hIMC parameter.
UINT
    ImeToAsciiEx(
    UINT uVirKey,
    UINT uScanCode,
    CONST LPBYTE lpbKeyState,
    LPTRANSMSGLIST lpTransMsgList,
    UINT fuState,
    HIMC hIMC
   )
Parameters
uVirKey
Specifies the virtual key code to be translated. When the property bit IME_PROP_KBD_CHAR_FIRST is on, the upper byte of the virtual key is the aid character code.
For Unicode, the upper word of uVirKey contains the Unicode character code if the IME_PROP_KBD_CHAR_FIRST bit is on.
uScanCode
Specifies the hardware scan code of the key to be translated.
LpbKeyState 
Points to a 256-byte array that contains the current keyboard state. The IME should not modify the content of the key state.
lpTransMsgList
Point to a TRANSMSGLIST buffer to receive the translated message result. This was defined as a double word buffer in Windows 95/98 and Windows NT 4.0 IME document, and the double word buffer format is [Length of the pass in translated message buffer] [Message1] [wParam1] [lParam1] {[Message2] [wParam2] [lParam2]{...{...{...}}}}.
fuState
Active menu flag.
hIMC
Input context handle.

>Return Values
The return value indicates the number of messages. If the number is greater than the length of the translated message buffer, the translated message buffer is not enough. The system then checks hMsgBuf to get the translation messages.
Comments
On Windows 2000, a new 32bit-width virtual key code, using VK_PACKET in LOBYTE of wParam and the high word is Unicode, can be injected by using SendInput. 
For ANSI IMEs that support IME_PROP_ACCEPT_WIDE_VKEY, ImeToAsciiEx may receive up to 16bit ANSI code for a character. It will be packed as below.  The character is injected from SendInput API through VK_PACKET. 

>24-31 bit
16-23 bit
8-15 bit
0-7 biy
Reserved
Trailing DBCS byte(if any)
Leading byte
VK_PACKET

>See Also
ImmToAsciiEx

## ImeToAsciiEx
该函数通过输入法的转换引擎执行一次转换。
``` c++
UINT ImeToAsciiEx(
    UINT uVirKey,
    UINT uScanCode,
    CONST LPBYTE lpbKeyState,
    LPTRANSMSGLIST lpTransMsgList,
    UINT fuState,
    HIMC hIMC
   )
```
** 参数 **
`uVirKey` 指定待翻译的虚拟键盘码。当属性位`IME_PROP_KBD_CHAR_FIRST`被置1，虚拟键盘码的高字节就是字符的ascii码。对于Unicode，当属性位`IME_PROP_KBD_CHAR_FIRST`被置1，`uVirKey`的高WORD为Unicode字符。
`uScanCode` 指定待翻译的硬件扫描码
`lpbKeyState` 指向256字节数组，该数组包含键盘的当前状态。输入法不要修改该数组的值。
`lpTransMsgList` 指向用于接收翻译消息的 `TRANSMSGLIST`缓冲区。该缓冲区被定义为双WORD缓冲区，双WORD的格式为[缓冲区长度][Message1][wParam1][lParam1]{[Message2][wParam2][lParam2]{...{...{...}}}}
`fuState` 活动菜单标志
`hIMC` 输入上下文句柄
** 返回值 **
返回值描述消息的个数，如果个数比翻译消息缓冲区尺寸大，缓冲区就不够用了。系统将检查`hMsgBuf`来获取翻译消息。
** 说明 **
在Win2000下，新的32位虚拟键盘码可以通过`SendInput`被注入，该键盘码在wParam的低字节填充VK_PACKET，高WORD填充Unicode。

对于支持IME_PROP_ACCEPT_WIDE_VKEY的ANSI版输入法，ImeToAsciiEx可以接收16位ANSI字符。它被打包成如下格式，可以通过`SendInput`并传入`VK_PACKET`参数来注入此字符：

24-31位|16-23位|8-15位|0-7位
----|----|----|----
保留|DBCS字节|先导字节|VK_PACKET

还可参见ImmToAsciiEx

>ImeRegisterWord
The ImeRegisterWord function registers a string into the dictionary of this IME.
BOOL WINAPI
    ImeRegisterWord(
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString
   )
Parameters
lpszReading
Reading string of the registered string.
dwStyle
Style of the registered string. The following values are provided.
Value
Description

>IME_REGWORD_STYLE_EUDC
String is within the EUDC range
IME_REGWORD_STYLE_USER_FIRST to IME_REGWORD_STYLE_USER_LAST
Constants range from IME_REGWORD_STYLE_USER_FIRST to IME_REGWORD_STYLE_USER_LAST and are used for private styles of the IME ISV. The IME ISV can freely define its own style. For example:
>#define MSIME_NOUN (IME_REGWORD_STYLE_USER_FIRST)
>#define MSIME_VERB (IME_REGWORD_STYLE_USER_FISRT +1)

>lpszString
String to be registered.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

## ImeRegisterWord
该函数向输入法字典中注册一个字符串
``` c++
BOOL WINAPI ImeRegisterWord(
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString
   )
```
** 参数 **
`lpszReading` 注册的读入串
`dwStyle` 注册串的风格，可取如下值：
* `IME_REGWORD_STYLE_EUDC` 字串在EUDC的范围
* `IME_REGWORD_STYLE_USER_FIRST` 到 `IME_REGWORD_STYLE_USER_LAST` 在此区间内的常量用来表示输入法私有风格，例如：
``` c++
#define MSIME_NOUN (IME_REGWORD_STYLE_USER_FIRST)
#define MSIME_VERB (IME_REGWORD_STYLE_USER_FISRT +1)
```
`lpszString` 待注册的字串

** 返回值 **
成功返回TRUE，否则返回FALSE

> ImeUnregisterWord
The ImeUnregisterWord function removes a registered string from the dictionary of this IME.
BOOL WINAPI
    ImeUnregisterWord(
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString
   )
Parameters
lpszReading
Reading string of the registered string.
dwStyle
Style of the registered string. Please refer to the ImeRegisterWord function for a description of dwStyle. 
lpszString
String to be unregistered.

>Return Values
If the function is successful, the return value is TRUE. Otherwise, the return value is FALSE.

## ImeUnregisterWord
该函数用于删除在输入法字典中注册的字符串。
``` c++
BOOL WINAPI ImeUnregisterWord(
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString
   )
```
** 参数 **
`lpszReading` 删除注册的读入串
`dwStyle` 待注册字串的风格，可参见函数`ImeRegisterWord`来获取dwStyle的描述。
`lpszString` 删除注册的字串
** 返回值 **
成功返回TRUE，失败返回FALSE。

>ImeGetRegisterWordStyle
The ImeGetRegisterWordStyle function gets the available styles in this IME.
UINT WINAPI
    ImeGetRegisterWordStyle(
    UINT nItem,
    LPSTYLEBUF lpStyleBuf
   )
Parameters
nItem
Maximum number of styles that the buffer can hold.
lpStyleBuf
Buffer to be filled.

>Return Values
The return value is the number of the styles copied to the buffer. If nItems is zero, the return value is the buffer size in array elements needed to receive all available styles in this IME.

## ImeGetRegisterWordStyle
该函数获得输入法风格。
``` c++
UINT WINAPI ImeGetRegisterWordStyle(
    UINT nItem,
    LPSTYLEBUF lpStyleBuf
   )
```
** 参数 **
`nItem` buffer中可容纳的最大风格数量
`lpStyleBuf` 待填充的缓冲区
** 返回值 **
返回拷贝到缓冲区的风格的数量。如果nItems为0，返回需要向buffer填充的当前输入法的风格个数。

>ImeEnumRegisterWord
The ImeEnumRegisterWord function enumerates the information of the registered strings with specified reading string, style, and registered string data.
UINT WINAPI
    ImeEnumRegisterWord(
    hKL,
    REGISTERWORDENUMPROC lpfnEnumProc,
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString,
    LPVOID lpData
   )
Parameters
hKL
Input language handle.
lpfnEnumProc
Address of callback function.
lpszReading
Specifies the reading string to be enumerated. If lpszReading is NULL, ImeEnumRegisterWord enumerates all available reading strings that match the specified dwStyle and lpszString parameters.
dwStyle
Specifies the style to be enumerated. If dwStyle is NULL, ImeEnumRegisterWord enumerates all available styles that match the specified lpszReading and lpszString parameters.
lpszString
Specifies the registered string to be enumerated. If lpszString is NULL, ImeEnumRegisterWord enumerates all registered strings that match the specified lpszReading and dwStyle parameters.
lpData
Address of application-supplied data.

>Return Values
If the function is successful, the return value is the last value returned by the callback function. Its meaning is defined by the application.
Comments
If all lpszReading dwStyle, and lpszString parameters are NULL, ImeEnumRegisterWord enumerates all registered strings in the IME dictionary. If any two of the input parameters are NULL, ImeEnumRegisterWord enumerates all registered strings matching the third parameter.

## ImeEnumRegisterWord
该函数枚举指定读入串、风格和注册串数据的注册串信息。
``` c++
UINT WINAPI ImeEnumRegisterWord(
    hKL,
    REGISTERWORDENUMPROC lpfnEnumProc,
    LPCTSTR lpszReading,
    DWORD dwStyle,
    LPCTSTR lpszString,
    LPVOID lpData
   )
```
** 参数 **
`hKL` 输入法键盘布局句柄
`lpfnEnumProc` 回调函数地址
`lpszReading` 待枚举的指定读入串。如果为NULL，该函数将枚举所有符合dwStyle和lpszString参数的读入串。
`dwStyle` 待枚举的指定风格。如果为空，该函数将枚举所有符合lpszReading和lpszString的风格。
`lpszString` 待枚举的注册串。如果为空，该函数将枚举所有符合lpszReading和dwStyle的注册串。
`lpData` 应用程序提供的数据地址。
** 说明 **
如果lpszReading、dwStyle和lpszString参数均为NULL，该函数将枚举所有在输入法字典中的注册串。如果任意两个输入参数为NULL，该函数将枚举匹配第三个参数的所有注册串。

>ImeGetImeMenuItems
The ImeGetImeMenuItems function gets the menu items that are registered in the IME menu.
DWORD WINAPI
    ImeGetImeMenuItems(
    HIMC hIMC,
    DWORD dwFlags,
    DWORD dwType,
    LPIMEMENUITEMINFO lpImeParentMenu,
    LPIMEMENUITEMINFO lpImeMenu,
    DWORD dwSize
   )
Parameters
hIMC
The lpMenuItem contains menu items that are related to this input context.
dwFlags
Consists of the following bit combinations.
Bit
Description

>IGIMIF_RIGHTMENU
If this bit is 1, this function returns the menu items for the right click Context menu.

>dwType
Consists of the following bit combinations.
Bit
Description

>IGIMII_CMODE
Returns the menu items related to the conversion mode.
IGIMII_SMODE
Returns the menu items related to the sentence mode.
IGIMII_CONFIGURE
Returns the menu items related to the configuration of IME.
IGIMII_TOOLS
Returns the menu items related to the IME tools.
IGIMII_HELP
Returns the menu items related to IME help.
IGIMII_OTHER
Returns the menu items related to others.
IGIMII_INPUTTOOLS
Returns the menu items related to the IME input tools that provide the extended way to input the characters.

>lpImeParentMenu
Pointer to the IMEMENUINFO structure that has MFT_SUBMENU in fType. ImeGetImeMenuItems returns the submenu items of this menu item. If this is NULL, lpImeMenu contains the top-level IME menu items.
lpImeMenu
Pointer to the buffer to receive the contents of the menu items. This buffer is the array of IMEMENUITEMINFO structure. If this is NULL, ImeGetImeMenuItems returns the number of the registered menu items.
dwSize
Size of the buffer to receive the IMEMENUITEMINFO structure.

>Return Values
The return value is the number of the menu items that were set into lpIM. If lpImeMenu is NULL, ImeGetImeMenuItems returns the number of menu items that are registered in the specified hKL.
Comments
ImeGetImeMenuItems is a new function for Windows 98 and Windows 2000.

## ImeGetImeMenuItems
该函数获得输入法菜单中注册的菜单项。
``` c++    
DWORD WINAPI ImeGetImeMenuItems(
    HIMC hIMC,
    DWORD dwFlags,
    DWORD dwType,
    LPIMEMENUITEMINFO lpImeParentMenu,
    LPIMEMENUITEMINFO lpImeMenu,
    DWORD dwSize
   )
```
** 参数 **
`hIMC` lpMenuItem包含的菜单项相关的输入上下文
`dwFlag` 如下标志的组合：
* `IGIMIF_RIGHTMENU` 如果为1，该函数返回邮件上下文菜单的菜单项
`dwType` 如下标志的组合：
* `IGIMII_CMODE` 返回与转换模式相关的菜单项
* `IGIMII_SMODE` 返回与句子模式相关的菜单项
* `IGIMII_CONFIGURE` 返回与输入法配置相关的菜单项
* `IGIMII_TOOLS` 返回与输入法工具相关的菜单项
* `IGIMII_HELP` 返回与输入法帮助相关的菜单项
* `IGIMII_OTHER` 返回与其它相关的菜单项
* `IGIMII_INPUTTOOLS` 返回与输入法输入工具相关的菜单项，该工具用于提供输入字符串的扩展方法。