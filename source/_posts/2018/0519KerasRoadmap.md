---
layout: post
title: Keras知识地图
date: 2018-05-19 14:00:00 +0800
categories: 知识地图
tags: 机器学习
toc: true
comments: true
mathjax: true
---
Keras的核心数据结构是“模型”，模型是一种组织网络层的方式。Keras中主要的模型是Sequential模型，Sequential是一系列网络层按顺序构成的栈。
<!-- more -->

# 基本框架
将网络层通过.add()堆叠起来，就构成了一个模型。之后需要

1. 使用`.compile()`编译模型
2. 使用`.fit(...)`训练网络
3. 使用`.evalute(...)`评估模型
4. 使用`.predict(...)`预测新数据

``` python
import keras
from keras.layers import Dense, Dropout, Activation
from keras.models import Sequential
from keras.optimizers import SGD
import numpy as np

def tc1(self):
    # 构造训练集和测试集
    x_train = np.random.random((1000, 20))
    y_train = keras.utils.to_categorical(
            np.random.randint(10, size=(1000, 1)), num_classes=10)
    x_test = np.random.random((100, 20))
    y_test = keras.utils.to_categorical(
            np.random.randint(10, size=(100, 1)), num_classes=10)

    # 1.构建模型
    model = Sequential()
    # 第一个隐藏层共64个节点，接收20个输入节点
    model.add(Dense(64, activation='relu', input_dim=20)) 
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu')) # 第二个隐藏层64个节点
    model.add(Dropout(0.5))
    model.add(Dense(10, activation='softmax'))  # 输出层10个节点

    # 2. 编译模型
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy',
                optimizer=sgd, metrics=['accuracy'])
    # 3. 训练网络
    model.fit(x_train, y_train, epochs=20, batch_size=128)
    # 4. 评估模型
    score = model.evaluate(x_test, y_test, batch_size=128)
    # 5. 预测新数据
    result = model.predict( np.random.random((1, 20)))
    logging.info(result) # 打印结果
```

# 参考
[快速开始：30s上手Keras](http://keras-cn.readthedocs.io/en/latest/#30skeras)  
