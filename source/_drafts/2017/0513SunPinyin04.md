---
layout: post
title: SunPinyin 代码导读（一）
date: 2017-05-13 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
转自[SunPinyin代码导读（一）](http://yongsun.me/2007/07/sunpinyin%E4%BB%A3%E7%A0%81%E5%AF%BC%E8%AF%BB%EF%BC%88%E4%B8%80%EF%BC%89)
<!-- more -->
首先clone输入法项目的代码： 
``` bash
$ git clone https://github.com/sunpinyin/sunpinyin.git sunpinyin
```
（但是其中并不包括ime/data目录下那些较大的数据文件，你可以到这里下载它们）

inputmethod/sunpinyin目录下是SunPinyin的代码，其中包括两部分：
slm目录下是统计语言模型的代码（slm: statistical language model），用来构建一个支持back-off（回退）的n-gram（n元语法）静态统计语言模型。
ime目录下是和输入法相关的接口（ime: input method engine）。

首先执行下面的步骤来编译各个工具：

$ ./autogen.sh --prefix=/usr
$ make

build：这个目录下保存编译好的各个工具（以及它们的object文件），例如ids2ngram、slmbuild等。通过查看这个目录下的Makefile.am，你可以了解如何一步一步地构建词库和统计语言模型的二进制文件。

$ export LC_ALL=zh_CN.UTF-8
因为语料库和词表都使用UTF-8的编码，因此在进行后续步骤之前，需要将当前的语言环境设置为任意一个UTF-8的locale。

$ make test_corpus (或real_corpus)
这一步在raw目录中，建立一个corpus.utf8的符号链接。你完全可以手工建立这个链接。

$ make trigram
这一步建立一个trigram语言模型。

首先使用mmseg（最大正向分词），根据词表，对语料库进行分词，并将词的ID序列输出到一个文件中（../swap/lm_sc.ids）。
然后使用ids2ngram，对所有3元组出现的次数进行统计，并输出到一个文件中。例如下面的句子：ABCEBCA。得到的3元序列包括：(<S> A B), (A B C), (B C E) ... ( B C A), (C A '。'), (A '。' </S>)。<S>和</S>分别表示句首和句尾。
使用slmbuild来构造一个back-off的trigram语言模型，但是未经裁剪。
使用slmprune对刚输出的trigram语言模型进行剪裁，使用的算法是基于熵的剪裁算法。
使用slmthread对剪裁后的语言模型进行线索化，加快back-off（回退）查找的速度。将最终的结果输出到../data/lm_sc.t3g。
$ make bs_trigram
这个目标和上面的类似，不同的是使用slmseg进行分词，它借助刚刚生成的基于最大正向分词得到的语言模型，对语料库进行重新分词。这样可以进一步提高语言模型的精确程度。

$ make lexicon
根据生成语言模型中的unigram数据，对词表进行处理，得到一个支持不完全拼音的词库文件。

代码的细节我们随后再详述。