---
layout: post
title: 优雅地处理golang error
date: 2019-09-24 14:00:00 +0800
categories: 技术
tags: 
toc: false
comments: true
---

使用golang以来，打交道最频繁的是错误处理。和C/C++相比golang在错误处理上允许携带更多信息以方便调试跟踪，代价就是要在每个函数调用后处理error返回值。本来不是多大事儿，但由于函数调用太频繁，使得每次在写这三五行代码时，总希望更简洁并且不遗漏信息。本文总结我对error处理的演化过程。

<!-- more -->
# 源头生成错误信息，中间层层转手
假设程序的配置来自几个文件，代码初始化加载配置时要依次读取。最初的代码是这么写的：仅在错误生成的源头处产生错误信息，中间层不做额外处理，仅负责中转。
``` go
package main

import(
	"os"
	"io/ioutil"
	"github.com/golang/glog"
)

func readFile(path string)(buf []byte, err error){
	f, err := os.Open(path)
	if err != nil{
		return
	}
	defer f.Close()

	buf, err = ioutil.ReadAll(f)
	if err != nil{
		return
	}
	return
}

type Config struct{
	Config1Path string
	Config2Path string
}

func (c *Config)LoadConfig()(err error){
	content, err := readFile(c.Config1Path)
	if err != nil{
		return
	}
	glog.V(8).Infof("content:%v", content)
	// parse content ...

	content, err = readFile(c.Config2Path)
	if err != nil{
		return
	}

	glog.V(8).Infof("content:%v", content)
	// parse content ...
	return
}

func main(){
	config := Config{
		Config1Path: "/Users/palance/Desktop/config1.txt",
		Config2Path: "/Users/palance/Desktop/config2.txt",
	}
	err := config.LoadConfig()
	if err != nil{
		glog.Errorf("FAILED to ReadConfig. err=%v", err)
	}
	// ...
}
```
运行结果如下:
``` shell
$ go run test1.go
ERROR: logging before flag.Parse: E0925 14:47:47.528462   71768 test1.go:55] FAILED to ReadConfig. err=open /Users/palance/Desktop/config2.txt: no such file or directory
```
这么写的问题在于：由于中间层`LoadConfig(...)`多次调用`readFile(...)`，错误产生于后者，假设传入的配置文件路径不是这么明显，或者出错信息里不包含文件路径，那么从错误文本里就很难判断出错时的调用路径了。为了解决这个问题，需要在中间转手时追加更多信息。


# 源头生成错误信息，中间转手时追加辅助信息
``` go
package main

import(
	"fmt"
	"os"
	"io/ioutil"
	"github.com/golang/glog"
)

func readFile(path string)(buf []byte, err error){
	f, err := os.Open(path)
	if err != nil{
		err = fmt.Errorf("FAILED to os.Open(%v). err=%v", 
			path, err)	// 追加辅助信息
		return
	}
	defer f.Close()

	buf, err = ioutil.ReadAll(f)
	if err != nil{
		err = fmt.Errorf("FAILED to ioutil.ReadAll(%v). err=%v", 
			path, err)	// 追加辅助信息
		return
	}
	return
}

type Config struct{
	Config1Path string
	Config2Path string
}

func (c *Config)LoadConfig()(err error){
	content, err := readFile(c.Config1Path)
	if err != nil{
		err = fmt.Errorf("FAILED to readFile(%v). err=%v", 
			c.Config1Path, err)	// 追加辅助信息
		return
	}
	glog.V(8).Infof("content:%v", content)
	// parse content ...

	content, err = readFile(c.Config2Path)
	if err != nil{
		err = fmt.Errorf("FAILED to readFile(%v). err=%v", 
			c.Config2Path, err)	// 追加辅助信息
		return
	}

	glog.V(8).Infof("content:%v", content)
	// parse content ...
	return
}

func main(){
	config := Config{
		Config1Path: "/Users/palance/Desktop/config1.txt",
		Config2Path: "/Users/palance/Desktop/config2.txt",
	}
	err := config.LoadConfig()
	if err != nil{
		glog.Errorf("FAILED to ReadConfig. err=%v", err)
	}
	// ...
}
```
运行结果如下：
``` shell
$ go run test1.go
ERROR: logging before flag.Parse: E0925 16:12:26.266804   73648 test1.go:58] 
FAILED to ReadConfig. err=
FAILED to readFile(/Users/palance/Desktop/config2.txt). err=
FAILED to os.Open(/Users/palance/Desktop/config2.txt). err=
open /Users/palance/Desktop/config2.txt: no such file or directory
```
显然这个输出还是挺让人困惑的——不能直接定位到调用行数。

