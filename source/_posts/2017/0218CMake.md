---
layout: post
title: 使用CMake+Boost中遇到的几个问题
date: 2017-02-19 22:45:00 +0800
categories: 随笔笔记
tags: CMake
toc: true
comments: true
---
最近在新的Windows系统下使用CMake+Boost，不慎踩了好多坑，浪费不少时间。备忘如下：
<!-- more -->
# 安装Boost前先安装python
前文曾经介绍过，安装使用Boost本来是很简单的，只要执行`booststrap.bat`和`b2.exe`即可。注意：一定要仔细看二者的执行结果，`b2.exe`好像依赖python，如果没有安装python，这个编译会报错。python安装完成后要把`python.exe`的路径添加到环境变量`PATH`中。

# 编译Boost使用的VS要和CMake编译工程使用的VS版本一致
来`boost_1_62_0\stage\lib`下，可以看到编译出来的lib文件名是包含VC版本号的，如：
`libboost_atomic-vc140-mt-1_62.lib`。
`vc140`对应Visual Studio 2015，如果此时CMake编译project的Visual Studio版本不是2015，而又依赖了Boost：
``` cmake
set(Boost_USE_STATIC_LIBS ON) 
find_package(Boost COMPONENTS program_options log REQUIRED)
```
这会导致CMake能找到Boost，却找不到需要的`program_options`和`log`组件，这是因为CMake要找与指定Visual Studio版本对应的libboost库文件。报出的错是找不到指定的Boost版本，其实跟Boost版本无关，跟编译它使用的VS版本有关。

# 环境变量BOOST_ROOT
如果指定环境变量，BOOST_ROOT的值为boost所在的上一级目录，比如我的目录如下：
``` bash
c:\boost_1_62_0   <-- BOOST_ROOT指向这里
    ├─bin.v2
    ├─boost
    ├─doc
    ├─libs
    ├─more
    ├─stage
    ├─status
    ├─tools
    └─...
```
环境变量应设为：`BOOST_ROOT=c:\boost_1_62_0`。

我尝试不写这个环境变量，发现CMake依然能找到Boost，那就不要写了吧~