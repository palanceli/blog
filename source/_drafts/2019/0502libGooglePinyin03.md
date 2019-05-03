---
layout: post
title: libGooglePinyin（一）编译
date: 2019-05-02 23:00:00 +0800
categories: 技术
tags: 输入法
toc: true
comments: true
---
在macOS上编译起来。
<!-- more -->
额外引入了gtest、glog和gflag：
``` shell
$ git submodule update --init --recursive

$ git submodule add https://github.com/google/googletest.git modules/googletest
$ cd modules/googletest
$ git checkout release-1.8.0

$ cd libgooglepinyin
$ git submodule add https://github.com/google/glog.git modules/glog
$ cd modules/glog
$ git checkout v0.3.5

$ cd libgooglepinyin
$ git submodule add https://github.com/gflags/gflags.git modules/gflags
$ cd modules/gflags
$ git checkout v2.2.1
```
以上是三个模块对应的版本号。我尝试在一台机器提交后，在另一台机上貌似不能更新下来。我希望达到的效果是一条命令之后，直接可以cmake - 编译。❗️这个问题留作以后再查❗️

一旦本机有了这三个模块的代码树，以上工作就不用再操作了。接下来是编译和安装，我的系统是macOS，当系统升级后，macOS SDK版本发生变化，这些模块需要重新编译：
``` shell
cd modules/googletest
mkdir _build && cd _build && cmake .. && make && make install

cd modules/gflags
mkdir _build && cd _build && cmake .. && make && make install

cd modules/glog
mkdir _build && cd _build && cmake .. && make && make install
```