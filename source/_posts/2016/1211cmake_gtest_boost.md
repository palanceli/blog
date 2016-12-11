---
layout: post
title: CMake + gtest + boost
date: 2016-12-11 19:18:37 +0800
categories: 随笔笔记
tags: googletest CMake boost
toc: true
comments: true
---
最近参与一个跨平台协作的项目，其中的CMake、googletest的引入以及支撑层基础模块的组织形式，是我之前的项目里没有接触过的。很快我也需要组织一个类似的跨平台项目，所以趁这次参与，把相关的工具摸索一遍。<!-- more -->

# 用CMake实现跨平台项目配置
以前在Windows下写代码就是用Visual Studio生成solution，并在里面配置，同时把solution文件上传svn，在macOS下则使用xcode做同样的事情。但如果一个项目需要跨平台协作，需要在Windows、Linux、macOS下同时编译，这种方式就有很大的问题：项目需要引入哪些模块、模块之间的依赖关系，要在各平台下的IDE工具里各自完成，但他们之间无法相互同步，这就引入了很多重复工作，并且不同平台下可能是不同的RD在负责，很容易带来不一致。

这个时候就需要CMake出场了，它用来描述一个工程的组织形式，需要编译成可执行文件还是静态/动态库文件，各模块的编译选项、链接选项等等这些都是通过代码来实现的。CMake可以用这一套代码在各平台下生成指定IDE工具的工程文件，它支持的IDE包括Visual Studio、XCode、Makefiles、Eclipse等。

其实以前仅在Windows下使用Visual Studio的时候，也会遇到一个项目需要编译成多种形式的情况，比如最常见的32位、64位各自的项目配置需要同步，更复杂一些的对于同一份代码要编译出不同的形式，比如要把正式版的exe中部分模块以DEBUG Lib库的形式编译给另一个exe以完成单元测试。以前我就是用VS生成多套项目配置，当项目大到有百十个模块，一旦某些模块之间的依赖关系或者编译、链接选项有变化时，就十分痛苦，同样的设置要做N遍。

这都是CMake可以解决的问题。引入CMake以后，各IDE的工程文件就成了CMake的输出结果，因此只需要把CMakelists.txt上传svn，sln、xcodeproj之类工具相关的工程配置文件都不用再上传，每次生成就好了。

# 让模块真正成为积木
以前项目缺乏模块统一管理：A需要压缩，就下一份ziplib的代码放到工程里；B需要下载，再下一份libcurl；C也需要压缩，却不知道工程里已经有一份ziplib的代码，自己又弄了一套libzip过来，几年下来，工程混乱不堪，积重难返。

理想的做法应该是在选型的时候，对基础模块作出评估，找到质量最高、最稳定的模块，放到公共模块池里，这个模块池是独立于业务项目的。业务项目文件里仅存放自己开发的代码，用一个脚本把需要的基础模块从公共模块池中check out出来，然后再用CMake生成sln文件。这样，一个项目可能包含百十个模块，可是仅在svn中管理自己的代码，这样可以大大减少SVN的体积。

# 让单元测试成为习惯
这一点就不再多说了，以前我自己做过几个测试框架，针对不同特点的项目，曾经用C++、python做过各种自测机制。一个牛逼的开发，能够以一当十，除了高效，还要有高稳定性，不让测试整天追在屁股后头改bug。Googletest为此做了很不错的支撑。

# 坚决抵制闭门造车
在做项目的时候经常遇到对造车轮有瘾的人，如果这种人主导项目，那将是噩梦。今天的开源世界已经非常广阔且成熟，能针对需求找到最好的开源模块，把它吃透、应用到自己的项目当中绝对是开发能力的一部分。善于发现和使用优秀的开源项目好处多多，他们的设计、实现原理以及编码规范都能成为程序员之间沟通的标准协议。过去自己写的很多东西都能在开源世界里找到代替品，程序员每隔几年也应该升级一下自己大脑里的操作系统，把那些陈旧的东西永久删除，配备上最新的模块。

其实boost也不是啥新东西了，我的项目里大部分模块有一个公共需求，就是命令行参数解析，当年很多开发都为此各自实现一套，导致各自能接收的参数格式都不统一。我当年是从Solaris里拆出来的getopt，改吧改吧实现出Windows版本。前天写个小代码遇到第一件事儿又是参数解析，发现其实boost的program options已经有很完备的实现了，立马放弃自己的破玩意，改投boost。

