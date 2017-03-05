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

# 编译Boost
编译参数形式如下：
``` bash
b2.exe --build-dir=build --stagedir=./stage/x64 --build-type=complete address-model=64 threading=multi --toolset=msvc-14.0 runtime-link=static -j 12
```

参数|说明
----|----
variant=debug/release|编译版本类型，debug版文件名有_d，release版没有，生成_d也必然使用debug版的C++运行时库，因此_gd是同时出现的
link=static/shared|编译为静态库还是动态库，生成.lib还是.dll，对应文件中的BOOST_LIB_PREFIX
threading=single/multi|使用单线程还是多线程CRT，多线程版文件名有_mt，单线程版没有。对应文件中的BOOST_LIB_THREAD_OPT
runtime-link=static/shared|静态还是动态链接CRT，静态链接文件名有_s，对应文件中的BOOST_LIB_THREAD_OPT
address-model=32/64|32位或64位编译
--toolset|C++编译器
--build-dir=[builddir]|存放编译的临时文件
--stagedir=[stagedir]|存放编译后的库文件，默认是stage
--build-type=complete|编译所有版本，否则只编译一小部分版本（相当于:variant=release, threading=multi;link=shared/static;runtime-link=shared）
--with-[library]|只编译指定的库，如输入--with-regex就只编译regex库了。
--show-libraries|显示需要编译的库名称

## 生成文件的命名规则
以`libboost_regex-vc71-mt-d-1_34.lib`为例：
* `lib`  前缀：除了Microsoft Windows之外，每一个Boost库的名字都以此字符串开始。在Windows上，只有普通的静态库使用lib前缀；导入库和DLL不使用。
* `boost_regex` 库名称：所有boost库名文件以boost_开头。
* `-vc71` Toolset 标记：标识了构建该库所用的toolset和版本。
* `-mt` Threading 标记：标识构建该库启用了多线程支持。不支持多线程的库没有-mt。
* `-d` ABI标记：对于每一种特性，向标记中添加一个字母：

标记|含义
---|---
s|静态链接CRT
g|使用调试版本的CRT
d|构建调试版本的Boost
y|使用Python的特殊调试构建
p|使用STLPort标准库而不是编译器提供的默认库
n|使用STLPort已被弃用的“native iostreams”

* `-1_34`
版本标记：完整的Boost发布号，下划线代替点。例如，1.31.1版本将被标记为“-1_31_1”。
* `.lib`
扩展名：取决于操作系统。在大多数unix平台上，.a是静态库，.so是共享库。在Windows上，.dll表示共享库，.lib是静态或导入库。

可见，32位或64位信息并不体现在文件命名中，因此需要分目录存放。通常在生成库文件时，要执行如下两条命令：
``` bash
b2.exe --build-dir=build --stagedir=./stage/x64 --build-type=complete address-model=64 threading=multi --toolset=msvc-14.0 runtime-link=static -j 12
b2.exe --build-dir=build --stagedir=./stage/win32 --build-type=complete address-model=32 threading=multi --toolset=msvc-14.0 runtime-link=static -j 12
```

# 使用Boost
## 使用32/64位版本
可以在CMake中加入如下判断并设置`Boost_LIBRARY_DIR`：
``` cmake

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
  set(Boost_LIBRARY_DIR "$ENV{BOOST_ROOT}\\stage\\x64\\lib")
elseif(CMAKE_SIZEOF_VOID_P EQUAL 4)
  set(Boost_LIBRARY_DIR "$ENV{BOOST_ROOT}\\stage\\win32\\lib")
endif()

set(Boost_USE_STATIC_LIBS ON)
find_package(Boost COMPONENTS program_options log REQUIRED)

message(STATUS "Boost_LIBRARIES:${Boost_LIBRARIES}")
```

执行
` cmake -G "Visual Studio 14 Win64" ..`
输出`Boost_LIBRARIES`为：
```
-- Boost_LIBRARIES:.../stage/x64/lib/libboost_xxx-mt-s-1_62.lib;...
```

执行
` cmake -G "Visual Studio 14" ..`
输出`Boost_LIBRARIES`为：
```
-- Boost_LIBRARIES:.../stage/Win32/lib/libboost_xxx-mt-s-1_62.lib;...
```

## 多线程、CRT开关
使用Boost时，在CMake中有相应的选项对应不同的Boost生成库：

选项|说明
---|---
Boost_USE_MULTITHREADED|使用与单线程/多线程链接CRT的Boost（_mt），默认ON
Boost_USE_STATIC_LIBS|使用Boost的静态/动态库，默认OFF
Boost_USE_STATIC_RUNTIME|使用静态/动态链接CRT的Boost（_s），默认值依赖平台
Boost_USE_DEBUG_RUNTIME|使用链接了debug/release版CRT的Boost（_g)，默认为ON

但我发现这几个开关实际上并不是平行的各管各的，比如：
``` cmake

set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(Boost_USE_DEBUG_RUNTIME ON)
set(Boost_USE_MULTITHREADED ON)

find_package(Boost COMPONENTS log REQUIRED)

message(STATUS "Boost_LIBRARIES:${Boost_LIBRARIES}")
```
执行
` cmake -G "Visual Studio 14" ..`

** `Boost_USE_STATIC_LIBS=ON` **，输出的`Boost_LIBRARIES`为：
```
...libboost_xxx-mt-s-1_62.lib;...
```
** `Boost_USE_STATIC_RUNTIME=ON` **，`Boost_LIBRARIES`为：
```
optimized;...libboost_xxx-mt-s-1_62.lib;
debug;...libboost_xxx-mt-sgd-1_62.lib;
```
此时如果`Boost_USE_DEBUG_RUNTIME=OFF`则不生成sgd版本。
如果`Boost_USE_STATIC_RUNTIME=OFF`，开关`Boost_USE_DEBUG_RUNTIME`将不起作用，`Boost_LIBRARIES`总是为：
```
optimized;...libboost_xxx-mt-s-1_62.lib;
```
所以一般静态链接Boost时，使用如下两行即可满足Debug和Release版本的链接：
``` cmake
set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
```
Release版使用：



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