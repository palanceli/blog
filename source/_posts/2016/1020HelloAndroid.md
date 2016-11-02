---
layout: post
title: 在Android源码中编译生成apk
date: 2016-10-20 23:47:10 +0800
categories: Android
tags: Android开发环境
toc: true
comments: true
---
# 文件结构
我把代码放在了[HelloAndroid](https://github.com/palanceli/blog/tree/master/source/_drafts/2016/1020HelloAndroid/HelloAndroid)，文件结构为：
```
HelloAndroid
├──AndroidManifest.xml
├──Android.mk
├──src
│  └──palance/li/hello
│     └──HelloAndroid.java
└──res
   ├──layout
   │  └──main.xml
   ├──values
   │  └──strings.xml
   └──drawable
      └──icon.png
```
<!-- more -->
把该文件夹放到<Android源码>/packages/experimental目录下，我写了一个脚本HelloAndroid/ln2android.sh，只要执行
`$ sh ln2android.sh <android-dir>`
即可在<android-dir>/packages/experimental下生成指向HelloAndroid的软链接。
# 编译
执行如下命令：
``` bash
$ cd <android-dir>
$ source build/envsetup.sh
$ lunch aosp_arm_eng
$ mmm packages/experimental/HelloAndroid
```
即可生成apk文件：
`<android-dir>/out/debug/target/product/generic/system/app/HelloAndroid/HelloAndroid.apk`。
# 运行
为了不重新编译Android源码，需要执行：
``` bash
$ make snod
```
重新生成系统镜像，该应用就会被放置到桌面。
或者不要作为系统安装，启动了模拟器后，
``` bash
$ emulator& 
```
查询已安装的应用程序：
``` bash
$ adb shell pm list packages
package:com.android.providers.telephony
package:palance.li.hello
... ...
```
如果应用已安装，则先卸载再安装：
``` bash
$ adb uninstall palance.li.hello
... ...
$ adb install ~/HelloAndroid.apk
```