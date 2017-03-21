---
layout: post
title: macOS下基于IMK Framework的输入法
date: 2017-03-05 23:33:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
首先还是要以[NumberInput_IMKit_Sample](!https://developer.apple.com/library/content/samplecode/NumberInput_IMKit_Sample/Introduction/Intro.html#)为例，研究macOS InputMethodKit输入法的编写。<!-- more -->
# 使用Xcode创建输入法项目
初始步骤如下：
1. 在Xcode中选择`File > New > Project > macOS > Cocoa`点击Next
2. 填写`Project Name`为`IMKSample`，点击Next
3. 选择要保存的位置`IMKSample/`，点击`Create`。
4. 打开`Info.plist`文件编辑器，添加4个Key，见下表。
5. 添加图标文件`IMKSample/main.tif`
6. 选中左侧导航栏的`IMKSample`项目，选中TARGETS中的`IMKSample`，`General > Linked Frameworks and Libraries`点击`+`号，添加`InputMethodKit.framework`

| Key | Type | Value |
| --- | --- | --- |
|InputMethodConnectionName|String|IMKSampleConnection|
|InputMethodServerControllerClass|String|IMKSampleController|
|Application is background only|Boolean|YES|
|tsInputMethodIconFileKey|String|main.tif|
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
-(BOOL)inputText:(NSString*)string client:(id)sender // 添加此函数
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

const NSString* kConnectionName = @"IMKSampleConnection";
IMKServer*       server;

int main(int argc, const char * argv[]) {
  @autoreleasepool{
    NSString*       identifier;

    identifier = [[NSBundle mainBundle] bundleIdentifier];
    server = [[IMKServer alloc] initWithName:(NSString*)kConnectionName bundleIdentifier:[[NSBundle mainBundle] bundleIdentifier]];
    
//    [NSBundle loadNibNamed:@"MainMenu" owner:[NSApplication sharedApplication]];
    
    [[NSApplication sharedApplication] run];
  }
  return 0;
}
```
# 编译
1. 先编译生成IMKSample.app，然后将此生成文件拷贝到`/Library/Input Methods`
2. 来到Xcode中IMKSample的配置：`Build Settings > All > Build Locations > Per-configuration Build Products Path > Debug`改为`/Library/Input Methods`
注意一定要先做完第1步，再做第2步，以后再编译就只做第2步即可。如果跳过1直接进入第2步会提示没有权限生成文件。

# 编译
直接编译该例程的NumberInput0，构建的时候提示本地macOS版本低于NumberInput的部署要求版本。其实显然不是本地版本低，而是NumberInput的配置有问题。打开
`NumberInput工程配置 - General - Deployment Info - Deployment Target`
设为10.6即可。

# 指定输出路径
打开
`工程配置 - Build Settings - All - Build Locations - Per-configuration Build Products Path - Debug`
置为：
`/Library/Input Methods` ——这里是系统输入法app的位置。

编译后即可在`系统偏好设置 - 键盘 - 输入源 - 加号`中找到`NumberInput`，添加后即可在app中选择该输入法。

# ReadMe
NumberInput0里有四个文件，ReadMe中有一个大致的介绍。
## NumberInputController.h
派生自IMKInputController，声明了自己的input controller。

## NumberInputController.m
定义了自己的input controller。它实现了方法：
`-(BOOL)inputText:(NSString*)string client:(id)sender`
该方法定义在：
` /System/Library/Frameworks/InputMethodKit.framework/Headers/IMKInputController.h`
该方法最终将接收键盘输入。在本例中它只是返回NO，表示输入法不作任何处理地将键盘输入转给客户端程序。

## main.m
该文件定义了主入口。分配了IMKServer实例，该实例将通过NSConnection与客户端程序通讯，同时也会与每个输入法input controller实例进行通讯。

## Info.plist
该文件包含了输入法必须的信息。

# 调试
**不要在输入法中设置断点**，因为macOS的输入法是全局的——在某个app中修改了输入法，在其他所有app中都将生效。如果在记事本中命中了输入法的断点，此时焦点将切到xcode，xcode中的输入法也变成被调试的输入法，xcode本身也将被卡死。

在`-(BOOL)inputText:(NSString*)string client:(id)sender`函数中有NSLog输出，但是当我run起NumberInput输入法后，每次按键都输出如下内容：
```
2017-03-05 23:25:41.893 NumberInput[46492:5200485] IMKServer Stall detected, *please Report* your user scenario attaching a spindump (or sysdiagnose) that captures the problem - (activateServerWithReply:) block performed very slowly (0.00 secs)
... ...
2017-03-05 23:26:09.620 NumberInput[46492:5200485] IMKServer Stall detected, *please Report* your user scenario attaching a spindump (or sysdiagnose) that captures the problem - (deactivateServerWithReply:) block performed very slowly (0.00 secs)
```