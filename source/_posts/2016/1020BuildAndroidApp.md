---
layout: post
title: Android应用程序的编译（一）——源码下编译
date: 2016-11-06 17:51:10 +0800
categories: Android
tags: Android开发环境
toc: true
comments: true
---
这篇博文几经修改，本来想写成Android应用程序在源码、SDK下的编译方法，搞个花式编译方法的汇总贴。因为我是从Android源码开始学习的，一开始并不怎么关心app怎么写，偶尔写点代码，代码量都不大，主要为了验证和调试用的。所以最初主要就用简单的文本编辑器+源码下mmm来编译。此外我也不太喜欢动辄动用AndroidStudio这种大东西，至少在对它生成的一堆文件没有清楚理解之前，我没有把它当做学习Android的主要工具。
<!-- more -->
最近要学习的内容不断往应用层扩展，有必要对Android应用程序的编译彻底搞清楚了。所谓“彻底搞清楚”不是用AndroidStudio这种IDE一键完成，而是要知道这一键背后都做了什么，原生的方式怎么做。理解了这些，使用上层工具才能更深刻，人剑合一:)

这两天在学习的时候发现，关于SDK编译的大部分文章都比较老，比如都还在讲`apkbuilder`这种被Google废弃的方式；此外，不断深入，发现细节点还挺多的，比如命令行生成项目、环境变量的设置……这些细节掌握了，这些支撑层的环境做好了，对于以后把玩Android应用程序效率提升很有帮助。所以，我打算把原先的一篇文章做个拆分：“源码编译”作为一篇，“SDK编译”作为一篇，“NDK编译”……看情况吧，当下还没涉及到~

# 最简单的Android工程
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
## Android.mk
``` makefile
LOCAL_PATH:=$(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := $(call all-subdir-java-files)
LOCAL_PACKAGE_NAME := HelloAndroid
include $(BUILD_PACKAGE)
```
LOCAL_MODULE_TAGS是当前模块所包含的标签，一个模块可以包含多个标签。可选的值有：debug, eng, user, development, optional（默认值）。标签是提供给编译类型使用的，不同的编译类型会安装包含不同标签的模块：

名称|说明
---|----
eng|默认类型。该编译类型适用于开发阶段。当选择这种类型时，编译结果将：安装包含 eng, debug,user，development 标签的模块；安装所有没有标签的非 APK 模块；安装所有产品定义文件中指定的 APK模块
user|该编译类型适合用于最终发布阶段。当选择这种类型时，编译结果将：安装所有带有 user 标签的模块；安装所有没有标签的非 APK 模块；安装所有产品定义文件中指定的 APK 模块，APK模块的标签将被忽略
userdebug|该编译类型适合用于 debug 阶段。该类型和 user 一样，除了：会安装包含 debug 标签的模块，编译出的系统具有 root 访问权限

## AndroidManifest.xml
``` xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
          package="palance.li.hello"
          android:versionCode="1"
          android:versionName="1.0">
  <application android:icon="@drawable/icon"
               android:label="@string/app_name">
    <activity android:name=".HelloAndroid"
              android:label="@string/app_name">
      <intent-filter>
        <!-- 这两个属性的设置使得HelloAndroid组件可以作为应用程序的根组件 -->
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
    </activity>
  </application>
</manifest>
```

## HelloAndroid.java
java文件只在`onCreate(...)`函数中增加了一行log输出：
``` java
package palance.li.hello;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

public class HelloAndroid extends Activity{
    private final static String LOG_TAG = "palance.li.hello.HelloAndroid";

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        Log.i(LOG_TAG, "OnCreate OK.");
    }
}
```
## 资源文件layout/main.xml
``` xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
              android:orientation="vertical"
              android:layout_width="fill_parent"
              android:layout_height="fill_parent"
              android:gravity="center">
  <TextView
      android:layout_width="wrap_content"
      android:layout_height="wrap_content"
      android:gravity="center"
      android:text="@string/hello_android" >
  </TextView><!-- 在界面中间增加一个TextView，显示内容定义在values/strings.xml -->
</LinearLayout>
```

## 资源文件values/strings.xml
``` xml
<?xml version="1.0" encoding="utf-8" ?>
<resources>
  <string name="app_name">HelloAndroid</string>
  <string name="hello_android">Hello Android</string>
</resources>
```

# Android源码下编译
把该文件夹放到<Android源码>/packages/experimental目录下，我写了一个脚本HelloAndroid/ln2android.sh，只要执行
```
$ sh ln2android.sh <android-dir>
```
即可在<android-dir>/packages/experimental下生成指向HelloAndroid的软链接。执行命令：
``` bash
$ cd <android-dir>
$ source build/envsetup.sh
$ lunch aosp_arm_eng
$ mmm packages/experimental/HelloAndroid
```
即可生成apk文件：
`<android-dir>/out/debug/target/product/generic/system/app/HelloAndroid/HelloAndroid.apk`。
# 在源码编译的模拟器中运行
如果带着`HelloAndroid`的代码编译Android源码，生成的模拟器镜像文件中，`HelloAndroid`就是随系统安装的应用程序。如果以后修改了该程序，为了不重新编译Android源码，只需要执行：
``` bash
$ make snod
```
即可重新生成系统镜像。

但搞成系统自带应用并不便于调试，因为系统自带应用不能卸载，以后修改了代码，要重新调试就只能重新生成系统镜像。
可以在编译模拟器系统镜像的时候，不要把HelloAndroid放到`/packages/experimental`下，等模拟器启动后再单独编译`HelloAndroid`。编译完成后先查询模拟器中已安装的应用程序：
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