# 在每个中转处添加log以跟踪调用行号
``` go
content, err := readFile(c.Config1Path)
if err != nil{
    err = fmt.Errorf("FAILED to readFile(%v). err=%v", 
    	c.Config1Path, err)	// 追加辅助信息
    glog.Error(err.Error())
    return
}
```
输出结果为：
``` shell
$ go run test1.go
ERROR: logging before flag.Parse: E0925 18:09:40.68577 76292 test1.go:15] 
FAILED to os.Open(/Users/palance/Desktop/config2.txt). 
err=open /Users/palance/Desktop/config2.txt: no such file or directory

ERROR: logging before flag.Parse: E0925 18:09:40.68587 76292 test1.go:50] 
FAILED to readFile(/Users/palance/Desktop/config2.txt). err=
FAILED to os.Open(/Users/palance/Desktop/config2.txt). err=
open /Users/palance/Desktop/config2.txt: no such file or directory

ERROR: logging before flag.Parse: E0925 18:09:40.68588 76292 test1.go:66] 
FAILED to ReadConfig. err=
FAILED to readFile(/Users/palance/Desktop/config2.txt). err=
FAILED to os.Open(/Users/palance/Desktop/config2.txt). err=
open /Users/palance/Desktop/config2.txt: no such file or directory
```
还是不理想，行号是有了，重复信息太多。改进一下：err message不再层层累加，只在log时输出。
# 精简log
``` go
content, err := readFile(c.Config1Path)
if err != nil{
    glog.Errorf("FAILED to readFile(%v). err=%v", c.Config1Path, err)
    return
}
```
输出结果为：
``` shell
go run test1.go
ERROR: logging before flag.Parse: E0925 18:15:44.514380   76373 test1.go:14] 
FAILED to os.Open(/Users/palance/Desktop/config2.txt). err=
open /Users/palance/Desktop/config2.txt: no such file or directory

ERROR: logging before flag.Parse: E0925 18:15:44.514474   76373 test1.go:49] 
FAILED to readFile(/Users/palance/Desktop/config2.txt). err=
open /Users/palance/Desktop/config2.txt: no such file or directory

ERROR: logging before flag.Parse: E0925 18:15:44.514493   76373 test1.go:65] 
FAILED to ReadConfig. err=
open /Users/palance/Desktop/config2.txt: no such file or directory
```
这样err是由最初错误的生成点产生的，中途只是在log里添加辅助信息。依然不完美——log输出不是原子的，在多线程的环境中，上面的输出可能会被其它线程的log分隔很远，希望在一次错误输出里能呈现整个调用栈。

