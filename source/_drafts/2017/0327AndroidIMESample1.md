---
layout: post
title: 创建Android下的输入法
date: 2017-03-27 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
本文基于[《在Android下创建输入法（译）》](http://palanceli.com/2017/02/07/2017/0207CreatingAnInputMethod/)演示创建Android系统下的输入法。<!-- more -->

# 创建工程
打开AndroidStudio，选择`Start a new Android Studio project`，填写`Application name`为`AndroidIMESample`；`Company Domain`为`ime.palanceli.com` > Next > 选择`Add No Activity` > Next > Finish。

# 在manifest中添加服务
在app上右键 > New > Service > Service，添加`ClassName`为`AndroidIMESample`，点击`Finish`，来到AndroidManifest.xml，修改自动生成的`service`部分：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.palanceli.ime.androidimesample">

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/AppTheme">
        <service
            android:name=".AndroidIMESampleService"
            android:label="AndroidIMESample"
            android:permission="android.permission.BIND_INPUT_METHOD">
            <intent-filter>
                <action android:name="android.view.InputMethod" />
            </intent-filter>
            <meta-data android:name="android.view.im"
                android:resource="@xml/method" />
        </service>
    </application>

</manifest>
```
在服务中引用了元数据`@xml/method`，接下来添加它。
# 添加元数据
在工程res中创建xml目录，为之添加`XML Resource File`，名称为`method`内容如下：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<input-method xmlns:android="http://schemas.android.com/apk/res/android">
    <subtype
        android:label="English (US)"
        android:imeSubtypeLocale="en_US"
        android:imeSubtypeMode="keyboard" />
</input-method>
```
关于subtype的属性，可以参见[InputMethodSubtype](https://developer.android.com/reference/android/view/inputmethod/InputMethodSubtype.html?hl=zh-cn)：

`label`是该subtype的名字
`imeSubtypeLocale`是该subtype支持的语言类型
`imeSubtypeMode`是它所支持的模式，可以是keyboard或者voice，当输入法被调起是，系统会把用户选择的mode值传给输入法。
# 定义键盘布局
在res上右键 > New > XML > Layout XML File，填写`Layout File name`为`keyboard`，其内容为：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<android.inputmethodservice.KeyboardView
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/keyboard"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_alignParentBottom="true"
    android:keyPreviewLayout ="@layout/preview"
    />
```
继续在res/layout/中添加`Layout resource file`，选择`Available qualifiers`为`Keyboard`，`File name`为`preview`，其内容为：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<TextView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:gravity="center"
    android:background="#ffff00"
    android:textStyle="bold"
    android:textSize="30sp"
    >
</TextView>
```
在res/xml/中添加`qwerty.xml`文件，内容如下：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<Keyboard xmlns:android="http://schemas.android.com/apk/res/android"
    android:keyWidth="10%p"
    android:horizontalGap="0px"
    android:verticalGap="0px"
    android:keyHeight="60dp"
>
    <Row>
        <Key android:codes="113" android:keyLabel="q" android:keyEdgeFlags="left"/>
        <Key android:codes="119" android:keyLabel="w"/>
        <Key android:codes="101" android:keyLabel="e"/>
        <Key android:codes="114" android:keyLabel="r"/>
        <Key android:codes="116" android:keyLabel="t"/>
        <Key android:codes="121" android:keyLabel="y"/>
        <Key android:codes="117" android:keyLabel="u"/>
        <Key android:codes="105" android:keyLabel="i"/>
        <Key android:codes="111" android:keyLabel="o"/>
        <Key android:codes="112" android:keyLabel="p" android:keyEdgeFlags="right"/>
    </Row>
    <Row android:layout_centerHorizontal="true">
        <Key android:codes="97" android:keyLabel="a" android:horizontalGap="5%p" android:keyEdgeFlags="left"/>
        <Key android:codes="115" android:keyLabel="s"/>
        <Key android:codes="100" android:keyLabel="d"/>
        <Key android:codes="102" android:keyLabel="f"/>
        <Key android:codes="103" android:keyLabel="g"/>
        <Key android:codes="104" android:keyLabel="h"/>
        <Key android:codes="106" android:keyLabel="j"/>
        <Key android:codes="107" android:keyLabel="k"/>
        <Key android:codes="108" android:keyLabel="l" android:keyEdgeFlags="right"/>
    </Row>
    <Row>
        <Key android:codes="39" android:keyLabel="'" android:keyEdgeFlags="left"/>
        <Key android:codes="122" android:keyLabel="z"/>
        <Key android:codes="120" android:keyLabel="x"/>
        <Key android:codes="99" android:keyLabel="c"/>
        <Key android:codes="118" android:keyLabel="v"/>
        <Key android:codes="98" android:keyLabel="b"/>
        <Key android:codes="110" android:keyLabel="n"/>
        <Key android:codes="109" android:keyLabel="m"/>
        <Key android:codes="44" android:keyLabel=","/>
        <Key android:codes="46" android:keyLabel="." android:keyEdgeFlags="right"/>
    </Row>
    <Row android:rowEdgeFlags="bottom">
        <Key android:codes="63" android:keyLabel="\?" android:keyWidth="10%p"  android:keyEdgeFlags="left"/>
        <Key android:codes="47" android:keyLabel="/" android:keyWidth="10%p" />
        <Key android:codes="32" android:keyLabel=" " android:keyWidth="40%p" android:isRepeatable="true"/>
        <Key android:codes="-5" android:keyLabel="DEL" android:keyWidth="20%p" android:isRepeatable="true"/>
        <Key android:codes="-4" android:keyLabel="DONE" android:keyWidth="20%p" android:keyEdgeFlags="right"/>
    </Row>
</Keyboard>
```
# 添加服务代码
在app/java/com.palanceli.ime.androidimesample下添加Service，名称为``