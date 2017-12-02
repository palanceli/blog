---
layout: post
title: facemoji的开发过程
date: 2017-12-02 20:00:00 +0800
categories: Unity
tags: Unity
toc: true
comments: true
---
本章记录facemoji的开发过程中需要关注的点。
本章要点：
- 

<!-- more -->

faceCapture中
MainActivity文件中
``` java

    @ViewById(R.id.cam_button)	// 这种写法如何解读？
    protected Button mCamButton;

    @Click({R.id.cam_button})	// 这种写法如何解读？
    protected void launchCamera() {
        startActivity(new Intent(this, CameraActivity.class));
    }
```