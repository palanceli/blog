---
layout: post
title: 《Android Programming BNRG》笔记三十一
date: 2017-11-11 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章又开始了一个新的应用，本章子类化一个View，处理触摸事件。在主界面上，用户可以拖出一个个的长方形。

本章要点：
- 创建自定义视图
- 在View上绘制
<!-- more -->

# 创建自定义视图
以前创建的都是Activity、Fragment属于Controller的范畴，本节第一次自定义View。
## 1.派生View的子类
`BoxDrawingView`有两个构造函数，分别用于使用代码或从layout文件构造实例，后者会使用带`AttributeSet`参数的版本。
``` java
// BoxDrawingView.java
public class BoxDrawingView extends View {
    public BoxDrawingView(Context context){
        this(context, null);
    }

    public BoxDrawingView(Context context, AttributeSet attrs){
        super(context, attrs);
    }
}
```
## 2.布局文件
`fragment_drag_and_draw.xml`，在文件中必须使用`BoxDrawingView`的全路径名，这样inflater才能找到它。
``` xml
<com.bnrg.draganddraw.BoxDrawingView
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"/>
```
> 我对inflater这个名字的第一印象就是《三体》中的脱水，三体人脱水后变成一张纸，充水就变成了人肉。这里脱水的人皮纸就是xml布局文件，inflater会把它充水变成鲜活的界面布局。

## 3.使用自定义View
``` java
// DragAndDrawFragment.java
public class DragAndDrawFragment extends Fragment {
    ...
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        // 根据布局文件生成View
        View v = inflater.inflate(R.layout.fragment_drag_and_draw, container, false);
        return v;
    }
}
```

# 让View处理触屏事件
覆盖函数`public boolean View::onTouchEvent(MotionEvent event)`，让View的子类处理触屏时间。其中MotionEvent描述了动作发生的位置和行为，行为包括：

Action constants|Description
----|----
ACTION_DOWN|指头触到屏幕
ACTION_MOVE|指头在屏幕上移动
ACTION_UP|指头离开屏幕
ACTION_CANCEL|父视图拦截了触屏事件

# 在View上绘制
和Windows下的绘制有类似的概念，可以将View的设置为无效，这会导致下一轮消息循环中调用其onDraw()函数完成重绘。下面是处理触屏事件和绘制的代码：
``` java
// BoxDrawingView.java
public class BoxDrawingView extends View {
    private static final String TAG = "BoxDrawingView";
    private Box mCurrentBox;
    private List<Box> mBoxen = new ArrayList<>();
    private Paint mBoxPaint;
    private Paint mBackgroundPaint;
    ...
    @Override
    public boolean onTouchEvent(MotionEvent event){
        PointF current = new PointF(event.getX(), event.getY());
        String action = "";
        switch (event.getAction()){
            case MotionEvent.ACTION_DOWN:
                ...
                mCurrentBox = new Box(current); // 新建Box
                mBoxen.add(mCurrentBox);
                break;
            case MotionEvent.ACTION_MOVE:
                ...
                if(mCurrentBox != null){
                    mCurrentBox.setCurrent(current); // 设置Box
                    invalidate();   // 设置无效
                }
                break;
            case MotionEvent.ACTION_UP:
                ...
                mCurrentBox = null; // 完成Box创建
                break;
            case MotionEvent.ACTION_CANCEL:
                ...
                mCurrentBox = null;
                break;
        }
        ...
        return true;
    }

    @Override
    protected void onDraw(Canvas canvas){
        canvas.drawPaint(mBackgroundPaint);
        for(Box box:mBoxen){ // 遍历绘制Box
            float left = Math.min(box.getOrigin().x, box.getCurrent().x);
            float right = Math.max(box.getOrigin().x, box.getCurrent().x);
            float top = Math.min(box.getOrigin().y, box.getCurrent().y);
            float bottom = Math.max(box.getOrigin().y, box.getCurrent().y);
            canvas.drawRect(left, top, right, bottom, mBoxPaint);
        }
    }
}
```