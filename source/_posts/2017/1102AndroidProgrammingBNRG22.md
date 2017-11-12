---
layout: post
title: 《Android Programming BNRG》笔记二十二
date: 2017-11-02 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章介绍了如何修改一个view的style，以及如何通过修改theme影响整个app的展现。
本章要点：
- style的定义和应用
- theme的修改和覆盖
<!-- more -->

# Style
可以简单地修改几个配置完成style的修改。
首先定义style：
styles.xml
``` xml
<resources>
...
    <style name="BeatBoxButton">
        <item name="android:background">@color/dark_blue</item>
    </style>

    <style name="BeatBoxButton.Strong">
        <item name="android:textStyle">bold</item>
    </style>
</resources>
```
在这里添加style，其中`BeatBoxButton.Strong`表示继承自`BeatBoxButton`，还有一种等价的写法是：
``` xml
    <style name="StrongBeatBoxButton"
    parent="@string/BeatBoxButton">
        <item name="android:textStyle">bold</item>
    </style>
```
将定义的应用到Button：
``` xml
    <Button
        style="@style/BeatBoxButton.Strong"
        ...
        tools:text="Sound name"/>
```
很快就能得到背景色为蓝色，字体加粗的按钮：
![](1102AndroidProgrammingBNRG22/img01.png)

# Theme
使用style需要针对每一个wdiget设置，而theme可以定义一套自动应用于app所有wdiget的属性。在[《笔记九·Styles-themes和theme-attributes》](http://localhost:4000/2017/10/20/2017/1020AndroidProgrammingBNRG09/#Styles-themes和theme-attributes)介绍过，theme定义在AndroidManifest.xml：
``` xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bnrg.beatbox">
    <application
        ...
        android:theme="@style/AppTheme">
        ...
    </application>
</manifest>
```
AppTheme定义在res/values/styles.xml，定义如下：
``` xml
<resources>
    <!-- Base application theme. -->
    <style name="AppTheme" parent="Theme.AppCompat">
        <!-- Customize your theme here. -->
        <item name="colorPrimary">@color/red</item>
        <item name="colorPrimaryDark">@color/dark_red</item>
        <item name="colorAccent">@color/gray</item>
    </style>
    ...
</resources>
```
形式上，theme就是一个style，但是它定义的范围比style更广。AppTheme继承自Theme.AppCompat，这是被修改后的版本，AppCompat包含三个默认的theme：
- Theme.AppCompat 黑色主题
- Theme.AppCompat.Light 浅色主题
- Theme.AppCompat.LightDark 灰色主题

本节中使用的属性：
- colorPrimary 是app的主色调，主要应用于toolbar的背景
- colorPrimaryDark 用于状态栏，通常比colorPrimary深一点
- colorAccent 应当与colorPrimary形成鲜明对比，它用于为一些widget涂色，在本节中没有体现出来，因为Button不支持涂色。

通常在设置app主题时应当同时完成这三个属性，他们相互配合形成app的基本配色。

## 覆盖theme中的属性
修改theme中某个属性是个挺麻烦的事，因为没有完整的官方文档解释每个属性的含义，需要自己在代码里找。本节修改的是窗体的背景色，如果只修改某一个widget，可以修改其`android:background`属性，在theme中修改的麻烦在于要先找到该属性对应的关键字。在res/values/styles.xml中，可以看到：`AppTheme`继承自`Theme.AppCompat`
``` xml    
<style name="AppTheme" parent="Theme.AppCompat">
        ...
    </style>
```
⌘+右键`Theme.AppCompat`，找到其定义，发现它又继承自`Base.Theme.AppCompat`，继续往上找，发现他们的继承脉络为：`AppTheme` > `Theme.AppCompat` > `Base.Theme.AppCompat` > `Base.V7.Theme.AppCompat` > `Platform.AppCompat`（中间有多选时选择.../values/values.xml），最后在这里找到了`android:windowBackground`属性，根据字面意思猜测他就是用来定义窗体背景色的，于是在res/values/styles.xml中修改如下：
``` xml
    <style name="AppTheme" parent="Theme.AppCompat">
        ...
        <item name="android:windowBackground">@color/soothing_blue</item>
    </style>
```
这就完成了修改theme中的默认属性。

按照同样的方法，本节还覆盖了按钮的属性：
1. 找到继承关系`AppTheme` > `Theme.AppCompat` > `Base.Theme.AppCompat` > `Base.V7.Theme.AppCompat`
2. 找到按钮风格定义：
``` xml
    <style name="Base.V7.Theme.AppCompat" parent="Platform.AppCompat">
        ...
        <!-- Button styles -->
        <item name="buttonStyle">@style/Widget.AppCompat.Button</item>
        ...
    </style>
```
3. 继续找继承关系`Widget.AppCompat.Button` > `Base.Widget.AppCompat.Button`
4. 找到按钮属性定义：
``` xml
<style name="Base.Widget.AppCompat.Button" parent="android:Widget">
        <item name="android:background">@drawable/abc_btn_default_mtrl_shape</item>
        <item name="android:textAppearance">?android:attr/textAppearanceButton</item>
        <item name="android:minHeight">48dip</item>
        <item name="android:minWidth">88dip</item>
        <item name="android:focusable">true</item>
        <item name="android:clickable">true</item>
        <item name="android:gravity">center_vertical|center_horizontal</item>
```
5. 在res/values/styles.xml中覆盖该属性：
``` xml
    <style name="AppTheme" parent="Theme.AppCompat">
        ...
        <item name="buttonStyle">@style/BeatBoxButton</item>
    </style>

    <style name="BeatBoxButton" parent="Widget.AppCompat.Button">
        <item name="android:background">@color/dark_blue</item>
    </style>
```
`BeatBoxButton`继承自`Widget.AppCompat.Button`，只修改了`android:background`属性。然后在`AppTheme`中将该风格应用到`buttonStyle`。

注意，有的属性是以`android:`为前缀的，表示这些属性是固化在AndroidOS中；有的没有，如`buttonStyle`，因为它来自AppCompat，而不是AndroidOS。

## 包内继承和保外继承
在[Style](/2017/11/02/2017/1102AndroidProgrammingBNRG22/#Style)一节中提到从style的命名可以看出它派生自哪里，它的等价做法是添加`parent`属性显式定义派生源。但是在查找系统style时，可以发现有的名字已经体现了继承关系，但还会显式添加`parent`属性，比如：`style name="Platform.AppCompat" parent="android:Theme">此时优先按照显式声明实现继承关系。

通过命名指定父theme的做法仅在同一个包内生效，一旦跨包继承，例如AppCompat继承android的属性，那就需要显式指定`parent`属性了。