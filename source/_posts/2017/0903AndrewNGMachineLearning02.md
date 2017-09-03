---
layout: post
title: Andrew NG Machine Learning视频学习笔记二
date: 2017-09-03 23:00:00 +0800
categories: Machine Learning
tags: Andrew NG Machine Learning
toc: true
comments: true
---
本节深入学习了多变量线性回归。
<!-- more -->
# 多变量线性回归
当引入多个变量，如房价的高低可能不只是取决于房屋大小，还取决于居室个数、年限等，这些都是变量，因此模型的特征为：(x<sub>1</sub>, x<sub>2</sub>, ..., x<sub>n</sub>)

常用标记
n 表示特征的数量
x<sup>(i)</sup> 第i个训练实例，也是特征矩阵中第i行
x<sub>j</sub><sup>(i)</sup> 第i个训练实例的第j个特征，即特征矩阵中第i行第j列

## 预测函数
预测多变量的函数可以表示为：h<sub>θ</sub>(x) = θ<sub>0</sub> + θ<sub>1</sub>x<sub>1</sub> + θ<sub>2</sub>x<sub>2</sub> + ... + θ<sub>n</sub>x<sub>n</sub>
为了简化公式，引入x<sub>0</sub> = 1，预测函数可以写作：
![](0903AndrewNGMachineLearning02/img01.png)

## 代价函数
根据代价函数的定义（误差的平方和），可得：
![](0903AndrewNGMachineLearning02/img02.png)

对预测函数求偏导：
![](0903AndrewNGMachineLearning02/img03.png)

对代价函数求偏导：
![](0903AndrewNGMachineLearning02/img04.png)

## 梯度下降
于是多变量的梯度下降算法为：
![](0903AndrewNGMachineLearning02/img05.png)

将①代入上式，得到多变量的梯度下降，在初始时可随机选择一组参数，按照：
![](0903AndrewNGMachineLearning02/img06.png)
迭代，直到高度差收敛。

## 多项式回归
多项式回归 如果预测模型和特征值不是一次关系，而是二次或三次关系，如
h<sub>θ</sub>(x) = θ<sub>0</sub> + θ<sub>1</sub>x<sub>1</sub> + θ<sub>2</sub>x<sub>2</sub><sup>2</sup> + θ<sub>3</sub>x<sub>3</sub><sup>3</sup>
这就把模型转成了线性回归模型。

## 正规方程
梯度下降是求解J最小值的一种方案。另一种方案是对J求θ的偏导，并令偏导为0，这样就得出了局部最小值，一步计算出代价最小的解。
令特征向量X、标记空间Y和参数向量θ分别为：
![](0903AndrewNGMachineLearning02/img07.png)
![](0903AndrewNGMachineLearning02/img08.png)
故：
▽<sub>θ</sub>J(θ) = ▽<sub>θ</sub>(1/2) × (Xθ - y)<sup>T</sup>(Xθ - y)
 = (1/2) × ▽<sub>θ</sub>(θ<sup>T</sup>X<sup>T</sup> - y<sup>T</sup>)(Xθ - y)
 = (1/2) × ▽<sub>θ</sub>(θ<sup>T</sup>X<sup>T</sup>Xθ - θ<sup>T</sup>X<sup>T</sup>y - y<sup>T</sup>Xθ - y<sup>T</sup>y)
θ<sup>T</sup>是1×n矩阵，X<sup>T</sup>是n×m矩阵，X是m×n矩阵，θ是n×1矩阵，故θ<sup>T</sup>X<sup>T</sup>Xθ是个实数，上式括号内的多项式最终也是实数。对于 ∀a∈R => tra = a
故上式
▽<sub>θ</sub>J(θ) = (1/2) × ▽<sub>θ</sub> tr(θ<sup>T</sup>X<sup>T</sup>Xθ - θ<sup>T</sup>X<sup>T</sup>y - y<sup>T</sup>Xθ + y<sup>T</sup>y)
 = (1/2) × ▽<sub>θ</sub> (tr(θ<sup>T</sup>X<sup>T</sup>Xθ) - tr(θ<sup>T</sup>X<sup>T</sup>y) - tr(y<sup>T</sup>Xθ) + tr(y<sup>T</sup>y))
 其中 tr(θ<sup>T</sup>X<sup>T</sup>y) = tr(θ<sup>T</sup>X<sup>T</sup>y)<sup>T</sup> = tr(y<sup>T</sup>(θ<sup>T</sup>X<sup>T</sup>)<sup>T</sup>) = tr(y<sup>T</sup>Xθ)
故上式
▽<sub>θ</sub>J(θ) = (1/2) × ▽<sub>θ</sub> ( tr(θ<sup>T</sup>X<sup>T</sup>Xθ) - 2tr(y<sup>T</sup>Xθ) + tr(y<sup>T</sup>y) )   **……①**

已知公式：▽<sub>A</sub>ABA<sup>T</sup>C = B<sup>T</sup>A<sup>T</sup>C<sup>T</sup> + BA<sup>T</sup>C
令A<sup>T</sup> = θ， B = B<sup>T</sup> = X<sup>T</sup>X， C = I， A = θ<sup>T</sup>，代入公式得：
▽<sub>θ</sub>tr(θ<sup>T</sup>X<sup>T</sup>XθI) = X<sup>T</sup>XθI + X<sup>T</sup>XθI = X<sup>T</sup>Xθ + X<sup>T</sup>Xθ = 2X<sup>T</sup>Xθ   **……②**

已知公式：▽<sub>A</sub>tr(AB) = B<sup>T</sup>
故，▽<sub>A</sub>tr(y<sup>T</sup>Xθ) = （y<sup>T</sup>X)<sup>T</sup> = X<sup>T</sup>y   **……③**

将②③代入①得：
▽<sub>θ</sub>J(θ) = (1/2) × (2X<sup>T</sup>Xθ - 2X<sup>T</sup>y) = X<sup>T</sup>Xθ - X<sup>T</sup>y
于是，求代价函数J<sub>θ</sub>值最小的参数集θ，只须：▽<sub>θ</sub>J(θ) = 0
即 X<sup>T</sup>Xθ = X<sup>T</sup>y  
=> θ = (X<sup>T</sup>X)<sup>-1</sup>X<sup>T</sup>y

通过正规方程，我们可以找到令误差最小的参数向量，相比于梯度下降法，正规方程不需要多次迭代，直接计算出局部最优解。

----

其实还有一个思路是：若希望预测函数拟合出Y，则令H<sub>θ</sub>(X) = Y， 而H<sub>θ</sub> = X × θ，故X × θ = Y即可求解θ。
显然可以通过X<sup>-1</sup>Xθ = X<sup>-1</sup>Y求解，但是仅当X是方阵时才存在逆矩阵，所以应先把θ的乘数变成方阵：X<sup>-1</sup>Xθ = X<sup>T</sup>Y => θ = (X<sup>T</sup>X)<sup>-1</sup>X<sup>T</sup>Y
这就得到与正规方程相同的结果。
可是(X<sup>T</sup>X)<sup>-1</sup>不一定存在啊？后面会介绍它不存在时的处理方法。

> 矩阵A可逆的充要条件是|A| ≠0

<br>
> 最小二乘法（又称最小平方法）通过最小化误差的平方和寻找数据的最佳匹配，本章中代价函数就利用了最小二乘法。