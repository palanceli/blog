---
layout: post
title: DeepLearning.ai笔记（五）
date: 2018-03-28 10:00:00 +0800
categories: 机器学习
tags: 随笔
toc: true
comments: true
mathjax: true
---
本节主要从模型的心连方法上给出一些可优化的点，包括可以将数据分而治之的Mini-Batch、防止梯度下降方向变化率过大的指数加权平均以及RMSprop和Adam优化算法。

<!-- more -->
# 2.1 Mini-Batch梯度下降法
当样本量巨大时，有必要将海量样本拆分成更小的子集。因为海量样本的向量化会收到内存限制，拆分让分布式并行成为可能。  
例如，当有5,000,000样本时，可令1000个样本为一组，拆分成5000个子集：


> 本节作业可参见[https://github.com/palanceli/MachineLearningSample/blob/master/DeepLearningAIHomeWorks/mywork.py](https://github.com/palanceli/MachineLearningSample/blob/master/DeepLearningAIHomeWorks/mywork.py)`class Coding2_2`。