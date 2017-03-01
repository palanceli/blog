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

## Win98和Win2000的IMM/IME
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

## Win32 IME 结构体
>A new Win32 IME has to provide two components. One is the IME Conversion Interface and the other is the IME User Interface. The IME Conversion Interface is provided as a set of functions that are exported from the IME module. These functions are called by the IMM. The IME User Interface is provided in the form of windows. These windows receive messages and provide the user interface for the IME.

新的Win32 IME需要提供两个组件：一个是输入法转换接口，另一个是输入法用户接口。输入法转换接口是一套从ime文件中导出的函数。输入法用户接口则是以窗口的形式提供，这些窗口接收输入法消息，并提供输入法的用户交互。

## IME Aware 应用
> One of the main advantages of the new Win32 IME architecture is that it provides better communication logic between the application and the IME. Following is an example of how an application could be involved with the IME:
    IME Unaware Applications
These kinds of applications never intend to control the IME. However, as long as it accepts DBCS characters, a user can type any DBCS character to the application using IME.
    ME Half-aware Applications
These kinds of applications typically control the various contexts of the IME, such as open and close, and composition form, but it does not display any user interface for the IME.
    IME Full-aware Applications
These kinds of applications typically want to be fully responsible for displaying any information given by the IME.

>In Windows 95 and Windows NT 4.0 or later, one IME unaware application will be supported with one Default IME window and one Default Input Context. 
An IME half-aware application will create its own IME window(s), also called an application IME window, using a predefined system IME class, and may or may not handle its own Input Context given to the application.
An IME fully aware application will handle the Input Context by itself and will display any necessary information given by the Input Context not using the IME window.

Win32 IME架构最大的优势在于它提供了更好的在应用程序和输入法之间的通讯逻辑。下面是一个应用程序和输入法相结合的例子：
* IME unaware 应用
这类应用程序不会控制输入法，只要它能接收DBCS字符，用户就可以通过输入法向该应用发送DBCS字符。
* IME half-aware 应用
这类应用程序通常只控制个别的输入法上下文，比如打开、关闭、组合各种实体，但是它不负责显示输入法的用户界面。
* IME full-aware 应用
这类应用程序全面负责显示输入法各类信息。

在Win95和Win NT4.0或之后的Windows版本中，系统为IME unaware应用程序只提供一个默认的输入法窗口和一个输入上下文。
对于IME half-aware类应用程序，由它自己负责通过系统预定义的输入法类，创建自己的输入法窗口，这些窗口又被称为“应用程序输入法窗口”。应用程序可能操作也可能不操作自己的输入上下文。
而IME full-aware应用会自己操作输入上下文并自己显示输入上下文中必要的信息，而不借助于输入法。

# IME 用户接口
> The IME User Interface includes the IME window, the UI window, and the components of the UI window.

输入法用户接口包括输入法窗口、UI窗口和UI窗口的所有组件。
## 特性
> An IME class is a predefined global class that carries out any user interface portion of the IME. The normal characteristics of an IME class are the same as with other common controls. Its window instance can be created by CreateWindowEx. As with static controls, the IME class window does not respond to user input by itself, but receives various types of control messages to realize the entire user interface of the IME. An application can create its own IME window(s) by using this IME class or by obtaining the Default IME window through ImmGetDefaultIMEWnd. In comparison to Windows 3.1, an application that wants to control the IME with these window handles (an IME-aware application) can now achieve the following benefits:
    The new IME includes candidates listing windows. Each application can have its own window instance of the UI so a user can stop in the middle of any operation to switch to another application. In the Windows 3.1 Japanese Edition, the user had to first exit an operation before switching to another application.
    Since the IME User Interface window is informed about an application’s window handle, it can provide several default behaviors for the application. For example, this can include automatic repositioning of the IME window, automatic tracing of the window caret position, and mode indication for each application.

>Even though the system provides only one IME class, there are two kinds of IME window. One is created by the system for the DefWindowProc function especially for an IME unaware program. The IME User Interface for the DefWindowProc function is shared by all IME unaware windows of a thread and is called the default IME window in this documentation. The other windows are created by IME aware applications and are called the application IME window.

输入法类是一个全局预定义的类，用来负责输入法用户交互的部分。输入法类和一般的公共控件具有一样的属性，可以通过函数`CreateWindowEx`来创建其窗体实例。作为一个静态控制器，输入法类窗口并不直接响应用户输入，而是通过接收各类控制消息来实现输入法所有的用户交互。应用程序可以通过输入法类创建自己的输入法窗口，也可以通过`ImmGetDefaultIMEWnd`函数获得默认的输入法窗口。相对于之前的Windows版本，如果应用程序希望控制输入法（IME-aware 应用），它将可以：
* 新的输入法包括候选列表窗。每个应用可以拥有自己的窗口实例，用户可以在操作中途任一中断。而在Win3.1及之前的版本，用户必须先退出输入操作，才能切换到别的应用程序。
* 由于输入法窗口拥有宿主应用的窗口句柄，它可以为应用程序提供很多默认的操作行为。比如自动调整输入法窗口，自动跟踪光标位置，显示每个应用程序的当前模式。

## 默认输入法窗口和应用程序的输入法窗口
> The system creates a default IME window at thread initialization time, which is given to a thread automatically. This window then handles any IME user interface for an IME unaware application.
When the IME or IMM generates WM_IME_xxx messages, an IME unaware application passes them to DefWindowProc. Then, DefWindowProcB sends necessary messages to the default IME window, which provides default behavior of the IME User Interface for an unaware application. An IME aware application also uses this window when it does not hook messages from the IME. An application can use its own application IME window when it is necessary.

系统会在进程初始化时创建默认的输入法窗口，这使得输入法是自动与线程绑定的。对于IME unaware类应用，该窗口随即即可处理输入法用户交互了。

当IME或IMM生成WM_IME_xxx消息时，IME unaware 应用程序会把该消息交给`DefWindowProc`来处理。接着`DefWindowProc`发送必要的消息给默认的输入法窗口，该窗口提供了输入法的默认行为。必要的时候，应用程序可以自己创建和维护应用程序的输入法窗口。

## 输入法类
> The Win32 systems provides an IME class in the system. This class is defined by the user just as the predefined Edit class is. The system IME class handles the entire UI of the IME and handles entire control messages from the IME and application, including IMM functions. An application can create its own IME User Interface by using this class. The system IME class, itself, is not replaced by any IME, but is kept as a predefined class. 
This class has a window procedure that actually handles the WM_IME_SELECT message. This message has the hKL of the newly selected IME. The system IME class retrieves the name of the class defined by each IME with this hKL. Using this name, the system IME class creates a UI window of the currently active IME.

Win32提供了系统级的IME类，类似于Edit类，IME类也是系统预先定义好的。系统的IME类处理所有输入法UI展现和全部控制消息，包括IMM功能。应用程序可以通过该类创建自己的输入法窗口。系统输入法类作为预定义的类，不会被其它任何输入法覆盖掉。
该类拥有自己的窗体处理过程，并会处理WM_IME_SELECT消息。该消息参数中包含即将切出的输入法HKL。系统输入法类通过每个输入法的HKL获得对应的类名，使用该类名，系统输入法类就可以创建当前活动输入法的UI窗口了。

## 输入法UI类
> In this design, every IME is expected to register its own UI class for the system. The UI class provided by each IME should be responsible for IME-specific functionality. The IME may register the classes that are used by the IME itself when the IME is attached to the process. This occurs when DllEntry is called with DLL_PROCESS_ATTACH. The IME then has to set the UI class name in the lpszClassName parameter, which is the second parameter of ImeInquire. 
The UI class should be registered with CS_IME specified in the style field so every application can use it through the IME class. The UI class name (including the null terminator) can consist of up to 16 characters and may be increased in future versions.
The cbWndExtra of the UI class has to be 2 * sizeof(LONG). The purpose of this WndExtra is defined by the system (for example, IMMGWL_IMC and IMMGWL_PRIVATE).
The IME can register any class and create any window while working in an application.
The following sample shows how to register the IME User Interface Class:

按照这个设计思路，每个输入法都需要向系统注册它的UI类，该UI类负责响应输入法相关的功能请求。输入法应该在ime文件被attach到进程的嘶吼注册该UI类，这个时机正是使用DLL_PROCESS_ATTACH调用Dll入口函数的时候。输入法将UI类名赋给`ImeInquire`函数的第二个参数，即lpszClassName。

该UI类必须在类风格种植钉CS_IME标记，以便应用程序可以通过系统IME类使用它。输入法UI类名最多由16个字符组成（包含结尾的'\0'），这个阈值可能会在未来的版本增长。

该UI类的cbWndExtra必须为**2 * sizeof(LONG)**，系统要使用WndExtra来存放IMMGWL_IMC和IMMGWL_PRIVATE数据。

下面展示了如何注册输入法UI类：
``` c++
BOOL WINAPI DLLEntry (
    HINSTANCE    hInstDLL,
    DWORD        dwFunction,
    LPVOID       lpNot)
{
    switch(dwFunction){
    case DLL_PROCESS_ATTACH:
        hInst= hInstDLL;
        wc.style          = CS_MYCLASSFLAG | CS_IME;
        wc.lpfnWndProc    = MyUIServerWndProc;
        wc.cbClsExtra     = 0;
        wc.cbWndExtra     = 2 * sizeof(LONG);
        wc.hInstance      = hInst;
        wc.hCursor        = LoadCursor( NULL, IDC_ARROW );
        wc.hIcon          = NULL;
        wc.lpszMenuName   = (LPSTR)NULL;
        wc.lpszClassName  = (LPSTR)szUIClassName;
        wc.hbrBackground  = NULL;
        if( !RegisterClass( (LPWNDCLASS)&wc ) )
            return FALSE;
        wc.style          = CS_MYCLASSFLAG | CS_IME;
        wc.lpfnWndProc    = MyCompStringWndProc;
        wc.cbClsExtra     = 0;
        wc.cbWndExtra     = cbMyWndExtra;
        wc.hInstance      = hInst;
        wc.hCursor        = LoadCursor( NULL, IDC_ARROW );
        wc.hIcon          = NULL;
        wc.lpszMenuName   = (LPSTR)NULL;
        wc.lpszClassName  = (LPSTR)szUICompStringClassName;
        wc.hbrBackground  = NULL;
        if( !RegisterClass( (LPWNDCLASS)&wc ) )
            return FALSE;
        break;
    case DLL_PROCESS_DETACH:
        UnregisterClass(szUIClassName,hInst);
        UnregisterClass(szUICompStringClassName,hInst);
        break;
    }
    return TRUE;
}
```
## UI窗口
> The IME windows of the IME class are created by the application or by the system. When the IME window is created, the UI window provided by the IME itself is created and owned by the IME window.
Each UI window contains the current Input Context. This Input Context can be obtained by calling GetWindowLong with IMMGWL_IMC when the UI window receives a WM_IME_xxx message. The UI window can refer to this Input Context and handles the messages. The Input Context from GetWindowLong with IMMGWL_IMC is available at any time during the UI window procedure, except when handling a WM_CREATE message.
The cbWndExtra of the UI windows cannot be enhanced by the IME. When the IME needs to use the extra byte of the window instance, the UI window uses SetWindowLong and GetWindowLong with IMMGWL_PRIVATE. This IMMGWL_PRIVATE provides a LONG value extra of the window instance. When the UI window needs more than one LONG value extra for private use, the UI window can place a handle for a memory block into the IMMGWL_PRIVATE area.The UI window procedure can use DefWindowProc, but the UI window cannot pass a WM_IME_xxx message to DefWindowProc. Even if the message is not handled by the UI window procedure, the UI window does not pass it to DefWindowProc.
The following sample demonstrates how to allocate and use a block of private memory:

IME类的输入法窗口是由系统或应用程序创建的。当该窗口被创建时，输入法的UI窗口也被创建出来并属于IME类窗口。

每个UI窗口包含当前输入上下文，当此窗口收到WM_IME_xxx消息时，可以通过函数`GetWindowLong`并传入IMMGWL_IMC参数来获得输入上下文。UI窗口可以参考此输入上下文来处理输入法消息。可以在UI窗口函数的绝大多数时刻调用`GetWindowLong`来获得输入上下文，仅有一种情况例外——那就是在处理WM_CREATE消息时。

UI窗口的cbWndExtra字段无法通过输入法再扩展。当输入法需要使用窗体实例的extra字段时，UI窗体使用`SetWindowLong`和`GetWindowLong`函数，并传入IMMGWL_PRIVATE参数来获得。该字段为窗体实例提供一个LONG型的数据。如果需要存放多于一个LONG的数据时，可以把一个内存块的句柄放到窗体的IMMGWL_PRIVATE。UI窗体可以使用`DefWindowProc`来处理窗体消息，但是UI窗体不能把WM_IME_xxx消息传给`DefWindowProc`函数，即使UI窗体不处理该消息，也不要传给它。

下面的例子展示如何分配一个私有内存块：
``` c++
LRESULT UIWndProc (HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    HIMC hIMC;
    HGLOBAL hMyExtra;
     
    switch(msg){
    case WM_CREATE:
        // 为窗体实例分配内存块
        hMyExtra = GlobalAlloc(GHND, size_of_MyExtra);
        if (!hMyExtra)
            MyError();
        // 把内存块句柄放到 IMMGWL_PRIVATE
        SetWindowLong(hWnd, IMMGWL_PRIVATE, (LONG)hMyExtra);
            :
            :
        break;
    case WM_IME_xxxx:
        // Get IMC;
        hIMC = GetWindowLong(hWnd,IMMGWL_IMC);
        // 获取窗体实例的内存块句柄
        hMyExtra = GetWindowLong(hWnd, IMMGWL_PRIVATE);
        lpMyExtra = GlobalLock(hMyExtra);
            :
            :
        GlobalUnlock(hMyExtra);
        break;
            :
            :
         
    case WM_DESTROY:
        // 获取窗体实例的内存块句柄
        hMyExtra = GetWindowLong(hWnd, IMMGWL_PRIVATE);
        // 释放窗体实例的内存块句柄
        GlobalFree(hMyExtra);
        break;
     
    default:
        return DefWindowProc(hWnd, msg, wParam, lParam);
    }
}
```
>The UI window must perform all tasks by referring to the Input Context that is currently selected. When a window of an application is activated, the UI window receives a message that contains the current Input Context. The UI window then uses that Input Context. Thus, the Input Context must contain all the information needed by the UI window to display the composition window, the status window, and so forth.
The UI window refers to the Input Context, but does not need to update it. However, if the UI window wants to update the Input Context, it should call the IMM functions. Because the Input Context is managed by the IMM, the IMM along with the IME should be notified when the Input Context is changed.
For example, the UI window occasionally needs to change the conversion mode of the Input Context when the user clicks the mouse. At this point, the UI window should call ImmSetConversionMode. The ImmSetConversionMode function creates a notification for NotifyIME and the UI window with WM_IME_NOTIFY. If the UI window wants to change the display of the conversion mode, the UI window should wait for a WM_IME_NOTIFY message. 

UI窗口必须根据当前输入上下文处理所有输入法任务。当应用程序的窗体被激活，UI窗口会收到一条包含当前输入上下文的消息。输入上下文中应当包含UI窗口处理写作窗、候选窗和状态栏等等的一切输入法上下文信息。