# 引入"github.com/pkg/errors"
``` go
package main

import(
	"os"
	"io/ioutil"
	"github.com/golang/glog"
	"github.com/pkg/errors"
)

func readFile(path string)(buf []byte, err error){
	f, err := os.Open(path)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to os.Open(%v)", path)
		return
	}
	defer f.Close()

	buf, err = ioutil.ReadAll(f)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to ioutil.ReadAll(%v)", path)
		return
	}
	return
}

type Config struct{
	Config1Path string
	Config2Path string
}

func (c *Config)LoadConfig()(err error){
	content, err := readFile(c.Config1Path)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to readFile(%v)", c.Config1Path)
		return
	}
	glog.V(8).Infof("content:%v", content)
	// parse content ...

	content, err = readFile(c.Config2Path)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to readFile(%v)", c.Config1Path)
		return
	}

	glog.V(8).Infof("content:%v", content)
	// parse content ...
	return
}

func main(){
	config := Config{
		Config1Path: "/Users/palance/Desktop/config1.txt",
		Config2Path: "/Users/palance/Desktop/config2.txt",
	}
	err := config.LoadConfig()
	if err != nil{
		glog.Errorf("FAILED to ReadConfig. err=%+v", err)
	}
	// ...
}
```
执行结果如下：
``` shell
go run test1.go
ERROR: logging before flag.Parse: E0925 19:22:16.053087   78023 test1.go:58] 
FAILED to ReadConfig. err=open /Users/palance/Desktop/config2.txt: no such file or directory
FAILED to os.Open(/Users/palance/Desktop/config2.txt)
main.readFile
	/Users/palance/Desktop/test1.go:13
main.(*Config).LoadConfig
	/Users/palance/Desktop/test1.go:40
main.main
	/Users/palance/Desktop/test1.go:56
runtime.main
	/usr/local/go/src/runtime/proc.go:200
runtime.goexit
	/usr/local/go/src/runtime/asm_amd64.s:1337
FAILED to readFile(/Users/palance/Desktop/config1.txt)
main.(*Config).LoadConfig
	/Users/palance/Desktop/test1.go:42
main.main
	/Users/palance/Desktop/test1.go:56
runtime.main
	/usr/local/go/src/runtime/proc.go:200
runtime.goexit
	/usr/local/go/src/runtime/asm_amd64.s:1337
```
原子性问题解决了，但还是太冗长，它把每一次Wrap时的调用栈都记录下来了，其实可以在打印的时候只显示最深的那一层，要么修改`github.com/pkg/errors`/`errors.go`/`func (w *withStack) Format(s fmt.State, verb rune)`；要么调用侧代码仅在最底层代码调用`Wrap`，上层改用`WithMessage`。方案一以后再讨论，这里先演示方案二。
# 再次精简log
在MVC结构层次分明的代码里，使用方案二还是比较容易的——通常在model层产生错误的时候使用Wrap。
``` go
package main

import(
	"os"
	"io/ioutil"
	"github.com/golang/glog"
	"github.com/pkg/errors"
)

func readFile(path string)(buf []byte, err error){
	f, err := os.Open(path)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to os.Open path=%v", 
			path)	// 在error的产生除使用Wrap
		return
	}
	defer f.Close()

	buf, err = ioutil.ReadAll(f)
	if err != nil{
		err = errors.Wrapf(err, "FAILED to ioutil.ReadAll path=%v", 
			path)	// 在error的产生处使用Wrap
		return
	}
	return
}

type Config struct{
	Config1Path string
	Config2Path string
}

func (c *Config)LoadConfig()(err error){
	content, err := readFile(c.Config1Path)
	if err != nil{
		err = errors.WithMessagef(err, "FAILED to readFile(%v)", 
			c.Config1Path)	// 在error中转层仅附加Message
		return
	}
	glog.V(8).Infof("content:%v", content)
	// parse content ...

	content, err = readFile(c.Config2Path)
	if err != nil{
		err = errors.WithMessagef(err, "FAILED to readFile(%v)", 
			c.Config1Path)	// 在error中转层仅附加Message
		return
	}

	glog.V(8).Infof("content:%v", content)
	// parse content ...
	return
}

func main(){
	config := Config{
		Config1Path: "/Users/palance/Desktop/config1.txt",
		Config2Path: "/Users/palance/Desktop/config2.txt",
	}
	err := config.LoadConfig()
	if err != nil{
		glog.Errorf("FAILED to ReadConfig. err=%+v", err)
	}
	// ...
}
```
运行结果如下：
``` shell
$ go run test1.go
ERROR: logging before flag.Parse: E0925 19:38:20.13575 78715 test1.go:58] 
FAILED to ReadConfig. err=open /Users/palance/Desktop/config2.txt: no such file or directory
FAILED to os.Open path=/Users/palance/Desktop/config2.txt
main.readFile
	/Users/palance/Desktop/test1.go:13
main.(*Config).LoadConfig
	/Users/palance/Desktop/test1.go:40
main.main
	/Users/palance/Desktop/test1.go:56
runtime.main
	/usr/local/go/src/runtime/proc.go:200
runtime.goexit
	/usr/local/go/src/runtime/asm_amd64.s:1337
FAILED to readFile(/Users/palance/Desktop/config1.txt)
```
不算特别完美，log和调用栈是分离的，视觉比较跳跃：先看第一行，再循着中间的调用栈结合底部的log跟踪调用过程。如果调用栈和附加信息比较多，要不断在中间的调用栈和底部的log之间切换。

先这样吧，需要的信息都齐全了。以后自己改一个理想的版本。好消息是go1.13已经内置了[Error wrapping](https://golang.org/doc/go1.13#error_wrapping)，只需要`fmt.Errorf("error message err=%w", err)`即可完成Wrap，调用`UnWrap`得到内一层error，这要比github.com/pkg/errors更方便。

# 参考资料
[Golang error 的突围](https://zhuanlan.zhihu.com/p/82985617?utm_source=wechat_session&utm_medium=social&utm_oi=926941521738100736)
[package errors](https://godoc.org/github.com/pkg/errors)
[errors/example_test.go](https://github.com/pkg/errors/blob/master/example_test.go)
[Go语言错误处理](https://tonybai.com/2015/10/30/error-handling-in-go/)
[Error handling and Go](https://blog.golang.org/error-handling-and-go)