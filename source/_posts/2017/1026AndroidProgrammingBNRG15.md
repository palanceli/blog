---
layout: post
title: 《Android Programming BNRG》笔记十五
date: 2016-10-26 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章
本章要点：
- 在字符串资源中定义格式化字符
- 使用隐式Intents
<!-- more -->

# 在资源文件中定义格式化字符串
在strings.xml中有如下定义：
``` xml
    <string name="crime_report">%1$s!
    The crime was discovered on %2$s. %3$s, and %4$s
    </string>
```
它使用%1$s、%2$s作为字符串参数的占位符。这些参数在运行时才能确定具体值，使用它的java代码如下：
``` java
String report = getString(R.string.crime_report, mCrime.getTitle(), dateString, solvedString, suspect);
```

# 使用隐式Intents
## 显式Intents vs 隐式Intents
使用显式Intents时，需要指定待启动Activity的名称，如：
``` java
Intent intent = new Intent(getActivity(), CrimePagerActivity.class);
intent.putExtra(EXTRA_CRIME_ID, crimeId);
startActivity(intent);
```
使用隐式Intent时，需要向OS描述要完成什么工作，例如浏览网页、发送数据等。

## 定义隐式Intent
使用隐式Intent来描述要完成的工作，需要指定几个关键信息：
- 要执行的动作（action）。这是由`class Intent`定义的一些常量。例如，浏览一个URL，可以使用`Intent.ACTION_VIEW`；发送数据，可以使用`Intent.ACTION_SEND`。
- 数据的位置。这些数据可能不在本地，例如网页，但是它仍然可以使用URI来指向一个文件，或者指向ContentProvider的一条记录。
- action所服务的数据的类型。这是一个MINE类型，如text/html or audio/mpeg3。如果intent包含数据的位置，则该类型通常是来自该数据。
- 分类（categories）。action是用来描述要做什么，category则用来描述在哪、什么时间或者怎样使用Activity。例如：android.intent.category.LAUNCHER指定一个Activity作为应用程序的启动项；android.intent.category.INFO指定一个Activity向用户提供包信息。

## 匹配Intent的过程
一个用于浏览网页的隐式intent需要指定：action为Intent.ACTION_VIEW 和 网页的Uri。基于这些信息，操作系统将匹配合适的应用以及合适的的Activity（如果匹配到多个，则询问用户选择）。

Activity会在其manifest文件中通过intent filter向操作系统宣告自己适配ACTION_VIEW操作。例如，浏览器应用就需要在其manifest文件中注明：
``` xml
<activity
    android:name=".BrowserActivity"
    android:label="@string/app_name">
    <intent-filter>
        <action
        android:name="android.intent.action.VIEW"/>
        <category
        android:name="android.intent.category.DEFAULT"/>
        <data android:scheme="http"
        android:host="www.bignerdranch.com"/>
    </intent-filter>
</activity>
```
需要给category定义为DEFAULT，才能让该Activity响应隐式intent。action告诉操作系统该activity可以处理什么工作，DEFAULT category则告诉操作系统当OS为某一任务匹配备选时，应当考虑本Activity。

