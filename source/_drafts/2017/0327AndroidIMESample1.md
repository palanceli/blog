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
打开AndroidStudio，选择`Start a new Android Studio project`，填写
`Application name`：**AndroidIMESample**
`Company Domain`：**ime.palanceli.com**
点击 Next > Next > 选择`Add No Activity` > Finish。

# 在manifest中添加服务
在app上右键 > New > Service > Service，填写
`ClassName`：**AndroidIMESampleService**
点击 Finish。
编辑`AndroidManifest.xml`，修改自动生成的`service`部分：
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
            android:permission="android.permission.BIND_INPUT_METHOD"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.view.InputMethod" />
            </intent-filter>
            <meta-data android:name="android.view.im" 
                android:resource="@xml/method" />
        </service>
    </application>
</manifest>
```
其中`service`的`android:label`属性定义了输入法的名称，在系统输入法列表中看到的名称就是从此处获取到的。在`service`的`meta-data`中引用了元数据`@xml/method`，接下来添加它。
# 添加元数据
在工程res中创建xml目录，然后在res右键 > New > Android resource file 填写
`File name`：**method**
点击OK。修改其内容如下：
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
在res上右键 > New > XML > Layout XML File，填写
`Layout File name`：**keyboard**
点击Finish。修改其内容为：
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
继续在res/layout/中添加Layout XML File，填写
`Layout File name`：**preview**，其内容为：
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
在`AndroidIMESampleService::onCreateInputView()`函数中将根据`res/layout/keyboard.xml`来创建键盘视图，再根据`res/xml/qwerty.xml`将键盘布局创建在该视图上。

# 显示输入窗口
编辑文件app/java/com.palanceli.ime.androidimesample/AndroidIMESampleService.java：
``` java
package com.palanceli.ime.androidimesample;

import android.inputmethodservice.InputMethodService;
import android.inputmethodservice.Keyboard;
import android.inputmethodservice.KeyboardView;
import android.media.AudioManager;
import android.view.KeyEvent;
import android.view.View;
import android.view.inputmethod.InputConnection;

public class AndroidIMESampleService extends InputMethodService
        implements KeyboardView.OnKeyboardActionListener {

    private KeyboardView mKeyboardView; // 对应keyboard.xml中定义的KeyboardView
    private Keyboard mKeyboard;         // 对应qwerty.xml中定义的Keyboard

    @Override
    public View onCreateInputView() {
        // res/layout/keyboard.xml
        mKeyboardView = (KeyboardView)getLayoutInflater().inflate(R.layout.keyboard, null);
        mKeyboard = new Keyboard(this, R.xml.qwerty);  // res/xml/qwerty.xml
        mKeyboardView.setKeyboard(mKeyboard);
        // 将自己设为mKeyboardView的listener,以便接收和处理键盘消息
        mKeyboardView.setOnKeyboardActionListener(this);
        return mKeyboardView;
    }

    @Override
    public void onKey(int primaryCode, int[] keyCodes) {
        InputConnection ic = getCurrentInputConnection();
        switch(primaryCode){
            case Keyboard.KEYCODE_DELETE :
                ic.deleteSurroundingText(1, 0);
                break;
            case Keyboard.KEYCODE_DONE:
                ic.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER));
                break;
            default:
                char code = (char)primaryCode;
                ic.commitText(String.valueOf(code), 1);
        }
    }

    @Override
    public void onPress(int primaryCode) {
    }

    @Override
    public void onRelease(int primaryCode) {
    }

    @Override
    public void onText(CharSequence text) {
    }

    @Override
    public void swipeDown() {
    }

    @Override
    public void swipeLeft() {
    }

    @Override
    public void swipeRight() {
    }

    @Override
    public void swipeUp() {
    }

}
```
在函数`AndroidIMESample::onCreateInputView()`中，它将自己设为键盘视图的listener，因此`AndroidIMESample`必须实现[KeyboardView.OnKeyboardActionListener](https://developer.android.com/reference/android/inputmethodservice/KeyboardView.OnKeyboardActionListener.html)定义的几个接口方法：
* `onKey(int primaryCode, int[] keyCodes)` 向listener发送key press事件
* `onPress(int primaryCode)` 响应用户按下按键的动作
* `onRelease(int primaryCode)` 响应用户松开按键的动作
* `onText(CharSequence text)`   向listener发送一个字符序列
* `swipeDown()`    响应用户从上到下快速扫过的动作
* `swipeLeft()` 响应用户从右到左快速扫过的动作
* `swipeRight()` 响应用户从左到右快速扫过的动作
* `swipeUp()` 响应用户从下到上快速扫过的动作

# 构建apk并安装
点击Android Studio 菜单 Build > Build APK，构建完成后会弹出结果，在Finder中可以查看此APK。
在模拟器中安装该输入法：打开模拟器，将APK直接拖入模拟器完成安装。
在模拟器中点击：设置 > 语言和输入法 > 当前输入法 > 选择键盘，即可看到AndroidIMESample，将之开启。
再重新进入：设置 > 语言和输入法 > 当前输入法，即可选择AndroidIMESample。
随便进入一个可编辑区域，即可看到弹出的键盘。