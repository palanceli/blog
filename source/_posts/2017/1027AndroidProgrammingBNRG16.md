---
layout: post
title: 《Android Programming BNRG》笔记十六
date: 2016-10-27 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章使用摄像头为Details界面添加照片。
本章要点：
- 摄像头的使用
- Bitmap类的使用
- users-feature声明
<!-- more -->

# 文件和目录相关的Context API返回信息
Android应用的内部存储路径为：/data/data/< package name >
**files相关**
- `File getFilesDir()` 返回/data/data/< package name >/files/的File对象
- `FileInputStream openFileInput(String name)` 打开files/目录下的指定文件以读出数据。
- `FileOutputStream openFileOutput(String name)`打开files/目录下的指定文件以写入数据。
- `String[] fileList()` 获取应用程序私有目录下所有文件名

**custome dir**
- `File getDir(String name, int mode)` 返回应/data/data/< package name >/下指定的文件夹的File对象

**cache**
- `File getCacheDir()` 获取/data/data/< package name >/cache/的File对象，注意要保持该目录整洁。

# 使用FileProvider
在app之间共享文件，需要通过`ContentProvider`将文件暴露出来。这在[《笔记15·请求通讯录并接收返回数据》](http://palanceli.com/2016/10/26/2017/1026AndroidProgrammingBNRG15/#请求通讯录并接收返回数据)使用过。使用`ContentProvider`将文件的URI暴露出去，其它app就可以通过该URI下载或写入文件，通过这种方式确保文件所有者对于数据的可控性。

如果只是希望从其他app接收文件，使用`ContentProvider`略重，可以使用`FileProvider`。本节以拍照为例，让相机把拍摄的照片写入本app，操作步骤如下：
## 1.xml配置要暴露的文件
res右键 > New > Android resource file 在弹出窗口选择Resource type 为XML，创建文件res/xml/files.xml
``` xml
<paths>
    <files-path name="crime_photos" path="."/>
</paths>
```
这个配置的含义是：将私有存储的根目录映射为crime_photos

## 2.AndroidManifest.xml
``` xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bnrg.bnrg07">
    <application ...>
            ...
        <provider
            android:authorities="com.bnrg.bnrg07."
            android:name="android.support.v4.content.FileProvider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/files"/>
	</provider>
    </application>
</manifest>
```
其中authority是一个路径，表示文件存储的位置。
exported="false"表示禁止任何没有经过你授权的人使用你的provider
grantUriPermissions="true"表示当发送其他应用程序权限时，可以添加授权给该权限的URI
最后需要加上配置暴露文件的xml信息。

## 3.启动相机应用
``` java
// CrimeFragment.java
public void onCreate(Bundle savedInstance){
    ...
    mPhotoFile = CrimeLab.get(getActivity()).getPhotoFile(mCrime); // ③
}

@Override
public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstance){
    ...
    mPhotoButton = (ImageButton)v.findViewById(R.id.crime_camera);
    // ① 启动拍照app的隐式Intent
    final Intent captureImage = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
    // 检查是否有拍照的应用
    boolean canTakePhoto = (mPhotoFile != null && 
                captureImage.resolveActivity(packageManager) != null);

    mPhotoButton.setEnabled(canTakePhoto);
    mPhotoButton.setOnClickListener(new View.OnClickListener(){
        @Override
        public void onClick(View v){
            // ② 将本地文件翻译成Uri
            Uri uri = FileProvider.getUriForFile(getActivity(),
                    "com.bnrg.bnrg07.criminalintent.fileprovider", 
                    mPhotoFile);

            captureImage.putExtra(MediaStore.EXTRA_OUTPUT, uri);
            // 得到每一个可以拍照的Activity
            List<ResolveInfo> cameraActivities = 
                                getActivity().getPackageManager().
                                queryIntentActivities(captureImage, 
                                PackageManager.MATCH_DEFAULT_ONLY);

            // 为每一个Activity授权，可以写入Uri
            for(ResolveInfo activity: cameraActivities){
                getActivity().grantUriPermission(
                        activity.activityInfo.packageName,
                        uri, Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            }
            startActivityForResult(captureImage, REQUEST_PHOTO);
        }
    });
}
```
其中①，`MediaStore.ACTION_IMAGE_CAPTURE`将启动拍照app，但是默认并不拍摄全分辨率的照片，而只是一个低分辨率的缩略图，并且将它塞到Intent里通过`onActivityResult(...)`返回；要想得到全分辨率的照片，你需要向隐式Intent的`MediaStore.EXTRA_OUTPUT`写入Uri，这样拍照app将全分辨率的照片写入该Uri。

其中②，`FileProvider.getUriForFile(...)`将本地文件翻译成Uri，拍照app将照片文件写入该Uri，`mPhotoFile`的实际值是`/data/data/<包名>/files/IMG_xxxx.jpg`。

其中③，文件名的生成策略如下：
``` java
// Crime.java
public class Crime {
    ...
    public String getPhotoFilename(){   // 文件名
        return "IMG_" + getId().toString() + ".jpg";
    }
}
// CrimeLab.java
public class CrimeLab {
    ...
    public File getPhotoFile(Crime crime){  // 路径名 + 文件名
        File filesDir = mContext.getFilesDir();
        return new File(filesDir, crime.getPhotoFilename());
    }
}
```

## 4.将拍到的照片显示出来
更新照片的时机有两个：1、当Fragment初始化之后；2、重新拍摄照片之后。
对于1需要注意，在Fragment初始化之后，是不知道自己尺寸的，它最先获得自己的尺寸是在`onCreate(...)` > `onStart(...)` > `onResume(...)`之后。因此如果计算Bitmap应该的大小，要么是在`onResume(...)`里做；要么是在`onCreateView(...)`里做，但是只能粗略估算，本节是采用了后者。这个时候虽然不知道Fragment的具体尺寸，但能知道屏幕尺寸，本节就是根据屏幕尺寸确定照片的缩放比例。
<font color=red>此处待确认</font>

# 加载Bitmap
Bitmap仅对图像文件做了简单的封装，如果加载一个压缩的图像文件，载入到Bitmap对象后，将被完全解压。也就是说对于一个5M的压缩图片，加载到Bitmap的内存中可能会膨胀好几倍！

本节根据设备的尺寸对图像做了缩放，代码如下：
``` java
// PictureUtils.java
public class PictureUtils {
    public static Bitmap getScaledBitmap(String path, int destWidth, int destHeight){
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(path, options);
        float srcWidth = options.outWidth;  // 获得源图尺寸
        float srcHeight = options.outHeight;

        int inSampleSize = 1;               // 计算缩放系数
        if(srcHeight > destHeight || srcWidth > destWidth){
            float heightScale = srcHeight / destHeight;
            float widthScale = srcWidth / destWidth;
            inSampleSize = Math.round(heightScale > widthScale? heightScale: widthScale);
        }
        options = new BitmapFactory.Options();
        options.inSampleSize = inSampleSize;
        // 对源图缩放，获得新图
        return BitmapFactory.decodeFile(path, options);
    }
    ...
}
```

# users-feature声明
当app需要使用依赖设备特性的功能，如本节需要使用相机，最好把这个信息告诉Android系统，当Google Play分发应用时，它会根据这些信息决定是否在特定设备上分发。具体操作是在Manifest.xml中添加如下内容：
``` xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bnrg.bnrg07">
    <uses-feature android:name="android.hardware.camera"
        android:required="false"/>
    ...
</manifest>
```
其中`android:required="false"`表示即使没有摄像头，app也能正常运行，只是某些功能会受限。