---
layout: post
title: 使用Emacs
date: 2016-09-19 23:03:27 +0800
categories: 环境、配置
tags: Emacs
toc: true
comments: true
---
最近经常在不同操作系统下写C、Python和JAVA代码，需要持续不断地学习新的编辑器、IDE的使用，为了让学习成本尽快收敛住，还是决定捡起多年没用过的Emacs，把编辑、调试各种操作通透了，以后就再也不用学习新的编辑器了。

如果仅在Windows下做C++，精通VisualStudio就足够了。如果要跨平台或者跨语言，我认为最好还是能精通Vim或者Emacs。这俩货的学习曲线虽然陡峭，却是唯一在所有平台下通用的编程工具。一旦使顺手了，就不用在不同平台下适应不同的习惯；不用隔段时间就要学习新的编辑器；也不会因为隔段时间不用，让原先已经学会的工具由于版本更新又变得陌生了。<!-- more -->

我也认为学习这两样工具之前需要慎重考虑，有了十足的必要性再开动。因为学习成本真的不低，隔段时间不用又会忘掉，所以最忌讳学个三五成扔掉了，过一年半载的又觉得需要，再从头学。这种学法是最浪费精力，浪费时间的。也是我过去的学法:(

学习周期长没关系，每次学一点也无所谓。有效地沉淀和记录下来，日常用起来，总能在可预期的时间里把它啃下来。本文不是什么全面的总结，只是把我自己需要的配置、操作、注意点记录下来，确保有效积累。前面小节中记录下的点滴如果涉及到配置的，都会在最后一节的`.emacs文件配置`中体现出来。

# 安装Emacs
在mac OS下安装Emacs非常简单，去[emacs for mac osx](https://emacsformacosx.com/)下载安装最新版本即可。这个版本默认就带了cedet、semantic、speedbar等工具，不用额外下载，只需要完成配置即可。

# 设置主题
简单点，就用自带主题吧：
Options - Customize Emacs - Custom Theme - tsdh-dark
点击`Save Theme Settings`保存主题。

# 设置默认字体
Options - Set Default Font
选择字体`Curier New`，字号16。注意，该操作只能在本次会话中生效，如果想把它作为Emacs的默认设置，需要修改~/.emacs文件。

敲入命令：
`M-x describe-font 回车 回车`，
Emacs会列出当前使用的字体字号的文本描述：
`name (opened by): -*-Courier New-normal-normal-normal-*-16-*-*-*-m-0-iso10646-1`
在~/.emacs中加入：
`(set-default-font"-*-Courier New-normal-normal-normal-*-16-*-*-*-m-0-iso10646-1")`

# 标题栏显示文件完整路径
``` lisp
;;Emacs title bar to reflect file name
(defun frame-title-string ()
"Return the file name of current buffer, using ~ if under home directory"
(let 
((fname (or 
(buffer-file-name (current-buffer))
(buffer-name))))
;;let body
(when (string-match (getenv "HOME") fname)
(setq fname (replace-match "~" t t fname)) )
fname))

;;; Title = 'system-name File: foo.bar'
(setq frame-title-format '(:eval (frame-title-string)))
```

# 备份文件
``` lisp
;; 禁止生成配置文件
(setq make-backup-files nil)

;; 配置文件都生成到~/.backups下
(setq backup-directory-alist (quote (("." . "~/.backups"))))
```
若要恢复文件，可执行：
```
M-x recover-file <RET> 文件名 <RET>
yes <RET>
C-x C-s
```
# cscope
cscope是用来帮助阅读源码的，Emacs for mac osx默认自带cscope的支持。在使用之前，cscope也需要对代码进行索引。在emacs中可以这样做：
C-c s a 设定初始化的目录，一般是你代码的根目录
C-s s I 对目录中的相关文件建立列表并进行索引
C-c s s 寻找符号
C-c s g 寻找全局的定义
C-c s c 看看指定函数被哪些函数所调用
C-c s C 看看指定函数调用了哪些函数
C-c s e 寻找正则表达式
C-c s f 寻找文件
C-c s i 看看指定的文件被哪些文件include

# gdb
## 安装
macOS下默认没有gdb，需要另行下载安装：
``` bash
$ brew tap homebrew/dupes
$ brew install gdb
```
安装完成后，需要在~/.emacs中添加：
``` lisp
(setenv "PATH" "/usr/local/bin:$PATH" t)
 (add-to-list 'exec-path "/usr/local/bin")
```
如果没有这两行，emacs是找不到gdb的。
## 签名
macOS下使用gdb必须签名，否则不能调试。具体步骤是：
* 打开钥匙串访问，点击菜单钥匙串访问 - 证书助理 - 创建证书
* 名称：gdb-cert；身份类型：自签名根证书；证书类型：代码签名；勾选“让我覆盖这些默认值”
* 指定尽量长的有效期
* 一路回车直到“指定用于该证书的位置”，钥匙串：系统
* 一路完成后，在该证书上右键 - 显示简介，代码签名：始终信任

接下来打开终端，输入命令：
```bash
codesign -s gdb-cert /usr/local/bin/gdb
```
打开任务管理器，杀掉进程taskgated。接下来就可以正常使用gdb调试程序了。

## 使用
编译单个文件，不用写makefile脚本，直接执行g++就好了：
`M-x compile RET`把紧接着出现的命令改成：`g++ main.cpp -g -o main.out`
选择菜单Tools - Debugger，启动调试。
命令：
`M-x gdb-many-windows RET`
打开多个窗口。

# markdown支持
下载[markdown-mode.el](http://jblevins.org/projects/markdown-mode/markdown-mode.el)，放到~/.emacs.d/modes/markdown-mode.el，在~/.emacs文件中添加：
``` lisp
(add-to-list 'load-path "~/.emacs.d/modes")  
(autoload 'markdown-mode "markdown-mode.el"  
"Major mode for editing Markdown files" t)  
(setq auto-mode-alist  
      (cons '(".md" . markdown-mode) auto-mode-alist))
```
这样打开.md文件，emacs讲自动使用markdown-model.el。

# 常用基本命令

命令|说明
---|----
C-x C-f|打开文件
C-x k|关闭缓冲区
M-x scroll-down-line|向下滚动一行
M-x scroll-up-line|向上滚动一行
M-]|向后循环滚动buffer（自定义）
M-[|向前循环滚动buffer（自定义）
M-x shell|在buffer中开启命令行
C-x r m (M-x bookmark-set)|设置书签
C-x r l (M-x bookmark-bmenu-list)|列出书签
(M-x book-delete)|删除书签
C-x r b (M-x bookmark-jump)|跳转书签
(M-x bookmark-save)|将所有书签保存至~/.emacs.bmk
M-x load-file ~/.emacs|无需重启，直接加载配置文件并更新
M-x hs-minor-mode|开启折叠模式
s-<up> s-<down>|向上、向下滚动一行


# .emacs文件配置
正文就不贴到这里了，因为经常变化，我放到了[这里](https://github.com/palanceli/blog/blob/master/source/_posts/2016/_0919Emacs/dotemacs)。


