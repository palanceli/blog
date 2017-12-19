---
layout: post
title: git瘦身
date: 2017-12-18 20:00:00 +0800
categories: git
tags: git
toc: true
comments: true
---
最近在几台机器上频繁clone [dlib-android](https://github.com/palanceli/dlib-android)和[dlib-android-app](https://github.com/palanceli/dlib-android-app)，这两个库都巨大，其中因为有一个99M的人脸识别模型文件，我自己训练一个16.6M的小模型，替换后发现两个git目录尺寸并没有减小。原因是.git这个目录里记录了所有历史数据，本文记录该目录的瘦身过程。

<!-- more -->

先说一下造成git臃肿的原因：历史上可能误提交过一些大文件，或者一批本不该提交的文件，这会导致历史记录被永久保存到.git里，这部分历史记录没有什么意义。这种情况下，通过删除这些垃圾记录是有必要的。本文主要也是针对这种情况，因为我发现作者曾经把大量的.a、.so等本来可通过编译生成的文件也提交git了。

# 瘦身方法
网上有不少文章介绍git的瘦身方法，但在我这里都不生效，或者生效了也无法push到远端的仓库。经过多次试验，发现本地瘦身的方法没什么问题：

## 查找删除大索引文件
``` bash
# 查找大文件
$ git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -5 | awk '{print$1}')"

e759ec9c69f570834b6b078614261744a6f035f4 data/lena.bmp
...
f06aa74a57ce3a4129340cd4407ef3c0558e3193 <some-big-file-path>

# 删除指定的文件及相关记录
$ git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch <some-big-file-path>' --prune-empty --tag-name-filter cat -- --all
```
使用命令`git rev-list --objects --all`列出所有曾经提交过的文件及hash值，这个命令在此后还会用到。如果曾经提交过少数几个大文件，用这种方法可以很快瘦身。

## 删除一批碎文件
还有一种情况是：提交过一批碎文件，再用这种方法就很麻烦了，可以先只用`git rev-list --objects --all`命令找到这类文件，再通过通配符删除这些文件：
``` bash
# 列出曾经提交过的所有文件
$ git rev-list --objects --all
ea026732036637ce181e487a56f7ff9ad055d56a jni/tests
a7a11e6eb9d4d15de46c91a30bcbbb5f290bac55 jni/tests/Android.mk
6022a20f24bf1bbd6a9fc993c35475081f4de0e3 jni/tests/README.md
a6f141e3626348c81f714acb6f83459d105bb584 jni/tests/TestSelectiveSearch.cpp
d49af47035339a1bcb19ccaa7619d613fbf84a17 jni/tests/face_landmark_detection_ex.cpp
...

# 假设jni/tests/目录是本不该提交的，可以删除该目录
$ git filter-branch --force --index-filter 'git rm -rf --cached --ignore-unmatch jni/tests/*' --prune-empty --tag-name-filter cat -- --all
```

需要指出本文瘦身只适用于垃圾类历史记录，如果是有意义的提交记录，最好保留。理论上来说，它们也不应该太大。

## 压缩并提交
需要执行reflog和gc压缩才能看到瘦身后的效果：
``` bash
$ git reflog expire --expire=now --all && git gc --prune=now --aggressive
$ git push --mirror
```
最后一步提交一定要带上--mirror参数，否则.git目录的瘦身始终不会被提交到远端服务器，这是大部分网上的文章没提到的。我在这一步上折腾的也是最多的，最后还是看了BFG工具的例子，才受到启发。

# 参考
[寻找并删除Git记录中的大文件](http://harttle.land/2016/03/22/purge-large-files-in-gitrepo.html)
[BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
[使用BFG移除git库中的大文件或污点提交](https://www.awaimai.com/2202.html)