---
layout: post
title: 《Android Programming BNRG》笔记二十六
date: 2017-11-06 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章引入了一个带消息循环的子线程，主线程把需要呈现的图片的url发送给该子线程，子线程下载图片，再通知主线程更新界面。
![](1106AndroidProgrammingBNRG26/img01.png)
本章要点：
- Looper/MessageQueue/Message/Handler
- Picasso
- StrictMode
<!-- more -->

# 本章逻辑梳理
梳理一下到[《笔记25·从后台工作线程回归到前台》](/2017/11/05/2017/1105AndroidProgrammingBNRG25/#从后台工作线程回归到前台)为止的流程：
①在主线程，`PhotoGalleryFragment::onCreate(...)`创建并运行子线程`FetchItemsTask`，之后进入消息循环。
②在子线程`FetchItemsTask::doInBackground(...)`下载并解析概要信息，组织成List<GalleryItem>，完成后在主线程调用`FetchItemsTask::onPostExecute(List<GalleryItem> items)`。
③在主线程`FetchItemsTask::onPostExecute(List<GalleryItem> items)`中，将items赋给PhotoGalleryFragment::mItems；为`RecyclerView`设置Adapter，这会导致RecyclerView为可见的item绑定Holder。
④在主线程`PhotoAdapter::onBindViewHolder(...)`中根据位置找到对应的GalleryItem。

> 本节要继续根据概要信息下载缩略图，展现在主界面的RecyclerView上。最直观的做法是在后台继续使用`FetchItemsTask::doInBackground(...)`干这件事，但这么做显然问题很大——所有的缩略图必须全部下载完才能展现出来，而且只能展现一屏。更好的做法是让RecyclerView界面来驱动后台下载线程，显示到哪一格才下载这一格对应的图片。

> 于是，本节创建了另一个线程`ThumbnailDownloader`，维护一个消息循环。从`PhotoAdapter::onBindViewHolder(...)`入手，因为这里是显示的起点。在这里启动另一类工作线程下载图片：

⑤在主线程`PhotoGalleryFragment::onCreate(...)`中创建另一个工作线程`ThumbnailDownloader`，该线程有消息循环，接收下载图片的任务。
⑥在主线程`PhotoAdapter::onBindViewHolder(...)`中调用`mThumbnailDownloader.queueThumbnail(photoHolder, galleryItem.getUrl())`，后者做两件事：1、将＜holder, url＞记入线程；2、向线程ThumbnailDownloader发送MESSAGE_DOWNLOAD消息
⑦在线程ThumbnailDownloader中响应MESSAGE_DOWNLOAD消息，执行`ThumbnailDownloader::handleRequest(...)`，下载缩略图；下载完成后再向主线程的`mResponseHandler`post一个下载完成的消息，该消息由Runnable对象实现回调。
⑧在`Runnable::run()`回调将在主线程完成，它删除ThumbnailDownloader线程中下载完成的＜holder, url＞数据，并为holder绑定下载到的图片。

# MessageQueue/Looper/Message/Handler
## 概念模型
在Android中每个线程可以有一个消息循环，最多也只能有一个消息循环。Looper的角色是消息泵，负责从消息队列MessageQueue中获取消息Message，每个消息对应一个处理对象Handler，由它负责响应消息。

做一个类比：在不同的生产车间里生产不同型号的MP3播放器，每个车间有一套流水线——在传送带上摆放MP3套装，轮到被处理时，生产线会根据套装里指定的播放条目使用播放器来播放。
生产车间就是Android的线程，流水线就是Looper，传送带就是MessageQueue，MP3套装就是Message，其中的MP3播放器就是Handler。生产者在往传送带上放置套装就是发送消息，发送消息的时候可以附带参数，就是播放列表，还可以附带复杂的数据类型参数，这是在套装里附带了闪存。
不同型号的MP3只能在指定的车间里被处理——你可以在A车间里拿一个MP3套装，写入指定的播放列表，但只能把套装放回A车间的流水线上才能被处理。

映射到Android世界的故事是：Android的每个线程最多只有一个消息循环Looper，每个消息循环对应一个MessageQueue，在哪个线程里创建的Handler，它产生的消息只能在本线程被执行。

## 模型实现
### 启动带消息循环的子线程
``` java
...
Handler responseHandler = new Handler();
mThumbnailDownloader = new ThumbnailDownloader<>(responseHandler);//①
mThumbnailDownloader.setThumbnailDownloaderListener(
        new ThumbnailDownloader.ThumbnailDownloaderListener<PhotoHolder>() {
            @Override
            public void onThumbnailDownloaded(PhotoHolder photoHolder, Bitmap bitmap) {
                Drawable drawable = new BitmapDrawable(getResources(), bitmap);
                photoHolder.bindDrawable(drawable);
            }
        }
);
mThumbnailDownloader.start();// ②
mThumbnailDownloader.getLooper();// ③
...
// ④
mThumbnailDownloader.queueThumbnail(photoHolder, galleryItem.getUrl());
```
① 创建`ThumbnailDownloader`的实例，`ThumbnailDownloader`派生自`HandlerThread`。
② 调用`mThumbnailDownloader`的`start()`启动线程
③ 调用`getLooper()`确保线程的mLooper被创建完毕，之所以要等待是因为第④步将依赖mLooper的创建
④ `queueThumbnail(...)`是一个helper方法，最重要是向其handler发送消息，该handler是在子线程中创建的。

> 深入Android源码`HandlerThread::getLooper()`可以看到，如果mLooper没有创建完成，该函数将阻塞：
``` java
public Looper getLooper() {
 //先判断当前线程是否启动了
   if (!isAlive()) {
       return null;
   }
   // If the thread has been started, wait until the looper has been created.
   synchronized (this) {
       while (isAlive() && mLooper == null) {
           try {
               wait();//等待唤醒
           } catch (InterruptedException e) {
           }
       }
   }
   return mLooper;
}

@Override
public void run() {
        mTid = Process.myTid();
        Looper.prepare();
        synchronized (this) {
            mLooper = Looper.myLooper();
            notifyAll(); //唤醒等待线程
        }
        Process.setThreadPriority(mPriority);
        onLooperPrepared();
        Looper.loop();
        mTid = -1;
   }
```
<font color=red>书中说调用③是为了让`HandlerThread::onLooperPrepared()`被调用，从源码来看其实仍然不能保证，它只能保证mLooper被创建，在`HandlerThread::run()`中可以发现mLooper被创建和onLooperPrepared()被调用不能保证原子性。如果在这中间调用了`mThumbnailDownloader.queueThumbnail`依然会导致Handler为空。</font>
### 实现带消息循环的子线程
``` java
...
public class ThumbnailDownloader<T> extends HandlerThread { // ①
    private static final String TAG = "ThumbnailDownloader";
    private static final int MESSAGE_DOWNLOAD = 0;
    private boolean mHasQuit = false;
    private Handler mRequestHandler;
    private ConcurrentMap<T, String> mRequestMap = new ConcurrentHashMap<>();
    private Handler mResponseHandler;
    private ThumbnailDownloaderListener<T> mThumbnailDownloaderListener;

    public interface ThumbnailDownloaderListener<T>{
        void onThumbnailDownloaded(T target, Bitmap thumbnail);
    }

    public void setThumbnailDownloaderListener(ThumbnailDownloaderListener listener){
        mThumbnailDownloaderListener = listener;
    }

    public ThumbnailDownloader(Handler responseHandler){
        super(TAG);
        mResponseHandler = responseHandler;
    }

    @Override
    protected void onLooperPrepared(){  // ②
        mRequestHandler = new Handler(){
            @Override
            public void handleMessage(Message msg){
                if(msg.what == MESSAGE_DOWNLOAD){
                    T target = (T)msg.obj;
                    ...
                    handleRequest(target);
                }
            }
        };
    }

    private void handleRequest(final T target){ // ③
        try{
            final String url = mRequestMap.get(target);
            ...
            byte[] bitmapBytes = new FlickrFetchr().getUrlBytes(url);
            final Bitmap bitmap = BitmapFactory.decodeByteArray(bitmapBytes, 0,
                    bitmapBytes.length);
            // ④
            mResponseHandler.post(new Runnable() {
                @Override
                public void run() {
                    if(mRequestMap.get(target) != url || mHasQuit){
                        return;
                    }
                    mRequestMap.remove(target);
                    mThumbnailDownloaderListener.onThumbnailDownloaded(target, bitmap);
                }
            });
        }...
    }

    public void queueThumbnail(T target, String url){
        ...
            mRequestMap.put(target, url);
            mRequestHandler.obtainMessage(MESSAGE_DOWNLOAD, target)
                    .sendToTarget();//⑤
        ...
    }
    ...
}
```
① 从`HandlerThread`派生子类。
② 在`onLooperPrepared()`中创建Handler实例，该回调是在子线程中执行，因此Handler属于子线程。
③ 实现消息响应函数，完成下载后，再向`mResponseHandler`post一个消息。
④ post `Runnable`对象相当于向mResponseHandler发送一个匿名（不指定ID的）消息，当mResponseHandler接收到该消息后，将在它所在的线程执行`run()`函数。mResponseHandler是在[启动带消息循环的子线程](/2017/11/06/2017/1106AndroidProgrammingBNRG26/#启动带消息循环的子线程)中的①，在主线程创建并传入的，因此它的执行是在主线程。此处达到的效果是当图片下载完成后，通知主线程更新界面。
⑤ `obtainMessage(...)`从空闲消息池中取出消息，并按照参数组装成Message；`sendToTarget()`将消息发送给Handler。
④和⑤ 的做法是等价的，不同点在于：当线程A向线程B发送消息的时候，如果所有操作都在线程B中完成，可以采用⑤，如果两端都有一些代码要执行，采用④可以把这两段的代码写在一起，在逻辑结构上更清晰一些。我是这么理解的。

# Picasso
本节的结尾，介绍了第三方库[Picasso](http://square.github.io/picasso/)，使用该库可以替代本节中ThumbnailDownloader的工作，而且代码更简洁：
``` java
private class PhotoHolder extends RecyclerView.ViewHolder{
    ...
    public void bindGalleryItem(GalleryItem galleryItem){
        Picasso.with(getActivity()).load(galleryItem.getUrl())
        .placeHolder(R.drawable.bill_up_close)
        .into(mItemImageView);
    }
}
```
其中`load(...)`完成下载，尔后将下到的image通过`into(...)`更新到ImageView，通过`placeHolder(...)`设定在图片还未下到时使用什么资源占位。
所以在自己造轮子之前，要充分调研是否已经有更好的东西可用。

# StrictMode
开启StrictMode可以帮助你发现代码中的潜在问题，例如：
- 在主线程中执行的网络操作
- 在主线程中读写磁盘
- Activity在生命周期之外依然活着（俗称Activity泄露）
- 没有关闭的SQLite cursor
- 没有使用SSL/TLS的明文网络传输

在代码中调用`StrictMode.enableDefaults()`可以开启StrictMode。详情参见[《StrictMode》](https://developer.android.com/reference/android/os/StrictMode.html)