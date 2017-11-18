---
layout: post
title: 《Android Programming BNRG》笔记二十八
date: 2017-11-08 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章
本章要点：
- Service
- 检测网络是否可用
- AlarmManager
- PendingIntent
- Notifications
<!-- more -->

# Service
Service用于无需界面展现、交互，只需在后台工作的情况。
<font color=red>为什么不使用线程？</font>

## 创建IntentService
### 1.定义IntentService类
``` java
// PollService.java
public class PollService extends IntentService { // ①
    private static final String TAG = "PollService";

    public static Intent newIntent(Context context){
        return new Intent(context, PollService.class);
    }

    public PollService(){ super(TAG); }

    @Override
    protected void onHandleIntent(Intent intent){ // ②
        Log.i(TAG, "Received an intent: " + intent);
    }
}
```
① 定义派生自IntentService的类。
② 实现`onHandleIntent(...)`方法。

Service的Intent被称为命令，命令被发送给Service通知它完成约定的任务。
当收到第一条命令，IntentService被启动，并启动一个后台线程，将命令排队。在后台线程中，IntentService调用`onHandleIntent(...)`方法依次处理队列中的命令。新的命令可以继续入队，当队列中的命令被处理完，Service将终止和销毁。下图展现了这一过程：
![](1108AndroidProgrammingBNRG28/img01.png)

### 2.在AndroidManifest.xml声明
和Activity类似，Service需要响应来自内部或外部的intents，所以要在`AndroidManifest.xml`中声明：
``` xml
<manifest ...>
    ...
    <application ...>
        ...
        <service android:name=".PollService"/>
    </application>
</manifest>
```

### 3.调用
``` java
Intent i = PollService.newIntent(getActivity());
getActivity().startService(i);
```
<font color=red>不是说好收到第一个命令后，会自动档调起吗？为什么此处变手动挡呢？</font>

# 检测是否有网络可用
在Android系统下，用户可以关闭后台应用的联网权限，这对于控制手机的低功耗运行非常有帮助。应用程序需要对此作出判断，如果网络不可用，就不要再做后续的联网尝试了。
``` java
private boolean isNetworkAvailableAndConnected(){
    ConnectivityManager cm = (ConnectivityManager)
                            getSystemService(CONNECTIVITY_SERVICE);

    // ①如果系统关闭了“允许后台联网的开关”
    boolean isNetworkAvailable = (cm.getActiveNetworkInfo() != null);
    // ②如果开关是打开的，但网络连不上
    boolean isNetConnected = (isNetworkAvailable &&
                            cm.getActiveNetworkInfo().isConnected());
    return isNetConnected;
}
```

在`AndroidManifest.xml`中声明`ACCESS_NETWORK_STATE`才有权限调用以上函数：
``` xml
<manifest ...>
    ...
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>

    <application ...>
        ...
    </application>
</manifest>
```

# 定期被动通知
本节中需要一种机制，能定期发送Service命令，让后台Service工作起来。
一种备选方案是`Handle::sendMessageDelayed(...)`或`Handle::PostDelayed(...)`，这种方案的缺陷在于：如果用户退出了所有Activity，进程也将退出，所有Handle就不会被执行了。
更好的方案是采用`AlarmManager`，它借助系统服务可以向你发送Intents，不管发送方的进程是否还活着。
``` java
private static final long POLL_INTERVAL_MS = TimeUnit.MINUTES.toMillis(1);
...
public static void setServiceAlarm(Context context, boolean isOn){
    Intent i = PollService.newIntent(context);
    PendingIntent pi = PendingIntent.getService(context, 0, i, 0);
    AlarmManager alarmManager = (AlarmManager)
                    context.getSystemService(Context.ALARM_SERVICE);
    if(isOn){
        alarmManager.setRepeating(AlarmManager.ELAPSED_REALTIME,
                SystemClock.elapsedRealtime(),
                POLL_INTERVAL_MS, pi);
    }else{
        alarmManager.cancel(pi);
        pi.cancel();
    }
}
```
## PendingIntent
PendingIntent是一种特殊的Intent，主要的区别在于Intent立刻执行，随所在的activity 消失而消失。而PendingIntent不是立刻执行，可以看作是对intent的包装，它执行的操作实质上是参数Intent传进来的的操作。
通常用`getActivity(...)`、`getBroadcast(...)`、`getService(...)`来得到PendingIntent的实例：
``` java
PendingIntent getService (
    Context context,  // 启动service的context
    int requestCode,  // 用来区分发送端
    Intent intent,    // 描述待启动service的intent
    int flags)        // 控制创建PendingItent的标志位
```
当前Activity并不马上启动PendingIntent所包含的Intent，而是在外部执行PendingIntent时，调用Intent。
由于在PendingIntent中保存了当前App的Context，使它赋予外部App可以如同当前App一样的执行PendingIntent里的 Intent，就算在执行时当前App已经不存在了，也能通过PendingIntent里的Context执行Intent。
Intent一般是用作Activity、Sercvice、BroadcastReceiver之间传递数据，而Pendingintent，一般用在 Notification上。

