---
title: 驱动->HAL->frameworks->app
date:   2016-08-15 00:51:21 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
跟着《Android系统源代码情景分析》第2章，我想把从`驱动层`到`硬件抽象层`到`frameworks层`再到`应用层`各层的工作完整地做一遍、调一遍。之前已经有了一些积累，我希望在Android最新的源码上，并且使用AndroidStudio能编译、调试得到每一层。按照我下一步计划，接下来将深入研究键盘消息处理机制，希望在开展这一步工作之前，能够对Android的格局有更进一步的理解，对AndroidStudio的使用能够更娴熟。

首先我会按照《Android系统源代码情景分析》，在命令行下，自下而上把各层工作跑一遍。尔后再从上到下，逐步把各层工作切换到AndroidStudio上来。计划用两周时间搞定。代码就放在[palanceli/androidex/hello-android](https://github.com/palanceli/androidex/tree/master/hello-android)下。
<!-- more -->
# 驱动层
androidex的文件结构如下：
```
├──android-6.0.1_r11           // Android源码
├──androidex
   ├──setup.sh                 // 调用每个子项目的setup.sh，完成初始化工作
   ├──hello-android
   │  └──hello-android-driver
   │     ├──hello-android.c
   │     ├──hello-android.h
   │     ├──Kconfig
   │     ├──Makefile
   │     └──setup.sh           
   ├──... ...
   └──
```
脚本`androidex/hell-android/hello-android-driver/setup.sh`创建
软链`kernel/goldfish/drivers/hello-android`指向
`androidex/hell-android/hello-android-driver/`。
## 执行`setup.sh`完成初始化

``` bash
$ cd androidex
$ sh setup.sh
```
这么做的目的是让Android源码和我的代码分离开，我的代码全都集中在androidex下，可以完整地提交到GitHub上去。随Android源码编译的需要，androidex散落到源码树中，建个软链就确保源码树下总能访问到最新androidex了。

## 修改内核Kconfig文件
Android源码是不包含内核源码的，内核源码需要独立下载。我从[这里](https://android.googlesource.com/kernel/goldfish.git)下到的Android内核源码，并使用了3.4分支。在该版本的内核中，需要修改kernel/goldfish/drivers/Kconfig文件，并在后面追加：
``` bash
source drivers/hello-android/Kconfig
```
它的原理和我前面做`androidex/setup.sh`是一样的，内核通过该`Kconfig`总文件知道都需要编译哪些子模块，具体子模块的编译规则，则存放在`hello-android/Kconfig`中。

## 修改内核Makefile文件
在`kernel/goldfish/drivers/Makefile`的尾部添加：
``` bash
obj-$(CONFIG_HA) += hello-android/
```
其中`obj-$()`括号内的内容，前半部分`CONFIG_`是固定的，后半部分是`drivers/hello-android/Kconfig`第一行中`config`的名字。

## 编译内核驱动模块
先运行make menuconfig（注意：android6.0+goldfish3.4，默认运行make menuconfig有坑，解决办法详见[这里](http://www.cnblogs.com/palance/p/5187103.html)）
``` bash
$ cd kernel/goldfish
$ make menuconfig
```
勾选`Enable loadable module support`，并进入勾选子菜单`Module unloading`。
进入`Device Drivers` - 找到`Hello Android Driver`按`M`，指定以模块的方式编译`Hello Android`

接下来就可以编译了：
``` bash
$ cd /Volumes/android-6.0.1_r11g/android-6.0.1_r11
$ source build/envsetup.sh
$ lunch aosp_arm-eng
... ...
$ cd kernel/goldfish
$ export ARCH=arm
$ export SUBARCH=arm
$ export CROSS_COMPILE=arm-eabi-
$ export PATH=/Volumes/android-6.0.1_r11g/android-6.0.1_r11/prebuilts/gcc/darwin-x86/arm/arm-eabi-4.8/bin:$PATH
$ make -j4
```
新编译的内核镜像文件被保存在`kernel/goldfish/arch/arm/boot/zImage`。

## 加载并运行内核驱动模块
启动模拟器并使用刚刚编译的新内核：
``` bash
$ emulator -kernel kernel/goldfish/arch/arm/boot/zImage &
```


把刚刚编译的ko文件拷贝到模拟器里：
``` bash
$ adb push drivers/hello-android/hello-android.ko /data
```

加载ko模块：
``` bash
adb shell insmod /data/hello-android.ko
```

列出已经安装好的模块：
``` bash
$ adb shell lsmod
Module                  Size  Used by
hello_android           2466  0
```
表明hello_android已经被成功加载了。

## 验证驱动模块各类接口
### 验证proc文件系统接口
验证虚拟设备ha的proc文件系统接口，返回值表明接口正常：
``` bash
$ adb shell cat proc/ha
0
$ adb shell "echo '1' > /proc/ha"
$ adb shell cat proc/ha
1
```
### 验证devfs文件系统接口
验证虚拟设备ha的devfs文件系统接口，返回值表明接口正常：
``` bash
$ adb shell "cd /sys/class/ha/ha && cat value"
1
$ adb shell "cd /sys/class/ha/ha && echo '3' > value"
$ adb shell "cd /sys/class/ha/ha && cat value"
3
```
### 验证dev文件系统接口
验证虚拟设备ha的dev文件系统访问接口略微麻烦，因为它读/写的内容是二进制的，需要编一个小程序来验证，源码详见[ha-driver-checker](https://github.com/palanceli/androidex/tree/master/hello-android/ha-driver-checker)。
该程序的编译同样先通过`androidex/setup.sh`完成初始化，然后单独编译ha-driver-checker：
``` bash
$ mmm external/ha-driver-checker
... ...
target Executable: ha (out/debug/target/product/generic/obj/EXECUTABLES/ha_intermediates/LINKED/ha)
target Unpacked: ha (out/debug/target/product/generic/obj/EXECUTABLES/ha_intermediates/PACKED/ha)
target Symbolic: ha (out/debug/target/product/generic/symbols/system/bin/ha)
Export includes file: external/ha-driver-checker/Android.mk -- out/debug/target/product/generic/obj/EXECUTABLES/ha_intermediates/export_includes
target Strip: ha (out/debug/target/product/generic/obj/EXECUTABLES/ha_intermediates/ha)
Install: out/debug/target/product/generic/system/bin/ha
```
输出信息已经清楚地写明了生成文件存放的路径，把它拷贝到模拟器上然后执行：
``` bash
$ adb push out/debug/target/product/generic/obj/EXECUTABLES/ha_intermediates/LINKED/ha /data
1843 KB/s (82652 bytes in 0.043s)
$ adb shell /data/ha
Read original value: 3.
Write value 13 to /dev/ha.
Read the value again:13.
```
说明dev文件系统访问接口正常！



