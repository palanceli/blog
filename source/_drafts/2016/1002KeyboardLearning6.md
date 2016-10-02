---
layout: post
title: 键盘消息处理学习笔记（六）
date: 2016-10-02 23:35:08 +0800
categories: Android
tags: 键盘消息处理学习笔记
toc: true
comments: true
---
承接[《键盘消息处理学习笔记（五）》](http://palanceli.com/2016/10/02/2016/1002KeyboardLearning5/)Step3。通过函数mInputManager.registerInputChannel(...)，把Server端InputChannel注册到InputManager，本文继续深入这个注册函数。
