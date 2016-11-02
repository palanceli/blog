---
layout: post
title: 热补丁之AndFix
date: 2016-11-01 22:50:58 +0800
categories: Android
tags: 热补丁
toc: true
comments: true
---
# AndFix的使用
Andfix是阿里巴巴的开源项目，完成热补丁的功能。先写一个测试app，代码树结构如下：<!-- more -->
```
HelloAndroid
├──AndroidManifest.xml
├──Android.mk
├──src
│  └──palance/li/hello
│     └──HelloAndroid.java
└──res
   ├──layout
   │  └──main.xml
   ├──values
   │  └──strings.xml
   └──drawable
      └──icon.png 
```
`HelloAndroid.java`中的代码很简单：
``` java
public class HelloAndroid extends Activity{
    private final static String LOG_TAG = "palance.li.hello.HelloAndroid";

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        TextView tv = (TextView)findViewById(R.id.tv);
        tv.setText("I'm a bug !v_v!");
        Log.i(LOG_TAG, "OnCreate OK.");
    }
}
```
假设函数`HelloAndroid::onCreate(...)`有问题，我们需要热更新该函数。更新之前运行界面如下：
![测试app被patch前](1101AndFix/img01.png)

为了让它具备热更新能力，从[alibaba/AndFix](https://github.com/alibaba/AndFix)可以下到源代码，把`AndFix-master/src`和`AndFix-master/jni`拷贝过来，之后的HelloAndroid代码树结构如下：
``` bash
HelloAndroid
├──AndroidManifest.xml
├──Android.mk
├──src
│  ├──palance/li/hello
│  │  └──HelloAndroid.java
│  └──com/alipay/euler/andfix  <来自AndFix>
│     ├──annotation
│     │  └──MethodReplace.java
│     ├──patch
│     │  ├──Patch.java
│     │  └──PatchManager.java
│     ├──security
│     │  └──SecurityChecker.java
│     ├──util
│     │  └──FileUtil.java
│     ├──AndFix.java
│     ├──AndFixManager.java
│     └──Compat.java
├──jni                         <来自AndFix>
│  ├──andfix.cpp
│  ├──common.h
│  ├──Android.mk
│  ├──Application.mk
│  ├──art
│  │  ├──art_method_replace_4_4.cpp
│  │  ├──art_method_replace_5_0.cpp
│  │  ├──art_method_replace_5_1.cpp
│  │  ├──art_method_replace_6_0.cpp
│  │  ├──art_method_replace_7_0.cpp
│  │  ├──art_method_replace.cpp
│  │  ├──art_4_4.h
│  │  ├──art_5_0.h
│  │  ├──art_5_1.h
│  │  ├──art_6_0.h
│  │  ├──art_7_0.h
│  │  └──art.h
│  └──dalvik
│     ├──dalvik_method_replace.cpp
│     └──dalvik.h
└──res
   ├──layout
   │  └──main.xml
   ├──values
   │  └──strings.xml
   └──drawable
      └──icon.png
```
关于源码编译带JNI的应用程序，可参见`<Android源码>/development/samples/SimpleJNI`