## 本节处理隐式Intent的代码
### 请求发送数据
本节在CrimeFragment长出了一个`crime report`按钮，点击后将发起一个隐式Intent请求
``` java
// CrimeFragment.java
    mReportButton = (Button)v.findViewById(R.id.crime_report);
    mReportButton.setOnClickListener(new View.OnClickListener(){
        public void onClick(View v){
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType("text/plain");
            i.putExtra(Intent.EXTRA_TEXT, getCrimeReport());
            i.putExtra(Intent.EXTRA_SUBJECT, getString(R.string.crime_report_suspect));
            i = Intent.createChooser(i, getString(R.string.send_report));
            startActivity(i);
        }
    });
```
如果系统找到多个可处理ACTION_SEND的应用，就会弹出选择窗口；如果没有弹出选择窗口，有两种可能：1、系统只有一个应用能处理ACTION_SEND；2、系统为隐式Intent设置了默认app。
当有多个备选应用可用时，如果希望总是向用户弹出选择询问窗口，可以如上面代码中调用`Intent.createChooser(...)`。
不过我没有找到系统设置的入口:(

### 请求通讯录并接收返回数据
和请求发送数据不同，请求通讯录后需要从通讯录得到选中的联系人，在请求代码处需要调用`startActivityForResult(...)`：
``` java
// CrimeFragment.java
    mSuspectButton = (Button)v.findViewById(R.id.crime_suspect);
    mSuspectButton.setOnClickListener(new View.OnClickListener(){
        public void onClick(View v){
            Intent i = new Intent(Intent.ACTION_PICK, ContactsContract.Contacts.CONTENT_URI);
            startActivityForResult(i, REQUEST_CONTACT);
        }
    });
```
在[笔记五·从启动的Activity返回数据](http://localhost:4000/2016/10/16/2017/1016AndroidProgrammingBNRG05/#从启动的Activity返回数据)中提到过，当被启动的Activity返回后，启动方Activity会收到`onActivityResult(...)`回调，代码如下：
``` java
// CrimeFragment.java
    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data){
        if(resultCode != Activity.RESULT_OK){
            return;
        }
        if(requestCode == REQUEST_DATE){
            ...
        }else if(requestCode == REQUEST_CONTACT && data != null){
            Uri contactUri = data.getData();

            String[] queryFields = new String[]{    // 待查询字段
                    ContactsContract.Contacts.DISPLAY_NAME
            };
            // 查询
            Cursor cursor = getActivity().getContentResolver()
                    .query(contactUri, queryFields, null, null, null);
            try{
                if(cursor.getCount() == 0){
                    return;
                }
                // 得到第1行第1列数据
                cursor.moveToFirst();
                String suspect = cursor.getString(0);
                mCrime.setSuspect(suspect);
                mSuspectButton.setText(suspect);
            }finally{
                cursor.close();
            }
        }
    }
```
考虑到通用性，通讯录的Activity只返回被选中联系人的uri，需要通过ContentResolver查询到该联系人的具体信息，查询方法同SQLite。

### 通讯录访问权限
只有得到contact app的授权才能访问通讯录数据，contact app具备访问联系人数据库的所有权限，当contact app向父activity返回URI时，它会注明Intent.FLAG_GRANT_READ_URI_PERMISSION，这是一个临时访问权限，确保父Activity只能访问一次数据，有效防止越权读取联系人数据库。

### 请求隐式Intent先检查是否有可响应的包
前面提到过，如果有多个应用可以响应隐式Intent，系统会弹出询问窗口供用户选择；但是有可能不存在候选应用——谁都无法处理该隐式Intent，此时如果直接调用`startActivity(...)`会导致崩溃，解决的办法是先检查是否有候选应用：
``` java
// CrimeFragment.java
    mSuspectButton = (Button)v.findViewById(R.id.crime_suspect);
    Intent pickContact = new Intent(Intent.ACTION_PICK, ContactsContract.Contacts.CONTENT_URI);
    mSuspectButton.setOnClickListener(new View.OnClickListener(){
        public void onClick(View v){
            startActivityForResult(i, REQUEST_CONTACT);
        }
    });
    PackageManager packageManager = getActivity().getPackageManager();
    // 如果没有匹配的应用，把按钮置灰
    if(packageManager.resolveActivity(pickContact, PackageManager.MATCH_DEFAULT_ONLY) == null){
        mSuspectButton.setEnabled(false);
    }
```
PackageManager知道所有安装在本地设备上的应用，调用其`resolveActivity(...)`方法会查找与Intent匹配的Activity，参数`MATCH_DEFAULT_ONLY`把搜索限制在有`CATEGORY_DEFAULT`标志的Activity，确保和`startActivity(Intent)`的逻辑一致。