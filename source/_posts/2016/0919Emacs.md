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

如果仅在Windows下做C++，精通VisualStudio就足够了。如果要跨平台或者跨语言，我认为最好还是能精通Vim或者Emacs。这俩货的学习曲线虽然陡峭，却是唯一在所有平台下通用的编程工具。一旦使顺手了，就不用在不同平台下适应不同的习惯；不用隔段时间就要学习新的编辑器；也不会因为隔段时间不用，让原先已经学会的工具由于版本更新又变得陌生了。

<!-- more -->

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

# ede
在菜单Tools - Project Support(EDE)中我发现了EDE，它属于cedet，也是Emacs for mac osx默认带的。

# .emacs文件配置
``` lisp
;; CC-mode配置
(require 'cc-mode)
(c-set-offset 'inline-open 0)       ;; 在.h文件中写函数，括号不缩进
(c-set-offset 'friend '-)

;; if (a > 0)
;;        {
;;            a = 3;
;;        }
;; 想让这两个括号与if同列，就可以把光标放在”{"上，然后按C-c C-s，emacs会显示它的缩进标签：(substatement-open xxx)。
;; 表明这个缩进所对应的cc-mode标签是substatement-open，然后就可以在style中设置这个substatement-open变量了。
;; 就本例而言，现在它的值应该是+，即缩进一个基本单位。将它设置为0即可。即加入：(substatement-open . 0)。
(c-set-offset 'substatement-open 0)

;; C/C++语言编辑策略
 
(defun my-c-mode-common-hook()
  (setq tab-width 4 indent-tabs-mode nil)
  ;;; hungry-delete and auto-newline
  (c-toggle-auto-hungry-state 1)
  ;;按键定义
  (define-key c-mode-base-map [(control \`)] 'hs-toggle-hiding)     ;; 使用C-q折叠与展开当前段的代码
  (define-key c-mode-base-map [(return)] 'newline-and-indent)       ;; 自动缩进
  (define-key c-mode-base-map [(f7)] 'compile)                  ;; F7编译
  (define-key c-mode-base-map [(meta \`)] 'c-indent-command)        ;; 按照C缩进
  ;;  (define-key c-mode-base-map [(tab)] 'hippie-expand)           ;; 自动补齐
  (define-key c-mode-base-map [(tab)] 'my-indent-or-complete)       ;; 
  (define-key c-mode-base-map [(meta ?/)] 'semantic-ia-complete-symbol-menu)    ;; 弹出菜单来自动补全

;;预处理设置
(setq c-macro-shrink-window-flag t)     ;; 窗口 *Macroexpansion* 不要过高
;; 如果想让c-macro-expand调用另外一个c预处理器命令而不是默认的“/lib/cpp -C”（选项“-C”表示“把注释保留在输出里”），
;; 就需要对变量c-macro-preprocessor做相应的设置。强烈建议保留“-C”选项以免预处理器删掉代码中的注释。
(setq c-macro-preprocessor "cpp -C")    
(setq c-macro-cppflags " ")     ;; 
(setq c-macro-prompt-flag t)        ;; 
(setq hs-minor-mode t)          ;; 代码折叠
;; (setq abbrev-mode t)             ;; 自定义短语
)
(add-hook 'c-mode-common-hook 'my-c-mode-common-hook)   ;; 
 
;; C++语言编辑策略
(defun my-c++-mode-hook()
(setq tab-width 4 indent-tabs-mode nil)
(c-set-style "stroustrup")
;;  (define-key c++-mode-map [f3] 'replace-regexp)
)

;; 配置Semantic的检索范围
(setq semanticdb-project-roots 
(list
(expand-file-name "/")))

;; 自定义自动补齐命令，如果在单词中间就补齐，否则就是tab。
(defun my-indent-or-complete ()
  (interactive)
  (if (looking-at "\\>")
      (hippie-expand nil)
    (indent-for-tab-command))
  )
 
(global-set-key [(control tab)] 'my-indent-or-complete)

;; hippie的自动补齐策略，优先调用了senator的分析结果
(autoload 'senator-try-expand-semantic "senator")
 
(setq hippie-expand-try-functions-list
      '(
        senator-try-expand-semantic
        try-expand-dabbrev
        try-expand-dabbrev-visible
        try-expand-dabbrev-all-buffers
        try-expand-dabbrev-from-kill
        try-expand-list
        try-expand-list-all-buffers
        try-expand-line
        try-expand-line-all-buffers
        try-complete-file-name-partially
        try-complete-file-name
        try-expand-whole-kill
        )
      )

;; F5切换speedbar
(global-set-key [(f5)] 'speedbar)

;; 显示行号
(global-linum-mode t)

;;设置默认宽和高
(setq default-frame-alist
'((height . 40) (width . 150)))

;; 设置默认字体
(set-default-font"-*-Courier New-normal-normal-normal-*-16-*-*-*-m-0-iso10646-1")

 ;; 最近打开文件
 (require 'recentf)
 (setq recentf-max-saved-items 100)
 (recentf-mode 1)
 (add-to-list 'recentf-keep 'file-remote-p) ;; 不要检查远程文件

;; 加载ede
(require 'cedet)
(global-ede-mode 1)

```
<font color='red'>未完待续...</font>

