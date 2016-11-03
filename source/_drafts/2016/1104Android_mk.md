---
layout: post
title: Android.mk文件介绍
date: 2016-11-04 22:50:58 +0800
categories: Android
tags: 编译
toc: true
comments: true
---
Android.mk是Android提供的一种makefile文件，用来指定诸如：
* 编译生成so库名、
* 引用的头文件目录
* 需要编译的.c/.cpp文件
* .a静态库文件等。
<!-- more -->
要掌握jni，就必须熟练掌握Android.mk的语法规范。 

# Android.mk文件的用途 
一个android子项目中会存在一个或多个Android.mk文件 
1. 单一的Android.mk文件。直接参考<Android源码>/development/ndk/samples/hello-jni项目，在这个项目中只有一个Android.mk文件 

2. 多个Android.mk文件。如果需要编译的模块比较多，可以将模块放置在相应的目录中，可以在每个目录中定义对应的Android.mk文件（类似于上面的写法），最后，在根目录放置一个Android.mk文件，内容为：
`include $(call all-subdir-makefiles)`。
只需要这一行就可以了，它的作用就是包含所有子目录中的Android.mk文件。
3. 多个模块共用一个Android.mk文件。这个文件允许你将源文件组织成模块，这个模块中含有： 
  * 静态库（.a文件）
  * 动态库（.so文件） 

只有共享库才能被安装/复制到您的应用软件（APK）包中。

`include $(BUILD_STATIC_LIBRARY)`，编译出的是静态库；
`include $(BUILD_SHARED_LIBRARY)`，编译出的是动态库。

# 自定义变量 
以下是在 Android.mk中依赖或定义的变量列表，可以定义其他变量为自己使用，但是NDK编译系统保留下列变量名： 
* 以 LOCAL_开头的名字（例如 LOCAL_MODULE） 
* 以 PRIVATE_, NDK_ 或 APP_开头的名字（内部使用） 
* 小写名字（内部使用，例如‘my-dir’） 

如果为了方便在 Android.mk 中定义自己的变量，建议使用 MY_前缀，一个小例子： 
``` makefile
MY_SOURCES := foo.c 
ifneq ($(MY_CONFIG_BAR),) 
MY_SOURCES += bar.c 
endif 
LOCAL_SRC_FILES += $(MY_SOURCES) 
```
> 注意：‘:=’是赋值的意思；'+='是追加的意思；‘$’表示引用某变量的值。 



# GNU Make系统变量 
  这些 GNU Make变量在你的 Android.mk 文件解析之前，就由编译系统定义好了。注意在某些情况下，NDK可能会多次分析 Android.mk，每一次某些变量的定义会有不同。 
* CLEAR_VARS : 指向一个编译脚本，几乎所有未定义的 LOCAL_XXX变量都在"Module-description"节中列出。必须在开始一个新模块之前包含这个脚本：
```
include$(CLEAR_VARS)
```
  用于重置除LOCAL_PATH变量外的，所有LOCAL_XXX系列变量。 

* BUILD_SHARED_LIBRARY : 指向编译脚本，根据所有的在 LOCAL_XXX 变量把列出的源代码文件编译成一个共享库。 
> 注意，必须至少在包含这个文件之前定义 LOCAL_MODULE 和 LOCAL_SRC_FILES。 
* BUILD_STATIC_LIBRARY : 变量用于编译一个静态库。静态库不会复制到的APK包中，但是能够用于编译共享库。 
示例：
```
include $(BUILD_STATIC_LIBRARY)
```
  注意，这将会生成一个名为 lib$(LOCAL_MODULE).a 的文件 
* TARGET_ARCH : 目标 CPU平台的名字 
* TARGET_PLATFORM : Android.mk 解析的时候，目标 Android 平台的名字.详情可考/development/ndk/docs/stable- apis.txt. 

  * android-3 -> Official Android 1.5 system images 
  * android-4 -> Official Android 1.6 system images 
  * android-5 -> Official Android 2.0 system images 
* TARGET_ARCH_ABI : 暂时只支持两个值，armeabi 和 armeabi-v7a 
* TARGET_ABI : 目标平台和 ABI 的组合， 
                               
# 模块描述变量 
下面的变量用于向编译系统描述你的模块。应该定义在
`include  $(CLEAR_VARS)`和`include $(BUILD_XXXXX)`之间。
  
  $(CLEAR_VARS)是一个脚本，清除所有这些变量。 

* LOCAL_PATH : 用于给出当前文件的路径。必须在 Android.mk 的开头定义，可以这样使用：
```
LOCAL_PATH := $(call my-dir) 
```
  如当前目录下有个文件夹名称 src，则可以这样写：
```
$(call src)
```
  那么就会得到 src 目录的完整路径。这个变量不会被$(CLEAR_VARS)清除，因此每个 Android.mk只需要定义一次(即使在一个文件中定义了几个模块的情况下)。 
* LOCAL_MODULE : 这是模块的名字，它必须是唯一的，而且不能包含空格。必须在包含任一的$(BUILD_XXXX)脚本之前定义它。模块的名字决定了生成文件的名字。 
* LOCAL_SRC_FILES : 这是要编译的源代码文件列表。只要列出要传递给编译器的文件，因为编译系统自动计算依赖。注意源代码文件名称都是相对于 LOCAL_PATH的，你可以使用路径部分，例如： 
```
LOCAL_SRC_FILES := foo.c toto/bar.c\ 
    Hello.c
```
  文件之间可以用空格或Tab键进行分割,换行请用"\" 。如果是追加源代码文件的话，请用`LOCAL_SRC_FILES += `
