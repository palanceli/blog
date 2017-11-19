---
layout: post
title: 《Android Programming BNRG》笔记二十九
date: 2017-11-09 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章
本章要点：
- 
<!-- more -->

# Broadcast Intents
Broadcast intents和普通的intents类似，不同点在于它可以同时被多个组件接收。
![](1109AndroidProgrammingBNRG29/img01.png)

本节引入Boradcast是因为：尽管Alarm可以在进程被杀掉依然存活，但当遭遇系统重启它就只能中断了，因为没有进程启动Alarm。解决的办法就是让app接收系统的`BOOT_COMPLETED`广播。当系统启动完成后，一定会发出一个`BOOT_COMPLETED`广播。app要做的就是注册并创建standalone broadcast receiver，并实现处理逻辑。

`standalone broadcast receiver`需要在manifest声明，这样即使app没有被启动，依然能接收到它声明的broadcast。与之相对的是`dynamic receiver`，它不需要在manifest声明，而是在代码中完成注册，仅在app处于活动状态时，它才能收到broadcast。

## 创建注册standalone receiver
创建broadcast receiver很简单，就是实现其`onReceive(...)`方法，当一个intent被`StartupReceiver(...)`调用，其对应的broadcast receiver的`onReceive(...)`方法将被回调。
``` java
// StartupReceiver.java
public class StartupReceiver extends BroadcastReceiver {
    private static final String TAG = "StartupReceiver";

    @Override
    public void onReceive(Context context, Intent intent){
        Log.i(TAG, "Received broadcast intent: " + intent.getAction());
    }
}
```
和Service和Activity一样，broadcast receiver必须事先向系统注册，这样当广播发生时，系统才知道调用其回调接口。在`AndroidManifest.xml`中完成注册：
``` xml
<manifest ...>
    ...
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>

    <application ...>
        ...
        <receiver android:name=".StartupReceiver">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED"/>
            </intent-filter>
        </receiver>
    </application>
</manifest>
```
①添加`receiver`标签，以及`intent-filter`属性，这样`StartupReceiver`就可以监听`BOOT_COMPLETED`事件。②这需要相应的权限，因此添加`uses-permission`标签，声明`RECEIVE_BOOT_COMPLETED`权限。

OK了，当收到filter中指定的broadcast，该receiver将被唤醒，并调用其`onReceive(...)`函数，然后receiver将被销毁。

使用`Android Device Montiro`跟踪这一过程：Android Studio > Tools > Android > Android Device Monitor：
![](1109AndroidProgrammingBNRG29/img02.png)
稍后会发现该app会退出。

## 使用receiver
在使用receiver的时候需要注意：
- 不要在`onReceive(...)`中使用异步API，例如注册任何listeners，因为在`onReceive(...)`执行完成后不久，该receiver将被销毁，甚至它所在的app都会退出。
- 不要在`onReceive(...)`中执行长程操作（如网络操作或者大量的I/O），因为该函数是在主线程中执行，长程操作会导致主线程阻塞而引发ANR。

可以将receiver当做逻辑最初的起点，在该函数中启动另一个Activity或者Service等等。

本节在SharedPreference中记录了是否开启alarm，在receiver中判断该记录，如果为true则启动alarm service：
``` java

public class QueryPreferences {
    ...
    private static final String PREF_IS_ALARM_ON = "isAlarmOn";
    ...
    public static boolean isAlarmOn(Context context){
        return PreferenceManager.getDefaultSharedPreferences(context)
                .getBoolean(PREF_IS_ALARM_ON, false);
    }

    public static void setAlarmOn(Context context, boolean isOn){ // ③
        PreferenceManager.getDefaultSharedPreferences(context)
                .edit()
                .putBoolean(PREF_IS_ALARM_ON, isOn)
                .apply();
    }
}

// PollService.java
public class PollService extends IntentService {
    ...
    public static void setServiceAlarm(Context context, boolean isOn){
        ...
        QueryPreferences.setAlarmOn(context, isOn);// ②
    }
    ...
}

// PhotoGalleryFragment.java
public class PhotoGalleryFragment extends Fragment {
    ...
    @Override
    public boolean onOptionsItemSelected(MenuItem item){
        switch(item.getItemId()){
            ...
            case R.id.menu_item_toggle_polling:
                boolean shouldStartAlarm = !PollService.isServiceAlarmOn(getActivity());
                PollService.setServiceAlarm(getActivity(), 
                                        shouldStartAlarm);// ①
                getActivity().invalidateOptionsMenu();
                return true;
            ...
        }
    }
    ...
}

// StartupReceiver.java
public class StartupReceiver extends BroadcastReceiver {
    ...
    @Override
    public void onReceive(Context context, Intent intent){
        ...
        boolean isOn = QueryPreferences.isAlarmOn(context); // ④
        PollService.setServiceAlarm(context, isOn);
    }
}
```
①当用户点击`Start polling`菜单时，设置ServiceAlarm为开启状态。
②③该状态被写入SharedPreference。
④当系统启动后，StartupReceiver收到启动广播，读取SharedPreference，如果ServiceAlarm的启动标记为true，则启动该服务。

## 创建dynamic receiver
dynamic receiver的关键点在于注册/反注册以及实现`onReceive(...)`，本节引入了一个抽象类`VisibleFragment`，并在其`onStart()`和`onStop()`回调中分别完成注册和反注册：
``` java
public abstract class VisibleFragment extends Fragment {
    private static final String TAG = "VisibleFragment";

    @Override
    public void onStart(){
        super.onStart();
        IntentFilter filter = new IntentFilter(PollService.ACTION_SHOW_NOTIFICATION);
        getActivity().registerReceiver(mOnShowNotification, filter);
    }

    @Override
    public void onStop(){
        super.onStop();
        getActivity().unregisterReceiver(mOnShowNotification);
    }

    private BroadcastReceiver mOnShowNotification = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Toast.makeText(getActivity(), "Got a broadcast: " + intent.getAction(),
                    Toast.LENGTH_LONG).show();
        }
    };
}
```
在注册dynamic reciever的时候需要传入一个BoradcastReceiver实例，我们定义内部类并实例化mOnShowNotification。

以上的代码不涉及业务逻辑，具体到本节解决的问题是：
<font color=red>我咋觉得解决的问题和实际方案是反的？他希望仅在应用没有打开的时候得到notification，而到目前为止，必须要求应用在打开的时候才能收到notification！</font>

它在`PollService.java`中当收到新图片时将发送dynamic broadcast：
``` java
// PollService.java
public class PollService extends IntentService {
    ...
    public static final String ACTION_SHOW_NOTIFICATION = "com.bnrg.photogallery.SHOW_NOTIFICATION";
    ...
    @Override
    protected void onHandleIntent(Intent intent){
        ...
        if(resultId.equals(lastResultId)){
            Log.i(TAG, "Got an old result: " + resultId);
        }else{
            Log.i(TAG, "Got a new result: " + resultId);
            doNotifiy();
            sendBroadcast(new Intent(ACTION_SHOW_NOTIFICATION));
        }
        ...
    }
    ...
}
```
再让PhotoGalleryFragment继承自VisibleFragment即可：
``` java
// PhotoGalleryFragment.java
public class PhotoGalleryFragment extends VisibleFragment {
    ...
}
```