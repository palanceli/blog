---
layout: post
title: libpinyin
date: 2017-05-14 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
libpinyin在macOS下默认编译就遇到问题，说找不到pkg-config和GLIB2，执行
``` bash
$ brew install pkgconfig
$ brew install glib
```
安装后解决。
<!-- more -->**继续报错**：
``` bash
CMake Warning (dev):
  Policy CMP0042 is not set: MACOSX_RPATH is enabled by default.  Run "cmake
  --help-policy CMP0042" for policy details.  Use the cmake_policy command to
  set the policy and suppress this warning.

  MACOSX_RPATH is not specified for the following targets:

   libpinyin

This warning is for project developers.  Use -Wno-dev to suppress it.
```
需要在CMakeLists.txt头部加上：`set (CMAKE_MACOSX_RPATH 1)`即可。

**继续报错**：说找不到`PhraseLargeTable3`、`ChewingLargeTable2`这些定义，再研究代码发现依赖了`BerkleyDB`或者`Kyoto Cabinet`，后者不知道是什么，猜应该也是类似数据库之类的。继续安装：
``` bash
$ brew install berkeley-db
```

**继续报错**：说找不到`config.h`，发现是CMakeLists.txt写得有毛病，在include路径里添加：
``` cmakelist
include_directories(
    ...
    ${PROJECT_BINARY_DIR}
)
```

**继续报错**：链接错误，找不到`pinyin::ForwardPhoneticConstraints::diff_result`，这个函数定义在`phonetic_lookup.cpp`中，在`libpinyin/src/lookup/CMakeLists.txt`中添加该文件：
``` cmake
set(
    LIBLOOKUP_SOURCES
    ...
    phonetic_lookup.cpp  # 添加此行
    ...
)
```

**继续报错**：链接错误，找不到`_db_create`，该函数来自BerkeleyDB，在`libpinyin/src/CMakeLists.txt`中添加：
``` cmake
target_link_libraries(
    libpinyin
    storage
    lookup
    ${DB_LIBRARY}  # 添加此行
)
```

**继续报错**：在执行`libpinyin/data/CMakeLists.txt`时，没有wget命令，把文件[model14.text.tar.gz](http://downloads.sourceforge.net/libpinyin/models/model14.text.tar.gz)放到了`libpinyin/data下`，并将`libpinyin/data/CMakeLists.txt`修改如下：
``` cmake
add_custom_command(
    OUTPUT
        ${CMAKE_SOURCE_DIR}/data/gb_char.table
        ${CMAKE_SOURCE_DIR}/data/gbk_char.table
        ${CMAKE_SOURCE_DIR}/data/interpolation2.text
    COMMENT
        "Downloading textual model data..."
    # COMMAND  # 注掉这两行
       # wget http://downloads.sourceforge.net/libpinyin/models/model14.text.tar.gz
    COMMAND
       tar xvf ${CMAKE_SOURCE_DIR}/data/model14.text.tar.gz -C ${CMAKE_SOURCE_DIR}/data    # 修改这一行
)
```

**继续报错**：在执行`libpinyin/data/CMakeLists.txt`时找不到`gen_binary_files`，全局搜索一下，修改`libpinyin/data/CMakeLists.txt`如下：
``` cmake
set(
    gen_binary_files_BIN
    ${CMAKE_BINARY_DIR}/utils/storage/Debug/gen_binary_files  # 在本行添加Debug部分
)
```