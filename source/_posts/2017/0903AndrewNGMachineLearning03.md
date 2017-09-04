---
layout: post
title: Andrew NG Machine Learning视频学习笔记三
date: 2017-09-04 23:00:00 +0800
categories: Machine Learning
tags: Andrew NG Machine Learning
toc: true
comments: true
---
本节和视频教程没什么关系，学完了线性回归，自己想两个题目做做吧。
<!-- more -->
题目是这样的，假设用户词库是由中文词条或拼音串组成，词条个数和词库大小呈线性关系。词库来自于libGooglePinyin中的语料。接下来我们就生成训练集，训练模型，并用模型验证测试样本。

代码我传到了[线性回归练习](https://github.com/palanceli/MachineLearningSample)

# 单变量线性回归练习
单变量线性回归练习中，词库里只有中文词条，输入变量就是词条个数，输出变量是词库大小。
我截取了主要代码如下：
``` python
def SingleFeatureLearning():
	# 单变量线性回归学习过程
    dc = DataCreator()
    # 生成训练样本
    cSamples = 30		# 训练样本个数
    samples = dc.CreateSampleForSingleFeature(cSamples) 

    csvData = 'lines,bytes\n'
    for s in samples:
    	csvData += '%d,%d\n' % (s[0], s[1])

    # 将训练样本读入dataFrame
    dataFrame = pandas.read_csv(io.StringIO(csvData.decode('utf-8')))
    logging.debug(dataFrame)

    # 建立线性回归模型
    regr = sklearn.linear_model.LinearRegression()

    # 拟合
    regr.fit(dataFrame['lines'].values.reshape(-1, 1), dataFrame['bytes']) # reshape(-1, 1)是什么意思？

    # 生成测试样本
    cSample = 5			# 测试样本个数
    samples = dc.CreateSampleForSingleFeature(cSample)
    csvTestData = 'lines,bytes\n'
    for s in samples:
    	csvTestData += '%d,%d\n' % (s[0], s[1])

    # 将训练样本读入dataFrame
    testDataFrame = pandas.read_csv(io.StringIO(csvTestData.decode('utf-8')))
    print(testDataFrame)

    # 预测10000条词的大小
    logging.debug(regr.predict(10000))

    # 画图
    # 1. 训练样本的点
    matplotlib.pyplot.scatter(dataFrame['lines'], dataFrame['bytes'], color='blue')

    # 2. 测试样本的点
    matplotlib.pyplot.scatter(testDataFrame['lines'], testDataFrame['bytes'], marker='x', color='green')

    # 3. 拟合直线
    matplotlib.pyplot.plot(dataFrame['lines'], regr.predict(dataFrame['lines'].values.reshape(-1, 1)), color='red')

    ......
    matplotlib.pyplot.show()
```
运行结果如下图：
![](0903AndrewNGMachineLearning03/img01.png)
横轴是词条的个数，纵轴是词库的大小。蓝点表示训练样本，绿叉表示测试样本，直线是训练出来的预测函数。本例中共30个训练样本，5个测试样本。

从这附图上看起来无论训练样本还是测试样本，好像严格遵守了一次函数的线性关系。我猜测这是因为数据取值范围过大导致的肉眼无法在图形上分辨误差了。这套训练样本的词条数在(6000, 60000)之间。

可以把每个样本中词条数的取值范围缩小到几百的量级，样本个数不变，图形就变成这样了：
![](0903AndrewNGMachineLearning03/img02.png)


# 两个变量的线性回归练习
两个变量的线性回归练习中，词库里包含中文词条和拼音串，二者个数不一定相等，输出变量是词库大小。