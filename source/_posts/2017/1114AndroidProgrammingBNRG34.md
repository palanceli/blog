---
layout: post
title: 《Android Programming BNRG》笔记三十四
date: 2017-11-14 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章会把附近图片的经纬度标到地图上。
本章要点：
- 
<!-- more -->

# 获取地图API key
使用Map API需要在AndroidManifest.xml文件中配置一个API key，该API key是用来证明此app已经获得了Google Map Service的授权。在[《Google Maps API》](https://developers.google.com/maps/documentation/)有官方说明。具体操作步骤可以follow AndroidStudio的指示，包名右键 > New > Activity > Gallery
![](1114AndroidProgrammingBNRG34/img01.png)
选择Google Maps Activity：
![](1114AndroidProgrammingBNRG34/img02.png)
这会生成MapsActivity.java和google_maps_api.xml两个文件，打开后者：
``` xml
<resources>
    <!--
    TODO: Before you run your application, you need a Google Maps API key.

    To get one, follow this link, follow the directions and press "Create" at the end:

    https://console.developers.google.com/flows/enableapi?apiid=maps_android_backend&keyType=CLIENT_SIDE_ANDROID&r=84:99:B8:6F:79:C0:48:5E:A0:3D:F5:2B:3A:E3:EC:ED:A3:BE:A6:A8%3Bcom.bnrg.locatr
    ...
    -->
    <string name="google_maps_key" templateMergeStrategy="preserve" translatable="false">AIzaSyBFYVpfsIF7k4MJa3vxDHZDpbmKNS9UPxA</string>
</resources>

```