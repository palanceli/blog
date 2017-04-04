---
layout: post
title: 创建Android下的输入法(二)——绘制候选窗口
date: 2017-04-03 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
本文在前文的基础上演示绘制候选窗口。<!-- more -->

# 创建候选窗口
在app/java/com.palanceli.ime.androidimesample 右键 > New > Java Class，填写
Name：CandidateView
Superclass：android.view.View
点击OK。编辑其内容为：
``` java
package com.palanceli.ime.androidimesample;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.Log;
import android.view.View;
import java.util.ArrayList;
import java.util.List;

public class CandidateView extends View {
    private List<String> mSuggestions;      // 存放候选列表
    private static final int X_GAP = 10;    // 每个候选之间的间隔
    private Paint mPaint;                   // 用于绘制候选
    private int mCandidateVPadding;         // 候选文字上下边距

    public CandidateView(Context context) {
        super(context);
        Log.d(this.getClass().toString(), "CandidateView: ");

        Resources r = context.getResources();
        mCandidateVPadding = r.getDimensionPixelSize(R.dimen.candidateVerticalPadding);
        setBackgroundColor(r.getColor(R.color.candidateBackground, null)); // 设置背景色
        mPaint = new Paint();
        mPaint.setColor(r.getColor(R.color.candidate, null));               // 设置前景色
        mPaint.setAntiAlias(true);      // 设置字体
        mPaint.setTextSize(r.getDimensionPixelSize(R.dimen.candidateFontHeight));   // 设置字号
        mPaint.setStrokeWidth(0);

        setWillNotDraw(false);  // 覆盖了onDraw函数应清除该标记
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        Log.d(this.getClass().toString(), "onMeasure: ");
        int wMode = MeasureSpec.getMode(widthMeasureSpec);
        int wSize = MeasureSpec.getSize(widthMeasureSpec);

        int measuredWidth = resolveSize(50, widthMeasureSpec);
        final int desiredHeight = ((int)mPaint.getTextSize()) + mCandidateVPadding;

        // 系统会根据返回值确定窗体的大小
        setMeasuredDimension(measuredWidth, resolveSize(desiredHeight, heightMeasureSpec));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        Log.d(this.getClass().toString(), "onDraw: ");
        super.onDraw(canvas);

        if (mSuggestions == null)
            return;

        // 依次绘制每组候选字串
        int x = 0;
        final int count = mSuggestions.size();
        final int height = getHeight();
        final int y = (int) (((height - mPaint.getTextSize()) / 2) - mPaint.ascent());

        for (int i = 0; i < count; i++) {
            String suggestion = mSuggestions.get(i);
            float textWidth = mPaint.measureText(suggestion);
            final int wordWidth = (int) textWidth + X_GAP * 2;

            canvas.drawText(suggestion, x + X_GAP, y, mPaint);
            x += wordWidth;
        }
    }

    public void setSuggestions(List<String> suggestions) {
        // 设置候选字串列表
        if (suggestions != null) {
            mSuggestions = new ArrayList<String>(suggestions);
        }
        invalidate();
        requestLayout();
    }
}
```
其中需要实现关键的函数为：
* onDraw(Canvas canvas);    绘制候选窗
* onMeasure(int widthMeasureSpec, int heightMeasureSpec); 告诉系统候选窗的大小

# 显示候选窗口
在AndroidIMESampleService中添加如下代码：
``` java
public class AndroidIMESampleService extends InputMethodService
        implements KeyboardView.OnKeyboardActionListener {
    ...
    private CandidateView mCandidateView;   // 候选窗
    private StringBuilder m_composeString = new StringBuilder(); // 保存写作串

    @Override public View onCreateCandidatesView(){
        Log.d(this.getClass().toString(), "onCreateCandidatesView: ");
        mCandidateView = new CandidateView(this);
        return mCandidateView;
    }

    @Override public void onStartInput(EditorInfo editorInfo, boolean restarting){
        super.onStartInput(editorInfo, restarting);
        Log.d(this.getClass().toString(), "onStartInput: ");

        m_composeString.setLength(0);
        setCandidatesViewShown(false);
    }

        @Override
    public void onKey(int primaryCode, int[] keyCodes) {
        InputConnection ic = getCurrentInputConnection();
        switch(primaryCode){
            ...
            default:
                char code = (char)primaryCode;
                if(code == ' '){ // 如果收到的是空格
                    if(m_composeString.length() > 0) {  // 如果有写作串，则将首个候选提交上屏
                        ic.commitText(m_composeString, m_composeString.length());
                        m_composeString.setLength(0);
                    }else{                              // 如果没有写作串，则直接将空格上屏
                        ic.commitText(" ", 1);
                    }
                    setCandidatesViewShown(false);
                }else {          // 否则，将字符计入写作串
                    m_composeString.append(code);
                    ic.setComposingText(m_composeString, 1);
                    if(mCandidateView != null){
                        ArrayList<String> list = new ArrayList<String>();
                        list.add(m_composeString.toString());
                        mCandidateView.setSuggestions(list);
                    }
                }
        }
    }
    ...
}
```
其中
* `onCreateCandidatesView()`函数会在输入法初始化时被系统调用，详见[输入法生命周期](http://localhost:4000/2017/02/07/2017/0207CreatingAnInputMethod/#输入法生命周期（The-IME-Lifecycle）)
* `onStartInput(...)`函数会在输入区域获得焦点时被系统调用，详见[处理不同的输入类型](http://localhost:4000/2017/02/07/2017/0207CreatingAnInputMethod/#处理不同的输入类型)
* 修改`onKey(...)`中的主要逻辑为：除空格以外的字符均暂存如写作串，空格用来使首个候选上屏
