---
layout: post
title: 《iOS Programming BNRG》笔记二
date: 2017-07-22 23:00:00 +0800
categories: iOS Programming
tags: BNRG笔记
toc: true
comments: true
---
第二章概览了Swift的语法。更细节的可以参见[《The Swift Programming Language (Swift 4)》](https://developer.apple.com/library/content/documentation/Swift/Conceptual/Swift_Programming_Language/TheBasics.html#//apple_ref/doc/uid/TP40014097-CH5-ID309)。本节的要点有：
- 数据类型
- optional变量
- 字符串插值
<!-- more -->

# 1 数据类型
## 1.1 Swift的数据类型分三类：结构体，类和枚举
每种数据类型都有：
`属性` - 关联到类型的值
`构造器` - 初始化类的实例的代码
`实例方法` - 关联到类型的函数，可以被该类型的实例调用
`类方法` - 也叫静态方法，关联到类型的函数，可以被类型调用

Swift下一些基本的数据类型都是结构体，比如：
数字：Int, Float, Double
布尔：Bool
文本：String, Character
集合：Array<Element>, Dictionary<Key:Hashable, Value>, Set<Element:Hashable>

<font color=red>这种分类的依据是什么？他们之间有什么不同点？</font>

# 2 optional变量
## 2.1 什么是optional变量
optional表示该变量可能并没有保存任何值。
``` objc
var reading1: Float?
```
末尾的问号表示该变量是一个optional 变量：它可能指向一个实例，也可能指向nil。
``` objc
var x1: Float?
var x2: Float?
let avg = (x1 + x2) / 2    // 这么写法会导致编译错误，因为x1和x2是optional变量，需要展开
```

## 2.2 为什么引入optional
有解释归因于Swift是强类型语言，无法让nil与其他类型相兼容。swift引入optional实质的做法是为该类型包装了一个enum：
``` objc
enum Optional<T> {
    case Nil
    case Some( value:T )
} 
```
这样就容易理解String?与String根本就是两种数据类型：String?的类型是Optional<String>而不再是String。而nil就是Optional.Nil。unwrap 做的事情 （ a! ）就是提取 .Some 中的 value 变量。

> <font color=red>C++也是强类型语言，不就做到了nullptr与各类指针的比较么？让编译器实现nil与其他类型相比较，有什么障碍呢？A?类型判空不也得和nil比较？也就是Optional<A>.Nil和nil的比较，这俩类型也是不相同的吧？</font>

## 2.3 展开optional变量
print一个String?变量会得到在其外面包裹`Optional("")`的字符串：
``` objc
var x:String? = "abc"
print(x)    // 输出：Optional("abc")
```
这就是因为optional变量和本尊是两种类型，此处做了转换。可以通过强制展开把String?转换成String：
``` objc
var x:String? = "abc"
print(x!)    // 输出：abc。但是如果x是nil，此处会引发【运行时崩溃】！
```
强制展开是一种不安全的做法，它会导致运行时崩溃。还使用optional binding来安全展开：
``` objc
if let xx = x{
    print(xx)
}else{
    print("nil")
}
// 上面的代码等价于：
if x != nil{
    let xx = x!
    print(xx)
}else{
    print("nil")
}
```

## 2.4 if-let的本质依然是if...else
可以把if中的`let A=B`等效于`(let A=B) != nil`，因此在其判断列表中还可以添加更多的Bool值：
``` objc
if let text = textField.text, !text.isEmpty { 
    celsiusLabel.text = text
} else {
    celsiusLabel.text = "???"
}
```

> 既没有缀?也没有缀!的变量是什么变量呢？根据2.2的分析，应该就是本尊咯：
``` objc
var a:String
a = nil     // 此处会有编译错误：Nil cannot be assigned to type 'String'
```

# 3. 在字符串内插值
``` objc
let qaDict = ["What is your name?": "Palance", "How old are you?": "36"]
for (question, answer) in qaDict {
    let msg = "Question is \(question), answer is \(answer)"
}
```
写在`\()`之间的内容会当做变量（也可以是函数），在运行时求值。

---
# 4. 参考资料
[Swift 的 Optional 机制有什么用？](https://www.zhihu.com/question/28026214?sort=created)
[Swift为什么定义Optional类型？如果说是为了类型安全，那么在其他OOP语言中是怎么解决这个问题的？](https://www.zhihu.com/question/26512698)
[https://swiftcafe.io/2015/12/27/optional/](https://swiftcafe.io/2015/12/27/optional/)