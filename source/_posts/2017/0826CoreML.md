---
layout: post
title: CoreML初探
date: 2017-08-26 23:00:00 +0800
categories: iOS Programming
tags: CoreML
toc: true
comments: true
---
本章把玩苹果发布的CoreML例程以及CoreMLTools，对CoreML有个感性认识。
本章要点：
- 怎么操作CoreML
- model文件是什么
![](0826CoreML/img01.png)
<!-- more -->

首先，运行CoreML，操作系统必须大于macOS 10.13或iOS11，Xcode版本要在9或以上。Xcode9-beta稳定性还可以，而且自带iOS11 simulator，macOS 10.13现在还很不稳定，升级要慎重:P

苹果官方对CoreML的资料还不多。

[Build more intelligent apps with machine learning](https://developer.apple.com/machine-learning/)对CoreML有个导入性的介绍：1、可以把当下广泛的机器学习的数据模型整合到app中，包括tree ensembles、SVMs、generalized linear和深度学习；2、可以无缝利用苹果设备的CPU和GPU为机器学习提供最高的性能和效率。
目前可以应用在图像识别、文本检测、目标跟踪以及自然语言处理如语言识别、词干提取等。

[Core ML](https://developer.apple.com/documentation/coreml)则是技术文档的入口。包含一个简单的例程：[Integrating a Core ML Model into Your App](https://github.com/palanceli/IntegratingaCoreMLModelintoYourApp)我在这个例程里加了一些自己的代码，所以url是我的github。

# Integrating a Core ML Model into Your App
从这个例程可以对CoreML的用法有个大致了解。它根据一块地产的太阳能板个数、温室的间数和面积三个输入参数来预测这块地产的价格。CoreML和CoreData在用法上很相似，步骤如下。

## 1 把CoreML文件导入工程。
Xcode支持对数据模型文件的解析和展现，输入、输出都有哪些字段，数据类型。如图这是Xcode看到的mlmodel文件：
![mlmodel](0826CoreML/img02.png)
Xcode会为mlmodel生成相应的接口文件，这个文件从工程里是找不到的，点击上图MarsHabitatPricer右侧的箭头可以打开此文件，它是对model数据的封装。
## 2 通过mlmodel接口文件访问数据：
``` objc
let model = MarsHabitatPricer()	// 创建mlmodel实例

// 从界面上得到三个输入参数
func selectedRow(for feature: Feature) -> Int {
    return pickerView.selectedRow(inComponent: feature.rawValue)
}

let solarPanels = pickerDataSource.value(for: selectedRow(for: .solarPanels), feature: .solarPanels)
let greenhouses = pickerDataSource.value(for: selectedRow(for: .greenhouses), feature: .greenhouses)
let size = pickerDataSource.value(for: selectedRow(for: .size), feature: .size)

// 向mlmodel输入参数，得到预测价格
guard let marsHabitatPricerOutput = try? model.prediction(solarPanels: solarPanels, greenhouses: greenhouses, size: size) else {
    fatalError("Unexpected runtime error.")
}
let price = marsHabitatPricerOutput.price
priceLabel.text = priceFormatter.string(for: price)
```
例程的界面如下：
![app UI](0826CoreML/img03.png)

CoreML的使用就这么简单，但越是简单的东西，越吸引人去了解它的内部构造，因为你知道它不是简单的查表，也不是一次方程算出的结果，而是根据喂进去数据训练出模型，再根据模型预测新的输入/输出关系。

# mlmodel文件
深入的第二步就是探究这个mlmodel文件是怎么产生的。
在官方文档上说：现在大多数第三方机器学习工具产生的数据文件，都可以通过[Core ML Tools](https://pypi.python.org/pypi/coremltools)来转换成mlmodel文件。在[coremltools 文档](https://apple.github.io/coremltools/)中可以看到它的用法。
在我的[palanceli/IntegratingaCoreMLModelintoYourApp/testcoreml.py](https://github.com/palanceli/IntegratingaCoreMLModelintoYourApp/blob/master/testcoreml.py)中有对这个工具的测试。

## 测试mltools

# 遇到的问题
## 关闭SIP升级numpy
在macOS下通过命令`pip install numpy --upgrade`升级numpy默认会失败，这是因为没有System Integrity Protection权限。解决办法：
1. 重启电脑，启动前按住⌘+R
2. 启动后在菜单中找到“终端”并打开，输入`csrutil disable`
3. 重启电脑
4. 之后就可以成功执行`pip install numpy --upgrade`升级numpy了。
5. 完成后记得再用`csrutil enable`恢复SIP设置。

## unable to find utility "coremlcompiler"错误
coremltools已经安装就虚了，初次跑会提示如下错误：
`RuntimeError: Got non-zero exit code 72 from xcrun. Output was: xcrun: error: unable to find utility "coremlcompiler", not a developer tool or in PATH`

这是因为命令行路径没有指向Xcode beta，在命令行下执行下面命令即可：
``` bash
sudo xcode-select --switch /Applications/Xcode-beta.app/Contents/Developer
```