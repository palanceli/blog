---
layout: post
title: pandas使用
date: 2018-03-27 10:00:00 +0800
categories: 机器学习
tags: 基础工具
toc: true
comments: true
mathjax: true
---
pandas主要用于数据分析，拿到一批数据后，对数据有个宏观深入的理解非常重要，比如分布、均值、方差等，这是pandas的用武之地。

<!-- more -->

# 观察数据分布
``` python
data = np.array([1, 1, 1, 2, 3, 4, 5, 6], np.uint32)
df = pd.DataFrame(data, columns=['number'])
logging.info(data)
logging.info('\n%s' % df.describe())
```
这段代码的输出结果如下：
``` bash
        number
count  8.00000
mean   2.87500  平均值
std    1.95941  标准差 
min    1.00000  最小数
25%    1.00000  四分位数，第2个和第3个数的均值
50%    2.50000  第二四分位数，第4和第5个数的均值
75%    4.25000  
max    6.00000  最大数
```
其中标准差$δ=\sqrt{\frac{1}{N} \sum_{i=1}^{N}{ (x_i - μ)^2 }} ，\; 均值μ=\frac{1}{N} \sum_{i=1}^{N}x_i$

## 自定义分位数
``` python
data = np.array(np.linspace(1, 20, 20), np.uint32).reshape(10, 2)
df = pd.DataFrame(data, columns=['a', 'b'])
logging.info('\n%s' % df.describe(percentiles=[.20, .40, .60, .80]))
```
输出结果：  
``` bash
               a          b
count  10.000000  10.000000
mean   10.000000  11.000000
std     6.055301   6.055301
min     1.000000   2.000000
20%     4.600000   5.600000
40%     8.200000   9.200000
50%    10.000000  11.000000
60%    11.800000  12.800000
80%    15.400000  16.400000
max    19.000000  20.000000
```