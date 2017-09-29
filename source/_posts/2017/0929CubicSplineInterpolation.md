---
layout: post
title: 三次样条插值（Cubic Spline Interpolation）
date: 2017-09-29 23:30:00 +0800
categories: 技术随笔
tags: 技术随笔
toc: true
comments: true
---
常见的一维插值方法有：
- 多项式插值（polynormal interpolation）
- 分段线性插值（piecewise linear interpolation）
- 3次样条插值（cubic spline interpolation）

本文介绍3次样条插值的原理。
<!-- more -->
# 定义
有节点序列：(x<sub>0</sub>, y<sub>0</sub>),(x<sub>1</sub>, y<sub>1</sub>),……(x<sub>n</sub>, y<sub>n</sub>)，其中a=x<sub>0</sub> < x<sub>1</sub> < ... < x<sub>n</sub> = b
在每个分段区间[x<sub>i</sub>, x<sub>i+1</sub>]，样条曲线S<sub>i</sub>(x)都是一个三次多项式；S(x)、S'(x)、S"(x)在区间[a, b]上是连续的，即S(x)曲线是光滑的。
S<sub>i</sub>可以写作：
S<sub>i</sub>(x) = a<sub>i</sub> + b<sub>i</sub>(x - x<sub>i</sub>) + c<sub>i</sub>(x - x<sub>i</sub>)<super>2</super> + d<sub>i</sub>(x - x<sub>i</sub>)<super>3</super>  其中i = 0, 1, ..., n-1
a<sub>i</sub>、b<sub>i</sub>、c<sub>i</sub>、d<sub>i</sub>是未知系数，接下来需要求解它们。

# 求解
每一段样条曲线的节点与已知序列重合，故：
S<sub>i</sub>(x<sub>i</sub>) = y<sub>i</sub>
S<sub>i</sub>(x<sub>i+1</sub>) = y<sub>i+1</sub>  　　　其中i=0, 1, ..., n-1
相邻的两段样条曲线在接缝处是平滑的，故：
S'<sub>i</sub>(x<sub>i+1</sub>) = S'<sub>i+1</sub>(x<sub>i+1</sub>)
S"<sub>i</sub>(x<sub>i+1</sub>) = S"<sub>i+1</sub>(x<sub>i+1</sub>) 　　　其中i=0, 1, ..., n-2
样条曲线方程及微分方程：
S<sub>i</sub>(x) = a<sub>i</sub> + b<sub>i</sub>(x - x<sub>i</sub>) + c<sub>i</sub>(x - x<sub>i</sub>)<sup>2</sup> + d<sub>i</sub>(x - x<sub>i</sub>)<sup>3</sup>  　　　…①
S'<sub>i</sub>(x) = b<sub>i</sub> + 2c<sub>i</sub>(x - x<sub>i</sub>) + 3d<sub>i</sub>(x - x<sub>i</sub>)<sup>2</sup>  　　　　　　　…②
S"<sub>i</sub>(x) = 2c<sub>i</sub> + 6d<sub>i</sub>(x - x<sub>i</sub>)  　　　　　　　　　　　　…③

将S<sub>i</sub>(x<sub>i</sub>) = y<sub>i</sub>代入①得：
a<sub>i</sub> = y<sub>i</sub>　　　　　　　　　　　　　　　　　　　　…⑥

将S<sub>i</sub>(x<sub>i+1</sub>) = y<sub>i+1</sub>代入①得：
a<sub>i</sub> + b<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>) + c<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>)<sup>2</sup> + d<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>)<sup>3</sup> = y<sub>i+1</sub>
令h<sub>i</sub> = x<sub>i+1</sub> - x<sub>i</sub>为步长，代入上式得：
a<sub>i</sub> + b<sub>i</sub>h<sub>i</sub> + c<sub>i</sub>h<sub>i</sub><sup>2</sup> + d<sub>i</sub>h<sub>i</sub><sup>3</sup> = y<sub>i+1</sub>　　　　　　　　　　…⑦

将S'<sub>i</sub>(x<sub>i+1</sub>) = S'<sub>i+1</sub>(x<sub>i+1</sub>)代入②得：
b<sub>i</sub> - b<sub>i+1</sub> + 2c<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>) + 3d<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>)<sup>2</sup> = 0
即：b<sub>i</sub> - b<sub>i+1</sub> + 2c<sub>i</sub>h<sub>i</sub> + 3d<sub>i</sub>h<sub>i</sub><sup>2</sup> = 0　　　　　　　　　…⑧

将S"<sub>i</sub>(x<sub>i+1</sub>) = S"<sub>i+1</sub>(x<sub>i+1</sub>)代入③得：
2(c<sub>i</sub> - c<sub>i+1</sub>) + 6d<sub>i</sub>(x<sub>i+1</sub> - x<sub>i</sub>) = 0
=> 2(c<sub>i</sub> - c<sub>i+1</sub>) + 6d<sub>i</sub>h<sub>i</sub> = 0
=> d<sub>i</sub> = 2(c<sub>i</sub> - c<sub>i+1</sub>)/6h<sub>i</sub>
令 m<sub>i</sub> = S"<sub>i</sub>(x<sub>i</sub>) = 2c<sub>i</sub>
=> c<sub>i</sub> = m<sub>i</sub> / 2　　　　　　　　　　　　　　　　　　…④
=> d<sub>i</sub> = (m<sub>i+1</sub> - m<sub>i</sub>)/6h<sub>i</sub>　　　　　　　　　　　　　　…⑤

将④⑤⑥代入⑦：