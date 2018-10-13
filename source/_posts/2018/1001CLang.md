---
layout: post
title: CLang
date: 2018-10-01 14:00:00 +0800
categories: 技术随笔
tags: 随笔
toc: true
comments: true
---

本文想利用clang生成的AST，遍历其每个节点并追溯生成IR的过程，企图生成自己的指令体系，并用一个简版的VM来执行，最终达到热更新的目的。

<!-- more -->

参考[《How to write RecursiveASTVisitor based ASTFrontendActions.》](http://clang.llvm.org/docs/RAVFrontendAction.html)，这篇文章演示了如何遍历AST。在阅读代码之前有必要先了解RecursiveASTVisitor/FrontEndAction/ASTConsumer的概念以及相互关系。

# Visitor/Action/Consumer结构

## RecursiveASTVisitor
查找AST中的节点，既可以遍历AST，也可以使用Clang封装好的算法——RecursiveASTVisitor

<font color=red>待续...</font>