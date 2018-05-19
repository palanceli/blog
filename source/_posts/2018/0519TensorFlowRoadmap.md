---
layout: post
title: TensorFlow知识地图
date: 2018-05-19 14:00:00 +0800
categories: 知识地图
tags: 机器学习
toc: true
comments: true
mathjax: true
---

TensorFlow图描述了一个计算的过程，图必须在`会话`里启动，会话将图的op（operation）分发到诸如CPU或GPU之类的设备上，同时提供执行op的方法。这些方法执行后，将产生的tensor返回。在Python语言中，返回的tensor是`numpy ndarray`对象；在C和C++语言中，返回的tensor是`tensorflow::Tensor`实例。  <!-- more -->

# 基本框架
TensorFlow程序通常被组织成`构建阶段`和`执行阶段`。在构建阶段，op的执行步骤被描述成一个图；在执行阶段，使用会话执行执行图中的op。  
``` python
import tensorflow as tf

def tc1(self):
    # TensorFlow库有一个默认图，此处就使用了该默认图。
    # 1. 创建三个节点：两个constant() op，一个matmul() op
    matrix1 = tf.constant([[3., 3.]])
    matrix2 = tf.constant([[2.], [2.]])
    product = tf.matmul(matrix1, matrix2)

    # 2. 在会话中启动图
    sess = tf.Session()
    result = sess.run(product)
    logging.info(result)
    sess.close()
```
它的输出为：
```
12:08 0025 INFO     [[12.]]
```
## 交互式使用
上例通过一行`sess.run()`调用，完成图的计算。如果要查看计算过程中某个变量的取值，可以采用交互式会话`InteractiveSession`来替代`Session`，并使用`Tensor.eval()`获得取值：
``` python
import tensorflow as tf

def tc2(self):
    sess = tf.InteractiveSession()
    x = tf.Variable([1.0, 2.0])
    a = tf.constant([3.0, 3.0])

    x.initializer.run()
    logging.info(x.eval())      # 查看x的取值

    sub = tf.subtract(x, a)     # 执行减法
    logging.info(sub.eval())    # 查看结果取值
```
它的输出为：
```
13:01 0035 INFO     [1. 2.]
13:01 0038 INFO     [-2. -1.]
```

# Tensor
TensorFlow程序使用tensor数据结构来代表所有数据。在计算图中，操作间传递的数据都是tensor。可以把TensorFlow tensor看作是一个n维的数组或列表。
## 变量
``` python
import tensorflow as tf

def tc3(self):
    state = tf.Variable(0, name="counter")  # 创建一个变量，初始化为标量0

    one = tf.constant(1)
    new_value = tf.add(state, one)          # 创建一个实现累加的op
    update = tf.assign(state, new_value)

    # 启动图后, 变量必须先经过初始化
    init_op = tf.initialize_all_variables() # 创建一个初始化变量的 op

    with tf.Session() as sess:
        sess.run(init_op)                   # 执行初始化
        logging.info(sess.run(state))       # 打印初值
        for _ in range(3):
            sess.run(update)
            logging.info(sess.run(state))   # 打印累加值

```
它的输出为：
```
13:24 0051 INFO     0
13:24 0054 INFO     1
13:24 0054 INFO     2
13:24 0054 INFO     3
```
对于操作数，可以执行`Session::run(op)`来获取其值。

## feed_dict
在定义变量或常量时，可以只定义一个占位符，等到执行时通过`feed_dict`字典变量指定这些占位符的实际值：
``` python
import tensorflow as tf

def tc4(self):
    ''' 在运行时指定输入实参 '''
    input1 = tf.placeholder(tf.float32) # 定义占位符形参
    input2 = tf.placeholder(tf.float32)
    output = tf.multiply(input1, input2)

    with tf.Session() as sess:
        logging.info(sess.run([output], feed_dict={input1:[7.], input2:[2.]}))
```
它的输出为：
```
13:31 0062 INFO     [array([14.], dtype=float32)]
```

# 参考
[TensorFlow的基本使用](http://www.tensorfly.cn/tfdoc/get_started/basic_usage.html)  
[TensorFlow Tutorials](https://www.tensorflow.org/tutorials/)