可以调用`PendingIntent::send()`立刻发出Intent，此时执行发出的是系统，发出者仍然是当前app。可以把PendingIntent转交给其他人发出，此时发出者还是当前app。调用了`cancel()`的PendingIntent，即使`send()`也不会再被发出了。

对于同一个Intentqq请求两次PendingIntent得到的是同一个实例。在flag中传入`PendingIntent::FLAG_NO_CREATE`，当PendingIntent已经存在时，返回该存在的实例，如果不存在则返回null。

## AlarmManager
``` java
void setRepeating (int type,            // alarm类型
                long triggerAtMillis,   // 首次启动alarm的时间
                long intervalMillis,    // 每次间隔毫秒数
                PendingIntent operation)// 要执行的操作
```
其中type可以取值为`RTC_WAKEUP`、`RTC`、`ELAPSED_REALTIME_WAKEUP`或`ELAPSED_REALTIME`。
`RTCxxx`表示绝对时间（System.currentTimeMillis()）
`ELAPSED_REALTIMExxx`表示相对于系统启动的时间（SystemClock.elapsedRealtime()）
`xxx_WAKEUP` 如果设备处于休眠模式，如灭屏时，强制alarm唤醒设备
没有`_WAKEUP` 的版本当设备处于休眠模式时，不会强制唤醒设备

`setRepeating(...)`并不会精确地按照`intervalMillis`唤醒alarm，主要是系统处于功耗的考虑。如果系统有10个应用，分别15分钟唤醒一次，如果他们完全错开，最差的情况会让系统在一小时内被唤醒40次。系统会尽量把他们的唤醒时间安排在一起，比较好的情况是一小时内系统只被唤醒4次了。如果需要绝对精准，可以调用`AlarmManager::setWindow(...)`或`AlarmManager::setExact(...)`

`AlarmManager::Cancel(Pending)`用于取消alarm。

# Notifications
在系统的顶部，有一个通知栏，下拉显示通知列表。但是按照本书的写法，在AndroidO上不能正常运行，会弹出如下错误：
<font color=red>记得贴图</font>
因为在AndroidO中引入了通知频道（Notification Channel）的概念，开发者为需要发送的每个不同的通知类型创建一个通知渠道，所有发布至通知渠道的通知都具有相同的行为。当用户修改任何`重要性`、`声音`、`光`、`振动`、`在锁屏上显示`、`替换免打扰模式`这些特性的行为时，修改将作用于通知渠道。

先来看一下通知的直观表现：
![](1108AndroidProgrammingBNRG28/img02.png)

创建Notification实例可以发送通知。一个Notification至少需要包含：
<font color=red>此处应该贴个图</font>
具体代码如下：
``` java
Resources resources = getResources();
Intent i = PhotoGalleryActivity.newIntent(this);
PendingIntent pi = PendingIntent.getActivity(this, 0, i, 0);
Notification notification = new
        NotificationCompat.Builder(this)
        .setTicker(resources.getString(R.string.new_pictures_title))
        .setSmallIcon(android.R.drawable.ic_menu_report_image)
        .setContentTitle(resources.getString(R.string.new_pictures_title))
        .setContentText(resources.getString(R.string.new_pictures_text))
        .setContentIntent(pi)
        .setAutoCancel(true)
        .build();

NotificationManagerCompat notificationManager =
                        NotificationManagerCompat.from(this);
notificationManager.notify(0, notification);
```