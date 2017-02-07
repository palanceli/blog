---
layout: post
title: 在Android下创建输入法（译）
date: 2017-02-07 23:07:00 +0800
categories: Android开发
tags: 输入法
toc: true
comments: true
---

原文来自Android Delelopers开发官网：[Creating an Input Method](https://developer.android.com/guide/topics/text/creating-input-method.html)。<!-- more -->

# 概述
> An input method editor (IME) is a user control that enables users to enter text. Android provides an extensible input-method framework that allows applications to provide users alternative input methods, such as on-screen keyboards or even speech input. After installing the desired IMEs, a user can select which one to use from the system settings, and use it across the entire system; only one IME may be enabled at a time.

输入法是种交互控件，通过它用户得以输入文字。安卓通过提供可扩展的输入法框架，使应用程序可以向用户提供如基于触屏键盘的或基于语音的输入法。用户可以自主安装输入法，在系统设置里选择为默认，然后就能使用了。同一时刻只能使用一个输入法。

> To add an IME to the Android system, you create an Android application containing a class that extends InputMethodService. In addition, you usually create a "settings" activity that passes options to the IME service. You can also define a settings UI that's displayed as part of the system settings.
  

要在安卓系统创建输入法，首先应该让应用创建一个从`InputMethodService`基类派生的子类，此外通常还需要创建一个设置activity，用来设置输入法开关。还可以定义包含于系统设置界面中的输入法设置界面。

> This guide covers the following:
* The IME lifecycle
* Declaring IME components in the application manifest
* The IME API
* Designing an IME UI
* Sending text from an IME to an application
* Working with IME subtypes

本文将覆盖如下主题：
* 输入法生命周期
* 在manifest文件中声明输入法组件
* 输入法API
* 设计输入法UI
* 从输入法向应用程序上屏文字
* 输入法子类

> If you haven't worked with IMEs before, you should read the introductory article Onscreen Input Methods first. Also, the SoftKeyboard sample app included in the SDK contains sample code that you can modify to start building your own IME.

如果之前没有接触过输入法，建议先阅读[《触屏输入法》](http://android-developers.blogspot.com/2009/04/updating-applications-for-on-screen.html)这篇介绍性文章。SDK中包含了一个例子[SoftKeyboard](https://android.googlesource.com/platform/development/+/master/samples/SoftKeyboard/)也是学习编写输入法不错的参考。

# 输入法生命周期（The IME Lifecycle）
> The following diagram describes the life cycle of an IME:

下图展示了输入法的生命周期：
![输入法的生命周期](0207CreatingAnInputMethod/img1.png)

> The following sections describe how to implement the UI and code associated with an IME that follows this lifecycle.

本文剩下的部分将按照该生命周期介绍如何实现输入法的界面和编码。

# 在Manifest文件中声明输入法组件（Declaring IME Components in the Manifest）
> In the Android system, an IME is an Android application that contains a special IME service. The application's manifest file must declare the service, request the necessary permissions, provide an intent filter that matches the action action.view.InputMethod, and provide metadata that defines characteristics of the IME. In addition, to provide a settings interface that allows the user to modify the behavior of the IME, you can define a "settings" activity that can be launched from System Settings.

在安卓系统中，输入法是一类特殊的应用程序，它必须包含一个IME服务。需要在manifest文件中声明该服务和必要的权限，提供匹配`action.view.InputMethod`的intent filter，提供定义输入法特征的元数据。此外，还要提供一个设置界面，通过该界面可以让用户修改输入法配置；还可以定义一个能从系统设置界面中启动的输入法设置界面。

> The following snippet declares an IME service. It requests the permission BIND_INPUT_METHOD to allow the service to connect the IME to the system, sets up an intent filter that matches the action android.view.InputMethod, and defines metadata for the IME:

下面的代码段就声明了一个输入法服务。它申请了BIND_INPUT_METHOD权限，该权限允许本服务将输入法连接到系统。它创建了一个匹配`android.view.InputMethod`的intent filter，并定义了元数据：
``` xml
<!-- 定义IME 服务 -->
    <service android:name="FastInputIME"
        android:label="@string/fast_input_label"
        android:permission="android.permission.BIND_INPUT_METHOD">
        <intent-filter>
            <action android:name="android.view.InputMethod" />
        </intent-filter>
        <meta-data android:name="android.view.im"
android:resource="@xml/method" />
    </service>
```

> This next snippet declares the settings activity for the IME. It has an intent filter for ACTION_MAIN that indicates this activity is the main entry point for the IME application:

下面的代码段声明了输入法的设置activity。它在`intent filter`中指定了`ACTION_MAIN`，表明该activity是输入法应用的主入口。
``` xml
<!-- 可选设置: 控制输入法设置的Activity -->
    <activity android:name="FastInputIMESettings"
        android:label="@string/fast_input_settings">
        <intent-filter>
            <action android:name="android.intent.action.MAIN"/>
        </intent-filter>
    </activity>
```
> You can also provide access to the IME's settings directly from its UI.

还可以在输入法界面里提供访问输入法设置的入口。

# 输入法相关的API（The Input Method API）
>Classes specific to IMEs are found in the android.inputmethodservice and android.view.inputmethod packages. The KeyEvent class is important for handling keyboard characters.

在包[android.inputmethodservice](https://developer.android.com/reference/android/inputmethodservice/package-summary.html)和[android.view.inputmethod](https://developer.android.com/reference/android/view/inputmethod/package-summary.html)中可以找到和输入法相关的类。[KeyEvent](https://developer.android.com/reference/android/view/KeyEvent.html)也是处理键盘数据的重要类。

>The central part of an IME is a service component, a class that extends InputMethodService. In addition to implementing the normal service lifecycle, this class has callbacks for providing your IME's UI, handling user input, and delivering text to the field that currently has focus. By default, the InputMethodService class provides most of the implementation for managing the state and visibility of the IME and communicating with the current input field.

输入法的核心部分是从[InputMethodService](https://developer.android.com/reference/android/inputmethodservice/InputMethodService.html)派生的一个服务组件。除了要实现普通服务的生命周期以外，该类还未输入法UI绘制、用户输入处理、上屏文字提供了相应的回调函数。[InputMethodService](https://developer.android.com/reference/android/inputmethodservice/InputMethodService.html)已经实现了大部分管理输入法状态、是否可见以及和输入区域交互的默认行为。

>The following classes are also important:

> * BaseInputConnection
Defines the communication channel from an InputMethod back to the application that is receiving its input. You use it to read text around the cursor, commit text to the text box, and send raw key events to the application. Applications should extend this class rather than implementing the base interface InputConnection.
* KeyboardView
An extension of View that renders a keyboard and responds to user input events. The keyboard layout is specified by an instance of Keyboard, which you can define in an XML file.

下面的类同样重要：
* [BaseInputConnection](https://developer.android.com/reference/android/view/inputmethod/BaseInputConnection.html)
定义从[InputMethod](https://developer.android.com/reference/android/view/inputmethod/InputMethod.html)回调宿主应用的通信通道。使用该类可以读取光标附近的文字，上屏输入法写作、候选窗中文本，把原始的按键事件发送给应用程序。应用程序应该派生该类，而不只是实现[InputConnection](https://developer.android.com/reference/android/view/inputmethod/InputConnection.html)的接口。

* [KeyboardView](https://developer.android.com/reference/android/inputmethodservice/KeyboardView.html)
提供键盘布局并响应按键事件的[View](https://developer.android.com/reference/android/view/View.html)。可以通过xml文件定义[keyboard](https://developer.android.com/reference/android/inputmethodservice/Keyboard.html)，来描述一个键盘布局。