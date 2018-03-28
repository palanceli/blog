---
layout: post
title: numpy使用
date: 2017-09-29 23:00:00 +0800
categories: 机器学习
tags: 基础工具
toc: true
comments: true
---
最近频繁接触numpy，不管是Machine Learning还是opencv，都要用到它。这里写一篇简单的使用手册，以便查阅。
<!-- more -->
# 生成数列，简单变形
``` python
x = numpy.linspace(1, 8, 8) # ① 生成等差数列
print(x)

print(x.reshape((2, 4)))    # ② 变形成 2*4 的矩阵

print(x.reshape((2, 2, 2))) # ③ 变形成 2*2*2 的矩阵
```
输出：
```
[ 1.  2.  3.  4.  5.  6.  7.  8.]   ①

[[ 1.  2.  3.  4.]                  ②
 [ 5.  6.  7.  8.]]

[[[ 1.  2.]                         ③
  [ 3.  4.]]

 [[ 5.  6.]
  [ 7.  8.]]]
```
# 变形前后的数组共享内存
变形后的数组和原数组共享内存，因此修改变形的数组，原数组也会变：
``` python
x = numpy.linspace(1, 8, 8)
y = x.reshape(2, 4)
y[1, 1] = 10
print(y)            # ① y
print(x)            # ② x
```
输出：
```
[[  1.   2.   3.   4.]                      ① y
 [  5.  10.   7.   8.]]
 
[  1.   2.   3.   4.   5.  10.   7.   8.]   ② x
```
# 参数为-1的变形
变形的参数为-1，会根据数组长度和剩余维度推断出来：
``` python
x = numpy.linspace(1, 8, 8)
print(x.reshape(-1, 2, 2))
```
输出：
```
[[[  1.   2.]
  [  3.   4.]]

 [[  5.  10.]
  [  7.   8.]]]
```
# 矩阵初始化
``` python
x = numpy.zeros((2, 3, 4), numpy.uint8)	# ① 初始化 2*3*4 全0矩阵
print(x)

x = numpy.ones((2, 3, 4), numpy.uint8)	# ② 初始化 2*3*4 全1矩阵
print(x)
```
输出：
```
[[[0 0 0 0]                              ①
  [0 0 0 0]
  [0 0 0 0]]

 [[0 0 0 0]
  [0 0 0 0]
  [0 0 0 0]]]

[[[1 1 1 1]                              ②
  [1 1 1 1]
  [1 1 1 1]]

 [[1 1 1 1]
  [1 1 1 1]
  [1 1 1 1]]]
```
如下使用array、linspace和zeros三种写法得出的数据结构是相同的：
``` python
  x = numpy.array([[1, 2], [3, 4], [5, 6]], numpy.uint8)        # ①
  y = numpy.linspace(1, 6, 6, dtype=numpy.uint8).reshape(3, 2)  # ②
  z = numpy.zeros((3, 2), numpy.uint8)                          # ③
  z[:, 0] = [1, 3, 5]
  z[:, 1] = [2, 4, 6]

  print(x)
  print(y)
  print(z)
```
输出：
```
[[1 2]  ① x
 [3 4]
 [5 6]]
[[1 2]  ② y
 [3 4]
 [5 6]]
[[1 2]  ③ z
 [3 4]
 [5 6]]
```

# 矩阵赋值
``` python
x = numpy.ones((2, 3, 4), numpy.uint8)
x[:] = 2        # ① 全部赋值为2
print(x)

x = numpy.ones((2, 3, 4), numpy.uint8)
x[1, :, :] = 4  # ② 修改第1维（0 based）的所有数据为4
print(x)

x = numpy.ones((2, 3, 4), numpy.uint8)
x[:, 1, :] = 4  # ③ 修改第2维为1（0 based）的所有数据为4
print(x)

x = numpy.ones((2, 3, 4), numpy.uint8)
x[:, :, 1] = 4  # ④ 修改第3维为1（0 based）的所有数据为4
print(x)
```
输出：
```
[[[2 2 2 2]     ① 全部赋值为2
  [2 2 2 2]
  [2 2 2 2]]

 [[2 2 2 2]
  [2 2 2 2]
  [2 2 2 2]]]

[[[1 1 1 1]     ② 修改第1维为1（0 based）的所有数据为4
  [1 1 1 1]
  [1 1 1 1]]

 [[4 4 4 4]
  [4 4 4 4]
  [4 4 4 4]]]

[[[1 1 1 1]     ③ 修改第2维为1（0 based）的所有数据为4
  [4 4 4 4]
  [1 1 1 1]]

 [[1 1 1 1]
  [4 4 4 4]
  [1 1 1 1]]]

[[[1 4 1 1]     ④ 修改第3维为1（0 based）的所有数据为4
  [1 4 1 1]
  [1 4 1 1]]

 [[1 4 1 1]
  [1 4 1 1]
  [1 4 1 1]]]
```
## 修改某列为一个序列
``` python
x = numpy.ones((2, 3, 4), numpy.uint8)
x[:, :, 1] = [2, 3, 4]
print(x)
print('\n')
```
输出：
```
[[[1 2 1 1]
  [1 3 1 1]
  [1 4 1 1]]

 [[1 2 1 1]
  [1 3 1 1]
  [1 4 1 1]]]
```
x相当于由2个3*4的矩阵组成，此处给每个矩阵的第1列赋值为[2, 3, 4]。左值元素的个数必须等于矩阵的行数3，否则会出错。

# 参考
[官网手册](https://docs.scipy.org/doc/)
[NumPy v1.11手册中文版](http://python.usyiyi.cn/translate/NumPy_v111/index.html)
本文涉及的代码放在[numpySamples.py](https://github.com/palanceli/MachineLearningSample/blob/master/UtilSamples/numpySamples.py)

## 安装
如果是python2
$ pip install scipy
如果是python3，可以执行：
$ python3 -m pip install scipy
