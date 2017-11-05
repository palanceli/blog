---
layout: post
title: 《机器学习》西瓜书笔记一
date: 2017-10-29 20:00:00 +0800
categories: 机器学习
tags: 西瓜书笔记
toc: true
comments: true
---
![](1029XiGuaShu01/img01.png)
本章主要介绍基本术语，这些术语成为后面描述问题的基础。

本章要点：
- 
<!-- more -->

# 基本术语和概念
假设手机一批西瓜的数据：
(色泽=青绿; 根蒂=蜷缩; 敲声=浊响)
(色泽=乌黑; 根蒂=稍蜷; 敲声=沉闷)
(色泽=浅白; 根蒂=硬挺; 敲声=清脆)
……

以上这组记录的集合称为一个<span style="border-bottom:1px dashed red;">数据集（data set）</span>。

每条记录是关于一个事件或对象的描述，称为一个<span style="border-bottom:1px dashed red;">示例（instance）或样本（sample）</span>。

反映事件或对象在某方面的表现或性质，例如“色泽”、“根蒂”、“敲声”称为<span style="border-bottom:1px dashed red;">属性（attribute）或特征（feature）</span>。属性的取值，如“青绿”、“乌黑”称为<span style="border-bottom:1px dashed red;">属性值（attribute value）</span>，属性张成的空间称为<span style="border-bottom:1px dashed red;">属性空间（attribute space）或样本空间（sample space）或输入空间（input space）</span>。

把“色泽”、“根蒂”、“敲声”作为三个坐标轴，它们张成一个用于描述西瓜的三维空间，每个西瓜都可以在这个空间中找到自己的坐标，由于空间中每个点对应一个坐标向量，因此把一个示例称为一个<span style="border-bottom:1px dashed red;">特征向量（feature vector</span>）。

令D={x<sub>1</sub>, x<sub>2</sub>, ...,  x<sub>m</sub>}表示包含m个样本的数据集，每个样本由d个属性描述，则每个样本x<sub>i</sub>=(x<sub>i1</sub>; x<sub>i2</sub>;...;x<sub>id</sub>)是d维样本空间X中的一个向量，x<sub>i</sub>∈X，其中x<sub>ij</sub>是x<sub>i</sub>在第j个属性上的取值，d称为样本x<sub>i</sub>的<span style="border-bottom:1px dashed red;">维数（dimensionality）</span>。

从数据中学的模型的过程称为<span style="border-bottom:1px dashed red;">学习（learning）或训练（training）</span>。
训练过程中使用的数据称为<span style="border-bottom:1px dashed red;">训练数据（training data）</span>，其中每个样本称为<span style="border-bottom:1px dashed red;">训练样本（training sample）</span>，训练样本组成的集合称为<span style="border-bottom:1px dashed red;">训练集（training set）</span>，学得模型对应了关于数据的某种潜在规律称为<span style="border-bottom:1px dashed red;">假设（hypothesis）</span>，这种潜在规律自身称为<span style="border-bottom:1px dashed red;">真相或事实（ground-truth)</span>。

如果希望学得一个能判断没剖开的是不是“好瓜”的模型，仅有前面的样本数据是不够的，还需要获得训练样本的“结果”信息，该结果信息称为<span style="border-bottom:1px dashed red;">标记（label）</span>，有了标记信息的样本称为<span style="border-bottom:1px dashed red;">样例（example）</span>。用(x<sub>i</sub>, y<sub>i</sub>)表示第i个样例，其中y<sub>i</sub>∈Y是样本x<sub>i</sub>的标记，Y是所有标记的集合，称为<span style="border-bottom:1px dashed red;">标记空间（label space）或输出空间</span>。

如果待预测的是离散值，例如“好瓜”、“坏瓜”，这类学习任务称为<span style="border-bottom:1px dashed red;">分类（classification）</span>，如果待预测的是连续值，例如西瓜成熟度0.95、037，这类学习问题称为<span style="border-bottom:1px dashed red;">回归（regression）</span>

学的模型后，使用其进行预测的过程称为<span style="border-bottom:1px dashed red;">测试（testing）</span>，被预测的样本称为<span style="border-bottom:1px dashed red;">测试样本（testing Sample）</span>

将训练集中的西瓜分成若干组，每组称为一个簇（cluster），这些自动形成的簇可能对应一些潜在的概念划分，这样的学习过程称为<span style="border-bottom:1px dashed red;">聚类（clustering）</span>，在聚类学习中，这些潜在的概念是事先不知道的，而且学习过程中使用的训练样本通常没有标记信息。

根据训练数据是否有标记信息，学习任务可划分为两大类：<span style="border-bottom:1px dashed red;">监督学习（supervised learning）和无监督学习（unsupervised learning）</span>，分类和回归是前者的代表，聚类是后者的代表。

机器学习的目标是视学得的模型能很好的适用于新样本，而不是仅仅在训练样本上工作的很好。学得模型适用于新样本的能力称为<span style="border-bottom:1px dashed red;">泛化（generalization）能力</span>

假设样本空间中全体样本服从一个未知<span style="border-bottom:1px dashed red;">分布（distribution）D</span>，我们获得的每个样本都是独立地从这个分布上采样获得的，即<span style="border-bottom:1px dashed red;">独立同分布（independent and identically distributed，简称i.i.d）</span>

# 归纳偏好
机器学习算法在学习过程中对某种类型假设的偏好，称为<span style="border-bottom:1px dashed red;">归纳偏好（inductive bias）或简称偏好</span>。

归纳偏好有点类似于排序算法中的“稳定性”的概念。一个有效的机器学习算法必有其归纳偏好，否则它将被假设空间中看似在训练集上“等效”的假设所迷惑，而无法产生确定的学习结果。即学得的模型对于同一个样本时而告诉我们它是好的，时而告诉我们它是不好的，这样的学习结果是没有意义的。

本节祭出牛逼闪闪的“没有免费的午餐”定理（No Free Lunch Theorem，简称NFL定理）[Wolpert, 1996; Wolpert and Macready, 1995]，表明无论学习算法𝞷<sub>a</sub>多聪明多牛逼，学习算法𝞷<sub>b</sub>多笨拙多傻逼，它们的期望性能是相同的。
对于给定的训练集，可能学习出模型A和模型B：
![](1029XiGuaShu01/img02.png)
当测试样本为（a）时，A就优于B，当测试样本为（b）时，B就优于A：
![](1029XiGuaShu01/img03.png)
NFL定理有一个重要前提是：所有“问题”出现的机会相同，而实际情况常常不是这样，我们只关注自己正在试图解决的问题。
NFL所表达的含义是：脱离具体问题，空泛谈论“什么学习算法更好”毫无意义，因为如果考虑所有潜在问题，所有学习算法都一样好。要谈论算法的相对优劣，必须针对具体的学习问题。这个工作还是依赖“人”对业务的理解程度，所以在“人工智能”的领域，更需要产品思维导向，渗透和理解业务，才能选取更贴切的归纳偏好。这是我个人的理解。