UI窗口使用输入上下文，如果需要更新它，则应调用IMM函数。这是因为输入上下文是由IMM管理的，通过IMM函数修改上下文，可以确保IMM和IME收到变化通知。

例如UI窗口可能会在用户鼠标点击状态栏时修改当前的转换模式，此时UI窗口就应该调用`ImmSetConversionMode`函数，该函数会产生一个一个通知调用输入法的NotifyIME函数，并向UI窗口发送WM_IME_NOTIFY消息。如果UI窗口希望展现出转换模式的变化，它应当在收到该消息时再处理。
## UI窗口的组件
> The UI window can register and show the composition window and the status window by referring to the current Input Context. The class style of the components of the UI window must include the CS_IME bit. A window instance of the UI window gets information about the composition string, font, and position from the current Input Context. 
When a window of the application is getting focused, the system gives the Input Context to this window and sets the current Input Context to the UI window. The system then sends a WM_IME_SETCONTEXT message with the handle of its Input Context to the application. The application then passes this message to the UI window. If current Input Context is replaced by another Input Context, the UI window should repaint the composition window. Any time the current Input Context is changed, the UI window displays a correct composition window. Thus, the status of the IME is assured.
A UI window can create a child window or pop-up window to display its status, composition string, or candidate lists. However, these windows have to be owned by the UI window and created as disabled windows. Any windows that are created by the IME should not get the focus.

UI窗口可以根据当前输入上下文注册和显示写作窗和状态栏。这些窗体的窗体类风格必须包含CS_IME标记。UI窗体可以通过输入上下文取得写作串、字体以及写作窗的位置。

当应用程序的窗体获得焦点时，系统会把输入上下文给到这个窗体，并为UI窗口设置当前的输入上下文。系统会向应用程序发送WM_IME_SETCONTEXT消息，通过该消息把输入上下文告诉应用程序。应用程序紧接着把消息传递给UI窗口。如果当前的输入上下文被替换了，UI窗口应当重新绘制写作窗。只要输入上下文发生变化，UI窗口就应当检查是否要更新写作窗、状态栏。

UI窗口可以创建子窗口或弹出式窗口来显示它的状态、写作串或者候选列表。这些窗口都应当作为UI窗口的子窗口，并且必须是disable的，任何由IME创建的窗口都不能获得焦点。

# 输入法的输入上下文
> Each window is associated with an IME Input Context. The IMM uses the Input Context to maintain IME status, data, and so forth, and communicate with the IME and with applications. 

每个窗口都有关联的输入上下文，IMM使用输入上下文来维护输入法状态、数据等，并通过该上下文和输入法、应用程序来通讯。

## 默认输入上下文
> By default, the system creates a default Input Context for each thread. All IME unaware windows of the thread share this context.

系统给每个线程创建默认的输入上下文，线程中的所有IME unaware窗口会共享该上下文。

## 应用程序创建的输入上下文
> A window of an application can associate its window handle to an Input Context to maintain any status of the IME, including an intermediate composition string. Once an application associates an Input Context to a window handle, the system automatically selects the context whenever the window is activated. In this way, an application is free from complicated in and out focus processing.

应用程序的窗口可以通过自己的窗口句柄查到与之关联的输入上下文的相关信息，例如当前的写作串。一旦应用程序将输入上下文和窗口句柄建立了关联，系统会在窗体被激活时自动为之选择上下文。这样应用程序就不用关心和处理输入法切入和切出的工作了。

## 使用输入上下文
> When an application or system creates a new Input Context, the system prepares the new Input Context with the components of the IMC (IMCC). These include hCompStr, hCandInfo, hGuideLine, hPrivate, and hMsgBuf. Basically, the IME does not need to create the Input Context and the components of the Input Context. The IME can change the size of them and lock them to get the pointer for them.

当应用程序或系统创建了一个新的输入上下文，系统会把它配备为IMC的一个组件（IMCC）。这些组件包括hCompStr, hCandInfo, hGuideLine, hPrivate和hMsgBuf。一个最基本的输入法不需要创建新的输入上下文组件就能正常运行。IME可以修改IMCC的尺寸并通过锁定来获取指向某个组件的指针。

### 访问HIMC
> When an IME accesses the Input Context, the IME has to call ImmLockIMC to get the pointer of the Input Context. ImmLockIMC increments the IMM lock count for IMC, while ImmUnlockIMC decrements the IMM lock count for IMC.

输入法需要调用`ImmLockIMC`来获取输入上下文，进而访问它。该函数会让IMM增加IMC持有锁的锁定次数，`ImmUnlockIMC`则会减少锁定次数。

### 访问HIMCC
> When an IME accesses a component of the Input Context, the IME has to call ImmLockIMCC to get the pointer of the IMCC. ImmLockIMCC increments the IMM lock count for IMCC, while ImmUnlockIMC decrements the IMM lock count for IMCC. ImmReSizeIMCC can resize the IMCC to the size specified in the input parameter.
On occasion, an IME needs to create a new component in the Input Context. The IME can call ImmCreateIMCC to do so. To destroy a newly created component in the Input Context, the IME can call ImmDestroyIMCC.
The following example shows how to access the IMCC and change the size of a component:

输入法可以调用`ImmLockIMCC`函数来获得指向某个IMCC的指针，进而访问它。该函数会增加IMCC持有锁的锁定次数，函数`ImmUnlockIMCC`则减少该持有锁的锁定次数。函数`ImmReSizeIMCC`可以重新分配IMCC的尺寸到指定的值。

有些时候，输入法也需要在输入上下文中创建新的组件。输入法可以调用`ImmCreateIMCC`来完成创建；调用`ImmDestroyIMCC`来销毁输入上下文中的组件。

下面的例子展示了如何访问IMCC并改变组建的尺寸：

``` c++
LPINPUTCONTEXT      lpIMC;
LPCOMOSITIONSTRING  lpCompStr;
HIMCC               hMyCompStr;
 
if (hIMC){    // It is not NULL context.
    lpIMC = ImmLockIMC(hIMC);
    if (!lpIMC){
        MyError( “Can not lock hIMC”);
        return FALSE;
    }
     
    // Use lpIMC->hCompStr.
    lpCompStr = (LPCOMPOSITIONSTRING)ImmLockIMCC(lpIMC->hCompStr);
    // Access lpCompStr.
    ImmUnlockIMCC(lpIMC->hCompStr);
     
    // ReSize lpIMC->hCompStr.
    if (!(hMyCompStr = ImmReSizeIMCC(lpIMC->hCompStr,dwNewSize)){
        MyError(“Can not resize hCompStr”);
        ImmUnlockIMC(hIMC);
        return FALSE;
    }
    lpIMC->hCompStr = hMyCompStr;
    ImmUnlockIMC(hIMC);
}
```

# 生成消息
> IMEs need to generate IME messages. When an IME initiates the conversion process, the IME has to generate a WM_IME_STARTCOMPOSITION message. If the IME changes the composition string, the IME has to generate a WM_IME_COMPOSITION message. 
There are two ways an IME can generate a message: one is by using the lpdwTransKey buffer provided by ImeToAsciiEx, and the other is by calling ImmGenerateMessage. 

输入法会产生各种消息，例如：当开始了转换处理，它就会产生一个WM_IME_STARTCOMPOSITION消息。如果输入法修改了输入串，它会产生一个WM_IME_COMPOSITION消息。

输入法有两种方式可以产生消息：一种是使用由函数`ImeToAsciiEx`提供的lpdwTransKey缓冲区；另一种是调用`ImmGenerateMessage`函数。

## 使用lpTransMsgList来生成消息
> Events initiated by IMEs are realized as generating messages to the window associated with the Input Context. Basically, IMEs use the lpTransMsgList provided by the parameter of ImeToAsciiEx to generate the message. The IMEs put the messages into the lpTransMsgList buffer when ImeToAsciiEx is called. 
The buffer specified by lpTransMsgList in the ImeToAsciiEx function is provided by the system. This function can place messages in this buffer all at one time. The real number of messages that can be placed is given at the first double word of the buffer. However, if the ImeToAsciiEx function wants to generate more messages than the given number, ImeToAsciiEx can put all the messages into hMsgBuf in the Input Context and then return the number of messages. 
When the return value of ImeToAsciiEx is larger than the specified value in lpTransMsgList, the system does not pick up the messages from lpTransMsgList. Instead, the system looks up hMsgBuf in the Input Context, which is passed as a parameter of ImeToAsciiEx.
Following is the code sample for ImeToAsciiEx implementation:

由输入法触发的事件会以消息的形式发送给和输入上下文关联的窗口。最常见的，输入法会使用函数`ImeToAsciiEx`函数的`lpTransMsgList`参数来生成消息。当`ImeToAsciiEx`被调用时，输入法会把消息组装到`lpTransMsgList`缓冲区中。

该缓冲区是由系统提供的，实际填充的消息条数被放到缓冲区开头的双字区域。但是如果`ImeToAsciiEx`希望生成的消息个数超过了给定的缓冲大小，该函数可以把消息都塞到输入上下文的hMsgBuf里，并返回消息的个数。

当`ImeToAsciiEx`的返回值大于lpTransMsgList指定的大小时，系统不再从lpTransMsgList中获取消息，而是检查输入上下文的hMsgBuf字段，输入上下文会作为参数传给函数`ImeToAsciiEx`。
``` c++
UINT ImeToAsciiEx(
    UINT uVirKey,
    UINT uScanCode,
    CONST LPBYTE lpbKeyState,
    LPTRANSMSGLIST lpTransMsgList,
    UINT fuState,
    HIMC hIMC
   )
{
    DWORD dwMyNumMsg = 0;
    . . .
    // 在这里组装输入法生成的消息
    pTransMsgList->TransMsg[0].message =msg;
    pTransMsgList->TransMsg[0].wParam = wParam;
    pTransMsgList->TransMsg[0].lParam = lParam;
 
    // 生成的消息个数
    dwMyNumMsg++;
    . . .
    return dwMyNumMsg;
}
```
## 使用消息缓冲区来生成消息
> Even if ImeToAsciiEx is not called, IMEs can still generate the message to the window associated with the Input Context by using the message buffer of the Input Context. This message buffer operates as a handle of a memory block and the IME puts the messages into this memory block. The IME then calls the ImmGenerateMessage function, which sends the messages stored in the message buffer to the proper window.
Following is the code sample for ImmGenerateMessage implementation. 

不调用`ImeToAsciiEx`，输入法依然可以通过消息缓冲区生成消息并发送给与输入上下文关联的窗口。该消息缓冲区是一个内存块，输入法通过其句柄来操作它。通过调用函数`ImmGenerateMessage`向相关窗口发送保存在消息缓冲区的消息。

下面代码展示了如何使用该函数：
``` c++
MyGenerateMesage(HIMC hIMC, UINT msg, WPARAM wParam, LPARAMlParam)
{
    LPINPUTCONTEXT lpIMC;
    HGLOBAL hTemp;
    LPTRANSMSG lpTransMsg;
    DWORD dwMyNumMsg = 1;
    
    // 获取IMC
    lpIMC = ImmLockIMC(hIMC);
    if (!lpIMC)         // Error!
        ...
    // 重新分配消息缓冲区的内存块大小
    hTemp = ImmReSizeIMCC(lpIMC->hMsgBuf, (lpIMC->dwNumMsgBuf + dwMyNumMsg) * sizeof(TRANSMSG));
    if (!hTemp)         // Error!
        ...
    lpIMC->hMsgBuf = hTemp;
    // 锁定并获取消息缓冲区
    lpTransMsg = ImmLockIMCC(lpIMC->hMsgBuf);
    if (!lpTransMsg)    // Error!
        ...


    // 在消息缓冲区中组装输入法消息
    lpTransMsg[lpIMC->dwNumMsg].message = msg;
    lpTransMsg[lpIMC->dwNumMsg].wParam = wParam;
    lpTransMsg[lpIMC->dwNumMsg].lParam = lParam;

    // 设置消息个数
    lpIMC->dwNumMsgBuf += dwMyNumMsg;


    // 解锁消息缓冲区和IMC
    ImmUnlockIMCC(lpIMC->hMsgBuf);
    ImmLockIMC(hIMC);
 
    // 发送消息
    ImmGenerateMessage(hIMC);
}
```

### WM_IME_COMPOSITION消息
> When an IME generates a WM_IME_COMPOSITION message, the IME specifies lParam as the GCS bits. The GCS bits then inform the available members of the COMPOSITIONSTRING structure. Even if the IME does not update and a member is available, the IME can set the GCS bits.
When an IME generates a WM_IME_COMPOSITION message, the IME can also change the string attribute and clause information all at once. 

当输入法生成了WM_IME_COMPOSITION消息，其lParam会被当做GCS位来解释。GCS为用来标识`COMPOSITIONSTRING`结构体中可用的成员都有哪些。

当输入法生成WM_IME_COMPOSITION消息时，输入法有机会在这里修改字符串属性和分词信息。

# ImeSetCompositionString
> The ImeSetCompositionString function is used by applications to manipulate the IME composition string. By specifying different flags, an application can change composition string, attribute, clause, and so forth. 
The second parameter of this function, dwIndex, specifies how the composition string should be adjusted in an IME. It includes values such as SCS_SETSTR ,SCS_CHANGEATTR, SCS_CHANGECLAUSE, SCS_QUERYRECONVERTSTRING. Each value represents a specific feature. 

应用程序使用函数`ImeSetCompositionString`来控制输入法写作串。通过指定不同的标志位，应用程序可以修改输入串的字串、属性、分词等信息。

该函数的第二个参数`dwIndex`指定写作串应当如何调整。该值可以为： `SCS_SETSTR` ,`SCS_CHANGEATTR`, `SCS_CHANGECLAUSE`, `SCS_QUERYRECONVERTSTRING`，每种取值代表一种特定的操作。

## ImeSetCompositionString 都能干什么
>When an IME does not have the capability of ImeSetCompositionString, it will not specify any SCS capability in the IMEINFO structure. When an IME can handle ImeSetCompositionString, it sets the SCS_COMPSTR bit. If an IME can generate the reading string from the composition string, it will set the SCS_CAP_MAKEREAD bit.
If an IME has SCS_CAP_COMPSTR capability, ImeSetCompositionString will be called. In response to this call, the IME should use the new composition string generated by an application and then generate a WM_IME_COMPOSITION message.

如果输入法没有`ImeSetCompositionString`的能力，它将不能在IMEINFO结构体中指定SCS的是能标记。如果输入法可以调用`ImeSetCompositionString`，它才设置SCS_COMPSTR标记。如果输入法可以从写作串生成读入串，它将设置SCS_CAP_MAKEREAD标记。

如果输入法有SCS_CAP_COMPSTR能力，`ImeSetCompositionString`会被调用，作为回应，输入法将使用应用程序生成的新的写作串，并产生一个WM_IME_COMPOSITION消息。
### SCS_SETSTR
> If dwIndex of ImeSetCompositionString is SCS_SETSTR, the IME can clean up all the COMPOSITIONSTR structures of hIMC.
If necessary, the IME can also update the candidate information and generate the candidate message WM_IME_NOTIFY with the submessage as IMN_OPENCANDIDATE, CHANGECANDIDATE, or IMN_CLOSECANDIDATE.
An IME needs to respond to the application requirement based on different input parameters as follows:
    If the lpRead parameter of ImeSetCompositonString is available:
