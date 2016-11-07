---
title: macOS 下NDK的安装
date:   2016-08-12 10:28:49 +0800
categories: Android
tags: Android开发环境
toc: true
comments: true
---
本来是个很初级的操作步骤，可是在macOS 10.11.6下安装NDK的时候遇到了
`bad interpreter: Operation not permitted`
的问题，有必要记录下解决过程，以免再踩坑。
<!-- more -->
# 下载
从[NDK Downloads](https://developer.android.com/ndk/downloads/index.html)下载Package文件，也可以去国内的网站[AndroidDevTools](http://www.androiddevtools.cn/)下载。

# 解压
稍老一点的版本解开zip后是个`.bin`文件，需要先给`.bin`文件添加`x`属性再执行，如下：
`ndk$ chmod a+x android-ndk-r10c-darwin-x86_64.bin`
`ndk$ ./android-ndk-r10c-darwin-x86_64.bin`
执行`.bin`文件会把最终的文件解压出来。最新版NDK解开zip后就是最终文件，我放在了
`~/Desktop/android-ndk-r12b`。

# 修改属性
按照官方文档说明，解开最终文件后就可以直接使用。
可是在macOS下执行`ndk-build`时会提示：
`... /bin/sh: bad interpreter: Operation not permitted`
这是因为下载的文件会被macOS附上属性`com.apple.quarantine`，该属性用于用户首次执行下载文件的时候会弹出提示，问用户是否确认，以免染毒。在命令行下执行的时候弹不出提示，直接就禁止了，所以会出现上面的问题。

知道原因，解决起来就比较容易了，删除所有文件的`com.apple.quarantine`属性即可：
`sudo xattr -r -d com.apple.quarantine ~/Desktop/android-ndk-r12b`

# 验证
下载NDK Sample文件，验证NDK是否可以正常使用。在[NDK Samples Overview](https://developer.android.com/ndk/samples/index.html)可以找到[NDK Samples](https://github.com/googlesamples/android-ndk)和[Vulkan Samples](https://github.com/LunarG/VulkanSamples)，随便下载一个project，执行如下：
```
$ cd samples/hello-jni
$ ~/Desktop/android-ndk-r12b/ndk-build
Android NDK: WARNING: APP_PLATFORM android-24 is larger than android:minSdkVersion 3 in ./AndroidManifest.xml
[arm64-v8a] Gdbserver      : [aarch64-linux-android-4.9] libs/arm64-v8a/gdbserver
[arm64-v8a] Gdbsetup       : libs/arm64-v8a/gdb.setup
[x86_64] Gdbserver      : [x86_64-4.9] libs/x86_64/gdbserver
[x86_64] Gdbsetup       : libs/x86_64/gdb.setup
[mips64] Gdbserver      : [mips64el-linux-android-4.9] libs/mips64/gdbserver
[mips64] Gdbsetup       : libs/mips64/gdb.setup
[armeabi-v7a] Gdbserver      : [arm-linux-androideabi-4.9] libs/armeabi-v7a/gdbserver
[armeabi-v7a] Gdbsetup       : libs/armeabi-v7a/gdb.setup
[armeabi] Gdbserver      : [arm-linux-androideabi-4.9] libs/armeabi/gdbserver
[armeabi] Gdbsetup       : libs/armeabi/gdb.setup
[x86] Gdbserver      : [x86-4.9] libs/x86/gdbserver
[x86] Gdbsetup       : libs/x86/gdb.setup
[mips] Gdbserver      : [mipsel-linux-android-4.9] libs/mips/gdbserver
[mips] Gdbsetup       : libs/mips/gdb.setup
[arm64-v8a] Install        : libhello-jni.so => libs/arm64-v8a/libhello-jni.so
[x86_64] Install        : libhello-jni.so => libs/x86_64/libhello-jni.so
[mips64] Install        : libhello-jni.so => libs/mips64/libhello-jni.so
[armeabi-v7a] Install        : libhello-jni.so => libs/armeabi-v7a/libhello-jni.so
[armeabi] Install        : libhello-jni.so => libs/armeabi/libhello-jni.so
[x86] Install        : libhello-jni.so => libs/x86/libhello-jni.so
[mips] Install        : libhello-jni.so => libs/mips/libhello-jni.so
```
说明OK了！

# 设置环境变量
我把ndk文件放在`~/Document/android/android-ndk-r12b`下，并在文件`~/.bash_profile`中添加如下两行：
`export NDK_ROOT=/Users/palance/Documents/android/android-ndk-r12b`
`export PATH=$PATH:$NDK_ROOT`
让环境变量立刻生效：
`$ source ~/.bash_profile`
接下来就可以直接使用`ndk-build`了。