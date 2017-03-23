---
layout: post
title: Input Method Kit（译）
date: 2017-03-06 20:53:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
（本文来自[《Input Method Kit API Reference》](https://developer.apple.com/reference/inputmethodkit)）
Input Method Kit用于开发输入法，并管理与客户端应用之间的通讯，管理候选窗口和输入模式等。<!-- more -->

# 概要
OSX 在10.5版本中引入了IMK，该框架提供了输入法开发的原型接口，与老版本的mac相比，这套接口大大简化了输入法开发的工作量。该框架与文字服务管理器充分整合，使得32位和64位应用程序和输入法之间可以无缝合作。

IMK通过几个类和协议来支持输入法与客户端应用间的通讯，并管理候选窗和输入模式等。输入法从转换引擎提供转换后的文字（该引擎可以用C，C++，Objective-C，Python等编写），还会提供键盘绑定、可选的事件处理、通过一个扩展的Info.plist文件提供更多输入法信息。还可以通过菜单项支持输入法的特殊命令或偏好设置。

接下来看IMK涉及的类、协议和其它数据结构。

# IMKCandidates
IMKCandidates类用来表示候选。在用户选择了一个候选后，会通知对应的[IMKInputController](#IMKInputController)对象。候选是对已经输入的文字序列转换后的结果。IMKCandidates类支持在你的输入法中使用一个候选窗口来展现内容。该类的使用是可选的，不是所有输入法都需要它。

当创建一个IMKCandidates对象，你需要将它归属给输入法的IMKServer对象。然后重写IMKInputController的方法`candidateSelectionChanged: `和`candidateSelected:`，并在你的代理对象中实现一个候选方法。IMKInputController子类通过实现候选方法来为IMKCandidate对象提供候选。当需要显示候选窗时，可以调用候选方法来更新候选列表并显示候选窗口。该类涉及的方法如下：

## 初始化候选窗
[init!(server: IMKServer!, panelType: IMKCandidatePanelType)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385500-init)
&emsp; 返回初始化的IMKCandidates对象

## 管理选择按键
[func setSelectionKeys([Any]!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385522-setselectionkeys)
&emsp; 为候选设置选择键

[func selectionKeys()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385537-selectionkeys)
&emsp; 返回一个NSNumber对象的数组，每个元素代表一个虚拟键盘码

[func setSelectionKeysKeylayout(TISInputSource!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385422-setselectionkeyskeylayout)
&emsp; 设置用来映射虚拟键盘码到字符的键盘布局

[func selectionKeysKeylayout()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385428-selectionkeyskeylayout)
&emsp; 返回用来映射虚拟键盘码到字符的键盘布局

## 管理窗口展现和行为
[func show(IMKCandidatesLocationHint)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385391-show)
&emsp; 显示候选窗

[func hide()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385498-hide)
&emsp; 隐藏候选窗

[func isVisible()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385504-isvisible)
&emsp; 返回候选窗是否可见

[func setDismissesAutomatically(Bool)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385379-setdismissesautomatically)
&emsp; 设置候选窗是否自动取消的标志

[func dismissesAutomatically()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385463-dismissesautomatically)
&emsp; 返回候选窗是否自动取消的标志

[func update()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385516-update)
&emsp; 更新候选窗上的候选列表

## 管理窗体类型和文字属性
[func panelType()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385448-paneltype)
&emsp; 返回候选窗的风格

[func setPanelType(IMKCandidatePanelType)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385545-setpaneltype)
&emsp; 设置候选窗风格

[func setAttributes([AnyHashable : Any]!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385465-setattributes)
&emsp; 设置候选窗属性

[func attributes()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385440-attributes)
&emsp; 返回候选窗属性

## 显示注释窗口
[func showAnnotation(NSAttributedString!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385354-showannotation)
&emsp; 在注释窗口上显示注释串

## 常量
[IMKCandidatePanelType](https://developer.apple.com/reference/inputmethodkit/imkcandidatepaneltype)
&emsp; IMK提供的候选窗口的类型

[IMKCandidatesLocationHint](https://developer.apple.com/reference/inputmethodkit/imkcandidateslocationhint)
&emsp; 放置候选窗口的位置提示

[IMKCandidatesOpacityAttributeName](https://developer.apple.com/reference/inputmethodkit/imkcandidates/imkcandidatesopacityattributename)
&emsp; 候选窗口的透明度级别

## 初始化器
[init!(server: IMKServer!, panelType: IMKCandidatePanelType, styleType: IMKStyleType)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385467-init)
&emsp; 

## 实例方法
[func attachChild(IMKCandidates!, toCandidate: Int, type: IMKStyleType)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385455-attachchild)
&emsp; 
[func candidateFrame()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385426-candidateframe)
&emsp; 
[func candidateIdentifier(atLineNumber: Int)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385471-candidateidentifier)
&emsp; 
[func candidateStringIdentifier(Any!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385512-candidatestringidentifier)
&emsp; 
[func clearSelection()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385356-clearselection)
&emsp; 
[func detachChild(Int)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385457-detachchild)
&emsp; 
[func hideChild()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385494-hidechild)
&emsp; 
[func lineNumberForCandidate(withIdentifier: Int)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385488-linenumberforcandidate)
&emsp; 
[func selectCandidate(Int)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385543-selectcandidate)
&emsp; 
[func selectCandidate(withIdentifier: Int)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385559-selectcandidate)
&emsp; 
[func selectedCandidate()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385514-selectedcandidate)
&emsp; 
[func selectedCandidateString()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385402-selectedcandidatestring)
&emsp; 
[func setCandidateData([Any]!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385508-setcandidatedata)
&emsp; 
[func setCandidateFrameTopLeft(NSPoint)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385459-setcandidateframetopleft)
&emsp; 
[func show()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385404-show)
&emsp; 
[func showChild()](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385518-showchild)
&emsp; 
[func showSublist([Any]!, subListDelegate: Any!)](https://developer.apple.com/reference/inputmethodkit/imkcandidates/1385492-showsublist)
&emsp; 

# IMKInputController
IMKInputController为用户自定义的输入控制器提供一个基类。由[IMKServer为](#IMKServer)每个输入会话创建输入控制器，IMKServer通常在main函数的开头创建，输入会话则由客户端应用负责创建。对于每个输入会话都会有一个对应的输入控制器即IMKInputController对象。

IMKInputController对象用纸输入法侧的文本输入。它管理来自应用程序的事件和文本以及被输入法引擎转换后的文本。IMKInputController完全实现了[IMKStateSetting](#IMKStateSetting)协议和[IMKMouseHandling](#IMKMouseHandling)协议。通常你不需要覆写该类，而只需要为你感兴趣的方法实现代理对象。IMKInputController协议方法的版本会检查代理对象是否实现了某方法，如果存在则调用此代理版本。以下是它的成员：

## 初始化InputController
[init!(server: IMKServer!, delegate: Any!, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385385-init)
&emsp; 通过设置代理，初始化输入控制器

## 区域相关
[func compositionAttributes(at: NSRange)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385453-compositionattributes)
&emsp; 返回文本属性的字典

[func selectionRange()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385414-selectionrange)
&emsp; 返回选中文本的区域，该区域的文本会被选中且替换掉

[func replacementRange()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385486-replacementrange)
&emsp; 返回客户端文档中应当被替换掉的文本的区域

[func mark(forStyle: Int, at: NSRange)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385381-mark)
&emsp; 返回文本属性的字典，这些属性可以用来标注一段属性串的区域并发送给客户端应用

## 管理代理
[func setDelegate(Any!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385557-setdelegate)
&emsp; 为输入法控制器对象设置代理

## 获得客户端和服务端对象
[func server()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385418-server)
&emsp; 返回管理输入控制器的server对象

[func client()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385490-client)
&emsp; 返回与输入控制器关联的client对象

## 跟踪选择
[func annotationSelected(NSAttributedString!, forCandidate: NSAttributedString!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385432-annotationselected)
&emsp; 向输入控制器发送被选中的候选串和注释串

[func candidateSelectionChanged(NSAttributedString!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385365-candidateselectionchanged)
&emsp; 通知输入控制器当前候选窗中选中的候选项发生了变化

[func candidateSelected(NSAttributedString!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385451-candidateselected)
&emsp; 通知输入控制器一个新的候选被选中了

## 管理写作串
[func updateComposition()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385502-updatecomposition)
&emsp; 通知输入控制器写作串发生变化

[func cancelComposition()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385479-cancelcomposition)
&emsp; 取消当前写作串，并用原始串替代当前标记的文本

## 隐藏用户界面
[func hidePalettes()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385430-hidepalettes)
&emsp; 通知输入法隐藏用户界面

## 用户自定义命令
[func doCommand(by: Selector!, command: [AnyHashable : Any]!)](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385553-docommand)
&emsp; 传递由非输入法进程产生的命令

[func menu()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385406-menu)
&emsp; 返回输入法的命令菜单

## 实例方法
[func delegate()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385555-delegate)
&emsp; 

[func inputControllerWillClose()](https://developer.apple.com/reference/inputmethodkit/imkinputcontroller/1385375-inputcontrollerwillclose)
&emsp; 

# IMKServer
IMKServer类管理客户端与输入法的连接。应当在main函数中创建IMKServer对象，永远不要修改该类，不要从它派生子类。下面是它的成员：
## 初始化对象
[init!(name: String!, bundleIdentifier: String!)](https://developer.apple.com/reference/inputmethodkit/imkserver/1385475-init)
&emsp; 根据plist文件提供的信息创建并返回一个server对象

[init!(name: String!, controllerClass: AnyClass!, delegateClass: AnyClass!)](https://developer.apple.com/reference/inputmethodkit/imkserver/1385520-init)
&emsp; 根据参数创建并返回一个server对象

## 获得输入法的Bundle
[func bundle()](https://developer.apple.com/reference/inputmethodkit/imkserver/1385387-bundle)
&emsp; 返回输入法的NSBundle对象

## 常量
[IMKModeDictionary](https://developer.apple.com/reference/inputmethodkit/imkserver/imkmodedictionary)
&emsp; 输入法模式字典关键字

[IMKControllerClass](https://developer.apple.com/reference/inputmethodkit/imkserver/imkcontrollerclass)
&emsp; 输入法控制器类的关键字

[IMKDelegateClass](https://developer.apple.com/reference/inputmethodkit/imkserver/imkdelegateclass)
&emsp; 输入法代理类的关键字

## 实例方法
[func lastKeyEventWasDeadKey()](https://developer.apple.com/reference/inputmethodkit/imkserver/1385506-lastkeyeventwasdeadkey)
&emsp; 

[func paletteWillTerminate()](https://developer.apple.com/reference/inputmethodkit/imkserver/1385358-palettewillterminate)
&emsp; 

# IMKMouseHandling
这是一个协议，它定义了输入法可以实现的鼠标处理事件。一下是它的成员：
## 处理鼠标事件
[func mouseDown(onCharacterIndex: Int, coordinate: NSPoint, withModifier: Int, continueTracking: UnsafeMutablePointer<ObjCBool>!, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkmousehandling/1385444-mousedown)
&emsp; 处理发送给输入法的鼠标按下事件

[func mouseUp(onCharacterIndex: Int, coordinate: NSPoint, withModifier: Int, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkmousehandling/1385410-mouseup)
&emsp; 处理发送给输入法的鼠标抬起事件

[func mouseMoved(onCharacterIndex: Int, coordinate: NSPoint, withModifier: Int, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkmousehandling/1385551-mousemoved)
&emsp; 处理发送给输入法的鼠标移动事件

# IMKServerInput
这是一个协议，它定义了处理文本事件的方法。这不是一个正式协议，因为有三种方式来处理事件，输入法选择其中之一来实现对应方法。如下：

* 键盘绑定。系统把每一个键盘按下事件映射到到输入法的一个方法。如果成功（找到此映射方法），系统调用`didCommandBySelector:client:`，否则（没有找到该方法）调用`inputText:client:`。针对此方式，你应当实现`input​Text:​client:​` 和`did​Command​By​Selector:​client:​`两个方法。

* 只处理文本数据。这种方式下你无需键盘绑定就能接收到所有键盘事件，然后解析相关的文本数据。键盘事件会包含Unicodes，产生它们的键盘码，修饰标记。该数据被发送给方法`input​Text:​key:​modifiers:​client:​`，你应当实现该方法。

* 处理所有事件。这种方式下你会接收到来自文本服务管理器的所有方法，这些方法被封装为NSEvent对象。你必须实现方法`handle​Event:​client:​`。

## 支持键盘绑定
[- (BOOL)inputText:(NSString *)string client:(id)sender;](https://developer.apple.com/reference/objectivec/nsobject/1385446-inputtext?language=objc)
&emsp; 处理没有映射到响应方法的键盘按下事件

[- (BOOL)didCommandBySelector:(SEL)aSelector client:(id)sender;](https://developer.apple.com/reference/objectivec/nsobject/1385394-didcommandbyselector?language=objc)
&emsp; 处理由用户行为产生的命令，比如按下某个按键或点击了鼠标按键

## 解析文本数据
[- (BOOL)inputText:(NSString *)string key:(NSInteger)keyCode modifiers:(NSUInteger)flags client:(id)sender;](https://developer.apple.com/reference/objectivec/nsobject/1385436-inputtext)
&emsp; 接收unicode、键盘码以及键盘的修饰标记数据

## 直接从文本服务管理器接收事件
[- (BOOL)handleEvent:(NSEvent *)event client:(id)sender;](https://developer.apple.com/reference/objectivec/nsobject/1385363-handle)
&emsp; 处理键盘按下和鼠标事件

## 提交写作串
[func commitComposition(Any!)](https://developer.apple.com/reference/objectivec/nsobject/1385539-commitcomposition)
&emsp; 通知控制器，提交组织串

## 获得输入串和候选串
[func composedString(Any!)](https://developer.apple.com/reference/objectivec/nsobject/1385416-composedstring)
&emsp; 返回当前组织串

[func originalString(Any!)](https://developer.apple.com/reference/objectivec/nsobject/1385400-originalstring)
&emsp; 返回组织前的unicode字串

[func candidates(Any!)](https://developer.apple.com/reference/objectivec/nsobject/1385360-candidates)
&emsp; 返回候选列表

## 常量
[Info Dictionary Keys](https://developer.apple.com/reference/inputmethodkit/imkserverinput/info_dictionary_keys)
&emsp; 

# IMKStateSetting
这是一个协议，它定义了设置和修改输入法状态的方法。下面是它的成员
## 激活和解除激活Server
[func activateServer(Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385434-activateserver)
&emsp; 激活输入法server

[func deactivateServer(Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385424-deactivateserver)
&emsp; 解除激活输入法server

## 显示偏好设置窗口
[func showPreferences(Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385549-showpreferences)
&emsp; 显示偏好设置窗口

## 获得支持的事件
[func recognizedEvents(Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385535-recognizedevents)
&emsp; 返回表示事件掩码的无符号整形数

## 获得模式字典
[func modes(Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385461-modes)
&emsp; 返回与输入法关联的模式字典

## 存取值
[func value(forTag: Int, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385547-value)
&emsp; 返回与tag匹配的值

[func setValue(Any!, forTag: Int, client: Any!)](https://developer.apple.com/reference/inputmethodkit/imkstatesetting/1385412-setvalue)
&emsp; 将值保存到key下

# NSObject
这是Objective-C派生体系的根类，从该类可以继承Objective-C对象的基本能力。