The IME should create the composition string from the reading string contained in lpRead. The IME then creates the attribute and clause information for both the new composition string and reading string of lpRead. The IME generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD. On occasion, an IME may finalize the conversion automatically. The IME can then generate a WM_IME_COMPOSITION message with either GCS_RESULT or GCS_RESULTREAD instead of GCS_COMPxxx.
    If the lpComp parameter of ImeSetCompositonString is available:
The IME should create the composition attribute and clause information from the composition string contained in lpComp. The IME then generates a WM_IME_COMPOSITION message with GCS_COMP. If the IME has the capability of SCS_CAP_MAKEREAD, the IME should also make the new reading string at the same time. The IME then generates a WM_IME_COMPOSITION message with either GCS_COMP orGCS_COMPREAD. On occasion, an IME may finalize the conversion automatically. The IME can then generate a WM_IME_COMPOSITION message with either GCS_RESULT or GCS_RESULTREAD instead of GCS_COMPxxx.
    If both lpRead and lpComp are available:
The IME should create the composition string and the reading string accordingly. In this case, the IME does not need to follow lpComp and lpRead completely. If an IME cannot find the relation between lpRead and lpComp specified by the application, it should correct the composition string. The IME can then create the attribute and clause information for both the new composition string and reading string of lpRead. The IME then generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD. On occasion, the IME may finalize the conversion automatically. The IME can then generate a WM_IME_COMPOSITION message with either GCS_RESULT or GCS_RESULTREAD instead of GCS_COMPxxx.

如果`ImeSetCompositionString`的`dwIndex`参数是SCS_SETSTR，输入法可以清除IMC中的所有COMPOSITIONSTR结构体。

必要的时候，输入法还可以更新候选信息并生成候选消息WM_IME_NOTIFY，该消息的子消息为IMN_OPENCANDIDATE，IMN_CHANGECANDIDATE或IMN_CLOSECANDIDATE。

输入法需要基于不同的输入参数响应应用程序的需求，如下。
* 如果`ImeSetCompositionString`的lpRead参数有效：
输入法根据lpRead中的读入串创建写作串。接着为lpRead对应的新的写作串和读入串创建属性和分词信息。输入法生成一条带有GCS_COMP或GCSCOMPREAD参数的WM_IME_COMPOSITION消息。有时候，输入法会自动终结转换。输入法可以生成一条带有GCS_RESULT或GCS_RESULTREAD而不是GCS_COMPxxx参数的WM_IME_COMPOSITION消息。
* 如果`ImeSetCompositionString`的lpComp参数有效：
输入法应当根据lpComp中的写作串创建写作串属性和分词信息。输入法紧接着生成一个带有GCS_COMP参数的WM_IME_COMPOSITION消息。如果输入法有SCS_CAP_MAKEREAD能力，输入法应当同时生成读入串。然后产生一条带有GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。有时候，输入法可能会自动终止转换。输入法会紧接着生成一条带有GCS_RESULT或GCS_RESULTREAD而不是GCS_COMPxxx的WM_IME_COMPOSITION消息。
* 如果lpRead和lpComp都有效：
输入法应当生成相应的写作串和读入串。这种情况下舒服啊不需要完全跟随lpComp和lpRead。如果输入法找不到应用程序指定的lpRead和lpComp之间的关系，它应当纠正写作串。输入法可以为lpRead中新的写作串和读入串创建属性和分词信息。然后在生成一条参数为GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。有时候输入法会自动终止转换。输入法紧接着生成一条参数为GCS_RESULT或GCS_RESULTREAD而不是GCS_COMPxxx的WM_IME_COMPOSITION消息。

### SCS_CHANGEATTR
>SCS_CHANGEATTR effects only attribute information. The IME should not update the composition string, the clause information of the composition string, the reading of the composition string, or the clause information of the reading of the composition string.
The IME first has to check whether the new attribute is acceptable or not. It then sets the new attribute in the COMPOSITIONSTRING structure of hIMC. Last, the IME generates a WM_IME_COMPOSITION message.
If necessary, the IME can update the candidate information and generate the candidate messages WM_IME_NOTIFY with the submessage as IMN_OPENCANDIDATE, CHANGECANDIDATE, or IMN_CLOSECANDIDATE of WM_IME_NOTIFY. 
For this feature, an IME cannot finalize the composition string.
An IME needs to respond to the application requirement based on different input parameters as follows:
    If the lpRead parameter of ImeSetCompositonString is available:
The IME should follow the new attribute in lpRead and then create a new attribute of the composition string for the current composition string. In this case, the clause information does not change.
The IME generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD. If an IME cannot accept the new attribute contained in lpRead, it does not generate any messages and returns FALSE.
    If the lpComp parameter of ImeSetCompositonString is available:
The IME follows the new attribute in lpComp. In this case, the clause information does not change.
If the capability of the IME has SCS_CAP_MAKEREAD and the reading string is available, the IME should create a new attribute of the reading of the composition string for the current reading of the composition string.
    If both lpRead and lpComp are available:
If the IME can accept the new information, it sets the new information in the COMPOSITION structure of hIMC and generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD.

SCS_CHANGEATTR仅仅影响属性信息。输入法不应更新写作串、写作串的分词信息以及读入串的分词信息。

输入法首先应该检查新的属性是否能被接受。然后设定IMC中`COMPOSITIONSTRING`字段下的新属性。最后输入法生成一条WM_IME_COMPOSITION消息。

如果必要，输入法可以更新候选信息，并生成候选消息WM_IME_NOTIFY，该消息的子消息指定为IMN_OPENCANDIDATE、IMN_CHANGECANDIDATE或IMN_CLOSECANDIDATE。

输入法应当响应应用程序基于如下不同参数的请求：
* 如果lpRead参数有效：
输入法应当遵循lpRead中新的属性，并为当前的写作串创建新的属性。这种情况下分词信息不会发生变化。
舒服啊生成一条参数为GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。如果输入法不能接受lpRead指定的新属性，它将不产生任何消息并返回FALSE。
* 如果lpComp参数有效：
输入法将遵循lpComp中的新属性，这种情况下分词信息不发生变化。
如果输入法的使能标志包含SCS_CAP_MAKEREAD并且读入串有效，舒服啊应当为当前的写作串创建新属性。
* 如果lpRead和lpComp都有效：
如果输入法可以接受新信息，它将设置IMC中COMPOSITION结构体的新信息，并产生一条参数为GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。

### SCS_CHANGECLAUSE
> SCS_CHANGECLAUSE effects the string and attribute for both the composition string and the reading of the composition string.
If necessary, an IME can update the candidate information and generate the candidate message WM_IME_NOTIFY with the submessages as IMN_OPENCANDIDATE, CHANGECANDIDATE, or IMN_CLOSECANDIDATE.
An IME needs to respond to the application requirement based on different input parameters. Following are the instances in which an IME cannot finalize the composition string.
    If the lpRead parameter of ImeSetCompositonString is available:
The IME follows the new reading clause information of lpRead and has to correct the attribute of the reading of the composition string. The IME can then update the composition string, the attribute, and the clause information of the composition string. The IME generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD.
    If the lpComp parameter of ImeSetCompositonString is available:
The IME follows the new clause information and has to correct the composition string and the attribute of the composition string. Then, the IME can update the reading attribute and the clause information of the reading attribute. The IME generates a WM_IME_COMPOSITION message with either GCS_COMPSTR or GCS_COMPREAD.
    If both lpRead and lpComp are available:
If the IME can accept the new information, it sets the new information in the COMPOSITION structure of hIMC and generates a WM_IME_COMPOSITION message with either GCS_COMP or GCS_COMPREAD.

SCS_CHANGECLAUSE会影响到写作串和读入串的字串和属性信息。

如果必要，输入法可以更新候选信息，并产生一条候选消息WM_IME_NOTIFY，该消息的子消息为IMN_OPENCANDIDATE、IMN_CHANGECANDIDATE或IMN_CLOSECANDIDATE。

输入法需要基于不同的输入参数响应应用程序，但输入法不可以定案写作串，下面是不同的例子。
* 如果lpRead有效：
输入啊遵循lpRead中新的读入分词信息更正写作串的属性。输入法可以更新写作串极其属性和分词信息。输入法会生成一个参数为GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。
* 如果lpComp有效：
输入法遵循新的分词信息并纠正写作串和写作串属性，随后输入法更新读入串和读入串的分词信息。舒服啊生成一条带有参数GCS_COMPSTR或GCS_COMPREAD的WM_IME_COMPOSITION消息。
* 如果lpRead和lpComp均有效：
如果输入法可以接受新信息，它将设置IMC中COMPOSITION结构体的新信息，并生成一个带有参数GCS_COMP或GCS_COMPREAD的WM_IME_COMPOSITION消息。

# 软键盘
> Soft Keyboard is a special window displayed by the IME. Because some IMEs have special reading characters, an IME can provide a soft keyboard to display these special reading characters. In this way, the user does not have to remember the reading character for each key. For example, an IME can use bo po mo fo for its reading characters, while another IME can use radicals for its reading characters. 
An IME can change the reading characters of keys and notify the user of these key changes, depending on the conversion state. For example, during candidate selection time, an IME can show just the selection keys to the user.
An IME can also create its own user interface for a soft keyboard or use the system predefined soft keyboard. If an IME wants to use the system predefined soft keyboard, it needs to specify UI_CAP_SOFTKBD in the fdwUICaps member of the IMEINFO structure when ImeInquire is called.
An IME needs to call ImmCreateSoftKeyboard to create the soft keyboard window . It can also call ImmShowSoftKeyboard to show or hide the soft keyboard. Because the soft keyboard window is one component of the UI window, the owner should be the UI window as well. 
There are different types of soft keyboards. Each one is designed for a specific country or special purpose. An IME can change the reading characters on the soft keyboard by using one of two methods: IMC_SETSOFTKBDSUBTYPE or IMC_SETSOFTKBDDATA

软键盘是输入法显示的特殊窗口。有的输入法有特殊的读入串，输入法可以提供软键盘来显示这些特殊的读入串。通过这种方式，用户不必记住每个按键的读入串。比如，输入法可以使用`bo` `po` `mo` `fo`作为读入串，也可以使用原型串作为读入串。

输入法可以根据当前的转换状态修改读入串的按键，并告知用户这些按键的变化。比如，在选择候选的阶段，输入法可以仅显示选择键给用户。

输入法既可以创建自己的软键盘界面，也可以使用系统预定义的软键盘。如果输入法希望使用系统预定义的软键盘，它应该在`ImeInquire`函数被调用时，在IMEINFO::fdwUICap中设置UI_CAP_SOFTKBD标志。

输入法可以调用`ImmCreateSoftKeyboard`来创建软键盘窗口。可以调用`ImmShowSoftKeyboard`来显示或隐藏。由于软键盘窗口是输入法UI窗口的一个组件，因此它的父窗口就应该是输入法UI窗口。

有两种不同的软键盘，每一种是为特殊国家或特殊目的设计的。输入法可以通过两个方法`IMC_SETSOFTKBDSUBTYPE`或`IMC_SETSOFTKBDDATA`来修改软键盘中的读入串。

# 重新转换
> Reconversion is a new IME function for Windows 98 and Windows 2000. It provides the capability to reconvert a string that is already inserted in an application’s document. Specifically, whatever the string is, an IME is instructed to recognize the string, convert it to the reading or typing information, and then display the candidate list.
New and advanced intelligent IMEs are capable of recognizing and interpreting a complete sentence. When an IME is supplied with better information about a string, such as full sentence and string segmentation, it can accomplish better conversion performance and accuracy. For example, by supplying an entire sentence as opposed to just the reconverted strings, the IME can reconvert the string without having to first convert to reading or typing information.
Editing after the determination is harder than before today. This is because determination will discard most of the information undetermined string had, like reading, phrases, and part of speech. Reconversion will get these information back, making editing after the determination as easier as before the determination. Users will be able to choose different homonym words from candidates, change phrase break and let IME analyze again, and so forth.

重新转换是Win98/Win2000的输入法新功能。这是一种将已上屏的字串做重新转换的能力。无论该上屏串是什么，输入法都会收到指示来识别该串，将它转化为读入串或按键信息，然后重新显示候选列表。

新型输入法和更智能的输入法应具备识别和解释一个完整句子的能力。当输入法获得了比较完备的字串信息，比如完整的句子或段落，输入法能更高效更精准地完成转换。比如，当提供给输入法一个完整的句子用来做重新转换时，输入法不需要转换成读入串也不需要按键信息就能完成重新转换。

重新转换上屏串会比首次转换更难，因为上屏串已经抛弃了一些中间信息，比如按键、分词或者语音信息。重新转换需要重新找回这些信息，使得上屏后编辑能和首次一样容易。用户可以再重新转换的过程中选择不同的候选，修改不同的断句等等。

![](0224Win32ImeDev/img01.png)
`RECONVERTSTRING`结构体可以保存完整的句子和需要转换的起点位置和长度。如果dwStartOffset为0，dwLen为句子的长度，则需要输入法重新转换全部串。
## 简单重新转换
> The simplest reconversion is when the target string and the composition string are the same as the entire string. In this case, dwCompStrOffset and dwTargetStrOffset are zero, and dwStrLen, dwCompStrLen, and dwTargetStrLen are the same value. An IME will provide the composition string of the entire string that is supplied in the structure, and will set the target clause by its conversion result. 

最简单的重新转换是当目标串和输入法完全相同时。这种情况下dwCompStrOffset和dwTargetStrOffset为0，dwStrLen, dwCompStrLen和dwTargetStrLen均相等。输入法可以提供结构体中完整串的输入串，并根据转换结果设置目标分词信息。

## 普通重新转换
> For an efficient conversion result, the application should provide the RECONVERTSTRING structure with the information string. In this case, the composition string is not the entire string, but is identical to the target string. An IME can convert the composition string by referencing the entire string and then setting the target clause by its conversion result.

对于一个高效的转换结果，应用程序应当在结构体RECONVERTSTRING中提供信息串。在这种情况下，输入穿不是完整串，但可以被识别为目标串。输入法可以根据完整串来转换输入串，并根据转换结果设置分词信息。

## 高阶的重新转换
> Applications can set a target string that is different from the composition string. The target string (or part of the target string) is then included in a target clause in high priority by the IME. The target string in the RECONVERTSTRING structure must be part of the composition string. When the application does not want to change the user’s focus during the reconversion, the target string should be specified. The IME can then reference it.

应用程序可以把目标串和输入串设置为不同的字串。目标串被输入法以更高的优先级包含到目标分词信息中。结构体RECONVERTSTRING中的目标串必须作为输入串的一部分。如果应用程序不想在重新转换期间修改用户焦点，就需要指定目标串，输入法随后可以参考该串。

## 输入法取消重新转换
> When a user cancels the composition string generated by the reconversion, the IME should determine the original reconverted string. Otherwise, the application will loose the string.

当用户取消了由重新转换生成的写作串，输入法应当确定原始的重新转换串。否则应用程序会失去该写作串。

