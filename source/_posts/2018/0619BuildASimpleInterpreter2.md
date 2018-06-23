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
在Part7之前，语法解析和解释执行一直是合在一起的。这种解释其被称为**语法导向解释器**，这种解释器对源码只进行一次遍历，就直接得出结果，它适用于比较基本的语言处理程序。Part7开始将两部分分离开，第一步先构建出源码的**中间表示形式Intermediate representation (IR)**，第二步再对照IR执行。这方便应对更复杂的编程语言，语法解析器负责构建IR，解释器则负责执行IR。

通过IR对源代码构建起的数据结构称为**抽象语法树abstract-syntax tree(AST)**，AST的每个非叶子节点代表一个运算符，叶子节点代表一个操作数。优先级越高的运算，放在AST中越靠近叶子的层级。下图是一个AST的示例：
![](0619BuildASimpleInterpreter2/img01.png)

