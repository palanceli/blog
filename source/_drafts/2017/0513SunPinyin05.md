---
layout: post
title: SunPinyin（一）
date: 2017-05-13 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
SunPinyin代码树的本尊是不带词库的，按照说明，我把配套词库也放到fork的代码树上了，省得每次都单独下载了。<!-- more -->

# 制作词库
解压词库文件`sunpinyin/data/dict.utf8-20131214.tar.bz2` 和 `sunpinyin/data/lm_sc.3gm.arpa-20140820.tar.bz2`，放到临时目录，如：`sunpinyin/temp/`下。
执行：
``` bash
$ scons
$ scons install
```
把生成的文件`sunpinyin/doc/SLM-inst.mk`拷贝到`sunpinyin/temp/`下，并命名为`Makefile`。此时该临时目录下共有三个文件：`Makefile`、`dict.utf8`和`lm_sc.3gm.arpa`。执行：
``` bash
$ make
$ make install
```
如果提示错误：
``` bash
$ make install
install -d /usr/local/share/sunpinyin
install -Dm644 lm_sc.t3g pydict_sc.bin /usr/local/share/sunpinyin
install: illegal option -- D
```
可以把Makefile中最后一段由
``` makefile
slm3_dist: ${TSLM3_DIST_FILE} lexicon3
slm3_install: ${TSLM3_DIST_FILE} ${PYTRIE_FILE}
    install -d ${SYSTEM_DATA_DIR}
    install -Dm644 $^ ${SYSTEM_DATA_DIR}
```
改为
``` makefile
slm3_dist: ${TSLM3_DIST_FILE} lexicon3
slm3_install: ${TSLM3_DIST_FILE} ${PYTRIE_FILE}
    install -d ${SYSTEM_DATA_DIR}
    install $^ ${SYSTEM_DATA_DIR}
```
# 编译mac版本的输入法
打开`sunpinyin/wrapper/macos/SunPinyin.xcodeproj`，编译提示找不到文件`data/pydict_sc.bin`和`data/lm_sc.t3g`，这两个文件刚刚都生成到了临时文件夹，将他们从`sunpinyin/temp/`下拷贝到`sunpinyin/data/`下即可。

如果是为了调试输入法内核，不建议在mac下直接跑这个工程，因为mac的输入法框架对于调试支持得很不好，调试起来很不方便。我在wrapper下面创建了一个`convertor`目录。