## SCS_SETRECONVERSTRIN 和 SCS_QUERYRECONVERTSTRING 标记
> Applications can ask an IME to reconvert the string by calling ImmSetCompositionString. They can use either the SCS_SETSTR flag or the SCS_SETRECONVERTSTRING flag to create a new composition string. However, by using SCS_SETRECONVERTSTRING, the application can pass RECONVERTSTRING to the IME for better conversion efficiency.
Initially, the application should call ImmSetCompositionString with SCS_QUERYRECONVERTSTRING. The selected IME can then adjust the given RECONVERTSTRING structure for appropriate reconversion. The application then calls ImmSetCompositionString with SCS_SETRECONVERTSTRING to request that the IME generate a new composition string. If the application asks the IME to adjust the RECONVERTSTRING structure by calling SCS_QUERYRECONVERTSTRING, efficient reconversion can be accomplished. 
SCS_SETRECONVERTSTRING or SCS_QUERYRECONVERTSTRING can be used only for IMEs that have an SCS_CAP_SETRECONVERTSTRING property. This property can be retrieved by using the ImmGetProperty function.

应用程序可以调用`ImmSetCompositionString`函数让输入法进行重新转换。可以使用SCS_SESTR标记或SCS_SETRECONVERTSTRING标记来创建新的输入串。但是通过使用SCS_SETRECONVERTSTRING标记，应用程序可以讲RECONVERTSTRING结构体传入输入法做更高效的转换。

首先，应用程序应调用函数`ImmSetCompositionString`，并传入SCS_QUERYRECONVERTSTRING。输入法将调整传入的RECONVERTSTRING结构体以便为重新转换做准备。应用程序接下来调用`ImmSetCompositionString`并传入SCS_SETRECONVERTSTRING来请求输入法生成一个新的写作串，如果应用程序通过SCS_QUERYRECONVERTSTRING请求输入法调整RECONVERTSTRING结构体，将完成一次有效转换。

SCS_SETRECONVERTSTRING或SCS_QUERYRECONVERTSTRING仅适用于带SCS_CAP_SETRECONVERTSTRING属性的输入法。该属性可以通过调用函数`ImmGetProperty`函数来获得。
## IMR_RECONVERSTRING 和 IMR_CONFIRMRECONVERTSTRING 消息
> When an IME wants to reconvert, it can ask the application to provide the string to be reconverted. For example, when a user presses the Reconversion key or selects the Reconversion button in the IME status window, the IME sends a WM_IME_REQUEST message with IMR_RECONVERTSTRING to get the target string. Initially, the IME needs to send this with NULL lParam in order to get the required size of RECONVERTSTRING. The IME then prepares a buffer to receive the target string and sends the message again with the pointer of the buffer in lParam. 
After the application handles IMR_RECONVERTSTRING, the IME may or may not adjust the RECONVERTSTRING structure given by the application. Finally, the IME sends a WM_IME_REQUEST message with IMR_CONFIRMRECONVERTSTRING to confirm the RECONVERTSTRING structure. 
If the application returns TRUE for IMR_CONFIRMRECONVERTSTRING, the IME generates a new composition string based on the RECONERTSTRING structure in the IMR_CONFIRMRECONVERTSTRING message. If the application returns FALSE, the IME generates a new composition string based on the original RECONVERTSTRING structure given by the application in the IMR_RECONVERTSTRING message. An IME will not generate a composition string for reconversion before IMR_CONFIRMRECONVERTSTRING
The given string should not be changed by SCS_QUERYRECONVERTSTRING or IMR_CONFIRMRECONVERTSTRING. An IME can change only CompStrOffset, CompStrLen, TargetStrOffset, and TargetStrLen to re-confirm it

当输入法希望做重新转换时，它可以请求应用程序提供待转换的字符串。比如，当用户按下了`重新转换`的按键，或者在输入法状态栏上点击了相应的按钮，输入法就会发送带有IMR_RECONVERTSTRING参数的WM_IME_REQUEST消息。首先，输入法应当在发送该消息时设置lParam为NULL，以便得到RECONVERTSTRING的尺寸，然后输入法根据该尺寸准备缓冲区来接收待转换的字串，并再次发送该消息，将lParam指向缓冲区。

应用程序处理完IMR_RECONVERTSTRING，输入法可能要根据应用程序提供的RECONVERTSTRING结构体来调整它。最终，输入法发送一条带有参数IMR_CONFIRMRECONVERTSTRING的WM_IME_REQUEST消息来确认RECONVERTSTRING结构体。

如果应用程序对IMR_CONFIRMRECONVERTSTRING返回TRUE，输入法将，基于在IMR_RECONVERTSTRING消息中的RECONVERTSTRING结构体生成一个新的写作串。如果应用程序返回FALSE，输入法将基于应用程序在消息IMR_RECONVERTSTRING中指定的原始RECONVERTSTRING结构体生成一个新的写作串。输入法将不会在IMR_CONFIRMRECONVERTSTRING之前重新转换成写作串。

给定的字串应当根据SCS_QUERYRECONVERTSTRING或IMR_CONFIRMRECONVERTSTRING而变化。输入法只能修改CompStrOffset, CompStrLen, TargetStrOffset, 和 TargetStrLen。

# IME 菜单函数
> The purpose of this function set is to reduce the IME-related icon in the system task bar. It is a new feature for Windows 98 and Windows 2000. 
The Windows system program installs two icons in the task bar when the current hKL is an IME. One icon is the System ML icon that indicates the current keyboard layout in the system task bar. The other is the System Pen icon that shows the IME status of the focused window. 
Usually, an IME places an additional icon in the task bar. The context menu for this icon is completely dependent on the IME. Having IME icons in a task bar is a quick way for a user to access an IME’s special functions. However, there are three icons associated with the IME and these additional icons may be more than a user wants to deal with.
If the system provides a way for an IME to insert IME menu items into the System Pen icon, the IME then does not need to add its extra icons to the task bar.
The IMM calls the IME function ImeGetImeMenuItems to get the IME menu items.
An application can use ImmGetImeMenuItems to get an IME’s special menu items, which it can add to its context menu. By calling ImmNotify, the selected items can be processed by the IME.

该函数群的目的是为了缩减系统任务栏中输入法相关的图标。如果系统当前的HKL是一个输入法，Windows系统程序会在任务栏安装两个图标。一个是系统多语言图标来表示当前的键盘布局；另一个是系统的笔形图标表示当前焦点窗口的输入法状态。输入法通常很少在任务栏放更多的图标。该图标的上下文菜单完全依赖于输入法。通过任务栏访问输入法图标是用户使用输入法功能的一种便捷的途径。然而如果输入法有太多的图标，这可能会让用户无法应付。

系统为输入法提供了一种向系统笔形图标添加菜单项的途径，这样输入法就不必项任务栏添加太多图标了。

IMM可以调用`ImeGetImeMenuItems`来获得输入法菜单项。

应用程序可以调用`ImmGetImeMenuItems`来获得输入法的指定菜单项，该菜单项可能是被输入法添加进来的。通过调用`ImmNotify`，输入法有机会处理选中的菜单项。
## 输入法菜单通知
> When an application wants to handle an IME’s menu items, it can call ImmNotifyIME. When the menu items added by the IME are selected, NotifyIME is called under the focused thread. 

应用程序可以调用`ImmNotifyIME`来处理输入法菜单项。当输入法添加的菜单项被点击时，函数`NotifyIME`会在焦点线程中调用。

# IME 帮助文件
> The IME help file is a new function added into Windows 98 and Windows NT. The right click menu of the System Pen Icon has two menu items. One is the setting for the IME system and is used to change the setting of the selected IME of the focus thread. The other menu item is an online Help file that has never been enabled. Thus, this menu item is always grayed. The purpose of this menu item was to display an IME’s online Help. However, because the system does not provide the IME with a way to specify the name of the IME help file, the system task bar program is not able to display it.

右键系统笔形图标会有两个菜单项，一个用来设置焦点线程的输入法设置选项；另一个去到在线帮助。如果菜单项的使能标记为FALSE，菜单就会置灰。

## IME_ESC_GETHELPFILENAME
> The IME_ESC_GETHELPFILENAME escape allows an IME to specify its help file name. On return from the function, the (LPTSTR)lpData is the full path file name of an IME’s help file. 
If the help content is HTML help format, please make sure the help file extension is .chm so the Windows User knows which help engine to start.

转移功能`IME_ESC_GETHELPFILENAME`允许输入法指定帮助文件。该函数会将帮助文件的路径名传入lpData返回给调用端。

如果帮助内容是HTML格式，请确认帮助文件的后缀名为.chm，以便输入法用户知道应当启动什么帮助引擎。

# 输入法指示器
> By using a set of messages defined in Windows 98 and Windows 2000, an IME can change the icon and ToolTip string for the System Pen icon on the system task bar.

输入法可以修改系统语言栏笔形图标即提示文字。
## 指示窗口
> An IME can get the window handle of the indicator by using FindWindow with INDICATOR_CLASS. 

输入法可以通过调用函数`FindWindow`并传入INDICATOR_CLASS来获得指示器句柄：
``` c++
// 得到指示器窗口句柄
hwndIndicator = FindWindow(INDICATOR_CLASS, NULL);
if (!hwndIndicator){ // 没有指示器窗口，托盘没有笔形图标
    return FALSE;
}
// 修改笔形图标
PostMessage(hwndIndicator, INIDCM_SETIMEICON, nIconIndex, hMyKL);
```

> Note
Due to the internal design requirement in the task bar manager, the IME must use PostMessage for INDICM_xxx messages.

**注意**
由于系统任务栏管理器设计的内部需要，输入法必须使用`PostMessage`函数来发送`INDICM_xxx`类消息。

## 消息
> IMEs can send the following messages ‹MAKE INTO JUMPS›to the Indicator window to perform different tasks:

输入法可以向指示器发送如下消息来完成不同的任务：
INDICM_SETIMEICON
INDICM_SETIMETOOLTIPS
INDICM_REMOVEDEFAULTMENUITEMS

# WinNT和Win2000议题
> The following topics primarily describe the special issues related to Windows NT/2000. However, some of these issues may also apply to Windows 98. 

下面的议题主要与WinNT和Win2000相关。
## 输入法和本地化语言能力
> Windows 2000 has full-featured IME support in any localized language version. That is, an IME can be installed and used with any Windows 2000 language. IME developers should test their IME on these environments. This new feature also requires IME developers to prepare their IME help content to include correct charset and font information so it shows up correctly on different language operating systems. 
Also, IME developers should develop Unicode IME for Windows 2000. Unicode IMEs will work with Unicode applications under any system locale. For non-Unicode IMEs, the user must change the system locale to support the same language that the IME supports in order to use them. 

Win2000包含了IME框架支持的所有功能。输入法可以在任何语言的Win2000系统中安装和使用。输入法开发者应当在这些环境下充分测试。该特性还需要输入法的开发者准备好正确的字符集、字体信息，以便输入法能在不同语言的操作系统上正常运行。

此外，输入法的开发者还应为Win2000开发Unicode版本。Unicode输入法将能在任何语言下的Unicode程序中正常运行。对于非unicode的输入法，用户必须修改系统locale来支持相同语言的输入法，才能让它正常运行。
## Unicode接口
> Along with the ANSI version of the IMM/IME interface originally supported by Windows 95, Windows NT and Windows 98 support Unicode interface for the IME. To communicate with the system by Unicode interface, an IME should set the IME_PROP_UNICODE bit of the fdwProperty member of the IMEINFO structure, which is the first parameter of the ImeInquire function. Although ImeInquire is called to initialize the IME for every thread of the application process, the IME is expected to return the same IMEINFO structure on a single system. Windows 98 supports all the Unicode functions, except for ImmIsUIMessage.

从WinNT和Win98开始，系统支持输入法的Unicode接口。为了能和系统之间以Unicode接口来通讯，输入法需要在`ImeInquire`函数中为IMEINFO::fdwProperty设置IME_PROP_UNICODE标记。对于应用程序中的每个线程，系统会调用函数`ImeInquire`用来初始化输入法，输入法每次都会返回相同的IMINFO结构体。
## 安全考虑
> There are two primary security concerns for Windows NT. One involves named objects and the other involves Winlogon.

有两个主要的安全议题需要考虑：一个是命名对象，另一个是Winlogon进程。
### 命名内核对象
> An IME may want to create various named objects that should be accessed from multiple processes on the local system. Such objects may include file, mutex, or event. Since a process might belong to a different user who is interactively logging onto the system, the default security attribute (created by the system when an IME creates an object with the NULL parameter as the pointer to the security attribute) may not be appropriate for all processes on the local system. 
On Windows NT, the first client process of the IME may be the Winlogon process that lets a user log onto the system. Since the Winlogon process belongs to the system account during the log-on session and is alive until the system shuts down, named objects created by the IME with the default security attribute during the log-on session cannot be accessed through other processes belonging to a logged-on user.
A sample IME source code that creates the security attribute appropriated for named objects is provided in the Microsoft Platform DDK. By using the sample code, IME writers can create various named objects that can be accessed from all client processes of the IME on the local system. The security attribute allocated by the sample code is per process. An IME that frequently creates named objects may want to initialize the security attribute attach time and free the security attribute at the process detach time. An IME that does not create named objects often may want to initialize the security attribute just before the creation of the named object and then free the security attribute just after the object is created.

输入法可以创建各种跨进程访问的命名对象。这些对象可能有文件、锁或事件。由于进程可能属于不同的Windows用户，默认的安全属性（输入法传入NULL作为安全属性参数而创建的命名对象）未必适用于所有的本地进程。

在WinNT下，输入法第一个宿主进程可能是Winlogon，通过它，用户可以登录到系统。由于Winlogon进程属于系统账号，它的生命周期始于系统登录前，到关机才终止。输入法在Winlogon中以默认安全属性创建的命名对象可能在其它的登录用户进程里无法访问。

微软Platform DDK中提供的输入法示例代码中演示了如何为命名对象创建合适的安全属性。该段代码可以指导输入法开发人员如何创建各种在所有进程中都可以访问的命名对象。命名对象的安全属性是每进程一份的。经常创建命名对象的输入法可能希望在进程attach时完成安全属性的初始化，在进程detach时完成安全属性的释放。一个不创建命名对象的输入法，常常希望在创建命名对象前完成初始化安全属性，在创建之后释放安全属性。
### Winlogon
> Since a user in the log-on session has not been granted the access right to the system yet, information provided by an IME’s configuration dialog boxes can create security problems. Even though, the system administrator can configure the system so such an IME cannot be activated on the log-on session. A well-behaved IME should not allow users to open configure dialog boxes if the client process is a Winlogon process. An IME can check if the client process executing a log-on session is a Winlogon process by checking the IME_SYSTEMINFO_WINLOGON bit of the dwSystemInfoFlags parameter of ImeInquire.

由于在登录期间，用户并没有赋予访问系统的权限，此时弹出输入法设置对话框可能会带来安全问题。尽管系统管理员可能要配置系统，但在尚未登录时，输入法不应该被激活。输入法应当不允许用户在Winlogong中打开输入法配置对话框。输入法可以在函数`ImeInquire`中检查dwSystemInfoFlags是否具有 IME_SYSTEMINFO_WINLOGON标志位来确定当前是否在Winlogon进程中。
# IME文件格式和数据
> The following topics discuss the IME file format and data structures used by the IME. 