可以`LOCAL_SRC_FILES := $(call all-subdir-java-files)`这种形式来包含`local_path`目录下的所有java文件。 
* LOCAL_C_INCLUDES:  可选变量，表示头文件的搜索路径。默认的头文件的搜索路径是LOCAL_PATH目录。 
* LOCAL_STATIC_LIBRARIES: 表示该模块需要使用哪些静态库，以便在编译时进行链接。 
* LOCAL_SHARED_LIBRARIES:  表示模块在运行时要依赖的共享库（动态库），在链接时就需要，以便在生成文件时嵌入其相应的信息。它不会附加列出的模块到编译图，也就是仍然需要在Application.mk 中把它们添加到程序要求的模块中。 
* LOCAL_LDLIBS:  编译模块时要使用的附加的链接器选项。这对于使用‘-l’前缀传递指定库的名字是有用的。 例如，
`LOCAL_LDLIBS := -lz`表示告诉链接器生成的模块要在加载时刻链接到`/system/lib/libz.so`
可查看 docs/STABLE-APIS.TXT 获取使用 NDK发行版能链接到的开放的系统库列表。 
* LOCAL_MODULE_PATH 和 LOCAL_UNSTRIPPED_PATH : 在 Android.mk 文件中， 还可以用LOCAL_MODULE_PATH 和LOCAL_UNSTRIPPED_PATH指定最后的目标安装路径。不同的文件系统路径用以下的宏进行选择： 
TARGET_ROOT_OUT：表示根文件系统。 
TARGET_OUT：表示 system文件系统。 
TARGET_OUT_DATA：表示 data文件系统。 
用法如：
```
LOCAL_MODULE_PATH :=$(TARGET_ROOT_OUT) 
```
  至于LOCAL_MODULE_PATH 和LOCAL_UNSTRIPPED_PATH的区别，暂时还不清楚。 
* LOCAL_JNI_SHARED_LIBRARIES：定义了要包含的so库文件的名字
*  
LOCAL_JNI_SHARED_LIBRARIES := libxxx
这样在编译的时候，NDK自动会把这个libxxx打包进apk； 放在youapk/lib/目录下 

# NDK提供的函数宏 
GNU Make函数宏，必须通过使用'$(call  )'来调用，返回值是文本化的信息。 
* my-dir:返回当前 Android.mk 所在的目录的路径，相对于 NDK 编译系统的顶层。这是有用的，在 Android.mk 文件的开头如此定义：
```
LOCAL_PATH := $(call my-dir)
```

* all-subdir-makefiles: 返回一个位于当前'my-dir'路径的子目录中的所有Android.mk的列表。例如，某一子项目的目录层次如下：
```
src/foo
├──Android.mk 
├──lib1
│  └──Android.mk
└──lib2
   └──Android.mk
```

  如果 src/foo/Android.mk 包含一行： 
`include $(call all-subdir-makefiles)`
那么它就会自动包含 src/foo/lib1/Android.mk 和 src/foo/lib2/Android.mk。这项功能用于向编译系统提供深层次嵌套的代码目录层次。注意，在默认情况下，NDK 将会只搜索在 src/*/Android.mk 中的文件。 

* this-makefile:  返回当前Makefile 的路径(即这个函数调用的地方) 
* parent-makefile:  返回调用树中父 Makefile 路径。即包含当前Makefile的Makefile 路径。 
* grand-parent-makefile：返回调用树中父Makefile的父Makefile的路径 

# Android.mk示例 
```
#编译静态库  
LOCAL_PATH := $(call my-dir)  
include $(CLEAR_VARS)  
LOCAL_MODULE = libhellos  
LOCAL_CFLAGS = $(L_CFLAGS)  
LOCAL_SRC_FILES = hellos.c  
LOCAL_C_INCLUDES = $(INCLUDES)  
LOCAL_SHARED_LIBRARIES := libcutils  
LOCAL_COPY_HEADERS_TO := libhellos  
LOCAL_COPY_HEADERS := hellos.h  
include $(BUILD_STATIC_LIBRARY)  
  
#编译动态库  
LOCAL_PATH := $(call my-dir)  
include $(CLEAR_VARS)  
LOCAL_MODULE = libhellod  
LOCAL_CFLAGS = $(L_CFLAGS)  
LOCAL_SRC_FILES = hellod.c  
LOCAL_C_INCLUDES = $(INCLUDES)  
LOCAL_SHARED_LIBRARIES := libcutils  
LOCAL_COPY_HEADERS_TO := libhellod  
LOCAL_COPY_HEADERS := hellod.h  
include $(BUILD_SHARED_LIBRARY)  
  
#使用静态库  
LOCAL_PATH := $(call my-dir)  
include $(CLEAR_VARS)  
LOCAL_MODULE := hellos  
LOCAL_STATIC_LIBRARIES := libhellos  
LOCAL_SHARED_LIBRARIES :=  
LOCAL_LDLIBS += -ldl  
LOCAL_CFLAGS := $(L_CFLAGS)  
LOCAL_SRC_FILES := mains.c  
LOCAL_C_INCLUDES := $(INCLUDES)  
include $(BUILD_EXECUTABLE)  
  
#使用动态库  
LOCAL_PATH := $(call my-dir)  
include $(CLEAR_VARS)  
LOCAL_MODULE := hellod  
LOCAL_MODULE_TAGS := debug  
LOCAL_SHARED_LIBRARIES := libc libcutils libhellod  
LOCAL_LDLIBS += -ldl  
LOCAL_CFLAGS := $(L_CFLAGS)  
LOCAL_SRC_FILES := maind.c  
LOCAL_C_INCLUDES := $(INCLUDES)  
include $(BUILD_EXECUTABLE)
```