---
layout: post
title: 《Android Programming BNRG》笔记三十五
date: 2017-11-15 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章是对[Material Design官方文档](https://developer.android.com/design/material/index.html)的总结。
<!-- more -->

笔记就不多写了，还是直接看官方文档吧。终于把这本书啃完了，这本书相比《iOS Programming BNRG》品质略差，主要不足是结构不是很紧凑，一些机制本来属于一脉的体系，被分割到多个章节，或者被业务逻辑打散了。学习平台的机制是学习这本书的主要目标。

这本书的读书笔记要点列出如下，便于自己未来查阅。
[笔记一](/2017/09/10/2017/0909AndroidProgrammingBNRG01/)
- 使用Interface Builder构建界面布局
- 为控件关联代码变量和响应函数
- 使用约束确保兼容不同的尺寸的设备
- 修改app图标
- iOS应用的UI刷新机制

[笔记二](/2017/10/16/2017/1016AndroidProgrammingBNRG02/)
- 数据类型
- optional变量
- 字符串插值

[笔记三](/2017/10/16/2017/1016AndroidProgrammingBNRG03/)
- 点和像素

[笔记四](/2017/10/16/2017/1016AndroidProgrammingBNRG04/)
- 响应TextField的变化事件
- 在TextField失去焦点后收起键盘
- Property observer
- 协议和代理

[笔记五](/2017/10/16/2017/1016AndroidProgrammingBNRG05/)
- TabBarViewController的使用
- 具有多个ViewController的应用
- framework
- 在项目中添加图片资源

[笔记六](/2017/10/17/2017/1017AndroidProgrammingBNRG06/)
- Android API level版本号和发行版的对应关系
- 设置VC的View
- 创建约束条件
- 为控件关联事件

[笔记七](/2017/10/18/2017/1018AndroidProgrammingBNRG07/)
- Fragment的概念、使用步骤
- Localization的基本概念
- 控件尺寸校验

[笔记八](/2017/10/19/2017/1019AndroidProgrammingBNRG08/)
- animate函数的使用

[笔记九](/2017/10/20/2017/1020AndroidProgrammingBNRG09/)
- 调试技巧

[笔记十](/2017/10/21/2017/1021AndroidProgrammingBNRG10/)
- UITableView的运作原理
- 初始化函数
- 依赖倒置原则

[笔记十一](/2017/10/22/2017/1022AndroidProgrammingBNRG11/)
- UITableView的编辑模式
- Alerts的使用

[笔记十二](/2017/10/23/2017/1023AndroidProgrammingBNRG12/)
- 子类化UITableViewCell
- 让字体随系统设置动态调整

[笔记十三](/2017/10/24/2017/1024AndroidProgrammingBNRG13/)
- 创建菜单，并关联响应函数
- 添加系统图标
- 设置层级导航关系

[笔记十四](/2017/10/25/2017/1025AndroidProgrammingBNRG14/)
- SQLite数据的操作步骤

[笔记十五](/2017/10/26/2017/1026AndroidProgrammingBNRG15/)
- 在字符串资源中定义格式化字符
- 使用隐式Intents

[笔记十六](/2017/10/27/2017/1027AndroidProgrammingBNRG16/)
- 摄像头的使用
- Bitmap类的使用
- users-feature声明

[笔记十七](/2017/10/28/2017/1028AndroidProgrammingBNRG17/)
- 为资源创建别名
- 为不同尺寸的屏幕创建不同的布局

[笔记十八](/2017/10/29/2017/1029AndroidProgrammingBNRG18/)
- 添加不同的语种字符资源

[笔记十九](/2017/10/30/2017/1030AndroidProgrammingBNRG19/)
- TalkBack

[笔记二十](/2017/10/31/2017/1031AndroidProgrammingBNRG20/)
- Data Binding
- MVVM vs MVC
- assets 资源

[笔记二十一](/2017/11/01/2017/1101AndroidProgrammingBNRG21/)
- 播放音频
- 使用JUnit编写单元测试
- 使用mockito和hamcrest
- 使用Data Binding在XML中为widget关联响应函数
- retain Fragment

[笔记二十二](/2017/11/02/2017/1102AndroidProgrammingBNRG22/)
- style的定义和应用
- theme的修改和覆盖

[笔记二十三](/2017/11/03/2017/1103AndroidProgrammingBNRG23/)
- drawable资源的定义和使用
- shape drawable的定义和使用
- State List Drawable资源的定义和使用
- 根据屏密度分割apk和mipmap资源
- 9段拉伸图片

[笔记二十四](/2017/11/04/2017/1104AndroidProgrammingBNRG24/)
- 遍历系统所有应用
- 任务和进程
- concurrent documents

[笔记二十五](/2017/11/05/2017/1105AndroidProgrammingBNRG25/)
- 联网操作
- json数据解析
- 主线程和后台线程

[笔记二十六](/2017/11/06/2017/1106AndroidProgrammingBNRG26/)
- Looper/MessageQueue/Message/Handler
- Picasso
- StrictMode

[笔记二十七](/2017/11/07/2017/1107AndroidProgrammingBNRG27/)
- Shared Preferences
- 使用SearchView

[笔记二十八](/2017/11/08/2017/1108AndroidProgrammingBNRG28/)
- Service
- 检测网络是否可用
- AlarmManager
- PendingIntent
- Notifications

[笔记二十九](/2017/11/09/2017/1109AndroidProgrammingBNRG29/)
- 创建、注册standalone receiver
- 创建、注册dynamic reciever
- 使用receiver
- 限定broadcast的传播范围
- 有序广播

[笔记三十](/2017/11/10/2017/1110AndroidProgrammingBNRG30/)
- 使用WebView
- 令Activity不随转屏重建

[笔记三十一](/2017/11/11/2017/1111AndroidProgrammingBNRG31/)
- 创建自定义视图
- 在View上绘制

[笔记三十二](/2017/11/12/2017/1112AndroidProgrammingBNRG32/)
- Property Animation
- Animation Set

[笔记三十三](/2017/11/13/2017/1113AndroidProgrammingBNRG33/)
- Google Play Services
- LocationService，申请权限，请求服务，使用结果
- 在模拟器上模拟位置变化

[笔记三十四](/2017/11/14/2017/1114AndroidProgrammingBNRG34/)
- 获取Google地图API key
- 显示Google地图
- 在Google地图上标注位置