---
layout: post
title: 《Android Programming BNRG》笔记十九
date: 2017-10-30 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章加入了无障碍支持。
本章要点：
- TalkBack
<!-- more -->

# TalkBack
TalkBack是Android的读屏服务，它是一个accessibility service，该服务可以读取屏幕上的文字，即使文字不属于自己的app，第三方也可以提供该服务。

在系统中开启该服务后，单击动作的含义是将焦点切换到视图，双击的含义才是正常模式下的点击。当某个视图获得焦点后，左划/右划分别表示将焦点移动到前序视图和后序视图。

## 为没有文字的视图添加读屏支持文字
比如图标按钮，当它获得焦点时，为了让读屏服务也能读出文字，只需要给该视图补充一个`contenDescription`属性既可：
``` xml
    <ImageView
        android:id="@+id/crime_photo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        app:layout_constraintLeft_toLeftOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        app:srcCompat="@mipmap/ic_launcher" 
        android:contentDescription="@string/crime_hpoto_no_image_description"/>
```

## 让视图可获得的焦点
例如ImageView这类视图它原本是不能获得焦点的，为了让它在读屏时也能获得焦点，需要为之添加focusable属性：

``` xml
    <ImageView
        android:id="@+id/crime_photo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        app:layout_constraintLeft_toLeftOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        app:srcCompat="@mipmap/ic_launcher" 
        android:contentDescription="@string/crime_hpoto_no_image_description"
        android:focusable="true"/>
```