下面的议题主要讨论IME文件格式和输入法使用到的数据结构。
## IME文件格式
> An IME needs to specify the following fields correctly in the version information resource. This includes the fixed file information part and the variable length information part. Please refer to the Microsoft Platform SDK for detailed information on version information resource. 
Following are the specific settings the IME file should include:
dwFileOS
The dwFileOS should be specified in the root block of the version information. The dwFileOS should be VOS__WINDOWS32 for Windows 95 and Windows NT IMEs.
dwFileType
The dwFileType should be specified in the root block of the version information. The value is VFT_DRV.
dwFileSubtype
The dwFileSubtype should be specified in the root block of the version information. The value is VFT2_DRV_INPUTMETHOD.
FileDescription
The FileDescription is specified in the language-specific block of the version information. This should include the IME name and the version. This string is for display purposes only. Currently, the string length is 32 TCHARS, but may be extended in a future version.
ProductName
The ProductName is specified in the language-specific block of the version information. 
Charset ID and Language ID
The code page (character set ID) and language ID are specified in the variable information block of the version information resource. If there are many code pages (character set ID) and language IDs are specified in the block, the IME uses the first code page ID to display the text and uses the first language ID for the IME language. The charset ID and language ID must match the IME language instead of the resource language. The file name of IME is 8.3. 

输入法的IME文件需要在资源文件的版本信息中指定如下的字段，它们包含文件信息的定长部分和变长部分。关于资源文件的版本信息的细节可以参见微软Plat SDK。下面是输入法的IME文件必须包含的：
** dwFileOS **
在版本信息的root块中定义，应当置为VOS_WINDOWS32
** dwFileType **
在版本信息的root块中定义，应当置为VFT_DRV
** dwFileSubtype **
在版本信息的root块中定义，应当置为VFT2_DRV_INPUTMETHOD
** FileDescription **
在版本信息的language-specific块中定义。应当包含输入法的名字和版本号。该字串仅仅是为了显示之用。目前最大长度为32个TCHAR，未来版本可能会扩充。
** ProductName **
在版本信息的language-specific块中定义。
** Charset ID和Language ID **
在版本信息的变量信息块中定义。如果指定了多个Charset ID和Language ID，输入法将使用第一个字符集代码页来显示文字信息，使用第一个Language ID作为输入法的语言。Charset ID和Language ID必须和输入法语言相匹配。
## IME注册表内容
> The IME HKEY_CURRENT_USER registry contains an Input Method key. The following table describes the contents of this Input Method.
Key
Contents

> Input Method
There are four value names: Perpendicular Distance, Parallel Distance, Perpendicular Tolerance, and Parallel Tolerance. The near caret operation IME refers to these values. If these four value names are not present, a near operation IME can set a default value, depending on the IME

> Value Name
Value Data


> Perpendicular Distance
Distance is perpendicular to the text escapement. This is the perpendicular distance (pixels) from the caret position to the composition window without the font height and width. The near caret operation IME will adjust the composition window position according to this value and Parallel Distance. It is in REG_DWORD format.

> Parallel Distance
Distance (pixels) is parallel to the text escapement. This is the parallel distance from the caret position to the composition window. It is in REG_DWORD format.

> Perpendicular Tolerance
Tolerance (pixels) is perpendicular to the text escapement. This is the perpendicular distance from the caret position to the composition window. The near caret operation IME will not refresh its composition window if the caret movement is within this tolerance. It is in REG_DWORD format.

> Parallel Tolerance
Tolerance (pixels) is parallel to the text escapement. This is the parallel distance from the caret position to the composition window. It is in REG_DWORD format.

> An IME can place the per-user setting into:
Under HKEY_CURRENT_USER\Software\<Company Name>\Windows\CurrentVersion\<IME Name>.

> An IME can place the per computer setting into:
Under HKEY_LOCAL_MAACHINE\Software\<Company Name>\Windows\CurrentVersion\<IME Name>.

在注册表HKEY_CURRENT_USER中包含了输入法的key，下面列出了这些Key和相关含义：
** Key = `Input Metod` **
有四个value name：`Perpendicular Distance`, `Parallel Distance`, `Perpendicular Tolerance` 和 `Parallel Tolerance`。如果这四个值不存在，最近的输入法操作会根据不同的输入法设置默认值。
* Value Name = `Perpendicular Distance`
Value Data 这是一个REG_DWORD类型的数据，是文本的垂直行距。即从光标位置到写作窗口的像素数，输入法会根据该值调整写作窗口的位置。不包含字体的宽高。
* Value Name = `Parallel Distance`
Value Data 这是一个REG_DWORD类型的数据，是文本的水平间距。即从光标位置到写作窗口水平距离的像素数。
* Value Name = `Perpendicular Tolerance`
Value Data 这是一个REG_DWORD类型的数据，是文本的垂直行距。即从光标位置到写作窗口的像素数，如果光标的移动区间在此范围内，输入法将不会刷新写作窗口。
* Value Name = `Parallel Tolerance`
Value Data 这是一个REG_DWORD类型的数据，是文本的水平间距。即从光标到写作窗口水平距离的像素数。

输入法可以将每个用户的设置放到：
HKEY_CURRENT_USER\Software\<Company Name>\Windows\CurrentVersion\<IME Name>
可以将每台机器的设置放到：
HKEY_LOCAL_MAACHINE\Software\<Company Name>\Windows\CurrentVersion\<IME Name>
## IMM和IME数据结构
> The following structures are used for IMM and IME communication. IMEs can access these structures directly, but applications cannot. 

下面是IMM和IME通讯时使用的数据结构，IME可以直接访问这些数据结构，但应用程序不能。
### INPUTCONTEXT
> The INPUTCONTEXT structure is an internal data structure that stores Input Context data.
typedef struct tagINPUTCONTEXT {
HWND hWnd;
BOOL fOpen;
POINT ptStatusWndPos;
POINT ptSoftKbdPos;
DWORD fdwConversion;
DWORD fdwSentence;
union {
            LOGFONTA    A;
            LOGFONTW    W;
} lfFont;
COMPOSITIONFORM cfCompForm;
CANDIDATEFORM cfCandForm[4];
HIMCC hCompStr;
HIMCC hCandInfo;
HIMCC hGuideLine
HIMCC hPrivate; 
DWORD dwNumMsgBuf;
HIMCC hMsgBuf;
DWORD fdwInit
DWORD dwReserve[3];
} INPUTCONTEXT;
 
>Members
hWnd
Window handle that uses this Input Context. If this Input Context has shared windows, this must be the handle of the window that is activated. It can be reset with ImmSetActiveContext.
fopen
Present status of opened or closed IME.
ptStatusWndPos
Position of the status window.
ptSoftKbdPos
Position of the soft keyboard.
fdwConversion
Conversion mode that will be used by the IME composition engine.
fdwSentence
Sentence mode that will be used by the IME composition engine.
lfFont
LogFont structure to be used by the IME User Interface when it draws the composition string.
cfCompForm
COMPOSITIONFORM structure that will be used by the IME User Interface when it creates the composition window.
cfCandForm[4]
CANDIDATEFORM structures that will be used by the IME User Interface when it creates the candidate windows. This IMC supports four candidate forms.
hCompStr
Memory handle that points to the COMPOSITIONSTR structure. This handle is available when there is a composition string.
hCandInfo
Memory handle of the candidate. This memory block has the CANDIDATEINFO structure and some CANDIDATELIST structures. This handle is available when there are candidate strings.
hGuideLine
Memory handle of GuideLine. This memory block has the GUIDELINE structure. This handle is available when there is guideline information.
hPrivate
Memory handle that will be used by the IME for its private data area.
dwNumMsgBuf
Number of messages that are stored in the hMsgBuf.
hMsgBuf
Memory block that stores the messages in TRANSMSG format. The size of the buffer should be able to store the dwNumMsgBuf amount of TRANSMSGs. This buffer was previously defined in Windows 95/98 and Windows NT 4.0 IME document as the format as [Message1] [wParam1] [lParam1] {[Message2] [wParam2] [lParam2]{...{...{...}}}}, andall values are double word for Win32 platforms.
fdwinit
Initialize flag. When an IME initializes the member of the INPUTCONTEXT structure, the IME has to see the bit of this member. The following bits are provided.
Bit
Description

>INIT_STATUSWNDPOS
Initialize ptStatusWndPos.
INIT_CONVERSION
Initialize fdwConversion.
INIT_SENTENCE
Initialize fdwSentence.
INIT_LOGFONT
Initialize lfFont.
INIT_COMPFORM
InitializecfCompForm.
INIT_SOFTKBDPOS
Initialize ptSoftKbdPos.

>dwReserve[3]
Reserved for future use.


>Note
During a call to ImeToAsciiEx, an IME can generate the messages into the lpdwTransKey buffer. However, if an IME wants to generate the messages to the application, it can store the messages in hMsgBuf and call ImmGenerateMessage. The ImmGenerateMessage function then sends the messages in hMsgBuf to the application.

该结构体用于存放输入上下文的数据
``` c++
typedef struct tagINPUTCONTEXT {
    // 使用该上下文的窗体句柄。如果多个窗体共享上下文，该句柄就是当前活动窗体的。
    // 可以通过ImmSetActiveContext函数来重置。
    HWND hWnd;
    BOOL fOpen;             // 输入法的开-闭状态
    POINT ptStatusWndPos;   // 状态栏位置
    POINT ptSoftKbdPos;     // 软键盘位置
    DWORD fdwConversion;    // 输入法的转换状态
    DWORD fdwSentence;      // 句子状态
    union {
        LOGFONTA    A;
        LOGFONTW    W;
    } lfFont;                   // 输入法绘制写作窗使用的字体
    COMPOSITIONFORM cfCompForm; // 创建写作窗时创建的结构体
    CANDIDATEFORM cfCandForm[4];// 创建候选窗时创建的结构体数组，有四个元素
    HIMCC hCompStr; // 指向COMPOSITIONSTR结构体的内存句柄，仅在有写作串时才有效

    // 候选的内存句柄，该内存块是一个CANDIDATEINFO结构体和若干
    // CANDIDATELIST结构体。仅在有候选串时该句柄才有效。
    HIMCC hCandInfo; 

    // GuideLine的内存句柄，该内存块是一个GUIDELINE结构体，
    // 仅在有guideline信息时，该句柄才有效。
    HIMCC hGuideLine
    HIMCC hPrivate;     // 输入法私有数据区域的内存句柄
    DWORD dwNumMsgBuf;  // 在hMsgBuf中保存了多少条消息

    // 该内存块中保存的是TRANSMSG格式的消息数组。其中具体格式为：
    // [Message1][wParam1][lParam1]{[Message2][wParam2][lParam2]
    // {...{...{...}}}}，每个数据都是一个双字。
    HIMCC hMsgBuf;
    DWORD fdwinit;      // 初始化标志，下面描述
    DWORD dwReserve[3]; // 保留字段
} INPUTCONTEXT;
```
在输入法初始化INPUTCONTEXT成员时，需要参见成员`fdwinit`，每个位的信息如下：

Bit|描述
----|----
INIT_STATUSWNDPOS|初始化ptStatusWndPos
INIT_CONVERSION|初始化fdwConversion.
INIT_SENTENCE|初始化fdwSentence.
INIT_LOGFONT|初始化lfFont.
INIT_COMPFORM|初始化cfCompForm.
INIT_SOFTKBDPOS|初始化ptSoftKbdPos.


** 注意 **
在调用`ImeToAsciiEx`函数时，输入法可以向lpdwTransKey缓冲区中组装消息。但是如果输入法希望向应用程序发送消息，它也可以把消息组装到hMsgBuf中并调用ImmGenerateMessage，该函数就会将hMsgBuf中的消息发送到应用程序。

### COMPOSITIONSTR
> The COMPOSITIONSTR structure contains the composition information. During conversion, an IME places conversion information into this structure.
typedef struct tagCOMPOSITIONSTR {
DWORD dwSize;
DWORD dwCompReadAttrLen;
DWORD dwCompReadAttrOffset;
DWORD dwCompReadClsLen;
DWORD dwCompReadClsOffset;
DWORD dwCompReadStrLen;
DWORD dwCompReadStrOffset;
DWORD dwCompAttrLen;
DWORD dwCompAttrOffset;
DWORD dwCompClsLen;
DWORD dwCompClsOffset;
DWORD dwCompStrLen;
DWORD dwCompStrOffset;
DWORD dwCursorPos;
DWORD dwDeltaStart;
DWORD dwResultReadClsLen;
DWORD dwResultReadClsOffset;
DWORD dwResultReadStrLen;
DWORD dwResultReadStrOffset;
DWORD dwResultClsLen;
DWORD dwResultClsOffset;
DWORD dwResultStrLen;
DWORD dwResultStrOffset;
DWORD dwPrivateSize;
DWORD dwPrivateOffset; 
} COMPOSITIONSTR;
 
> Members
dwSize
Memory block size of this structure. 
dwCompReadAttrLen
Length of the attribute information of the reading string of the composition string.
dwCompReadAttrOffset
Offset from the start position of this structure. Attribute information is stored here.
dwCompReadClsLen
Length of the clause information of the reading string of the composition string.
dwCompReadClsOffset
Offset from the start position of this structure. Clause information is stored here.
dwCompReadStrLen
Length of the reading string of the composition string.
dwCompReadStrOffset
Offset from the start position of this structure. Reading string of the composition string is stored here.
dwCompAttrLen
Length of the attribute information of the composition string.
dwCompAttrOffset
Offset from the start position of this structure. Attribute information is stored here.
dwCompClsLen
Length of the clause information of the composition string.
dwCompClsOffset
Offset from the start position of this structure. Clause information is stored here.
dwCompStrLen
Length of the composition string.
dwCompStrOffset
Offset from the start position of this structure. The composition string is stored here.
dwCursorPos
Cursor position in the composition string.
dwDeltaStart
Start position of change in the composition string. If the composition string has changed from the previous state, the first position of such a change is stored here. 
dwResultReadClsLen
Length of the clause information of the reading string of the result string.
dwResultReadClsOffset
Offset from the start position of this structure. Clause information is stored here.
dwResultRieadStrLen
Length of the reading string of the result string.
dwResultReadStrOffset
Offset from the start position of this structure. Reading string of the result string is stored at this point.
dwResultClsLen
Length of the clause information of the result string.
dwResultClsOffset
Offset from the start position of this structure. Clause information is stored here.
dwResultStrLen
Length of the result string.
dwResultStrOffset
Offset from the start position of this structure. Result string is stored here.
dwPrivateSize
Private area in this memory block.
dwPrivateOffset
Offset from the start position of this structure. Private area is stored here.


> Note
For Unicode: All dw*StrLen members contain the size in Unicode characters of the string in the corresponding buffer. Other dw*Len and dw*Offset members contain the size in bytes of the corresponding buffer.

> The format of the attribute information is a single-byte array and specifies the attribute of string. The following values are provided. Those not listed are reserved.
Value
Content

> ATTR_INPUT
Character currently being entered.
ATTR_TERGET_CONVERTED
Character currently being converted (already converted).
ATTR_CONVERTED
Character given from the conversion.
ATTR_TERGET_NOTCONVERTED
Character currently being converted (yet to be converted).
ATTR_FIXEDCONVERTED
Characters will not be converted anymore. 
ATTR_INPUT_ERROR
Character is an error character and cannot be converted by the IME.