# 组织一个test项目
接下来就把这几个玩具怎么拼接在一起记录下来。我的代码结构如下：
```
sgdxtest/
├── co.bat
└── src
    ├── CMakeLists.txt
    └── main
        └── program_options_unittest.cpp 
```
## 组织公共模块
其中co.bat用于checkout公共模块，在本项目中就是googletest，其内容如下：
``` bash
# co.bat
svn co http://svn.xxx.com/svn/sgdxmodules/googletest-1.8.0 src/
```
执行了co.bat之后，代码树为：
```
sgdxtest/
├── co.bat
└── src
    ├── CMakeLists.txt
    ├── googletest
    │   └── ... ...
    └── main
        └── program_options_unittest.cpp
```
googletest是从github下载的稳定版本，放到自己的svn公共模块池里。

## 编写CMakeLists.txt
CMakeLists.txt的内容如下：
``` makefile
cmake_minimum_required(VERSION 3.7)

project(SGDXTest)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
message(STATUS "C++11 support has been enabled by default.")

set(Boost_USE_STATIC_LIBS ON)  # 静态链接boost，并制定需要的lib库
find_package(Boost 1.62.0 COMPONENTS program_options REQUIRED)

if(NOT Boost_FOUND)
  message("未发现Boost!")
endif()

# 设置googletest的include目录
include_directories(${PROJECT_SOURCE_DIR}/googletest/include ${Boost_INCLUDE_DIRS})

# 添加googletest子项目
add_subdirectory(${PROJECT_SOURCE_DIR}/googletest)

# 指定生成的可执行文件以及需要链接的库文件
add_executable(sgdx_test ${PROJECT_SOURCE_DIR}/main/program_options_unittest.cpp)
target_link_libraries(sgdx_test gtest gtest_main)
target_link_libraries(sgdx_test ${Boost_LIBRARIES})
```
## 编写TestCase
program_options_unitest.cpp内容如下：
``` c++
#include <iostream>
#include <algorithm>
#include <iterator>
#include <gtest/gtest.h>
#include <boost/program_options.hpp>

namespace boost_test{

namespace po = boost::program_options;
using namespace std;

class ProgramOptionsTest : public testing::Test{
        protected:
        static void SetUpTestCase(){
        }

        static void TearDownTestCase(){
        }
};
TEST_F(ProgramOptionsTest, Test1)
{
        int opt;
        po::options_description desc("Allowed options");
        desc.add_options()
        ("help,h", "product help message")
        ("optimization_level", po::value<int>(&opt)->default_value(10))
        ("include-dir,I", po::value< vector<string> >(), "include path")
        ;

        // a.out --optimization_level 2 -I"c:/boost/include", "gtest/include"
        const char* argv[] = {"a.out", "--optimization_level", "2", "-I", "c:/boost/include", "-I", "gtest/include" };
        int argc = 7;

        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);

        ASSERT_EQ(vm.count("help"), 0);
        ASSERT_EQ(vm.count("optimization_level"), 1);
        ASSERT_EQ(vm["optimization_level"].as<int>(), 2);
        ASSERT_EQ(opt, 2);
        ASSERT_EQ(vm.count("include-dir"), 1);

        const vector<string> vct = vm["include-dir"].as< vector<string> >();
        ASSERT_EQ(vct.size(), 2);
        ASSERT_EQ(vct[0], "c:/boost/include");
        ASSERT_EQ(vct[1], "gtest/include");
};
```
它写了一个用例，用于测试boost::program_options的用法，为了让代码能编译，需要安装boost。

## 安装boost
在macOS下，安装boost非常简单，只需要执行
``` bash
$ brew install boost
```
即可。我试了在Windows下编译源码，也非常简单，只需要执行
``` bash
booststrap.bat
b2.exe
```
即可。

## 使用CMake生成工程文件
接下来即可使用CMake生成工程文件，我是在macOS下，然后使用make完成编译：
``` bash
$ cd sgdxtest/src
$ mkdir build
$ cd build
$ cmake ..
$ make
```