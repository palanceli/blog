---
layout: post
title: git submodules
date: 2018-06-22 14:00:00 +0800
categories: git
tags: 随笔
toc: true
comments: true
---
自己的版本库中常常引用一些开源的基础模块，比如googletest、glog，比较笨的做法是clone一份代码，直接再提交到自己的版本库中。更推荐的做法是使用git submodules。

<!-- more -->
当然，通常不会引用这些基础模块的最新版本，一有稳定性的考虑，二也有兼容性的考虑，所以再添加submodule的时候需要指定分支或Tag。以我的[libgooglepinyin](https://github.com/palanceli/libgooglepinyin.git)为例。  

- 在项目的根目录下添加submodule，它会在根目录下创建文件`.gitmodules`。
```
$ git submodule add https://github.com/google/googletest.git googletest
```
- 将模块检出到指定版本：
```
$ cd googletest
$ git checkout release-1.8.0
```
- 提交
```
$ cd ..
$ git commit -m"commit changes"
$ git push
```

下次再执行`git clone`主项目之后，再更新module：
```
$ git submodule update --init --recursive
```
将直接将指定tag的submodule更新下来。不过我没找到这个tag是记录在本地哪个配置文件中。  
在新的目录下执行clone验证一下：  
```
$ git clone https://github.com/palanceli/libgooglepinyin.git
$ cd libgooglepinyin/googletest
$ git describe --tags
release-1.8.0
```

删除某个submodule，需要1、在`.gitmodules`中删除相关字段；2、在`.git/config`中删除相关字段；3、删除模块的文件夹。