> Following is a description of the content for the values provided in the preceding table.
Content
Description
Character currently being entered.
Character that the user is entering. If this is Japanese, this character is a hiragana, katakana, or alphanumeric character that has yet to be converted by the IME.
Character currently being converted (already converted).
Character that has been selected for conversion by the user and converted by the IME.
Character given from conversion.
Character which the IME has converted.
Character currently being converted (yet to be converted).
Character that has been selected for conversion by the user and not yet converted by the IME. If this is Japanese, this character is a hiragana, katakana, or alphanumeric character that the user has entered.
Character is an error character and cannot be converted by the IME.
Character is an error character and the IME cannot convert this character. For example, some consonants cannot be combined.

> Comments
The length of the attribute information is the same as the length of the string. Each byte corresponds to each byte of the string. Even if the string includes DBCS characters, the attribute information has the information bytes of both the lead byte and the second byte.
For Windows NT Unicode, the length of the attribute information is the same as the length in Unicode character counts. Each attribute byte corresponds to each Unicode character of the string.
The format of the clause information is a double-word array and specifies the numbers that indicate the position of the clause. The position of the clause is the position of the composition string, with the clause starting from this position. At the least, the length of information is two double words. This means the length of the clause information is 8 bytes. The first double word has to be zero and is the start position of the first clause. The last double word has to be the length of this string. For example, if the string has three clauses, the clause information has four double words. The first double word is zero. The second double word specifies the start position of the second clause. The third double word specifies the start position of the third clause. The last double word is the length of this string.
For Windows NT Unicode, the position of each clause and the length of the string is counted in Unicode characters.
The dwCursorPos member specifies the cursor position and indicates where the cursor is located within the composition string, in terms of the count of that character. The counting starts at zero. If the cursor is to be positioned immediately after the composition string, this value should be equal to the length of the composition string. In the event there is no cursor, a value of -1 is specified here. If a composition string does not exist, this member is invalid.
For Windows NT Unicode, the cursor position is counted in Unicode characters.

该结构体包含了写作串信息。在转换期间，输入法会把转换信息放到该结构体中。
``` c++
typedef struct tagCOMPOSITIONSTR {
DWORD dwSize;   // 本结构体的尺寸
DWORD dwCompReadAttrLen;    // 读入串的属性信息的长度
DWORD dwCompReadAttrOffset; // 距离本结构体头部的偏移，保存属性信息
DWORD dwCompReadClsLen;     // 读入串的分词信息
DWORD dwCompReadClsOffset;  // 距离本结构体头部的偏移，保存分词信息
DWORD dwCompReadStrLen;     // 读入串的长度
DWORD dwCompReadStrOffset;  // 距离本结构体头部的偏移，保存读入串
DWORD dwCompAttrLen;        // 写作串的属性信息的长度
DWORD dwCompAttrOffset;     // 距离本结构体头部的偏移，保存属性信息
DWORD dwCompClsLen;         // 写作串分词信息的长度
DWORD dwCompClsOffset;      // 距离本结构体头部的偏移，保存分词信息
DWORD dwCompStrLen;         // 写作串的长度
DWORD dwCompStrOffset;      // 距离本结构体头部的偏移，保存写作串
DWORD dwCursorPos;          // 光标在写作串中的位置

// 写作串发生变化的起始位置，如果写作串从前一个位置发生变化，
// 每次变化的位置保存在这里
DWORD dwDeltaStart;
DWORD dwResultReadClsLen;   // 读入串的分词信息
DWORD dwResultReadClsOffset;// 距离本结构体头部的偏移，保存分词信息
DWORD dwResultReadStrLen;   // 结果串的读入串长度
DWORD dwResultReadStrOffset;// 距离本结构体头部的偏移，保存结果串的读入串
DWORD dwResultClsLen;       // 结果串的分词信息长度
DWORD dwResultClsOffset;    // 距离本结构体头部的偏移，保存分词信息
DWORD dwResultStrLen;       // 结果串长度
DWORD dwResultStrOffset;    // 距离本结构体头部的偏移，保存结果串
DWORD dwPrivateSize;        // 私有区域的内存块
DWORD dwPrivateOffset;      // 距离本结构体头部的偏移，保存私有区域
} COMPOSITIONSTR;
```
** 注意 **
对于Unicode，dw\*StrLen成员都表示Unicode字符个数；而dw\*Len或dw\*Offset则是以字节数计算的尺寸。

属性信息的格式是以单字节为元素的数组，下面列出了它们的取值范围和含义：

值|内容|说明
----|----|----
ATTR_INPUT|正在输入的字符|如果是日文，该字符是平假名、片假名或字母数字，正要交由输入法转换
ATTR_TERGET_CONVERTED|正在（已经）转换的字符|已经被用户选中即将交由输入法转换
ATTR_CONVERTED|转换后的结果字符|
ATTR_TERGET_NOTCONVERTED|正在转换（尚未完成）的字符|已经被用户选中即将交由输入法转换。如果是日文，该字符是平假名、片假名或字母数字，正要交由输入法转换。
ATTR_FIXEDCONVERTED|不会再被转换的字符|
ATTR_INPUT_ERROR|由于发生错误而不能转换的字符|例如一些辅音字母无法被转换

** 说明 **
属性信息的长度等同于字串长度。每个字节对应字串中的一个字节。即使字串中包含DBCS字符，属性信息依然有两个字节对应字符的两个字节。

对于WinNT Unicode，属性信息的长度等同于Unicode字符个数。每个属性字节对应一个Unicode字符。

分词信息是以双字为元素的数组，它指定了描述分词位置的数字。分词位置是在写作串中的位置，是分词的起始位置。最终的信息长度是两个双字，即8字节。第一个双子必须为0，表示第一个分词的起始位置；接下来的一个双字是字串的长度。比如如果字串有三个分词，分词信息将有4个双字。第一个为0，第二个指定了第二个分词的起始位置，第三个双字指定了第三个分词的起始位置，最后一个双字是该串的长度。

对于WinNT Unicode，每个分词的位置和字串长度都是以Unicode字符个数计算的。

dwCursorPos指定了光标位置，表示光标正在写作串中的什么位置，是基于0的以字符个数来计算的。如果光标在写作串的末尾，该值应当等于写作串的长度。如果没有光标，该值为-1。如果当前没有写作串，该值无效。

### CANDIDATEINFO
> The CANDIDATEINFO structure is a header of the entire candidate information. This structure can contain 32 candidate lists at most, and these candidate lists have to be in the same memory block.
typedef struct tagCANDIDATEINFO {
DWORD dwSize;
DWORD dwCount;
DWORD dwOffset[32];
DWORD dwPrivateSize;
DWORD dwPrivateOffset;
} CANDIDATEINFO;
 
> Members
dwSize
Memory block size of this structure. 
dwCount
Number of the candidate lists that are included in this memory block.
dwOffset[32]
Contents are the offset from the start position of this structure. Each offset specifies the start position of each candidate list.
dwPrivateSize
Private area in this memory block.
dwPrivateOffset
Offset from the start position of this structure. The private area is stored here.

该结构体只是完整的候选信息的头部。最长可以包含32个候选列表，这些候选列表必须在同一个内存块内。
``` c++
typedef struct tagCANDIDATEINFO {
    DWORD dwSize;           // 本结构体的长度
    DWORD dwCount;          // 候选列表的个数
    DWORD dwOffset[32];     // 距离本结构体头部的偏移，每个偏移指向一个候选列表
    DWORD dwPrivateSize;    // 私有区域
    DWORD dwPrivateOffset;  // 距离本结构体头部的偏移，保存私有区域
} CANDIDATEINFO;
```
### GUIDELINE
> The GUIDELINE structure contains the guideline information that the IME sends out.
typedef struct tagGUIDELINE {
DWORD dwSize;
DWORD dwLevel;      // the error level.
// GL_LEVEL_NOGUIDELINE, 
// GL_LEVEL_FATAL, 
// GL_LEVEL_ERROR, 
// GL_LEVEL_WARNNING,
// GL_LEVEL_INFORMATION
    DWORD dwIndex;      // GL_ID_NODICTIONARY and so on.
    DWORD dwStrLen;     // Error Strings, if this is 0, there 
                        // is no error string.
DWORD dwStrOffset;
DWORD dwPrivateSize;
DWORD dwPrivateOffset;
} GUIDELINE;
 

> Note
For Unicode, the dwStrLen member specifies the size in Unicode characters of the error string. Other size parameters such as dwSize dwStrOffset, dwPrivateSize contain values counted in bytes.

> Members
dwLevel
The dwLevel specifies error level. The following values are provided.
Value
Description

> GL_LEVEL_NOGUIDELINE
No guideline present. If the old guideline is shown, the UI should hide the old guideline.
GL_LEVEL_FATAL
Fatal error has occurred. Some data may be lost.
GL_LEVEL _ERROR
Error has occurred. Handling may not be continued.
GL_LEVEL _WARNING
IME warning to user. Something unexpected has occurred, but the IME can continue handling.
GL_LEVEL _INFORMATION
Information for the user.

> dwIndex
The following values are provided.
Value
Description

> GL_ID_UNKNOWN
Unknown error. The application should refer to the error string.
GL_ID_NOMODULE
IME cannot find the module that the IME needs.
GL_ID_NODICTIONARY
IME cannot find the dictionary or the dictionary looks strange.
GL_ID_CANNOTSAVE
Dictionary or the statistical data cannot be saved.
GL_ID_NOCONVERT
IME cannot convert anymore.
GL_ID_TYPINGERROR
Typing error. The IME cannot handle this typing.
GL_ID_TOOMANYSTROKE
Two many keystrokes for one character or one clause.
GL_ID_READINGCONFLICT
Reading conflict has occurred. For example, some vowels cannot be combined. 
GL_ID_INPUTREADING
IME prompts the user now it is in inputting reading character state.
GL_ID_INPUTRADICAL
IME prompts the user now it is in inputting radical character state.
GL_ID_INPUTCODE
IME prompts the user to input the character code state.
GL_ID_CHOOSECANIDATE
IME prompts the user to select the candidate string state.
GL_ID_REVERSECONVERSION
IME prompts the user to provide the information of the reverse conversion. The information of reverse conversion can be obtained through ImmGetGuideLine(hIMC, GGL_PRIVATE. lpBuf, dwBufLen).The information contained in lpBuf is in CANDIDATELIST format.
GL_ID_PRIVATE_FIRST
ID located between GL_ID_PRIVATE_FIRST and GL_ID_PRIVATE_LAST is reserved for the IME. The IME can freely use these IDs for its own GUIDELINE.
GL_ID_PRIVATE_LAST
ID located between GL_ID_PRIVATE_FIRST and GL_ID_PRIVATE_LAST is reserved for the IME. The IME can freely use these IDs for its own GUIDELINE.

> dwPrivateSize
Private area in this memory block.
dwPrivateOffset
Offset from the start position of this structure. The private area is stored here.

该结构体包含输入法的guideline信息。
``` c++
typedef struct tagGUIDELINE {
    DWORD dwSize;
    DWORD dwLevel;      // 错误级别，具体参见下面
    DWORD dwIndex;      // 具体参见下面 GL_ID_NODICTIONARY and so on.
    DWORD dwStrLen;     // Error Strings, if this is 0, there 
                        // is no error string.
    DWORD dwStrOffset;
    DWORD dwPrivateSize;    // 私有区域的内存块
    DWORD dwPrivateOffset;  // 距离本结构体头部的偏移，保存私有区域
} GUIDELINE;
```
** 注意 **
对于Unicode，dwStrLen表示Unicode字符数，dwSize、dwStrOffset、dwPrivateSize则是字节数。

dwLevel的取值范围和含义：

值|描述
----|----
GL_LEVEL_NOGUIDELINE|没有guideline提供。如果旧的guideline已经显示，UI将隐藏它
GL_LEVEL_FATAL|发生了致命的错误，可能有数据丢失
GL_LEVEL _ERROR|发生了错误，处理可能被终止
GL_LEVEL _WARNING|发生了异常，但输入法能继续处理
GL_LEVEL _INFORMATION|一般信息

dwIndex的取值范围和含义：

值|描述
----|----
GL_ID_UNKNOWN|未知错误，应用程序应当参见错误字串
GL_ID_NOMODULE|输入法找不到需要的模块
GL_ID_NODICTIONARY|输入法找不到字典
GL_ID_CANNOTSAVE|字典或静态数据无法保存
GL_ID_NOCONVERT|输入法无法完成转换
GL_ID_TYPINGERROR|按键错误，输入法无法处理该按键
GL_ID_TOOMANYSTROKE|对于一个字符或分词有两个以上的击键
GL_ID_READINGCONFLICT|读冲突，比如某些元音字母无法转换
GL_ID_INPUTREADING|输入法提示用户当前正处于输入读入串的状态
GL_ID_INPUTRADICAL|输入法提示用户当前正处于输入偏旁的状态
GL_ID_INPUTCODE|输入法提示用户当前正处于输入字符码的状态
GL_ID_CHOOSECANIDATE|输入法提示用户当前正处于选择候选的状态
GL_ID_REVERSECONVERSION|输入法提示用户提供反向转换信息。可以通过函数ImmGetGuideLine来获得该信息，该信息中包含lpBuf是以CANDIDATELIST的格式存在的。
GL_ID_PRIVATE_FIRST|在区间[GL_ID_PRIVATE_FIRST, GL_ID_PRIVATE_LAST]为输入法保留ID，输入法可以自由选择其间的ID用作GUIDELINE。
GL_ID_PRIVATE_LAST|同上

## 管理IME的结构体
> The following topics describe the structures used to manage IMEs.

下面适用于管理IME的结构体。
### IMEINFO
> The IMEINFO structure is used internally by IMM and IME interfaces.
typedef struct tagIMEInfo {
    DWORD dwPrivateDataSize;    // The byte count of private data 
                                // in an IME context.
    DWORD fdwProperty;          // The IME property bits. See 
                                // description below.
    DWORD fdwConversionCaps;    // The IME conversion mode 
                                // capability bits.
    DWORD fdwSentenceCaps;      // The IME sentence mode 
                                // capability.
    DWORD fdwUICaps;            // The IME UI capability.
    DWORD fdwSCSCaps;           // The ImeSetCompositionString 
                                // capability.
    DWORD fdwSelectCaps;        // The IME inherit IMC capability.
} IIMEINFO;
 
> Members
dwPrivateDataSize
Byte count of the structure.
fdwProperty
HIWORD of fdwProperty contains the following bits, which are used by the application.
Bit
Description

> IME_PROP_AT_CARET
Bit On indicates that the IME conversion window is at caret position. Bit Off indicates a near caret position operation IME.
IME_PROP_SPECIAL_UI
Bit On indicates that the IME has a special UI. The IME should set this bit only when it has an nonstandard UI that an application cannot display. Typically, an IME will not set this flag.
IME_PROP_CANDLIST_START_FROM_1
Bit ON indicates that the UI of the candidate list string starts from zero or 1. An application can draw the candidate list string by adding the 1, 2, 3, and so on in front of the candidate string.
IME_PROP_UNICODE
If set, the IME is viewed as Unicode IME. System and IME will communicate through Unicode IME interface. If clear, IME will use ANSI interface to communicate with system.
IME_PROP_COMPLETE_ON_
UNSELECT
New property bit defined for Windows 98 and Windows 2000. If set, the IME will complete the composition string when the IME is deactivated. If clear, the IME will cancel the composition string when the IME is deactivated (such as from a keyboard layout change).

