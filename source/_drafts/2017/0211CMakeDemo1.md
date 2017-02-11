---
layout: post
title: CMake Demo 1
date: 2017-02-11 19:26:00 +0800
categories: CMake
tags: CMake Demo
toc: true
comments: true
---

为了避免各隔几个礼拜再次使用的时候又要学习一遍，本文备忘CMake的一些基本用法。<!-- more -->
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

project(CMakeDemo)
set(src_list main.cpp demo.cpp demo.h)
message(STATUS "This is Binary dir " ${Demo1_BINARY_DIR})
message(STATUS "This is Source dir " ${Demo1_SOURCE_DIR})
add_executable(Demo1 ${src_list})
```
它包含cmake文件最基本的两个要素：project和add_executable。
project是给项目定义一个名字