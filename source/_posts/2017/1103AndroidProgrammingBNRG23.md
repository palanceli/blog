---
layout: post
title: 《Android Programming BNRG》笔记二十三
date: 2017-11-03 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章通过修改drawables资源，改变按钮形状和交互：按钮变成圆形，点击变成红色背景
![](1103AndroidProgrammingBNRG23/img01.png)
仅修改资源文件就能搞定，这一点挺酷的。

本章要点：
- drawable资源的定义和使用
- shape drawable的定义和使用
- State List Drawable资源的定义和使用
- 根据屏密度分割apk和mipmap资源
- 9段拉伸图片
<!-- more -->

# shape资源的定义和使用
本节将按钮定义成圆形，首先需要定义drawable资源`res/drawable/button_beat_box_normal.xml`：
``` xml
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="oval">
    <solid android:color="@color/dark_blue"/>
</shape>
```
这是一个形状资源，Android还支持更多形状，可参见[《可绘制对象资源》](https://developer.android.com/guide/topics/resources/drawable-resource.htm)

第二步就是在按钮中应用此资源，`res/values/styles.xml`：
``` xml
<resources>
    ...
    <style name="BeatBoxButton" parent="Widget.AppCompat.Button">
        <item name="android:background">@drawable/button_beat_box_normal</item>
    </style>
</resources>
```
轻松得到如下效果：
![](1103AndroidProgrammingBNRG23/img02.png)

# State List 资源的定义和使用
按钮是一个两态交互控件，分按下和抬起，如果希望两种状态有不同的展现，则需要用到Stat List Drawable了。
① 创建按下资源`res/drawable/button_beat_box_pressed.xml`：
``` xml
<shape xmlns:android="http://schemas.android.com/apk/res/android"
       android:shape="oval">
    <solid android:color="@color/red"/>
</shape>
```
② 创建state list drawable资源`res/drawable/button_beat_box.xml`：
``` xml
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@drawable/button_beat_box_pressed"
          android:state_pressed="true"/>
    <item android:drawable="@drawable/button_beat_box_normal"/>
</selector>
```
它定义了两态下分别对应的drawable资源。
③ 将state list drawable资源应用到按钮`res/values/styles.xml`：
``` xml
<resources>
    ...
    <style name="BeatBoxButton" parent="Widget.AppCompat.Button">
        <item name="android:background">@drawable/button_beat_box</item>
    </style>
</resources>
```
这就完成了两态不同的效果。state list drawable还支持多种类型的状态，包括disabled、focused、activated等，详情可参见[《状态列表》](https://developer.android.com/guide/topics/resources/drawable-resource.html#StateList)。

# Layer List 资源的定义和使用
Layer List可以令多个资源关联到同一个控件上，比如本节当按钮按下的时候，除了希望背景称为红色，还想在外围加一个灰色的环。具体操作只有一步，在`button_beat_box_pressed.xml`文件中添加layer list即可：
``` xml
<layer-list
    xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <shape xmlns:android="http://schemas.android.com/apk/res/android"
               android:shape="oval">
            <solid android:color="@color/red"/>
        </shape>
    </item>
    <item>
        <shape android:shape="oval">
            <stroke android:width="4dp" android:color="@color/gray"/>
        </shape>
    </item>
</layer-list>
```
于是，当按钮被按下时，除了画第一个item，还会在上面再画第二个item。效果如下：
![](1103AndroidProgrammingBNRG23/img03.png)

# Mipmap资源
drawable资源是与屏幕度无关的，其它的比如图片资源会按照屏幕度提供它所支持的个版本的文件，这会导致apk的膨胀，很多和屏密度相关的资源在针对具体设备时其实是没用的。AndroidStudio提供了apk分割的工具:[Build Multiple APKs](https://developer.android.com/studio/build/configure-apk-splits.html)可以将apk分割成供mdpi使用的apk、供hdpi使用的apk……

但是总有例外，比如启动图标。有的launcher会使用更高密度版本的图标作为app的启动图标，这样能让图标看起来更清晰。例如在hdpi的设备下，launcher会使用xdpi图标。因此按照平米度分割apk时，我们不希望这类资源被分割。可以将这类资源放到res/mipmap下：
![](1103AndroidProgrammingBNRG23/img04.png)
建议在mipmap下只放启动图标。

# 9段拉伸的图片
如果指定了9段拉伸，该图片就与屏密度无关了，因此应当放到res/drawable下。9段拉伸的图片和普通图片的差别在于：
1. 文件名以.9.png结尾。
2. 在原图边缘多出1个像素，用来指示拉伸区域。改过名之后用AndroidStudio打开图片，编辑器会支持设置拉伸区域。

如图调整顶部和左侧的黑边以设置拉伸区域
![](1103AndroidProgrammingBNRG23/img05.png)
我发现右侧和底部也有黑边可以设置，这是用来设置文字显示的区域。例如按照上面的设置，运行后的效果是：
![](1103AndroidProgrammingBNRG23/img06.png)

如果把底部的黑边也收窄：
![](1103AndroidProgrammingBNRG23/img07.png)
运行后的效果就变成了：
![](1103AndroidProgrammingBNRG23/img08.png)