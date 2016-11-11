---
layout: post
title: Android + Gradle
date: 2016-11-10 00:23:58 +0800
categories: Android
tags: Android开发环境
toc: true
comments: true
---
在命令行下
``` bash
$ android create project \
  --activity MainActivity \
  --target 4 \
  --package palance.li.hello \
  --path HelloAndroid \
  -g \             # 使用gradle 模板
  -v 0.11.+        # Gradle Android 插件的版本号
```
创建一个带有gradle脚本的Android工程。<!-- more -->文件结构如下：
```
HelloAndroid
├── build.gradle
├── gradle
│   └── wrapper # 运行时，发现系统没有对应版本的gradle，会通过gradle-wrapper.jar下载gradle-wrapper.properties中指定的gradle版本
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── gradlew     # 它和.bat支持多平台的gradle运行命令，通过gradlew，可以执行gradle构建任务
├── gradlew.bat
├── local.properties
└── src
    ├── androidTest/java/palance/li/hello   # 测试源文件
    │   └── MainActivityTest.java
    └── main                                # 工程源文件
        ├── AndroidManifest.xml
        ├── java/palance/li/hello
        │   └── MainActivity.java
        └── res
            └── ...
```
# 解决编译错误
在`HelloAndroid`目录下执行`gradlew`将启动工程的编译，首次执行会花几分钟下载必要的文件。执行结果遇到了错误：
``` bash
Execution failed for task ':dexDebug'.
> com.android.ide.common.internal.LoggedErrorException: Failed to run command:
    /Users/palance/Library/Android/sdk/build-tools/25.0.0/dx --dex --num-threads=4 --output /Users/palance/Documents/dev/HelloAndroid/build/intermediates/dex/debug /Users/palance/Documents/dev/HelloAndroid/build/intermediates/classes/debug /Users/palance/Documents/dev/HelloAndroid/build/intermediates/dependency-cache/debug
  Error Code:
    1
  Output:
    Exception in thread "main" java.lang.UnsupportedClassVersionError: com/android/dx/command/Main : Unsupported major.minor version 52.0
      at java.lang.ClassLoader.defineClass1(Native Method)
      at java.lang.ClassLoader.defineClass(ClassLoader.java:800)
      ... ...
```
原因是Java版本号不匹配，Java的主版本号如下：
```
J2SE 8 = 52
J2SE 7 = 51
J2SE 6.0 = 50
J2SE 5.0 = 49
JDK 1.4 = 48
JDK 1.3 = 47
JDK 1.2 = 46
JDK 1.1 = 45
```
所以结合报错信息，应该是本地没有装Java 1.8。可是在创建project的时候也没有指定java版本号呀，猜测应该是跟target的版本号绑定的，我把target指定为2，重新创建工程：
```
$ android create project --activity MainActivity --target 2 --package palance.li.hello --path HelloAndroid -g -v 0.11.+
```
打开`build.gradle`文件：
```
...
android {
    compileSdkVersion 'android-23'
    buildToolsVersion '23.0.2' # 这里原本是25.0.0，我改成本地已安装的23系列的SDK Build-tools
    ...
}
...
```
再次执行` ./gradlew build`，终于看到`BUILD SUCCESSFUL`的执行结果。
# 编译、安装、卸载
``` bash
$ ./gradlew build           # 编译
$ ./gradlew installDebug    # 安装
$ ./gradlew uninstallDebug  # 卸载
```