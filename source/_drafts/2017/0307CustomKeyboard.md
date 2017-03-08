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

由于自定义键盘只能绘制其[UIInputViewController](https://developer.apple.com/reference/uikit/uiinputviewcontroller)对象内的主视图，在它上面不能选择文字。选择文字是使用键盘的应用程序控制的。如果app提供了编辑菜单（如剪切、拷贝和粘贴），键盘是无权访问它的。自定义键盘不能提供在光标位置的自动inline纠错能力。

在iOS8.0下，如所有扩展app一样，自定义键盘不能访问麦克风，因此不能实现语音输入。

最后，显示插图不能超过键盘的主视图上边缘，系统键盘可以，但自定义键盘不行。如下图，可以发现自定义键盘和系统输入法的差别：![按键插图不能超越上边缘](0307CustomKeyboard/img1.png)

# 自定义键盘API
本节将给出开发自定义键盘的快速入门。如下图，它展示了键盘运行过程中一些重要的对象，以及它们在开发流程中的的位置：
![自定义键盘的基本结构](0307CustomKeyboard/img2.png)

自定义键盘模板（在iOS“Application Extension”目标模板组）包含一个[UIInputViewController](https://developer.apple.com/reference/uikit/uiinputviewcontroller)的子类，它是你开发的键盘的主视图控制器。该模板包含键盘所必需的“下一个键盘”按钮的实现，它调用了`UIInputViewController`类的[advanceToNextInputMode](https://developer.apple.com/reference/uikit/uiinputviewcontroller/1618191-advancetonextinputmode)方法。如上图所示，可以在输入视图控制器的主视图（在其[inputView](https://developer.apple.com/reference/uikit/uiinputviewcontroller/1618192-inputview)属性）中添加子视图、控制器以及手势识别器等。对于其它类型的扩展应用，在目标上并不存在窗体，因此也就没有根视图控制器了。

在模板的`Info.plist`文件中有预先配置好的键盘所需要的最基本的值。参见其中的`NSExtensionAttributes`字典关键字，配置一个键盘的关键字在[《配置自定义键盘的Info.plist文件》](https://developer.apple.com/library/content/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html#//apple_ref/doc/uid/TP40014214-CH16-SW18)中有介绍。

默认，键盘不能访问网络，不能和它的app共享容器。如果要具备这种能力，必须要将`Info.plist`文件中`RequestsOpenAccess`的值置为`YES`。这需要扩展键盘的沙盒，在[《设计用户信任》](https://developer.apple.com/library/content/documentation/General/Conceptual/ExtensibilityPG/CustomKeyboard.html#//apple_ref/doc/uid/TP40014214-CH16-SW3)中有介绍相关内容。

一个输入视图控制器遵从各种与文本输入对象内容交互的协议：

* 响应触摸消息时如果要插入或删除文本，可以使用[UIKeyInput](https://developer.apple.com/reference/uikit/uikeyinput)协议的[insertText:](https://developer.apple.com/reference/uikit/uikeyinput/1614543-inserttext)和[deleteBackward](https://developer.apple.com/reference/uikit/uikeyinput/1614572-deletebackward)方法。可以在视图控制器的[textDocumentProxy](https://developer.apple.com/reference/uikit/uiinputviewcontroller/1618193-textdocumentproxy)属性中调用这些方法，该属性代表当前文本输入对象，它遵从[UITextDocumentProxy](https://developer.apple.com/reference/uikit/uitextdocumentproxy)协议。如下：
``` Obj-C
[self.textDocumentProxy insertText:@"hello "]; // Inserts the string "hello " at the insertion point
[self.textDocumentProxy deleteBackward];       // Deletes the character to the left of the insertion point
[self.textDocumentProxy insertText:@"\n"];     // In a text view, inserts a newline character at the insertion point
```

* 在调用[deleteBackward](https://developer.apple.com/reference/uikit/uikeyinput/1614572-deletebackward)之前要先决定删除的字符数。可以通过[textDocumentProxy](https://developer.apple.com/reference/uikit/uitextdocumentproxy/1618190-documentcontextbeforeinput)的[documentContextBeforeInput](https://developer.apple.com/reference/uikit/uiinputviewcontroller/1618193-textdocumentproxy)属性，来获得光标附近的文本上下文信息。如下：
``` obj-c
NSString *precedingContext = self.textDocumentProxy.documentContextBeforeInput;
```
    然后就可以删除你指定的文字区域了，比如单个字符还是空格后的所有字符。如果要按照语义执行删除，比如一个单词、句子、还是一个段落，可以使用[《 CFStringTokenizer Reference》](https://developer.apple.com/reference/corefoundation/cfstringtokenizer-rf8)中描述的函数，注意每个语种的语义规则是不同的。

* 为了控制光标所在位置的操作，比如支持向前删除文字，需要调用`UITextDocumentProxy`协议中的[《adjustTextPositionByCharacterOffset: 》](https://developer.apple.com/reference/uikit/uitextdocumentproxy/1618194-adjusttextposition)方法。比如向前删除一个字符，代码如下：
``` obj-c
- (void) deleteForward {
    [self.textDocumentProxy adjustTextPositionByCharacterOffset: 1];
    [self.textDocumentProxy deleteBackward];
}
```

* 通过实现[《UITextInputDelegate》](https://developer.apple.com/reference/uikit/uitextinputdelegate)协议中的方法，可以相应当前输入文本对象的一些变化，比如内容变化以及用户触发的光标位置的变化。

为了展现与当前文本输入对象适配的键盘布局，需要参照该对象的[UIKeyboardType](https://developer.apple.com/reference/uikit/uikeyboardtype)属性，根据每种你的键盘所能支持的属性，变化布局内容。

在自定义键盘中，有两种方式来支持多语言：

* 为每个语言创建一个键盘，每个键盘都作为向容器app添加的独立的Target
* 创建一个多语言键盘，动态切换当前语言。可以使用`UIInputViewController`类的[primaryLanguage](https://developer.apple.com/reference/uikit/uiinputviewcontroller/1618200-primarylanguage)属性来动态切换语言。

根据你要支持的语言数量以及你想提供的用户体验，你可以从上面选择最合适的方案。

Every custom keyboard (independent of the value of its RequestsOpenAccess key) has access to a basic autocorrection lexicon through the UILexicon class. Make use of this class, along with a lexicon of your own design, to provide suggestions and autocorrections as users are entering text. The UILexicon object contains words from various sources, including:



Unpaired first names and last names from the user’s Address Book database
Text shortcuts defined in the Settings > General > Keyboard > Shortcuts list
A common words dictionary
You can adjust the height of your custom keyboard’s primary view using Auto Layout. By default, a custom keyboard is sized to match the system keyboard, according to screen size and device orientation. A custom keyboard’s width is always set by the system to equal the current screen width. To adjust a custom keyboard’s height, change its primary view's height constraint.

The following code lines show how you might define and add such a constraint:

CGFloat _expandedHeight = 500;
NSLayoutConstraint *_heightConstraint = 
    [NSLayoutConstraint constraintWithItem: self.view 
                                 attribute: NSLayoutAttributeHeight 
                                 relatedBy: NSLayoutRelationEqual 
                                    toItem: nil 
                                 attribute: NSLayoutAttributeNotAnAttribute 
                                multiplier: 0.0 
                                  constant: _expandedHeight];
[self.view addConstraint: _heightConstraint];
NOTE

In iOS 8.0, you can adjust a custom keyboard’s height any time after its primary view initially draws on screen.


# Development Essentials for Custom Keyboards
## Designing for User Trust
## Providing a Way to Switch to Another Keyboard
# Getting Started with Custom Keyboard Development
## Using the Xcode Custom Keyboard Template
### To create a custom keyboard in a containing app
### To customize the keyboard group name
### To run the custom keyboard and attach the Xcode debugger
## Configuring the Info.plist file for a Custom Keyboard
