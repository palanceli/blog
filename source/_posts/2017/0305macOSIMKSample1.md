---
layout: post
title: macOS下基于IMK Framework的输入法
date: 2017-03-05 23:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
[NumberInput_IMKit_Sample](https://developer.apple.com/library/content/samplecode/NumberInput_IMKit_Sample/Introduction/Intro.html#)和[《Input Method Kit API Reference》](https://developer.apple.com/reference/inputmethodkit)是苹果为输入法开发提供仅有的两篇材料，本文根据它们研究macOS 基于IMKit framework的输入法的编写。<!-- more -->

# 使用Xcode创建输入法项目
初始步骤如下：
1. 在Xcode中选择`File > New > Project > macOS > Cocoa`点击Next
2. 填写`Project Name`为`IMKSample`，注意在`Organization Identifier`中一定要包含`.InputMethod.`如：`palanceli.inputmethod`，点击Next
3. 选择要保存的位置`IMKSample/`，点击`Create`。
4. 打开`Info.plist`文件编辑器，添加4个Key，见下表。
5. 添加图标文件`IMKSample/main.tif`
6. 选中左侧导航栏的`IMKSample`项目，选中TARGETS中的`IMKSample`，`General > Linked Frameworks and Libraries`点击`+`号，添加`InputMethodKit.framework`
<style>
table th:nth-of-type(1){
    width: 300px;
}
table th:nth-of-type(2){
    width: 60px;
}
</style>

|Key| Type | Value |
| --- | --- | --- |
|InputMethodConnectionName|String|IMKSampleConnection|
|InputMethodServerControllerClass|String|IMKSampleController|
|Application is background only|Boolean|YES|
|tsInputMethodIconFileKey|String|main.tif|
|tsInputMethodCharacterRepertoireKey|Array|(String)Latn|
此时编译是没问题的，但该项目还只是一个普通的应用程序。

# 添加IMKSampleController
1. 为项目新建文件，选择`macOS > Cocoa Class`点击Next
2. 填写`Class`为`IMKSampleController`，`Subclass...`为`IMKInputController`，点击Next，选择要保存的位置，点击Create

修改生成的`IMKSampleController.h`如下：
``` obj-c
#import <Cocoa/Cocoa.h>
#import <InputMethodKit/InputMethodKit.h> // 添加此行

@interface IMKSampleController : IMKInputController

@end
```

修改生成的`IMKSampleController.m`如下：
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
@end

```
# 修改main.m文件
``` obj-c

#import <Cocoa/Cocoa.h>
#import <InputMethodKit/InputMethodKit.h> // 添加包含

// 每个输入法必须有唯一连接名称，注意：不能包含点和空格
const NSString* kConnectionName = @"IMKSampleConnection";
IMKServer*       server;

int main(int argc, const char * argv[]) {
  @autoreleasepool{
    // 获取bundle ID
    NSString* bundleID = [[NSBundle mainBundle] bundleIdentifier];
    server = [[IMKServer alloc] initWithName:(NSString*)kConnectionName
                            bundleIdentifier:bundleID];
    
    //finally run everything
    [[NSApplication sharedApplication] run];
  }
  return 0;
}

```
# 删除多余文件
删除`AppDelegate.h`、`AppDelegate.m`、`ViewController.h`、`ViewController.m`这些由模板生成的文件。

# 编译
1. 执行`sudo chmod -R 777 /Library/Input Methods`，确保Xcode可以直接生成app文件到这里。
2. 来到Xcode中IMKSample的配置：`Build Settings > All > Build Locations > Per-configuration Build Products Path > Debug`改为`/Library/Input Methods`。

# 调试
**不要在输入法中设置断点**，因为macOS的输入法是全局的——在某个app中修改了输入法，在其他所有app中都将生效。如果在记事本中命中了输入法的断点，此时焦点将切到xcode，xcode中的输入法也变成被调试的输入法，xcode本身也将被卡死。

在`-(BOOL)inputText:(NSString*)string client:(id)sender`函数中有NSLog输出，如果是用Xcode直接运行起app，可以在其Debug area中看到输出，如果不是通过Xcode调起，也可以在控制台中看到输出。

苹果关于IMKit的官方材料提供得很少，除了官方文档，还有些价值的还有`/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/HIToolbox.framework/Versions/A/Headers/TextInputSources.h`其中有大量的注释。