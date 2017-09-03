---
layout: post
title: Andrew NG Machine Learning视频学习笔记三
date: 2017-09-04 23:00:00 +0800
categories: Machine Learning
tags: Andrew NG Machine Learning
toc: true
comments: true
---
本节和视频教程没什么关系，学完了线性回归，自己想两个题目做做吧。
<!-- more -->
题目是这样的，假设用户词库是由中文词条或拼音串组成，词条个数和词库大小呈线性关系。单变量线性回归练习中，词库里只有中文词条，输入变量就是词条个数，输出变量是词库大小。两个变量的线性回归练习中，词库里包含中文词条和拼音串，二者个数不一定相等，输出变量是词库大小。词库来自于libGooglePinyin中的语料。接下来我们就生成训练集，训练模型，并用模型验证测试样本。

代码我传到了[线性回归练习](https://github.com/palanceli/MachineLearningSample)

# 单变量线性回归练习

# 两个变量的线性回归练习