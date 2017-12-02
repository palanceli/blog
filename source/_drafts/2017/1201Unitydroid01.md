---
layout: post
title: 让Dae在Unity中动起来
date: 2017-12-01 20:00:00 +0800
categories: Unity
tags: Unity
toc: true
comments: true
---
从facerig下到两个[人体3D模型](https://pan.baidu.com/s/1c2Nds1i)，我想把其中的`yexample`弄到unity让她动起来。
![](1201Unitydroid/img01.png)

本章要点：
- 

<!-- more -->

# 创建Project和前期准备
使用Unity创建一个新Project，取名为MGril。点击菜单 > Assets > Import New Asset... > 导入`yexample/anim/_laugh.dae`：
![](1201Unitydroid/img02.png)
按键⌘+s，保存为Assets/MGirlLaugh。

先调好各项导出设置，具体步骤可参见[Unity导出Android设置](/2017/11/30/2017/1130Unity2Android/#project导出设置)，点击`Export`确认都没问题。

# 添加Animation
将Assets中的`_laugh`拖入Scene中，并设置Position，确保照相机对准她：
![](1201Unitydroid/img03.png)

在Hierarchy选中`_laugh`，在Inspector中点击 Add Component > Animation 为`_laugh`添加动画
![](1201Unitydroid/img04.png)
将`_laugh`中的Take 001指定为Animation：
![](1201Unitydroid/img05.png)

点击Unity IDE顶部的三角，即可播放：
![](1201Unitydroid/img06.gif)

# 通过Unity代码控制动画
由于勾选了`Play Automatically`，点击播放会自动启动动画，把该选项勾掉。点击Hierarchy/_laugh > Inspector/Add Component > New Script > 填写Name，创建脚本：
![](1201Unitydroid/img07.png)
``` csharp
public class MGirlLaugh : MonoBehaviour {
	public Animation mAnimation;

	// Use this for initialization
	void Start () {
		
	}

	// Update is called once per frame
	void Update () {
		if (Input.GetKeyDown (KeyCode.G)) {
			Debug.Log ("key down G");
			StartCoroutine ("FireLaugh"); // 调用协同函数
		}
	}

	IEnumerator FireLaugh(){
		Debug.Log ("FireLaugh...");
		mAnimation = GetComponent<Animation> ();
		mAnimation.Play (mAnimation.clip.name);
		Debug.Log (mAnimation.clip.name);
		yield return new WaitForSeconds (mAnimation.clip.length);
	}
}
```
这里使用了一个协同函数`FireLaugh`，关于协同函数的概念，可参见[《协同程序》](https://nuysoft.gitbooks.io/unity-manual/content/Manual/Coroutines.html)。

# 将Unity导入Android
我把文件拷贝写成一个脚本：
``` bash
currDir=$(cd "$(dirname "$0")"; pwd)

projectName="MGirl"
unityName=$projectName"Unity"
androidName=$projectName"Android"

cp -f $unityName/build/$projectName/libs/unity-classes.jar $androidName/app/libs/unity-classes.jar
cp -rf $unityName/build/$projectName/src/main/assets/bin/ $androidName/app/src/main/assets/bin/
cp -rf $unityName/build/$projectName/src/main/jniLibs/ $androidName/app/src/main/jniLibs/
```
只要确保Unity和Android项目目录结构如下：
``` bash
MGirl
├── MGirlAndroid	# Android工程目录
├── MGirlUnity		# Unity工程目录
└── cpfiles.sh		# 文件拷贝脚本
```
每次从Unity导出之后只要执行该脚本即可，第一次需要在AndroidStudio中右键unity-classes.jar > Add As Library...将它添加到依赖中。

# 参考
[《Unity 5.5 手册（中文版）》](https://nuysoft.gitbooks.io/unity-manual/content/)
[《Unity Manual》](https://docs.unity3d.com/Manual/index.html)