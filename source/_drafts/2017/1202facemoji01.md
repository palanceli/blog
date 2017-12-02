---
layout: post
title: facemoji的开发过程
date: 2017-12-02 20:00:00 +0800
categories: Unity
tags: Unity
toc: true
comments: true
---
本章记录MGirl的开发过程中需要关注的点。
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

# 权限检查
MGirl需要读取位于sdcard上的人脸识别模型，需要使用摄像头，这两个权限属于dangerous类型，因此除了在AndroidManifest.xml中声明，还需要在运行时再申请：
``` java
private static String[] PERMISSIONS_REQ = {
		Manifest.permission.READ_EXTERNAL_STORAGE,
		Manifest.permission.WRITE_APN_SETTINGS,
		Manifest.permission.CAMERA
};
private static final int REQUEST_CODE_PERMISSION = 2;
...
if(Build.VERSION.SDK_INT <= Build.VERSION_CODES.M){
	ActivityCompat.requestPermissions(this,
			PERMISSIONS_REQ,
			REQUEST_CODE_PERMISSION);
}
```
相关的知识可参见[申请权限](/2017/11/13/2017/1113AndroidProgrammingBNRG33/#3-申请权限)。

> SurfaceView是做什么用的？它的三个构造函数不能像iOS那样重用吗？如果构造函数里逻辑比较多的话，这样危害很大。
[View与SurfaceView](http://www.jianshu.com/p/700defb6f14b)

> 以前在layout里放的都是系统widget，在MGirl里CameraPreivew是自定义的。

>android.hardware.Camera被废弃了，替代它的是什么？

事先应该把libandroid_dlib.so所在的jniLibs拷贝过来