> The LOWORD of fdwProperty contains the following bits, which are used by the system.
Bit
Description
IME_PROP_END_UNLOAD
Bit On indicates that the IME will unload when there is no one using it.
IME_PROP_KBD_CHAR_FIRST
Before the IME translates the DBCS character, the system first translates the characters by keyboard. This character is passed to the IME as an information aid. No aid information is provided when this bit is off.
IME_PROP_NEED_ALTKEY
IME needs the ALT key passed to ImeProcessKey.
IME_PROP_IGNORE_UPKEYS
IME does not need the UP key passed to ImeProcessKey.
IME_PROP_ACCEPT_WIDE_VKEY
Windows 2000: If set, the IME processes the injected Unicode that came from the SendInput function by using VK_PACKET. If clear, IME might not process the injected Unicode and the injected Unicode might be sent to application directly.

> fdwConversionCaps
Same definition as the conversion mode. If the relative bit is off, the IME does not have the capability to handle the conversion mode no matter whether the corresponding bit of the conversion mode is on or off.
Conversion mode
Description
IME_CMODE_KATAKANA
Bit On indicates that the IME supports KATAKANA mode. Otherwise, it does not.
IME_CMODE_NATIVE
Bit On indicates that the IME supports NATIVE mode. Otherwise, it does not.
IME_CMODE_FULLSHAPE
Bit On indicates that the IME supports full shape mode. Otherwise, it does not.
IME_CMODE_ROMAN
Bit On indicates that the IME supports ROMAN input mode. Otherwise, it does not.
IME_CMODE_CHARCODE
Bit On indicates that the IME supports CODE input mode. Otherwise, it does not.
IME_CMODE_HANJACONVERT
Bit On indicates that the IME supports HANJA convert mode. Otherwise, it does not.
IME_CMODE_SOFTKBD
Bit On indicates that the IME supports soft keyboard mode. Otherwise, it does not.
IME_CMODE_NOCONVERSION
Bit On indicates that the IME supports No-conversion mode. Otherwise, it does not.
IME_CMODE_EUDC
Bit On indicates that the IME the IME supports EUDC mode. Otherwise, it does not.
IME_CMODE_SYMBOL
Bit On indicates that the IME supports SYMBOL mode. Otherwise, it does not.
IME_CMODE_CHARCODE
Set to 1 if the IME supports character code input mode, but zero if it does not.
IME_CMODE_FIXED
Set to 1 if the IME supports fixed conversion mode, but zero if not. This mode allows preconversion by the IME, but not full conversion. An example of this is Fixed Conversion Mode with DBCS HIRAGANA ROMAN. Under this mode, the IME can convert key input characters to DBCS HIRAGANA by Roman Conversion. However, it prevents conversion from DBCS HIRAGANA to Kanji characters. 

> fdwSentenceCaps
Same constant definition as the sentence mode. If the relative bit is off, the IME does not have the capability to handle the sentence mode no matter if the corresponding bit of sentence mode is on or off.
Conversion mode
Description

> IME_SMODE_PLAURALCLAUSE
Bit On indicates that the IME supports plural clause sentence mode.
IME_SMODE_SINGLECONVERT
Bit On indicates that the IME supports single character sentence mode.
IME_SMODE_AUTOMETIC
Bit On indicates that the IME supports automatic sentence mode.
IME_SMODE_PHRASEPREDICT
Bit On indicates that the IME supports phrase predict sentence mode.
IME_SMODE_CONVERSATION
IME uses conversation mode. This is useful for chat applications. Chat applications can change the sentence mode of the IME to conversation style. This is a new mode for Windows 98 and Windows 2000.

> fdwUICaps
The fdwUICaps bits specify the UI ability of the IME. The following bits are provided.
Bit
Description

> UI_CAP_2700
UI supported when LogFont escape is zero or 2700.
UI_CAP_ROT90
UI supported when LogFont escape is zero, 900, 1800, or 2700.
UI_CAP_ROTANY
UI supported with any escape.
UI_CAP_SOFKBD
IME uses soft keyboard provided by the system.

> fdwSCSCaps
The fdwSCSCaps bits specify the SetCompositionString capability that the IME has. The following bits are provided.
Bit
Description

> SCS_CAP_COMPSTR
IME can generate the composition string by SCS_SETSTR.
SCS_CAP_MAKEREAD
When calling ImmSetCompositionString with SCS_SETSTR, the IME can create the reading of the composition string without lpRead. Under the IME that has this capability, the application does not need to set lpRead for SCS_SETSTR.

> fdwSelectCaps
The fdwSelectCaps capability is for the application. When a user changes the IME, the application can determine if the conversion mode will be inherited or not by checking this capability. If the newly selected IME does not have this capability, the application will not receive the new mode and will have to retrieve the mode again. The following bits are provided.
Bit
Description

> SELECT_CAP_CONVMODE
IME has the capability of inheritance of conversion mode at ImeSelect.
SELECT_CAP_SENTENCE
IME has the capability of inheritance of sentence mode at ImeSelect.

该结构体是IMM和输入法接口之间通讯时使用的内部数据结构。
``` c++
typedef struct tagIMEInfo {
    DWORD dwPrivateDataSize;    // 本结构体的尺寸
    DWORD fdwProperty;          // 输入法属性，详见下文
    DWORD fdwConversionCaps;    // 转换模式标记，详见下文
    DWORD fdwSentenceCaps;      // 句子模式标记，详见下文
    DWORD fdwUICaps;            // 指定输入法UI标记，详见下文
    DWORD fdwSCSCaps;           // The ImeSetCompositionString 
                                // capability，详见下文
    DWORD fdwSelectCaps;    // 输入法继承IMC的能力，该能力是针对应用程序的。
                            // 当用户切换输入法时应用程序决定是否继承前一个
                            // 转换/句子模式，详见下文
} IIMEINFO;
```

HIWORD(fdwProperty)|含义
----|----
IME_PROP_AT_CARET|ON表示输入法转换窗在光标附近，OFF表示窗口位置被调整过
IME_PROP_SPECIAL_UI|ON表示输入法有特殊的UI，当输入法有应用程序无法显示的非标准窗口时，应当置ON
IME_PROP_CANDLIST_START_FROM_1|ON表示候选列表UI始于0或1，以便应用程序绘制时可以在候选前加入候选序号
IME_PROP_UNICODE|ON表示输入法为Unicode，系统将通过Unicode接口与之通讯；否则为ANSI
IME_PROP_COMPLETE_ON_UNSELECT|ON表示输入法被deactivate时将上屏写作串，否则将取消

LOWORD(fdwProperty)|含义
----|----
IME_PROP_END_UNLOAD|ON表示输入法在不被使用时将unload
IME_PROP_KBD_CHAR_FIRST|ON表示在输入法转换DBCS字符前，系统先转换这些字符。这些字符将作为information aid被传入输入法
IME_PROP_NEED_ALTKEY|输入法需要将ALT键传入ImeProcessKey
IME_PROP_IGNORE_UPKEYS|输入法不需要将键盘抬起信息传入ImeProcessKey
IME_PROP_ACCEPT_WIDE_VKEY|ON表示输入法处理通过SendInput发出的注入消息，OFF则把该消息直接发给应用程序

fdwConversionCaps|含义
----|----
IME_CMODE_KATAKANA|ON表示输入法支持片假名模式
IME_CMODE_NATIVE|ON表示输入法支持NATIVE模式
IME_CMODE_FULLSHAPE|ON表示输入法支持全角模式
IME_CMODE_ROMAN|ON表示输入法支持ROMAN模式
IME_CMODE_CHARCODE|ON表示输入法支持CODE模式
IME_CMODE_HANJACONVERT|ON表示输入法支持韩语汉字模式
IME_CMODE_SOFTKBD|ON表示输入法支持软键盘模式
IME_CMODE_NOCONVERSION|ON表示输入法支持No-conversion模式
IME_CMODE_EUDC|ON表示输入法支持EUDC模式
IME_CMODE_SYMBOL|ON表示输入法支持符号模式
IME_CMODE_CHARCODE|ON表示输入法支持字符码输入模式
IME_CMODE_FIXED|ON表示输入法支持固定转换模式

fdwSentenceCaps|含义
----|----
IME_SMODE_PLAURALCLAUSE|ON表示输入法支持符合分句模式
IME_SMODE_SINGLECONVERT|ON表示输入法支持单字符句子模式
Bit On indicates that the IME supports single character sentence mode.
IME_SMODE_AUTOMETIC|ON表示输入法支持自动句子模式
Bit On indicates that the IME supports automatic sentence mode.
IME_SMODE_PHRASEPREDICT|ON表示输入法支持短语预测模式
IME_SMODE_CONVERSATION|ON表示输入法使用交谈模式。这对聊天类应用比较有用，它们可以修改输入法的句子模式为交谈模式

fdwUICap|含义
----|----
UI_CAP_2700|UI支持LogFont escape为0或2700
UI_CAP_ROT90|UI支持LogFont escape为0或900或1800或2700
UI_CAP_ROTANY|支持任何转义
UI_CAP_SOFKBD|输入法使用系统软键盘

fdwSCSCaps|含义
----|----
SCS_CAP_COMPSTR|输入法可以通过SCS_SETSTR生成写作串
SCS_CAP_MAKEREAD|当使用SCS_SETSTR调用函数ImmSetCompositionString时，输入法可以不用lpRead生成读入串，此时应用程序不必为SCS_SETSTR设置lpRead

fdwSelectCaps|含义
----|----
SELECT_CAP_CONVMODE|输入法在ImeSelect时继承转换模式
SELECT_CAP_SENTENCE|输入法在ImeSelect时继承句子模式

## IME使用的结构体
> The following topics describe the structures used for communication with IMEs.

接下来介绍与输入法通讯的数据结构。
### CANDIDATELIST
> The CANDIDATELIST structure contains information about a candidate list.
typedef struct tagCANDIDATELIST {
    DWORD dwSize;         // the size of this data structure.
    DWORD dwStyle;        // the style of candidate strings.
    DWORD dwCount;        // the number of the candidate strings.
    DWORD dwSelection;    // index of a candidate string now selected.
    DWORD dwPageStart;    // index of the first candidate string show in
                          // the candidate window. It maybe varies with
                          // page up or page down key.
    DWORD dwPageSize;     // the preference number of the candidate
                          // strings shows in one page.
    DWORD dwOffset[];     // the start positions of the first candidate
                          // strings. Start positions of other
                          // (2nd, 3rd, ..) candidate strings are
                          // appened after this field. IME can do this
                          // by reallocating the hCandInfo memory
                          // handle. So IME can access dwOffset[2] (3rd
                          // candidate string) or dwOffset[5] (6st
                          // candidate string).
// TCHAR chCandidateStr[];    // the array of the candidate strings.
} CANDIDATELIST;
 
>Members
dwsize
Size, in bytes, of the structure, the offset array, and all candidate strings.
dwStyle
Candidate style values. It can be one or more of the following values.
Error! Bookmark not defined.Value
Meaning
IME_CAND_UNKNOWN
Candidates are in a style other than listed here.
IME_CAND_READ
Candidates have the same reading.
IME_CAND_CODE
Candidates are in one code range.
IME_CAND_MEANING
Candidates have the same meaning.
IME_CAND_RADICAL
Candidates are composed of same radical character.
IME_CAND_STROKES
Candidates are composed of same number of strokes.

>For the IME_CAND_CODE style, the candidate list has a special structure depending on the value of the dwCount member. If dwCount is 1, the dwOffset member contains a single DBCS character rather than an offset, and no candidate string is provided. If the dwCount member is greater than 1, the dwOffset member contains valid offsets, and the candidate strings are text representations of individual DBCS character values in hexadecimal notation.
dwCount
Number of candidate strings.
dwSelection 
Index of the selected candidate string.
dwPageStart
Index of the first candidate string in the candidate window. This varies as the user presses the Page Up and Page Down keys.
dwPageSize
Number of candidate strings to be shown in one page in the candidate window. The user can move to the next page by pressing IME-defined keys, such as the Page Up or Page Down key. If this number is zero, an application can define a proper value by itself.
dwOffset
Offset to the start of the first candidate string, relative to the start of this structure. The offsets for subsequent strings immediately follow this member, forming an array of 32-bit offsets.

>Comments
The CANDIDATELIST structure is used for the return of ImmGetCandidateList . The candidate strings immediately follow the last offset in the dwOffset array. 

该结构体描述候选列表的信息。
``` c++
typedef struct tagCANDIDATELIST {
    DWORD dwSize;         // 本结构体的尺寸
    DWORD dwStyle;        // 候选风格，详见下文
    DWORD dwCount;        // 候选串个数
    DWORD dwSelection;    // 当前选中的候选串
    DWORD dwPageStart;    // 候选窗中显示的第一个候选串，可能会根据翻页而不同
    DWORD dwPageSize;     // 在当前页中选择的候选
    DWORD dwOffset[];     // 相对于本结构体头部的偏移，输入法可以通过该数组
                          // 得到对应的候选串
    // TCHAR chCandidateStr[];    // the array of the candidate strings.
} CANDIDATELIST;
```

dwStyle|含义
----|----
IME_CAND_UNKNOWN|未知的风格
IME_CAND_READ|候选与读入串相同
IME_CAND_CODE|候选是在一个编码范围
IME_CAND_MEANING|候选有相同的含义
IME_CAND_RADICAL|候选由偏旁组成
IME_CAND_STROKES|候选由数字组成

在IME_CAND_CODE风格下，候选列表会根据dwCount的值有特殊的结构体。如果dwCount为1，dwOffset包含一个单独的DBCS字符，而不是偏移，此时不提供候选串；如果dwCount>1，dwOffset包含一个有效的偏移，候选串就是以16进制形式给出的DBCS字符的文本

** 说明 **
调用`ImmGetCandidateList`可以获得该结构体，候选串就在dwOffset偏移数组指向的位置。

### COMPOSITIONFORM
>The COMPOSITIONFORM structure is used for IMC_SETCOMPOSITIONWINDOW and IMC_SETCANDIDATEPOS messages.
typedef tagCOMPOSITIONFORM {
DWORD dwStyle;
POINT ptCurrentPos;
RECT rcArea;
}COMPOSITIONFORM;
 
>Members
dwStyle
Position style. The following values are provided.
Error! Bookmark not defined.Value
Meaning
CFS_DEFAULT
Move the composition window to the default position. The IME window can display the composition window outside the client area, such as in a floating window.
CFS_FORCE_POSITION
Display the upper-left corner of the composition window at exactly the position given by ptCurrentPos. The coordinates are relative to the upper-left corner of the window containing the composition window and are not subject to adjustment by the IME.
CFS_POINT
Display the upper-left corner of the composition window at the position given by ptCurrentPos. The coordinates are relative to the upper-left corner of the window containing the composition window and are subject to adjustment by the IME.
CFS_RECT
Display the composition window at the position given by rcArea. The coordinates are relative to the upper-left of the window containing the composition window.

>ptCurrentPos
Coordinates of the upper-left corner of the composition window.
rcArea
Coordinates of the upper-left and lower-right corners of the composition window.

