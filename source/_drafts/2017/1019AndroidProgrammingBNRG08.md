---
layout: post
title: 《Android Programming BNRG》笔记八
date: 2016-10-19 20:00:00 +0800
categories: Android Programming
tags: BNRG笔记
toc: true
comments: true
---
本章继续CriminalIntent的list部分，并且让list和details公用Fragment的容器、类。
本章要点：
- 抽象一个通用的Fragment，包括xml容器和java实现

<!-- more -->

# 修改fragment的容器、java文件
## 重命名fragment xml容器文件
本节为了让Fragment更通用，把原先的`activity_crime.xml`改名为`activity_fragment.xml`：
![](1019AndroidProgrammingBNRG08/img01.png)
内容如下：
``` xml
<?xml version="1.0" encoding="utf-8"?>
    <android.support.constraint.ConstraintLayout
    android:id="@+id/fragment_container"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
```
AndroidStudio会自动修改引用该资源的代码，比如`CrimeActivity.java`：
``` java
public class CrimeActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        ...
        setContentView(R.layout.activity_fragment); // 自动修改
        ...
    }
}
```
如果没有自动修改，需要手动解决。
## 为通用的Fragment配备对应的java文件
xml容器文件只是在命名上体现出通用性，具体实现更多是在java代码上:
``` java
// SingleFragmentActivity.java
...
public abstract class SingleFragmentActivity extends AppCompatActivity {
    protected abstract Fragment createFragment();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_fragment);

        FragmentManager fm = getSupportFragmentManager();
        Fragment fragment = fm.findFragmentById(R.id.fragment_container);
        if(fragment  == null){
            fragment = createFragment();
            fm.beginTransaction().add(R.id.fragment_container, fragment).commit();
        }
    }
}
```
SingleFragmentActivity在`onCreate(...)`中加载Fragment容器文件，并创建Fragment实例，具体的实例的创建则由派生类来实现：
``` java
// CrimeActivity.java
...
public class CrimeActivity extends SingleFragmentActivity {
    @Override
    protected Fragment createFragment(){
        return new CrimeFragment();
    }
}
```

> 疑问：把Fragment的添加放到基类里，这不会导致所有Fragment共用同一个id么？FragmentManager是绑定在Activity的，也就是说Fragment ID的唯一性只要在具体Activity的范围内即可。

## 向manifest添加新的Activity并置为启动项
在[启动本应用内的Activity的要求](/2016/10/16/2017/1016AndroidProgrammingBNRG05/#启动本应用内的Activity的要求)中提到，如果希望应用的Activity能被启动，必须在其manifest文件中声明该组件。
``` xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bnrg.bnrg07">

    <application
        ... android:theme="@style/AppTheme">
        
        <!-- 新加入的Activity，并设置为启动项 -->
        <activity android:name=".CrimeListActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity android:name=".CrimeActivity">
        </activity>
    </application>

</manifest>
```