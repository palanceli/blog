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
- 播放音频
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

# 使用mockito和hamcrest进行UnitTest
## 引入mockito和hamcrest依赖
mockito库用于创建简单的mock对象；hamcrest库用于条件判断的简化处理。首先要在工程中添加对他们的依赖。右键app > Open Module Settings > app > Dependencies > 添加：
![](1101AndroidProgrammingBNRG21/img01.png)
查找并选择mockito和hamcrest：
![](1101AndroidProgrammingBNRG21/img02.png)
![](1101AndroidProgrammingBNRG21/img03.png)
修改Gradle Scripts/build.gradle(Module:app)：
```
...
dependencies {
    compile 'com.android.support:appcompat-v7:26.0.2'
    compile 'com.android.support:recyclerview-v7:26.0.2'
    ...
    testCompile 'org.mockito:mockito-core:2.12.0'
    testCompile 'org.hamcrest:hamcrest-junit:2.0.0.0'
} 
```
`testCompile`是告诉编译器这两个依赖仅用于项目中的`test`模块，这样就不会在apk中打入不需要的代码。

## 为指定的class添加UT
打开待UT的类文件，`⌘+Shift+T` > Create New Test...
![](1101AndroidProgrammingBNRG21/img04.png)
勾选setUp/@Before > OK
![](1101AndroidProgrammingBNRG21/img05.png)
选择.../app/src/test/java/com/bnrg/beatbox：
![](1101AndroidProgrammingBNRG21/img06.png)
其中androidTest是集成测试，它的case是以APK的形式跑在设备上，它需要Android的运行时库；而test是单元测试，它是跑在本机，不依赖Android运行时库。

## 编写UT
### 1.setUp()函数
对于每个待测class，都需要做一些相似的初始化工作：创建待测类的实例和它依赖的其它实例。JUnit为这类工作提供了一个关键字`@Before`，它标识的函数将确保在每个测试用例执行前被执行一次，我们约定俗成地把它标识的函数取名为`setUp()`。

### 2.使用mocked依赖撰写case
在`SoundViewModelTest::setUp()`函数中，首先要创建`SoundViewModel`实例：
``` java
SoundViewModel viewModel = new SoundViewModel(new BeatBox());
```
它的初始化依赖于BeatBox的初始化，如果后者挂了，它的初始化也将失败。这个时候可以使用一个mocked `BeatBox`实例，这个mocked实例其实是`BeatBox`子类的实例，只不过所有的函数都不会干活，因此也就不会挂掉。
``` java
// SoundViewModelTest.java
public class SoundViewModelTest {
    private BeatBox mBeatBox;
    private Sound mSound;
    private SoundViewModel mSubject;

    @Before
    public void setUp() throws Exception {
        mBeatBox = mock(BeatBox.class); // 创建mock实例
        mSound = new Sound("assetPath");
        mSubject = new SoundViewModel(mBeatBox);
        mSubject.setSound(mSound);
    }
    @Test
    public void exposesSoundNameAsTitle(){
        assertThat(mSubject.getTitle(), is(mSound.getName()));
    }
}
```
所有的test case函数需要标注为`@Test`，其中的`assertThat(...)`和`is(...)`均来自hamcrest库。

### 3.运行testcase
右键app/java/<包名>/ > Run 'Test in "beatbox"'，我遇到了错误 `!!! JUnit version 3.8 or later expected`。
修改Gradle Scripts/build.gradle(Module:app)：
```
dependencies {
    ...
    testCompile 'junit:junit:4.12'
    ...
}
```
把原先的`testImplementation`改为`testCompile`即可。