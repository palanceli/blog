---
layout: post
title: CMake Demo （二）带GoogleTest的多项目构建
date: 2017-02-11 19:26:00 +0800
categories: CMake
tags: CMake Demo
toc: true
comments: true
---

引入GoogleTest进行单元测试，同时构建GoogleTest和业务可执行程序几乎成了一种套路，所以单独把这种情况备忘下来。<!-- more -->

代码树为：
``` shell
demo2
├── CMakeLists.txt
├── co.sh       --> 该脚本用于拉取googletest
├── googletest  --> 被co.sh拉取到本地，不属于代码树
│   └── ...
├── include
│   └── MyLib.h --> mylib暴露出来的接口
├── myexe
│   ├── CMakeLists.txt
│   ├── MyDemo.cpp
│   ├── MyDemo.h
│   ├── MyDemo_unittest.cpp
│   └── main.cpp
└── mylib
    ├── CMakeLists.txt
    ├── MyLib.cpp
    └── MyLib_unittest.cpp
```
总体上，各子项目的构建就放到项目内的CMake文件里来做，demo2/CMakeLists.txt里只负责包含子项目，以及创建unittest项目。因为unittest没有必要按照业务逻辑再细分模块，这样就必须在每个子项目里都写一份类似的项目逻辑。

# 主CMakeLists.txt
``` cmake
cmake_minimum_required (VERSION 2.6)

project(CMakeDemo)

add_subdirectory(mylib)
add_subdirectory(myexe)
add_subdirectory(googletest)

# 构建unittest的可执行项目
include_directories(${PROJECT_SOURCE_DIR}/googletest/googletest/include)
include_directories(${PROJECT_SOURCE_DIR}/include)

# 收集各子项的*.cpp、*.h文件
foreach ( folder myexe mylib)
  file(GLOB_RECURSE SRC "${PROJECT_SOURCE_DIR}/${folder}/*.cpp" "${PROJECT_SOURCE_DIR}/${folder}/*.h")
  list(APPEND ALL_SRC ${SRC})
endforeach(folder)
# 屏蔽main函数，因为gtest_main已经有了
LIST(REMOVE_ITEM ALL_SRC "${PROJECT_SOURCE_DIR}/myexe/main.cpp")

add_executable(myexe_test ${ALL_SRC})
target_link_libraries(myexe_test gtest_main)
```
包含子项目的部分比较简单。构建unittest项目是把各子项目里所有源文件和_unittest.*汇总起来，编译并链接到gtest_main，gtest_main提供了一个main函数，并支持通过参数只运行指定的测试用例，比如：
``` bash
$ ./myexe_test --gtest_filter=MyDemoUnitTest*
$ ./myexe_test --gtest_filter=MyDemoUnitTest.Test*
```
因此需要把业务的main函数屏蔽掉。

# myexe/CMakeLists.txt
``` cmake
cmake_minimum_required (VERSION 2.6)

include_directories(${PROJECT_SOURCE_DIR}/include)
set(SRC MyDemo.cpp MyDemo.h main.cpp ${PROJECT_SOURCE_DIR}/include/MyLib.h)
add_executable(myexe ${SRC})
target_link_libraries(myexe mylib_shared) # 静态链接mylib
```
这个子CMake就很简单了，只负责构建自己的可执行文件即可。

# mylib/CMakeLists.txt
``` cmake
cmake_minimum_required (VERSION 2.6)

MESSAGE(STATUS "operation system is ${CMAKE_SYSTEM_NAME}")
include_directories(${PROJECT_SOURCE_DIR}/include)
set(SRC MyLib.cpp ${PROJECT_SOURCE_DIR}/include/MyLib.h)

if(APPLE)
  set(CMAKE_MACOSX_RPATH 1)
endif()

add_library(mylib_static STATIC ${SRC})
add_library(mylib_shared SHARED ${SRC})
```
这个子CMake也很简单，只负责构建自己的静态/动态库即可。

# 总结
CMake的分层处理让每个子项目负责做自己的构建逻辑，高层CMake只负责包含子模块和构建跨模块项目。如果是在VC里，这种交叉引用源文件的项目，如果子项目增加或删减了文件，就需要做一系列手工操作，如果有32位/64位两个版本，工作量就要翻倍。其实Demo2的CMake还可以做得更智能一些——如主CMake文件那样，通过代码找文件，而不是硬编码，这样未来增删文件都不会带来额外工作。相比之下效率上有量级的提升！