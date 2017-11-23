---
layout: post
title: 《Android Programming BNRG》笔记三十二
date: 2017-11-12 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章引入了一个太阳落山的动画，主要采用属性动画的方式搞定。
本章要点：
- Property Animation
- Animation Set
<!-- more -->

# 属性动画
本节引入的动画非常简单，让太阳从天空落到海平面以下，这是初始状态：
![](1112AndroidProgrammingBNRG32/img01.png)
点击蓝天背景后，太阳落到海平面以下：
![](1112AndroidProgrammingBNRG32/img02.png)

``` java
public class SunsetFragment extends Fragment {
    private View mSceneView;
    private View mSunView;
    private View mSkyView;
    private int mBlueSkyColor;
    private int mSunsetSkyColor;
    private int mNightSkyColor;
    ...
    
    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View view = inflater.inflate(R.layout.fragment_sunset, container,
                false);
        mSceneView = view;
        mSunView = view.findViewById(R.id.sun);
        mSkyView = view.findViewById(R.id.sky);

        Resources resources = getResources();
        mBlueSkyColor = resources.getColor(R.color.blue_sky);
        mSunsetSkyColor = resources.getColor(R.color.sunset_sky);
        mNightSkyColor = resources.getColor(R.color.night_sky);
        // 点击背景播放动画
        mSceneView.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v){
                startAnimation();
            }
        });
        return view;
    }

    private void startAnimation(){
        float sunYStart = mSunView.getTop();
        float sunYEnd = mSkyView.getHeight();
        // ① 移动太阳动画
        ObjectAnimator heightAnimator = ObjectAnimator.ofFloat(
                mSunView, "y", sunYStart, sunYEnd)
                .setDuration(3000);
        // 设置时间插值
        heightAnimator.setInterpolator(new AccelerateInterpolator());

        // ② 蓝天背景色过渡动画
        ObjectAnimator sunsetSkyAnimator = ObjectAnimator.ofInt(mSkyView,
                "backgroundColor", mBlueSkyColor, mSunsetSkyColor)
                .setDuration(3000);
        // 设置颜色插值
        sunsetSkyAnimator.setEvaluator(new ArgbEvaluator());
        // 执行动画
        heightAnimator.start();
        sunsetSkyAnimator.start();
    }
}
```
本例使用的是属性动画，本质上就是使用插值重复调用指定对象的setter方法。例如：`ObjectAnimator.ofFloat(mSunView, "y", 0, 1)`就是使用[0, 1]之间的浮点数，重复调用`mSunView.setY(float)`，这也是①的行为，紧接着它又插入了一个时间差值，用来控制速度。
②是对蓝天背景色做了过渡动画，对颜色设置插值是必须的，因为一个色值是由四个更小的数值拼合而成的，所以从一个色值到另一个色值的过渡并不是两个数值的简单递增或递减，ArgbEvaluator正是完成色值过渡的插值器。

除了变换位置坐标，还有三种变换方式：
1. 旋转，X轴偏移，Y轴偏移
![](1112AndroidProgrammingBNRG32/img03.png)
2. 横向缩放比例，纵向缩放比例
![](1112AndroidProgrammingBNRG32/img04.png)
3. X轴偏移，Y轴偏移
![](1112AndroidProgrammingBNRG32/img05.png)

还可以为属性动画添加时间插值，在本节中设置`AccelerateInterpolator`就是一个加速插值器，Android提供了类型丰富的时间插值器。

# 制作动画脚本
对于更复杂一些的动画，可以采用AnimatorListener或者AnimatorSet，后者更方便一些。因为Listener的代码跨度更大，而AnimatorSet是在一个单子里列出了要播放的动画及出场顺序，就好像是一个动画脚本。
``` java
// SunsetFragment.java
    // 太阳落山动画
    ObjectAnimator heightAnimator = ...
    // 蓝天背景色过渡动画
    ObjectAnimator sunsetSkyAnimator = ...
    // 太阳落山后天黑动画
    ObjectAnimator nightSkyAnimator = ...
    ...
    // 定义和播放动画集合
    AnimatorSet animationSet = new AnimatorSet();
    animationSet.play(heightAnimator)
            .with(sunsetSkyAnimator)
            .before(nightSkyAnimator);
    animationSet.start();
```
“播放动画集合”那一串调用的含义是：“`play` height animator `with` sunset sky animator `before` night sky animator”——在天黑之前，太阳落山同时天近黄昏。

# 延伸阅读
在Android4.4引入了透明动画（transitions framework），可以实现在两个视图之间切换，书里只是提了一嘴。稍后再深入学习。