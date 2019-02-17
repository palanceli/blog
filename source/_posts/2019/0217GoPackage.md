---
layout: post
title: Go包名规则
date: 2019-02-17 14:00:00 +0800
categories: 随笔笔记
tags: 随笔
toc: true
comments: true
---
每个`.go`模块文件，开头的`package`名称和文件名是什么关系？  
在`import`的时候，路径、文件名和包名又是什么关系？

<!-- more -->
# Go源码的做法
来看看系统怎么做的：
``` bash
$ cd %GOROOT%/src/fmt
$ tree .
.
├── format.go
├── print.go
├── scan.go
└── ...
```
这三个文件开头均为：
``` go
package fmt
...
```
于是可以推测
> 当`import XXX`时，编译器会查找`%GOROOT%/src/XXX`（其次再找`%GOPATH/src/XXX`）下以`package XXX`开头的所有go文件，并找到被引用的元素，完成编译。因此，**文件名其实是无所谓的**。

# 如果包名和路径名不一致呢
``` bash
$ cd %GOPAT%/src/test
$ tree .
.
├── test.go
├── pkgA
│   └── model.go   # 以 package model 开头
└── pkgB
    └── model.go   # 以 package model 开头
```
这种情况下`test.go`应该如何引用`pkgA/model.go`中的模块呢？如下：
``` go
import model "test/pkgA"

func main(){
      model.Func()
}
```
也就是说
> `import`语句可以包含`包名`和`包路径`，如果省略`包名`，则其默认值和导入目录下的文件所声明的包名一致。这就要求一个目录下的所有文件只能定义一个包名。

如果一个目录下包含的多个文件声明了多个包名呢？对不起，编译报错！
``` bash
$ cd %GOPAT%/src/test
$ tree .
.
├── test.go
├── pkgA
│   ├── model1.go   # 以 package model1 开头
│   └── model2.go   # 以 package model2 开头
└── ...
```
会报出如下错误：
```
found packages model1 (model1.go) and model2 (model2.go) in XXX/pkgA(undefined)
```
也就是说：
> `import 包名 包路径`中的`包名`并非指定要导入的包名，因为只要包路径确定了，包名就确定了。这个`包名`其实是给导入的包名指定一个别名。

# 如果不同目录定义了同名包名呢？
如下所示：
``` bash
$ cd %GOPAT%/src/test
$ tree .
.
├── test.go
├── pkgA
│   └── model.go   # 以 package model 开头
└── pkgB
    └── model.go   # 以 package model 开头
```
`test.go`在使用`pkgA`和`pkgB`时，应如下书写：
``` go
import modelA "test/pkgA"
import modelB "test/pkgB"

func main(){
      modelA.Func()
      modelB.Func()
}
```

# 官方文档的说法
在[Go 语言规范官方文档](https://go-zh.org/ref/spec#Package_clause)中有对`PackageName`和`ImportPath`的具体描述：
```
ImportDecl       = "import" ( ImportSpec | "(" { ImportSpec ";" } ")" ) .
ImportSpec       = [ "." | PackageName ] ImportPath .
ImportPath       = string_lit .
```
> The PackageName is used in qualified identifiers to access exported identifiers of the package within the importing source file. It is declared in the file block. If the PackageName is omitted, it defaults to the identifier specified in the package clause of the imported package. If an explicit period (.) appears instead of a name, all the package's exported identifiers declared in that package's package block will be declared in the importing source file's file block and must be accessed without a qualifier.

