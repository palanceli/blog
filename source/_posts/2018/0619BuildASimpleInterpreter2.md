---
layout: post
title: 编写编译器和解释器二
date: 2018-06-19 14:00:00 +0800
categories: 编译器
tags: 随笔
toc: true
comments: true
---

<!-- more -->
# 将语法解析和解释执行分离
在Part7之前，语法解析和解释执行一直是合在一起的。这种解释其被称为**语法导向解释器**，这种解释器对源码进行一次遍历，适用于比较基本的语言处理程序。Part7开始讲两部分分离开，构建出源码的**中间表示形式Intermediate representation (IR)**，以应对更复杂的b编程语言。语法解析器负责构建IR，解释器则负责执行IR。