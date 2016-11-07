---
layout: post
title: Python中把数据转成字节流
date: 2016-09-26 23:44:05 +0800
categories: 随笔笔记
tags: Python
toc: true
comments: true
---
Python真是个好东西！用来做测试用例，或者开发放在服务器端的小工具，用Python有如神助。因为它有丰富的库文件，Linux/Unix系默认都带，有个文本编辑器就能玩起来。

昨天遇到数据向字节流转换的一个需求，又折腾了一个小时，类似的事情过去应该折腾过不止一次，每次解决完过一段时间就忘了，下次遇上了再去Google……之所以这样，我觉得并没有理解问题的原因和解决办法，每次只求把眼下的障碍清除掉，至于为什么会产生这种障碍，其实是不清楚的，或者理解的不深刻。如果能把Python对象模型在内存里的结构弄清楚了，一定不会发生这样的事。不过这次并不是要研究ython对象模型，这个课题太大了。至少把眼下问题的本质是什么弄清楚了，下次再遇到同样的问题不至于再去折腾。
<!-- more -->

# 使用urllib2发送POST请求
需求是这样的：服务端刚刚上线一组服务，可是很不稳定，经常出现超时。其他组开发的，需要我中间介入调查，我认为首先应该把现状搞清楚：超时比是多少？于是写个脚本模拟客户端发请求，把每次从请求成功收到响应的时间记录下来。请求使用urllib2，套路比较简单：
``` python
import urllib2
import datetime
... ...

req = urllib2.Request(url = myUrl, data = myData)

req.add_header('Content-Type', 'application/octet-stream')
req.add_header('Connection', 'keep-alive')
... ...     # 添加Host、Accept等header
req.add_header('Accept-Encoding', 'gzip, deflate')

startTime = datetime.datetime.now()
res = urllib2.urlopen(req)
response = res.read()
endTime = datetime.datetime.now()
return (startTime, endTime, response)
```

# 使用struct.pack打包数据
其中myData是要POST的数据，是将一些int、short以及字符串数据组成一个byte流。如果是一般的英文字符，比较好处理，使用`struct.pack`即可。如下：
``` python 
import struct
... ...

myData = struct.pack('iH%ds' % len(myStr), iValue, hValue, myStr)
```
但是字符串都要求是utf-16le的形式，为之奈何？

## 打包unicode字符串
我一直以为应该怎么把utf-16le的字串用struct.pack打包成字节流，比如：
``` python
# -*- coding:utf-8 -*-
myStr = '测试数据'
utf16Str = myStr.decode('utf8')
myData = struct.pack('%dH' % len(utf16Str), utf16Str)
```
结果会报错：`pack expected 4 items for packing (got 1)`

最终的解决特别其实特别简单：
``` python
# -*- coding:utf-8 -*-
myStr = '测试数据'
utf16Str = myStr.decode('utf8').encode('utf-16le')
myData = struct.pack('iH', iValue, hValue) + utf16Str
print ['0x%02X' % ord(c) for c in myData]
```
输出结果：
> ['0x01', '0x00', '0x00', '0x00', '0x02', '0x00', '0x4B',  '0x6D', '0xD5', '0x8B', '0x70', '0x65', '0x6E', '0x63']

我以为unicode也应该是2字节或者4字节的字节流，应该总有办法把它pack到struct里去的，我稍微改一下：

``` python
# -*- coding:utf-8 -*-
myStr = '测试数据'
utf16Str = myStr.decode('utf8')
myData = struct.pack('iH', iValue, hValue) + utf16Str
print ['0x%02X' % ord(c) for c in myData]
```
输出结果就是：
> ['0x01', '0x00', '0x00', '0x00', '0x02', '0x00', '0x6D4B', '0x8BD5', '0x6570', '0x636E']

既然都是字节流，我没看出来二者有什么本质区别。有没有区别，把myData写到文件里就清晰了，我猜测写出来的文件应该是一样的。可结果出乎我意料，后者写文件时会得到如下错误：
> UnicodeEncodeError: 'ascii' codec can't encode characters in position 4-7: ordinal not in range(128)

## 为什么unicode不可以直接pack到struct中
仔细翻阅文档，发现unicode字符串的定义如下：
> The items of a Unicode object are Unicode code units. A Unicode code unit is represented by a Unicode object of one item and can hold either a 16-bit or 32-bit value representing a Unicode ordinal.

这段定义貌似也没说清楚Unicode code units是个啥玩意儿，可以写段代码来求证：
``` python
print type('测试数据'.decode('utf8')[0])
```
结果为：`<type 'unicode'>`，这说明unicode子串中每一个元素都是一个unicode对象，而不是一个字符。一个抽象数据类型不能强转成字节，因为缺少转换语义，这很容易理解。如果一定要转，就应该自己写转换逻辑了。utf16Str是一个unicode，因此不能直接用来pack到struct。如果一定要转成字节流，需要先转成struct.pack能认识的format，那只能是str。都已经是str了，也就不需要什么转换了，所以通过运算符“+”追加即可。

## struct.pack(...)可以追加整形数组么？
既然`u'测试数据'.encode('utf-16le')`是一个字符数组，可以直接追加到struct.pack(...)。那么一个整形数组本质上跟字符数组也没什么区别，是否也可以直接追加呢？答案是：不能！不能以C中memcpy的思考方式来类比，struct.pack(...)返回的是个str，“字符串+数组”显然是不合法的。随意追加数组的合法方式应该是把数组中每个元素转成struct.pack(...)能识别的格式，一一追加。

还有一个便捷的方式：
``` python
arr = (1, 2, 3, 4)
data = struct.pack('%dH' % len(arr), *arr)
print ['0x%02X' % ord(c) for c in data]
```
输出结果是：
> [''0x01', '0x00', '0x02', '0x00', '0x03', '0x00', '0x04', '0x00']
原来Python的数组可以取“*”运算的，运算的结果是把成员都取出来。
