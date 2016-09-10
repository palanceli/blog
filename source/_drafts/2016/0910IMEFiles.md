---
title: 输入法文件存储占用尺寸调查
date:   2016-09-10 14:40:21 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
# 了解各输入法的文件分布情况
下面就把各家输入法的文件夹pull到本地。
## 搜狗输入法
``` bash
$ adb pull /data/app/com.sohu.inputmethod.sogou-1/ /Users/palance/Desktop/IMEFiles/Sogou/app
$ adb pull /data/data/com.sohu.inputmethod.sogou/ /Users/palance/Desktop/IMEFiles/Sogou/data
```

## 百度输入法
``` bash
$ adb pull /data/app/com.baidu.input-1/ /Users/palance/Desktop/IMEFiles/Baidu/app

```
<!-- more -->