>Comments
When the style of the COMPOSITIONFORM structure is CFS_POINT or CFS_FORCE_POINT, the IME will draw the composition string from the position specified by ptCurrentPos of the COMPOSITIONFORM structure that is given by the application. If the style has CFS_RECT, the composition string will be inside the rectangle specified by rcArea. If not, rcArea will be the client rectangle of the application window.
When the application specifies the composition font, the composition window is rotated as the escapement of the composition font. The direction of the composition string follows the escapement of the font in a composition window. The IME then draws the composition string. Following is an example of this process using various values for the escapement of the composition font:
    Escapement of the composition font is zero
Typically, the escapement of the composition font is zero. When this is the case, ptCurrentPos of the composition form structure points to the left and top of the string. All IMEs support this type.
    Escapement of the composition font is 2700
This is in the case of a vertical writing. When the application provides the vertical writing, the application can set the 2700 escapement in the composition font set by ImmCompositoinFont. The composition string will then be drawn downward. IMEs that have UI_CAP_2700, UI_CAP_ROT90, or UI_CAP_ROTANY capability will support this type of composition window.
    Escapement of the composition font is 900 or 1800
IMEs that have UI_CAP_ROT90 or UI_CAP_ROTANY capability will support this type of composition window.
    Escapement of the composition font is any value
IMEs that have UI_CAP_ROTANY capability will support this type of composition window.


>Note
UI_CAP_ROT90 and UI_CAPS_ANY are the option for the enhancement of the IME. UI_CAP_2700 is recommended.

该结构体用于IMC_SETCOMPOSITIONWINDOW 和 IMC_SETCANDIDATEPOS消息。
``` c++
typedef tagCOMPOSITIONFORM {
    DWORD dwStyle;      // 详见下文
    POINT ptCurrentPos; // 写作窗左上角坐标
    RECT rcArea;        // 写作窗区域
}COMPOSITIONFORM;
```

dwStyle|含义
----|----
CFS_DEFAULT|把写作窗挪到默认位置，输入法窗体可以把写作窗显示到客户区域以外。
CFS_FORCE_POSITION|精确地把ptCurrentPos作为输入法写作窗的左上角坐标，且不会调整。
CFS_POINT|把ptCurrentPos作为输入法写作窗的左上角坐标，输入法可以调整该位置。
CFS_RECT|把rcArea作为输入法写作窗的显示区域。

** 说明 **
当COMPOSITIONFORM::dwStyle为CFS_POINT或CFS_FORCE_POINT，输入法会根据应用程序给定的COMPOSITIONFORM::ptCurrentPos来放置写作窗的位置。如果指定了ptCurrentPos，写作窗将在rcArea这个区域，否则，rcArea就是应用程序的客户区域。

如果应用程序指定了写作串字体，写作窗会根据字体而调整方向。
### CANDIDATEFORM
> The CANDIDATEFORM structure is used for IMC_GETCANDIDATEPOS and IMC_SETCANDIDATEPOS messages.
typedef tagCANDIDATEFORM {
DWORD dwIndex;
DWORD dwStyle;
POINT ptCurrentPos;
REC rcArea;
} CANDIDATEFORM;
 
Members
dwIndex
Specifies the ID of the candidate list. Zero is the first candidate list, 1 is the second one, and so on up to 3.
dwStyle
Specifies CFS_CANDIDATEPOS or CFS_EXCLUDE. For a near-caret IME, the dwStyle also can be CFS_DEFAULT. A near-caret IME will adjust the candidate position according to other UI components, if the dwStyle is CFS_DEFAULT.
ptCurrentPos
Depends on dwStyle. When dwStyle is CFS_CANDIDATEPOS, ptCurrentPos specifies the recommended position where the candidate list window should be displayed. When dwStyle is CFS_EXCLUDE, ptCurrentPos specifies the current position of the point of interest (typically the caret position).
rcArea
Specifies a rectangle where no display is allowed for candidate windows 

该结构体用于IMC_GETCANDIDATEPOS 和 IMC_SETCANDIDATEPOS消息。
``` c++
typedef tagCANDIDATEFORM {
    DWORD dwIndex;      // 指定候选列表的ID，第1个位0，第2个位1，直到3
    DWORD dwStyle;      // CFS_CANDIDATEPOS 或 CFS_EXCLUDE。对于near-caret输入法
                        // 可以为CFS_DEFAULT，此时输入法将根据其它UI调整候选窗位置
    POINT ptCurrentPos; // dwStyle为 CFS_CANDIDATEPOS，表示候选窗建议显示的位置
                        // 为CFS_EXCLUDE，表示当前光标位置
    REC rcArea;         // 
} CANDIDATEFORM;
```
### STYLEBUF
> The STYLEBUF structure contains the identifier and name of a style.
typedef struct tagSTYLEBUF {
DWORD dwStyle;
TCHAR szDescription[32]
} STYLEBUF;
 
>Members
dwStyle
Style of register word.
szDescription
Description string of this style. 


>Note
The style of the register string includes IME_REGWORD_STYLE_EUDC. The string is in EUDC range:
IME_REGWORD_STYLE_USER_FIRST and IME_REGWORD_STYLE_USER_LAST.
The constants range from IME_REGWORD_STYLE_USER_FIRST to IME_REGWORD_STYLE_USER_LAST and are for private IME ISV styles. The IME ISV can freely define its own style.

该结构体包含风格的id和名字。
``` c++
typedef struct tagSTYLEBUF {
    DWORD dwStyle;          // 风格的注册字
    TCHAR szDescription[32] // 风格的描述
} STYLEBUF;
```
** 注意 **
风格的注册字串包括IME_REGWORD_STYLE_EUDC，该字串的范围在[IME_REGWORD_STYLE_USER_FIRST, IME_REGWORD_STYLE_USER_LAST]。该范围内的常亮是给输入法的ISV风格使用。
### SOFTKBDDATA
> The SOFTKBDDATA defines the DBCS codes for each virtual key.
typedef struct tagSOFTKBDDATA {
UINT uCount;
WORD wCode[][256]
} SOFTKBDDATA;
 
>Members
uCount
Number of the 256-word virtual key mapping to the internal code array.
wCode[][256]
256-word virtual key mapping to the internal code array. There may be more than one 256-word arrays.


>Note
It is possible for one type of soft keyboard to use two 256-word arrays. One is for the nonshift state and the other is for the shift state. The soft keyboard can use two internal codes for displaying one virtual key.

该结构体定义了每个虚拟按键的DBCS编码。
``` c++
typedef struct tagSOFTKBDDATA {
    UINT uCount;        // 256字虚键映射到内部码数组的个数
    WORD wCode[][256]   // 256字虚键映射到内部码数组，可能有多于256个元素
} SOFTKBDDATA;
``` 
** 注意 **
一个软键盘可能会使用两个256字的数组。一个用于无shift状态，另一个是有shift状态。软键盘可以使用两个内部码来展现一个虚拟按键。

### RECONVERTSTRING
> The RECONVERTSTRING structure defines the strings for IME reconversion. It is the first item in a memory block that contains the strings for reconversion.
typedef struct _tagRECONVERTSTRING {
DWOPD dwSize;
DWORD dwVersion;
DWORD dwStrLen;
DWORD dwStrOffset;
DWORD dwCompStrLen;
DWORD dwCompStrOffset;
DWORD dwTargetStrLen;
DWORD dwTargetStrOffset;
} RECONVERTSTRING;
 
>Members
dwSize
Memory block size of this structure.
dwVersion
Reserved by the system. This must be zero.
dwStrlen
Length of the string that contains the composition string.
dwStrOffset
Offset from the start position of this structure. The string containing the reconverted words is stored at this point.
dwCompStrLen
Length of the string that will be the composition string.
dwCompStrOffset
Offset of the string that will be the composition string. 
dwTargetStrLen
Length of the string that is related to the target clause in the composition string.
dwTargetStrOffset
Offset of the string that is related to the target clause in the composition string.


>Note
The RECONVERTSTRING structure is a new structure for Windows 98 and Windows 2000. The dwCompStrOffset and dwTargetOffset members are the relative position of dwStrOffset. For Windows NT Unicode, dwStrLen, dwCompStrLen, and dwTargetStrLen are the TCHAR count, and dwStrOffset, dwCompStrOffset, and dwTargetStrOffset are the byte offset.

>Comments
If an application starts the reconversion process by calling ImmSetCompositionString with SCS_SETRECONVERTSTRING and SCS_QUERYRECONVERTSTRING, the application is then responsible for allocating the necessary memory for this structure as well as the composition string buffer. The IME should not use the memory later. If the IME starts the process, it should allocate the necessary memory for the structure and the composition string buffer.

该结构体定义输入法的再转换串。
``` c++
typedef struct _tagRECONVERTSTRING {
    DWOPD dwSize;               // 本结构体的尺寸
    DWORD dwVersion;            // 保留字段，必须为0
    DWORD dwStrLen;             // 包含写作串的长度
    DWORD dwStrOffset;          // 距离本结构体头部的偏移，包含再转换后的字串
    DWORD dwCompStrLen;         // 写作串的长度
    DWORD dwCompStrOffset;      // 写作串的偏移
    DWORD dwTargetStrLen;       // 与目标分词相关的字串长度
    DWORD dwTargetStrOffset;    // 与目标分词相关的字串偏移
} RECONVERTSTRING;
```
** 注意 **
dwCompStrOffset 和 dwTargetOffset是在dwStrOffset中的相对位置。
** 说明 **
如果应用程序通过传入参数SCS_SETRECONVERTSTRING 和 SCS_QUERYRECONVERTSTRING调用函数`ImmSetCompositionString`，应用程序会收到为该结构体分配的内存，输入法不应该使用该内存。如果输入法启动了处理过程，它应该为该结构体分配必要的内存。
### IMEMENUITEMINFO
>The IMEMENUITEMINFO structure contains information about IME menu items.
typedef _tagIMEMENUITEMINFO {
UINT cbSize;
UINT fType;
UINT fState;
UINT wID;
HBITMAP hbmpChecked;
HBITMAP hbmpUnchecked;
DWORD dwItemData;
TCHAR szString[48];
HBITMAP hbmpItem;
} IMEMENUITEMINFO;
 
>Members
cbSize
Size of the structure in bytes
fType
Menu item type. This member can be one or more of the following values.
Value
Meaning

>IMFT_RADIOCHECK
Displays checked menu items using a radio-button mark instead of a check mark if the hbmpChecked member is NULL.
IMFT_SEPARATOR
Specifies that the menu item is a separator. A menu item separator appears as a horizontal dividing line. The hbmpItem and szString members are ignored.
IMFT_SUBMENU
Specifies that the menu item is a submenu.

>fState
Menu item state. This member can be one or more of the following values.
Value
Meaning

>IMFS_CHECKED
Checks the menu item. For more information about checked menu items. See the hbmpChecked member.
IMFS_DEFAULT
Specifies that the menu item is the default. A menu can contain only one default menu item, which is displayed in bold.
IMFS_DISABLED
Disables the menu item so it cannot be selected, but does not gray it out.
IMFS_ENABLED
Enables the menu item so it can be selected. This is the default state.
IMFS_GRAYED
Disables the menu item and grays it out so it cannot be selected.
IMFS_HILITE
Highlights the menu item.
IMFS_UNCHECKED
Unchecks the menu item. For more information about unchecked menu items, see the hbmpUnchecked member.
IMFS_UNHILITE
Removes the highlight from the menu item. This is the default state.

>wID
Application-defined 16-bit value that identifies the menu item.
hbmpChecked
Handle to the bitmap to display next to the item if it is checked. If this member is NULL, a default bitmap is used. If the IMFT_RADIOCHECK type value is specified, the default bitmap is a bullet. Otherwise, it is a check mark.
hbmpUnchecked
Handle to the bitmap to display next to the item if it is not checked. If this member is NULL, no bitmap is used.
dwItemData
Application-defined value associated with the menu item.
szString
Content of the menu item. This member is a null-terminated string.
hbmpItem
Bitmap handle to display.


>Note
The IMEMENUITEMINFO structure is a new structure for Windows 98 and Windows 2000. The Unicode version of this structure has the szString member as the WCHAR.

该结构体包含输入法菜单项信息。
``` c++
typedef _tagIMEMENUITEMINFO {
UINT cbSize;            // 结构体尺寸
UINT fType;             // 菜单项类型，详见下文
UINT fState;            // 菜单项状态，详见下文
UINT wID;               // 应用程序定义的16位ID
HBITMAP hbmpChecked;    // 如果被选中，使用的位图
HBITMAP hbmpUnchecked;  // 如果为被选中，使用的位图
DWORD dwItemData;       // 应用程序定义的与该项关联的值
TCHAR szString[48];     // 菜单项的文字
HBITMAP hbmpItem;       // 菜单项显示的位图
} IMEMENUITEMINFO;
```

fType|含义
----|----
IMFT_RADIOCHECK|使用单选标记时展现复选菜单项
IMFT_SEPARATOR|分割线
IMFT_SUBMENU|子菜单

fState|含义
----|----
IMFS_CHECKED|选中
IMFS_DEFAULT|默认，一个菜单仅有一个默认项，会以粗体显示
IMFS_DISABLED|disabled，置灰
IMFS_ENABLED|enabled，可以被选中或者默认
IMFS_GRAYED|disabled，置灰
IMFS_HILITE|高亮
IMFS_UNCHECKED|未选中
IMFS_UNHILITE|删除高亮状态

### TRANSMSG
>The TRANSMSG structure contains transferred message, used by ImeToAsciiEx to receive IME generated message.
typedef _tagTRANSMSG {
UINT message;
WPARAM wParam;
LPARAM lParam;
} TRANSMSG;
 
>Members
message
Specify message identify
wParam
Specify additional information about the message. The exact meaning depends on the value of the message member. 
lParam
Specify additional information about the message. The exact meaning depends on the value of the message member.

>Note
This structure is added for future 64-bit Windows NT platform. This structure will be used together with TRANSMSGLIST by ImeToAsciiEx to replace the formerly used LPDWORD lpdwTransBuf. Using this structure will still keep the data in memory with the same offset and keep backward compatible.

该结构体用于携带消息，该结构体被`ImeToAsciiEx`用来发送输入法消息。
``` c++
typedef _tagTRANSMSG {
    UINT message;   // 指定消息ID
    WPARAM wParam; 
    LPARAM lParam;
} TRANSMSG;
```
** 注意 **
该结构体被添加到未来64位系统中。`ImeToSaciiEx`会将该结构体与TRANSMSGLIST结合使用，来替代以前的lpdwTransBuf。
### TRANSMSGLIST
>The TRANSMSGLIST structure contains transferred message list returned from ImeToAsciiEx.
typedef _tagTRANSMSGLIST {
UINT uMsgCount;
TRANSMSG TransMsg[1];
} TRANSMSGLIST;
 
>Members
uMsgCount
Specify the message number in TransMsg array.
TransMsg
Includes TRANSMSG data array. 

>Note
This structure is added for future 64-bit Windows NT platform. This structure will be used by ImeToAsciiEx to replace the formerly used LPDWORD lpdwTransBuf. Using this structure will still keep the data in memory with the same offset and keep backward compatible.

该结构体用于携带消息，该结构体被`ImeToAsciiEx`用来发送输入法消息。
``` c++
typedef _tagTRANSMSGLIST {
    UINT uMsgCount;         // 消息的个数
    TRANSMSG TransMsg[1];   // TRANSMSG数组
} TRANSMSGLIST;
```