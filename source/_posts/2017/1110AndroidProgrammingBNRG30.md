---
layout: post
title: 《Android Programming BNRG》笔记三十
date: 2017-11-10 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章继续PhotoGallery，点击图片缩略图后将浏览该图片所在的网页，本章使用两种方法浏览：1、使用系统浏览器；2、使用WebView。

本章要点：
- 
<!-- more -->

# 使用系统浏览器打开缩略图所在网页
这条路径上没有什么新东西，可以复习一下RecyclerView点击item的路径：
① 让PhotoHolder实现接口View.OnClickListener
② 实现接口函数onClick(...)
③ 在构造函数中设置将点击监听设为自己
④ 提供接口设置galleryItem
⑤ 在Adapter::onBindViewHolder(...)将galleryItem赋给Holder
``` java
// PhotoGalleryFragment.java
public class PhotoGalleryFragment extends VisibleFragment {
    ...
    private class PhotoHolder extends RecyclerView.ViewHolder
    implements View.OnClickListener{ // ①
        ...
        private GalleryItem mGalleryItem;

        public PhotoHolder(View itemView){
            ...
            itemView.setOnClickListener(this); // ③
        }

        // ④
        public void bindGalleryItem(GalleryItem galleryItem){
            mGalleryItem = galleryItem;
        }

        @Override
        public void onClick(View v){ // ②
            Intent i = new Intent(Intent.ACTION_VIEW, mGalleryItem.getPhotoPageUri());
            startActivity(i);
        }
    }

    private class PhotoAdapter extends RecyclerView.Adapter<PhotoHolder>{
        ...
        @Override
        public void onBindViewHolder(PhotoHolder photoHolder, int position){
            ...
            photoHolder.bindGalleryItem(galleryItem); // ⑤
            ...
        }
        ...
    }
}
```
使用系统浏览器打开url就在第②步，非常简单，采用ACTION_VIEW对Url构造Intent即可。

# 使用WebView打开网页
## 1.构造布局文件
在布局文件`fragment_photo_page.xml`中添加两个widget——上面是进度条，下面是WebView：
``` xml
<android.support.constraint.ConstraintLayout ...>
    <ProgressBar
        android:id="@+id/progress_bar"
        style="?android:attr/progressBarStyleHorizontal"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginEnd="8dp"
        android:layout_marginStart="8dp"
        app:layout_constraintBottom_toTopOf="@+id/web_view"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent" />

    <WebView
        android:id="@+id/web_view"
        android:layout_width="368dp"
        android:layout_height="495dp"
        android:layout_marginBottom="8dp"
        android:layout_marginEnd="8dp"
        android:layout_marginStart="8dp"
        android:layout_marginTop="8dp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toBottomOf="@+id/progress_bar" />
</android.support.constraint.ConstraintLayout>
```