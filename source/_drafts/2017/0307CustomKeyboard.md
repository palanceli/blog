---
layout: post
title: Custom Keyboard（译）
date: 2017-03-07 20:53:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
（本文来自[《Custom Keyboard》](https://developer.apple.com/library/content/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html)）
自定义键盘为那些希望体验更新颖的输入法或者需要用到iOS不支持的语言的用户，提供了替代系统键盘的备选。自定义键盘的核心功能很简单：响应按键、手势或其它输入事件，并提供转换后的文本字串，并将该字串插入到当前的光标位置。
<!-- more -->
> ** 开始阅读前 **
> 请先确认你需要开发的的确是系统范围的自定义键盘。如果只是希望在你的app内部提供可自定义的键盘，可以到[《Custom Views for Data Input 》](https://developer.apple.com/library/content/documentation/StringsTextFonts/Conceptual/TextAndWebiPhoneOS/InputViews/InputViews.html#//apple_ref/doc/uid/TP40009542-CH12)和[《Text Programming Guide for iOS》](https://developer.apple.com/library/content/documentation/StringsTextFonts/Conceptual/TextAndWebiPhoneOS/Introduction/Introduction.html#//apple_ref/doc/uid/TP40009542)了解`自定义输入视图`和`输入辅助视图`的相关内容，iOS SDK为此提供了更好的备选方案。

当用户选择了自定义键盘，该键盘即成为每个app的键盘。因此，你创建的键盘必须包含一些基本的功能。其中最重要的是，必须允许用户切换到其它键盘。

# 理解用户对键盘的预期
要理解用户对于自定义键盘的预期，可以系统键盘为标杆——它反应灵敏且高效。它不会用垃圾信息或请求打断用户输入。如果你提供了需要用户交互的功能，应该把它们放到键盘的app里，而不是键盘上。
## iOS用户预期的键盘功能
每个自定义键盘都必须提供的iOS用户所预期的键盘功能是：切换到其它键盘的方法。在系统键盘中，有一个小地球的按键用来完成此功能。iOS 8也提供了专门的API用于切换到下一个键盘，可以参见[《提供一种切换到其它键盘的方法》](https://developer.apple.com/library/content/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html#//apple_ref/doc/uid/TP40014214-CH16-SW4)。

系统键盘会根据当前文本输入对象的[UIKeyboardType](https://developer.apple.com/reference/uikit/uikeyboardtype)属性，展现与之匹配的键盘布局。如果当前的输入对象需要输入邮箱，系统键盘的句号建就会变化：长按会冒出一些顶级域名的后缀作为候选。你在设计自己的键盘布局时也应当考虑到当前的输入对象属性。

iOS用户还期望自动大写：在一个标准的文本输入区域，对于大小写敏感的语言来说，应当让句首的字母自动大写。

这类功能列出如下：

* 对输入对象的属性考虑适当的键盘布局
* 自动纠错和建议
* 自动大写
* 两个空格后自动添加句号
* Caps lock键的支持
* 键帽上的美观
* 对于象形文字的多层转换

你可以自行决定是否实现这些功能；系统并没有为这些功能提供专用的API，在自己的输入法中提供这些功能可以让你的产品更有竞争力。

## 系统键盘中的哪些功能不适用于自定义键盘
自定义键盘不能访问在系统设置中的通用键盘设置数据（设置 > 通用 > 键盘），比如自动大写、使Caps Lock可用。自定义键盘也不能访问字典还原信息（设置 > 通用 > 还原 > 还原键盘词典）。要满足你用户的灵活性要求，你应该创建一个标准的设置bundle，这个话题在[《偏好和设置编程指南》](https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/UserDefaults/Introduction/Introduction.html#//apple_ref/doc/uid/10000059i)的[《实现iOS设置Bundle》](https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/UserDefaults/Preferences/Preferences.html#//apple_ref/doc/uid/10000059i-CH6)中有讨论。这样你的自定义键盘的设置就会出现在系统设置的键盘区域。

还有一些文本输入对象，自定义键盘是不能在其上进行输入的。首先就是任何安全相关的文本输入对象。这类文本输入对象设置了其[secureTextEntry](https://developer.apple.com/reference/uikit/uitextinputtraits/1624427-securetextentry)属性为`YES`，在其上的输入内容将呈现为圆点。

当用户在密码框里输入时，系统会临时用系统键盘来替代自定义键盘。当用户在非密码框里输入时，自定义键盘又会恢复回来。

自定义键盘也无权在拨号输入的位置出现，例如通讯录的电话号码输入区域。对于这类输入对象，键盘是由运营商指定的一个数字/字母的小集合组成，并且具备如下属性：
[UIKeyboardTypePhonePad](https://developer.apple.com/reference/uikit/uikeyboardtype/1624426-phonepad)
[UIKeyboardTypeNamePhonePad](https://developer.apple.com/reference/uikit/uikeyboardtype/1624465-namephonepad)

当用户点击拨号输入对象时，系统将临时用系统键盘替换掉你的自定义键盘。当用户再点击其它标准输入对象时，自定义键盘又会恢复回来。

app的开发者可以选择在app内部不使用自定义键盘。例如银行类app，或者必须遵守美国HIPAA隐私规则的app，可以这么干。这类app实现来自`UIApplicationDelegate`协议的[application:shouldAllowExtensionPointIdentifier:](https://developer.apple.com/reference/uikit/uiapplicationdelegate/1623122-application)方法，并返回NO，以达到使用系统键盘的效果。

Because a custom keyboard can draw only within the primary view of its UIInputViewController object, it cannot select text. Text selection is under the control of the app that is using the keyboard. If that app provides an editing menu interface (such as for Cut, Copy, and Paste), the keyboard has no access to it. A custom keyboard cannot offer inline autocorrection controls near the insertion point.

由于自定义键盘只能绘制其[UIInputViewController](https://developer.apple.com/reference/uikit/uiinputviewcontroller)对象内的主视图，在它上面不能选择文字。选择文字是使用键盘的应用程序控制的。如果app提供了编辑菜单（如剪切、拷贝和粘贴），键盘是无权访问它的。自定义键盘不能提供在光标位置的自动inline纠错能力。

Custom keyboards, like all app extensions in iOS 8.0, have no access to the device microphone, so dictation input is not possible.

Finally, it is not possible to display key artwork above the top edge of a custom keyboard’s primary view, as the system keyboard does on iPhone when you tap and hold a key in the top row.

在iOS8.0下，如所有扩展app一样，自定义键盘不能访问麦克风，因此不能实现语音输入。

最后，


# API Quick Start for Custom Keyboards
# Development Essentials for Custom Keyboards
## Designing for User Trust
## Providing a Way to Switch to Another Keyboard
# Getting Started with Custom Keyboard Development
## Using the Xcode Custom Keyboard Template
### To create a custom keyboard in a containing app
### To customize the keyboard group name
### To run the custom keyboard and attach the Xcode debugger
## Configuring the Info.plist file for a Custom Keyboard
