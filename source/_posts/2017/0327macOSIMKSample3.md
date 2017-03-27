---
layout: post
title: macOS下基于IMK的输入法（三）——绘制候选窗口
date: 2017-03-27 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
在苹果给的例子[NumberInput_IMKit_Sample](https://developer.apple.com/library/content/samplecode/NumberInput_IMKit_Sample/Introduction/Intro.html#)中，`NumberInput2`指示了如何显示候选窗口，但这个候选窗口的绘制是由系统完成的，输入法只是给它提供候选数据，并指定横/竖排等属性，并不能参与到候选窗口的绘制，无法支持皮肤等特性，因此对于第三方输入法的开发意义不大。通常都是关闭该属性，而由输入法自行创建和绘制候选窗口。<!-- more -->

本文就介绍如何完成候选窗口的创建和绘制。本例的功能非常简单，还是缓存写作串，按空格或回车上屏。只是缓存的写作串将同时绘制到候选窗口上，上屏后候选窗口消失。

# 独立的输入法引擎
在前文中，输入法相关的数据直接放在`IMKSampleController`中维护，其实也只有写作串。如果要支持自绘候选窗，就需要在多个类中访问写作串，就需要将该数据独立出来，放到输入法引擎中了：
``` obj-c
// SGDXIMEngine.h
@interface SGDXIMEngine : NSObject
+(SGDXIMEngine*) sharedObject;

-(NSMutableString*) appendComposeString:(NSString*)string;  // 向写作串追加字符
-(void) cleanComposeString;         // 清除写作串
-(NSMutableString*) composeString;  // 获得写作串
@end
```
``` obj-c
// SGDXIMEngine.m
@implementation SGDXIMEngine
{
  NSMutableString* _composeString;
}

+(SGDXIMEngine*)sharedObject
{
  static SGDXIMEngine* sObject = nil;
  @synchronized (self) {
    if(sObject == nil){
      sObject = [[self alloc]init];
    }
  }
  return sObject;
}

-(NSMutableString*) composeString
{
  if(_composeString == nil){
    _composeString = [[NSMutableString alloc]init];
  }
  return _composeString;
}

-(void) setComposeString:(NSString*) value
{
  [[self composeString] setString:value];
}

-(NSString*)appendComposeString:(NSString *)string
{
  [[self composeString] appendString:string];
  return [self composeString];
}

-(void)cleanComposeString
{
  [[self composeString] setString:@""];
}
@end
```
# 添加显示写作串的候选视图
在这个视图中一般要显示候选串，此处并没有给输入法配备转换引擎，因此让它显示写作串即可。只需要实现函数-(void)drawRect:(NSRect)dirtyRect完成绘制：
``` obj-c
// IMKSCandidatesView.h
#import <Cocoa/Cocoa.h>

@interface IMKSCandidatesView : NSView
@end
```
``` obj-c
// IMKSCandidatesView.m
#import "IMKSCandidatesView.h"
#import "SGDXIMEngine.h"

@implementation IMKSCandidatesView

- (void)drawRect:(NSRect)dirtyRect 
{
  [super drawRect:dirtyRect];
    
  // Drawing code here.
  NSLog(@"IMKSCandidatesView::drawRect");
  // 绘制灰色背景
  NSRect bounds = [self bounds];
  [[NSColor lightGrayColor]set];
  [NSBezierPath fillRect:bounds];

  SGDXIMEngine *imEngine = [SGDXIMEngine sharedObject];
  // 绘制写作串
  NSMutableAttributedString* compString =
  [[NSMutableAttributedString alloc]initWithString:[imEngine composeString]];
  [compString addAttribute:NSFontAttributeName
                     value:[NSFont userFontOfSize:16]
                     range:NSMakeRange(0, [[imEngine composeString]length])];
  
  [compString drawInRect:[self bounds]];
}
@end
```
# 添加候选窗口
这个候选窗口包含前面创建的视图，负责在compString非空的时候显示，为空的时候隐藏。显示的位置位于光标的下方。
``` obj-c
// IMKSCandidatesWindow.h
#import <Cocoa/Cocoa.h>
#import <InputMethodKit/InputMethodKit.h>

@interface IMKSCandidatesWindow : NSWindow
-(void)update:(id<IMKTextInput, NSObject>)sender;
@end
```
``` obj-c
// IMKSCandidatesWindow.m
#import "IMKSCandidatesWindow.h"
#import "SGDXIMEngine.h"
#import "IMKSCandidatesView.h"

@implementation IMKSCandidatesWindow
{
  IMKSCandidatesView* _view;
}

-(id)initWithContentRect:(NSRect)contentRect styleMask:(NSWindowStyleMask)style
                 backing:(NSBackingStoreType)bufferingType defer:(BOOL)flag
{
  self = [super initWithContentRect:contentRect
                          styleMask:NSBorderlessWindowMask
                            backing:bufferingType defer:flag];
  if(self){
    [self setOpaque:NO];
    [self setLevel:NSFloatingWindowLevel];
    [self setBackgroundColor:[NSColor clearColor]];
    _view = [[IMKSCandidatesView alloc]initWithFrame:self.frame];
    [self setContentView:_view];
    [self orderFront:nil];
  }
  return self;
}

// 计算光标位置
-(NSPoint) getCaretPosition:(id<IMKTextInput, NSObject>)sender
{
  NSPoint ps;
  NSRect lineHeightRect;
  [sender attributesForCharacterIndex:0 lineHeightRectangle:&lineHeightRect];
  ps = NSMakePoint(lineHeightRect.origin.x, lineHeightRect.origin.y);
  return ps;
}

-(void)update:(id<IMKTextInput, NSObject>)sender
{

  NSPoint caretPosition = [self getCaretPosition:sender];
  SGDXIMEngine *imEngine = [SGDXIMEngine sharedObject];
  
  NSMutableAttributedString* compString =
  [[NSMutableAttributedString alloc]initWithString:[imEngine composeString]];
  [compString addAttribute:NSFontAttributeName
                     value:[NSFont userFontOfSize:16]
                     range:NSMakeRange(0, [[imEngine composeString]length])];
  
  NSRect rect = NSZeroRect;   // 写作串为空则不显示
  
  // 计算窗口区域
  if([[[SGDXIMEngine sharedObject]composeString] length] > 0){
    rect = NSMakeRect(caretPosition.x,
                      caretPosition.y - [compString size].height,
                      [compString size].width ,
                      [compString size].height);
  }
  
  NSLog(@"IMKSCandidatesWindow::update rect:(%.0f, %.0f, %.0f, %.0f)",
        rect.origin.x, rect.origin.y, rect.size.width, rect.size.height);
  [self setFrame:rect display:YES];
  // 计算视图区域
  [_view setFrame:NSMakeRect(0, 0, rect.size.width, rect.size.height)];
  [_view setNeedsDisplay:YES];

}
@end
```
# InputInputController子类
该子类的实现在之前的基础上需要：1、创建候选窗口；2、每次追加写作串或上屏后需要更新候选窗口：
``` obj-c
// IMKSampleController.h
#import <Cocoa/Cocoa.h>
#import <InputMethodKit/InputMethodKit.h>

@interface IMKSampleController : IMKInputController

@end
```
``` obj-c

#import "IMKSampleController.h"
#import "SGDXIMEngine.h"
#import "IMKSCandidatesWindow.h"

@implementation IMKSampleController
{
  IMKSCandidatesWindow* _candidatesWindow;
}
-(IMKSCandidatesWindow*) candidatesWindow
{
  if(_candidatesWindow == nil){
    _candidatesWindow = [[IMKSCandidatesWindow alloc]
               initWithContentRect:NSZeroRect
               styleMask:NSBorderlessWindowMask
               backing:NSBackingStoreBuffered
               defer:YES];
  }
  return _candidatesWindow;
}

-(void) appendComposedString:(NSString*) string client:(id)sender
{
  SGDXIMEngine* imEngine = [SGDXIMEngine sharedObject];
  NSString *compString = [imEngine appendComposeString:string];
  // 向光标处插入内嵌文字
  [sender setMarkedText:compString
         selectionRange:NSMakeRange(0, [compString length])
       replacementRange:NSMakeRange(NSNotFound, NSNotFound)];
  [[self candidatesWindow]update:[self client]]; // 更新候选窗
}

-(void) commitComposedString:(id)sender
{
  SGDXIMEngine* imEngine = [SGDXIMEngine sharedObject];
  // 向光标处插入上屏文字
  [sender insertText:[[SGDXIMEngine sharedObject] composeString] 
    replacementRange:NSMakeRange(NSNotFound, NSNotFound)];
  [imEngine cleanComposeString];
  [[self candidatesWindow]update:[self client]];  // 更新候选窗
}

- (BOOL)handleEvent:(NSEvent *)event client:(id)sender
{
//  NSLog(@"%@", event);
  if([event type] == NSKeyDown){
    unichar key = [[event characters] characterAtIndex:0];
    // 如果是字符则追加到写作串，并更新候选窗
    if((key >= 'a' && key <= 'z') ||(key >= '0' && key <= '9')){
      [self appendComposedString:[event characters] client:sender];
      return YES;
    }
    // 如果是空格或回车且有写作串则上屏，并更新候选窗
    if(([event keyCode] == kVK_Space || [event keyCode] == kVK_Return)&&
      [[[SGDXIMEngine sharedObject] composeString] length] > 0)
    {
      [self commitComposedString:sender];
      return YES;
    }
  }
  return NO;
}

- (NSUInteger)recognizedEvents:(id)sender {
  return NSEventMaskFlagsChanged | NSEventMaskKeyDown | NSEventMaskKeyUp;
}

@end
```