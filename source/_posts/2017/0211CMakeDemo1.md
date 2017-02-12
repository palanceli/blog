---
layout: post
title: CMake Demo （一）构建可执行文件的基本步骤
date: 2017-02-11 19:26:00 +0800
categories: CMake
tags: CMake Demo
toc: true
comments: true
---

为了避免各隔几个礼拜再次使用的时候又要学习一遍，本文备忘CMake的一些基本用法。不求系统全面，只把自己使用中遇到的问题备忘下来。系统全面那是官方教程应该做的事~<!-- more -->
# 构建可执行文件
代码树为：
``` shell
demo1
├── CMakeLists.txt
├── demo.cpp
├── demo.h
├── main.cpp
└── build     --> 该目录不属于代码树的一部分，构建文件创建在此
    └── ...
```
CMakeLists.txt内容如下：
``` cmake
cmake_minimum_required (VERSION 2.6)

project(CMakeDemo)  # 项目名
set(src_list main.cpp demo.cpp demo.h)
message(STATUS "This is Binary dir " ${CMakeDemo_BINARY_DIR})
message(STATUS "This is Source dir " ${CMakeDemo_SOURCE_DIR})
add_executable(Demo1 ${src_list})
```
它包含CMake文件最基本的两个要素：project和add_executable。
# project
project 用来给项目定义一个名字，如果生成的是Visual C++项目，该名字就是项目的Solution Name以及sln文件名。

我尝试把这行注掉，结果虽然还能生成项目文件，但是一些依赖该值的变量都会不正常，比如`CMakeDemo_BINARY_DIR`和`CMakeDemo_SOURCE_DIR`，没了这些基本变量会让CMake无法运作。

# add_executable
`add_executable(<name> source1 [source2 ...])`
定义了工程生成可执行文件的文件名，如果生成的是Visual C++项目，该行对应solution中的一个project，<name>就对应该project名称。

sourceN则是编译可执行文件需要的源文件。记得把.h文件也加进来，如果不加头文件，编译、构建都是没问题的，但是生成的IDE中也就不包含头文件了，这给编辑带来不便。

# set
`set(<variable> <value>... [PARENT_SCOPE])`
定义变量，此处定义了源文件列表，该列表可能被多次引用，所以早早地把它赋给变量src_list

# 隐式变量
`<projectname>_BINARY_DIR` 指向demo1/build
`<projectname>_SRC_DIR` 指向demo1
CMake系统也预定义了变量：
`PROJECT_BINARY_DIR`与`<projectname>_BINARY_DIR`一致
`PROJECT_SOURCE_DIR`与`<projectname>_SRC_DIR`一致
显然应当使用前者。

# message
`message([<mode>] "message to display" ...)`
显示一条消息，这是调试CMake文件最常用的方式，其中<mode>是消息类型，常见取值：
```
STATUS         = 次要信息
WARNING        = 警告信息，不打断CMake的处理
SEND_ERROR     = 错误信息，不打断CMake的处理，生成过程被跳过
FATAL_ERROR    = 错误信息，立即终止CMake的处理
```

# 关于大小写
CMake关键字不区分大小写，但是变量名是区分大小写的:
`MESSAGE(STATUS "This is Binary dir " ${PROJECT_BINARY_DIR})`✅
`message(STATUS "This is Binary dir " ${PROJECT_BINARY_DIR})`✅
`message(STATUS "This is Binary dir " ${project_binary_dir})`❌

# 关于CMake的GUI工具
刚开始以为这玩意儿是用来生成CMake文件的，原来只是依据CMake文件生成本地具体项目的工具。不过吧，能免去记忆CMake的参数形式，也还是有用。

> 本文源码在[CMakeDemo](https://github.com/palanceli/blog/tree/master/source/_attachment/20170211CMakeDemo)可下载。