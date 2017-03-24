---
layout: post
title: macOS下基于IMK的输入法（二）——处理流程
date: 2017-03-23 23:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
[前文](http://palanceli.com/2017/03/05/2017/0305macOSIMKSample1/)分析了基于IMK输入法的创建步骤，本文将分析对按键的处理流程和规范。[《Input Method Kit（译）》](http://palanceli.com/2017/03/06/2017/0306InputMethodKit/#IMKServerInput)中提到IMKServerInput对按键的处理模式有三种：键盘绑定，仅处理文本数据，处理所有事件。这三种模式，输入法的处理空间越来越大，灵活性越来越强，可实现的功能也越来越强大，当然要承担的职责也就越来越多。<!-- more -->
# 键盘绑定
> 系统把每一个键盘按下事件映射到到输入法的一个方法。如果成功（找到此映射方法），系统调用didCommandBySelector:client:，否则（没有找到该方法）调用inputText:client:。针对此方式，你应当实现inputText(_:client:) 和didCommand(by:client:)两个方法。

以上是苹果官方文档的描述，可以做个实验来观察这两个方法的调用流程：
``` obj-c
#import "IMKSampleController.h"

@implementation IMKSampleController
// 该方法接收来自客户程序的按键输入，InputMethodKit会把按键事件转换成NSString发送给本方法。
//返回YES表明输入法要处理，系统将不再把按键继续发送给应用程序；否则返回NO
-(BOOL)inputText:(NSString*)string client:(id)sender
{
  NSLog(@"%@", string);
  return NO;
}

-(BOOL)didCommandBySelector:(SEL)aSelector client:(id)sender
{
  // 如果输入法要处理该事件，则返回YES，否则返回NO
  NSLog(@"didCommandBySelector:%@", NSStringFromSelector(aSelector));
  return NO;
}
@end
```
切出输入法，按下`a`、`b`、`c`，可以在控制台看到如下输出：
```
默认  12:33:25.769423 +0800 IMKSample a
默认  12:33:33.385260 +0800 IMKSample b
默认  12:33:33.385260 +0800 IMKSample c
```
按下`Backspace`、`回车`、`Tab`以及上下左右键，看到如下输出：
```
默认  12:33:36.319315 +0800 IMKSample didCommandBySelector:deleteBackward:
默认  12:33:27.258984 +0800 IMKSample didCommandBySelector:insertNewline:
默认  12:33:45.027618 +0800 IMKSample didCommandBySelector:insertTab:
默认  12:36:20.385862 +0800 IMKSample didCommandBySelector:moveUp:
默认  12:36:21.633254 +0800 IMKSample didCommandBySelector:moveDown:
默认  12:36:21.063002 +0800 IMKSample didCommandBySelector:moveLeft:
默认  12:36:22.083668 +0800 IMKSample didCommandBySelector:moveRight:
```
我找不到系统在哪里做的按键与方法的映射，但可以用这种方法遍历出所有的方法选择器，可以得出**结论：**
1. 当按下字符键，将调用`input​Text:​client:​`并传入按下的字符
2. 当按下控制键，将调用`did​Command​By​Selector:​client:​`并传入该控制键对应的方法选择器

在两个函数中，如果输入法要处理该字符/控制键，则返回YES，该按键就不在传递给应用程序；否则返回NO，同时按键被发送到应用程序。

两个函数本质上是一样的，都是当用户有按键时被调用，只不过一个是按字符键，一个是按控制键，输入法要做的就是根据按键内容决定是否更新写作串、候选串以及是否上屏。
## 实现方法
假设要实现的输入法逻辑是：对于字符按键暂时缓存起来，通过回车或空格完成上屏。实现方法：在`input​Text:​client:​`中缓存空格以外的字符，如果是空格则上屏；在`did​Command​By​Selector:​client:​`中处理回车完成上屏。以下是这两个函数的实现：
``` obj-c
-(BOOL)inputText:(NSString*)string client:(id)sender
{
  NSLog(@"inputText:%@", string);
  if([string isEqualToString:@" "]){  // 如果是空格则上屏
    [self commitComposedString:sender];
  }else{                              // 否则追加到写作串
    [self appendComposedString:string client:sender];
    NSLog(@"composed String:%@", [self composedString]);
  }
  return YES;
}

-(BOOL)didCommandBySelector:(SEL)aSelector client:(id)sender
{
  // 如果输入法要处理该事件，则返回YES，否则返回NO
  NSLog(@"didCommandBySelector:%@", NSStringFromSelector(aSelector));
  if(aSelector == @selector(insertNewline:)){ // 如果是回车则上屏
    [self commitComposedString:sender];
    return YES;
  }
  return NO;
}
```
本节的实现代码参见[macIMKSample v1.1](https://github.com/palanceli/macIMKSample/tree/v1.1)。
# 仅处理文本数据
> 这种方式下你无需键盘绑定就能接收到所有键盘事件，然后解析相关的文本数据。键盘事件会包含Unicodes，产生它们的键盘码，修饰标记。该数据被发送给方法- (BOOL)inputText:key:modifiers:client:，你应当实现该方法。

按照与键盘绑定同样的方法实现`- (BOOL)inputText:key:modifiers:client:`并观察系统传入的参数：
``` obj-c
- (BOOL)inputText:(NSString*)string
              key:(NSInteger)keyCode
        modifiers:(NSUInteger)flags
           client:(id)sender
{
  NSLog(@"inputText:%@ key:0x%2lX modifiers:0x%4lX",
        string, (long)keyCode, (unsigned long)flags);
  return NO;
}
```
如果既实现了`input​Text:​client:​`又实现了`input​Text:​key:​modifiers:​client:​`，系统会调用后者。切出输入法，按下`a`、`shift-a`、`Ctrl-a`、`Backspace`、`回车`、`Tab`以及`→`键，看到如下输出：
```
17/3/24 上午1:17:03.266 IMKSample[7202]: inputText:a key:0x 0 modifiers:0x   0
17/3/24 上午1:17:06.854 IMKSample[7202]: inputText:A key:0x 0 modifiers:0x20000
17/3/24 上午1:17:08.136 IMKSample[7202]: inputText: key:0x 0 modifiers:0x40000
17/3/24 上午1:17:10.206 IMKSample[7202]: inputText: key:0x33 modifiers:0x   0
17/3/24 上午1:17:10.972 IMKSample[7202]: inputText:
 key:0x24 modifiers:0x   0
17/3/24 上午1:17:13.244 IMKSample[7202]: inputText:    key:0x30 modifiers:0x   0
17/3/24 上午1:17:16.203 IMKSample[7202]: inputText: key:0x7C modifiers:0xA00000
```
## 实现方法
在这种方式下实现输入法的方法和键盘绑定很像，只不过把在两个函数里做的事情放在`input​Text:​key:​modifiers:​client:​`这一个函数里干了。mac为keyCode定义了一套常量，位于`Events.h`中的`kVK_ANSI_xxx`。根据传入的按键，如果是字符则追加入写作串，如果是空格或回车，且写作串非空，则上屏。代码如下：
``` obj-c
- (BOOL)inputText:(NSString*)string
              key:(NSInteger)keyCode
        modifiers:(NSUInteger)flags
           client:(id)sender
{
  NSLog(@"inputText:%@ key:0x%02lX modifiers:0x%04lX",
        string, (long)keyCode, (unsigned long)flags);
  
  unichar key = [string characterAtIndex:0];
  if((key >= 'a' && key <= 'z') || (key >= '0' && key <= '9'))
  { // 如果是字符则追加到写作串
    [self appendComposedString:string client:sender];
    return YES;
    
  }
  
  if((keyCode == kVK_Space || keyCode == kVK_Return)
     && [[self composedString] length]>0)
  { // 如果是空格或回车且有写作串则上屏
    [self commitComposedString:sender];
    return YES;
  }
  return NO;
}
```
本节的实现代码参见[macIMKSample v1.2](https://github.com/palanceli/macIMKSample/releases/tag/v1.2)。
# 处理所有事件
> 这种方式下输入法会接收到来自文本服务管理器的所有方法，这些方法被封装为NSEvent对象。你必须实现方法handle​Event:​client:​。

同理，可以打印`handle​Event:​client:​`的参数，看系统都传入了什么。需要注意：如果输入法同时实现了三种实现方式，系统使用它们的优先级是：处理文本数据>处理所有事件>键盘绑定。所以在实现`handle​Event:​client:​`之前必须把`input​Text:​key:​modifiers:​client:​注掉。此外还要实现方法`recognizedEvents:`并返回输入法要处理的事件：
``` obj-c
- (NSUInteger)recognizedEvents:(id)sender {
  return NSEventMaskFlagsChanged | NSEventMaskKeyDown | NSEventMaskKeyUp;
}

- (BOOL)handleEvent:(NSEvent *)event client:(id)sender
{
  NSLog(@"%@", event);
  return NO;
}
```
切出输入法按下：`a`、`shift`、`control`、`option`、`command`看到如下输出：
```
... NSEvent: type=KeyDown      ... flags=0 win=0x0 winNum=0 ctxt=0x0 chars="a" unmodchars="a" repeat=0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0x20000 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0x40000 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0x80000 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0x100000 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0 win=0x0 winNum=0 ctxt=0x0 keyCode=0
... NSEvent: type=FlagsChanged ... flags=0x100000 win=0x0 winNum=0 ctxt=0x0 keyCode=0
```
可见，接管所有事件的方式可以收到`shift`、`control`、`option`、`command`等按键，这在键盘绑定或处理文本数据的方式下是收不到的。从`recognizedEvents:`的返回来看，输入法应该能响应每个按键的按下抬起，但实际上却只能收到控制键的抬起，收不到字符的按键抬起事件。

## 实现方法
要实现与前面同等功能的输入法，需要在`handle​Event:​client:​`函数中判断如果是字符按键则缓存，如果是回车或空格则上屏。代码如下：
``` obj-c
- (BOOL)handleEvent:(NSEvent *)event client:(id)sender
{
  NSLog(@"%@", event);
  if([event type] == NSKeyDown){
    unichar key = [[event characters] characterAtIndex:0];
    if((key >= 'a' && key <= 'z') ||(key >= '0' && key <= '9')){
      [self appendComposedString:[event characters] client:sender];
      return YES;
    }
    if(([event keyCode] == kVK_Space || [event keyCode] == kVK_Return)&&
      [[self composedString] length] > 0)
    {
      [self commitComposedString:sender];
      return YES;
    }
  }
  return NO;
}
```
本节的实现代码参见[macIMKSample v1.3](https://github.com/palanceli/macIMKSample/releases/tag/v1.3)。