---
layout: post
title: 消息循环几个常用类
date: 2017-01-31 09:24:00 +0800
categories: Android学习笔记
tags: 消息循环
toc: true
comments: true
---
# 带有消息循环的子线程 HandlerThread
一个典型的工作线程是这样的：
``` java
// 定义工作线程
public class WorkThread extends Thread{
    public WorkThread(String name){
        super(name);
    }

    public void run(){
        // work...
    }
}

// 使用工作线程
WorkThread workThread = new WorkThread("Work Thread");
workThread.start();
```
这种工作线程适合默默无闻在后台干活，当需要和其他线程有关联或交互的时候，就适合用一个配备了消息循环的子线程来处理了，这就是HandlerThread的用武之地。

假设有一个后台工作线程不断产生数据；前台UI也可以产生数据；这些数据都需要保存起来，我们使用HandlerThread来完成数据保存的工作。过程如下：
![场景1](0131MessageQueue5/img1.png)
* WorkThread中每隔一段时间产生一条数据，之后打印数据信息，并通知DataThread保存。
* MainThread中每次点击按钮就会产生一条数据，并通知DataThread保存。
* DataThread中收到保存请求时，先Sleep片刻表示正在保存，之后打印保存信息。

## 创建DataThread
创建数据线程与创建工作线程没有差别，只是需要拿到其Handler以备后面向线程发送消息：
``` java
// 创建数据线程
mDataThread = new HandlerThread("Data Thread");
mDataThread.start();
// 保存数据线程的Handler
mDataThreadHandler = new Handler(mDataThread.getLooper());
...
```
## 向DataThread发送消息
在工作线程中，每完成一项工作后向数据线程发送消息：
``` java
public class WorkThread extends Thread{
    private int mWorkNum;
    public WorkThread(String name){
        super(name);
    }

    public void run(){
        int tid = android.os.Process.myTid();
        for (; mWorkNum<10; mWorkNum++){
            try {
                Thread.sleep(1000);  // 工作线程完成每次工作
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            System.out.printf("[Work Thread %d] Complete Work %d.\n", tid, mWorkNum);

            // 向数据线程发送消息
            mDataThreadHandler.post(new DataTask(mWorkNum, true));
        }
    }
}
```
在主线程中，每按一次按钮也产生一次数据请求，发送给数据线程：
``` java
mManualWorkNum = 0;
final Button clickMeButton = (Button)findViewById(R.id.ManualWorkButton);
clickMeButton.setOnClickListener(new View.OnClickListener() {
                                     @Override
                                     public void onClick(View view) {
                                         mManualWorkNum++;
                                         mDataThreadHandler.post(new DataTask(mManualWorkNum, false));
                                     }
                                 });
```
## 封装成消息的数据请求
无论是手动还是自动数据请求，都是把DataTask对象封装成一条消息，post给DataThread。
DataTask实现了Runnable接口，并在其中完成数据线程的业务逻辑：
``` java
// 定义在数据线程中的工作任务
public class DataTask implements Runnable{
    private int mWorkNum;
    private boolean mAutoWork = true; // 手动还是自动
    public DataTask(int workNum, boolean autoWork){
        mWorkNum = workNum;
        mAutoWork = autoWork;
    }
    public void run(){
        int tid = android.os.Process.myTid();
        try {
            Thread.sleep(2000);       // 假设需要一段时间保存数据
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        if(mAutoWork)
            System.out.printf("[Data Thread %d] Save auto work %d\n", tid, mWorkNum);
        else
            System.out.printf("[Data Thread %d] Save manual work %d\n", tid, mWorkNum);
    }
}
```
在它的run()函数里，每次完成数据保存，都把当前的线程id打印出来。从log中可以发现：不管是从工作线程还是从主线程发起的post，在保存完成后打印的线程id都是DataThread的tid。
