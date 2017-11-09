---
layout: post
title: 《Android Programming BNRG》笔记二十一
date: 2017-11-01 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章
本章要点：
- 
<!-- more -->

# 播放音频
SoundPool可以加载多条音频文件，并控制同时播放的数量
``` java
mSoundPool = new SoundPool(MAX_SOUNDS, AudioManager.STREAM_MUSIC, 0);//①
...
AssetFileDescriptor afd = mAssets.openFd(sound.getAssetPath());
int soundId = mSoundPool.load(afd, 1); // ②
sound.setSoundId(soundId);
...

Integer soundId = sound.getSoundId();
mSoundPool.play(soundId, 1.0f, 1.0f, 1, 0, 1.0f); // ③

```
## 1.构造SoundPool实例
SoundPool构造函数中三个参数的含义分别为：
1. 同时播放的数量，如果超过这个数字，SoundPool将停止播放队列中首个音频
2. 音频流类型，安卓定义了多种类型的音频流，每种类型有各自独立的音量设置。当关闭音乐音量时，闹钟音量不受影响，就是因为他们属于不同的音频流类型。
3. 最后一个参数被忽略。

## 2.加载音频文件
`SoundPool::load(...)`加载音频文件，以备播放，它返回一个ID，接下来在播放的时候将使用该ID。

## 3.播放音频文件
`SoundPool::play(...)`播放音频文件，其中6个参数分别为：
1. 由`SoundPool::load(...)`返回的soundID
2. 左声道声音
3. 右声道声音
4. 忽略
5. 是否循环播放
6. 播放速率