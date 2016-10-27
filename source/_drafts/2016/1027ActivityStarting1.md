---
layout: post
title: Activity启动过程学习笔记（一）
date: 2016-10-27 22:36:58 +0800
categories: Android
tags: Activity启动过程
toc: true
comments: true
---
# 找到Launcher启动app的入口点
当在桌面上点击一个应用程序图标时，Luancher响应点击消息，会调用Launcher::onClick(...)。
<!-- more -->
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2458
    public void onClick(View v) {
        ... ...
        Object tag = v.getTag();
        if (tag instanceof ShortcutInfo) {
            onClickAppShortcut(v);
        } else if (tag instanceof FolderInfo) { ... } 
        else ...
    }

// :2591
    protected void onClickAppShortcut(final View v) {
        ... ...
        // Start activities
        startAppShortcutOrInfoActivity(v);
        ... ...
    }
// :2647
    @Thunk void startAppShortcutOrInfoActivity(View v) {
        Object tag = v.getTag();
        ... ...
        boolean success = startActivitySafely(v, intent, tag);
        ... ...
    }
```
接下来以`Launcher::startActivitySafely(...)`为起点进入app启动的分析。
# Step1 Launcher::startActivitySafely(...)
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2938
    public boolean startActivitySafely(View v, Intent intent, Object tag) {
        boolean success = false;
        ... ...
        try {
            success = startActivity(v, intent, tag);  // 🏁
        } catch (ActivityNotFoundException e) { ... }
        return success;
    }
```
其中参数intent中包含Activity组建的信息：
```
action="android.intent.action.MAIN"
category="android.instent.category.LAUNCHER"
cmp="palance.li.activity.MainActivity"
```
这些信息来自应用程序的AndroidManifest.xml文件，是在应用程序安装的时候由PackageManagerService解析并保存的。
# Step2 Launcher::startActivity(...)
``` java
// packages/apps/Launcher3/src/com/android/launcher3/Launcher.java:2871
    private boolean startActivity(View v, Intent intent, Object tag) {
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            ... ...
            if (user == null || user.equals(UserHandleCompat.myUserHandle())) {
                // Could be launching some bookkeeping activity
                startActivity(intent, optsBundle); // 🏁
            } else {...}
            return true;
        } catch (SecurityException e) { ... }
        return false;
    }
```
Launcher继承自Activity，这个`startActivity(...)`就来自该父类。
# Step3 Activity::startActivity(...)
``` java
// frameworks/base/core/java/android/app/Activity.java:4207
    public void startActivity(Intent intent, @Nullable Bundle options) {
        if (options != null) {
            startActivityForResult(intent, -1, options);
        } else {
            // Note we want to go through this call for compatibility with
            // applications that may have overridden the method.
            startActivityForResult(intent, -1);
        }
    }
```