---
layout: post
title: Android App安装过程学习笔记（二）
date: 2016-10-23 23:51:14 +0800
categories: Android
tags: 安装过程
toc: true
comments: true
---
在学习笔记（一）中，Android系统在启动时，解析packages.xml文件，加载记录在其中的安装信息。接下来将遍历所有可能安装有应用程序的目录，获取到实际的安装信息。
<!-- more -->
以/system/data为例，看一下其下的目录结构：
```
/system/data
├──BasicDreams
│  └──BasicDreams.apk
├──Bluetooth
│  ├──Bluetooth.apk
│  └──lib
... ...
└──webview
   └──webview.apk
```
每个目录下都有一个apk文件。
# Step9: PackageManagerService::scanDirLI(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:5624
    private void scanDirLI(File dir, int parseFlags, int scanFlags, long currentTime) {
        final File[] files = dir.listFiles();
        ... ...
        for (File file : files) {   // 遍历dir下的每个文件
            final boolean isPackage = (isApkFile(file) || file.isDirectory())
                    && !PackageInstallerService.isStageName(file.getName());
            if (!isPackage) {
                continue;
            }
            try {                   // 🏁继续解析Package
                scanPackageLI(file, parseFlags | PackageParser.PARSE_MUST_BE_APK,
                        scanFlags, currentTime, null); 
            } catch (PackageManagerException e) { ... }
        }
    }
```
# Step10: PackageManagerService::scanPackageLI(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:5735
    private PackageParser.Package scanPackageLI(File scanFile, int parseFlags, int scanFlags,
            long currentTime, UserHandle user) throws PackageManagerException {
        ... ...
        parseFlags |= mDefParseFlags;
        PackageParser pp = new PackageParser();
        pp.setSeparateProcesses(mSeparateProcesses);
        pp.setOnlyCoreApps(mOnlyCore);
        pp.setDisplayMetrics(mMetrics);
        ... ...
        final PackageParser.Package pkg;
        ... ...
        // 🏁Step11: 解析scanFile所描述的文件
        pkg = pp.parsePackage(scanFile, parseFlags); 
        ... ...
        // 🏁Step19: 安装pkg描述的应用程序文件，以便获得它的组件信息，并为它分配LinuxUID
        PackageParser.Package scannedPkg = scanPackageLI(pkg, parseFlags, scanFlags
                | SCAN_UPDATE_SIGNATURE, currentTime, user);
        ... ...
        return scannedPkg;
    }
```
# Step11: PackageParser::parsePackage(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:752
    public Package parsePackage(File packageFile, int flags) throws PackageParserException {
        if (packageFile.isDirectory()) {
            // 解析该目录中的所有APK文件，把他们当做一个单独的package来处理
            return parseClusterPackage(packageFile, flags);
        } else {
            return parseMonolithicPackage(packageFile, flags); // 🏁
        }
    }
```
根据要解析的是一个目录还是一个文件，这里分了两枝来处理。如果是一个文件，`parseClusterPackage(...)`会解析其中的所有APK文件，把目录当做一个package来处理。我们假设待处理的是单个apk文件，进入`parseMonolithicPackage(...)`。

# Step12: PackageParser::parseMonollithicPackage(...)
`parseMonolithicPackageLite(...)`将AndroidManifest.xml中的概要信息提取出来，并封装成一个轻量级对象PackageLite。
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:827
    public Package parseMonolithicPackage(File apkFile, int flags) throws PackageParserException {
        if (mOnlyCoreApps) { // 🏁此处解析出概要数据，封装为轻量级对象
            final PackageLite lite = parseMonolithicPackageLite(apkFile, flags);
            ... ...
        }
        // 这的逻辑有点奇怪，前面封装的lite并没有在下面派上用场
        final AssetManager assets = new AssetManager();
        ... ...
            // 🏁Step14 
            final Package pkg = parseBaseApk(apkFile, assets, flags);
            pkg.codePath = apkFile.getAbsolutePath(); 
            return pkg;
        ... ...
    }
```
# Step13: PackageParser::parseMonolithicPackageLite(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:657
    private static PackageLite parseMonolithicPackageLite(File packageFile, int flags)
            throws PackageParserException {
        // 🏁解析Apk的轻量级数据，并封装成PackageLite对象
        final ApkLite baseApk = parseApkLite(packageFile, flags); 
        final String packagePath = packageFile.getAbsolutePath();
        return new PackageLite(packagePath, baseApk, null, null, null);
    }
```
## Step13.1: PackageParser::parseApkLite(...)
这些概要信息包含：package name, split name, install location等。
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:1155
    public static ApkLite parseApkLite(File apkFile, int flags)
            throws PackageParserException {
        final String apkPath = apkFile.getAbsolutePath();
        ... ... // 将解析到的轻量级数据封装成ApkLite对象并返回
            return parseApkLite(apkPath, res, parser, attrs, flags, signatures);
        ... ...
    }
```
## Step13.2: PackageParser::parseApkLite(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:1274
    private static ApkLite parseApkLite(String codePath, Resources res, XmlPullParser parser,
            AttributeSet attrs, int flags, Signature[] signatures) throws IOException,
            XmlPullParserException, PackageParserException {
        // 🏁解析并生成<package, split>的pair
        final Pair<String, String> packageSplit = parsePackageSplitNames(parser, attrs, flags); 

        int installLocation = PARSE_DEFAULT_INSTALL_LOCATION;
        int versionCode = 0;
        int revisionCode = 0;
        boolean coreApp = false;
        boolean multiArch = false;
        boolean extractNativeLibs = true;
        // 解析这些标签
        for (int i = 0; i < attrs.getAttributeCount(); i++) {
            final String attr = attrs.getAttributeName(i);
            if (attr.equals("installLocation")) {
                installLocation = attrs.getAttributeIntValue(i,
                        PARSE_DEFAULT_INSTALL_LOCATION);
            } else if (attr.equals("versionCode")) {
                versionCode = attrs.getAttributeIntValue(i, 0);
            } else if (attr.equals("revisionCode")) {
                revisionCode = attrs.getAttributeIntValue(i, 0);
            } else if (attr.equals("coreApp")) {
                coreApp = attrs.getAttributeBooleanValue(i, false);
            }
        }
        ... ...
        // 将解析到的数据封装成ApkLite对象
        return new ApkLite(codePath, packageSplit.first, packageSplit.second, versionCode,
                revisionCode, installLocation, verifiers, signatures, coreApp, multiArch,
                extractNativeLibs);
    }
```
## Step 13.3: PackageParser::parsePackageSplitNames(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:123
    private static Pair<String, String> parsePackageSplitNames(XmlPullParser parser,
            AttributeSet attrs, int flags) throws IOException, XmlPullParserException,
            PackageParserException {

        int type;
        while ((type = parser.next()) != XmlPullParser.START_TAG
                && type != XmlPullParser.END_DOCUMENT) {
        }

        if (type != XmlPullParser.START_TAG) {...}
        if (!parser.getName().equals("manifest")) {... }
        // 找到manifest/package
        final String packageName = attrs.getAttributeValue(null, "package");
        if (!"android".equals(packageName)) {
            final String error = validateName(packageName, true, true);
            if (error != null) {...}
        }
        // 找到manifest/split
        String splitName = attrs.getAttributeValue(null, "split");
        if (splitName != null) {
            if (splitName.length() == 0) {
                splitName = null;
            } else {
                final String error = validateName(splitName, false, false);
                if (error != null) {...}
            }
        }
        // 生成<package, split>的pair
        return Pair.create(packageName.intern(),
                (splitName != null) ? splitName.intern() : splitName);
    }
```
# 一个AndroidManifest.xml的样例
有必要抓一个AndroidManifest.xml拿来看一眼，一般的apk解压后，AndroidManifest.xml文件是需要反编译的，可以下一个AXMLPrinter2.jar，执行：
``` bash
java -jar AXMLPrinter2.jar AndroidManifest.xml
```
即可打印明文：
``` xml
<?xml version="1.0" encoding="utf-8"?>
<manifest
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:versionCode="590"
    android:versionName="8.5"
    android:installLocation="1"
    package="com.sohu.inputmethod.sogou"
    platformBuildVersionCode="23"
    platformBuildVersionName="6.0-2704002"
    >
    <uses-sdk
        android:minSdkVersion="11"
        android:targetSdkVersion="23"
        >
    </uses-sdk>
    <supports-screens
        android:anyDensity="true"
        android:smallScreens="true"
        android:normalScreens="true"
        android:largeScreens="true"
        android:xlargeScreens="true"
        >
    </supports-screens>
    <uses-permission
        android:name="com.xiaomi.permission.AUTH_SERVICE"
        >
    </uses-permission>
    ... ...
    <uses-feature
        android:name="android.hardware.telephony.gsm"
        android:required="false"
        >
    </uses-feature>
    <uses-permission
        android:name="android.permission.READ_EXTERNAL_STORAGE"
        >
    </uses-permission>
    <uses-feature
        android:name="android.hardware.camera"
        android:required="false"
        >
    </uses-feature>
    <application
        android:label="@7F0B0329"
        android:icon="@7F02041F"
        android:name="com.sohu.inputmethod.sogou.SogouAppApplication"
        android:process="com.sohu.inputmethod.sogou"
        android:allowBackup="false"
        >
        <service
            android:label="@7F0B0329"
            android:icon="@7F02041F"
            android:name="com.sohu.inputmethod.sogou.SogouIME"
            android:permission="android.permission.BIND_INPUT_METHOD"
            >
            <intent-filter
                android:priority="100"
                >
                <action
                    android:name="android.view.InputMethod"
                    >
                </action>
                <category
                    android:name="android.intent.category.DEFAULT"
                    >
                </category>
            </intent-filter>
            <meta-data
                android:name="android.view.im"
                android:resource="@7F060009"
                >
            </meta-data>
        </service>
        ... ...
        <receiver
            android:name="com.sohu.inputmethod.multimedia.MultiMediaTransferReceiver"
            >
        </receiver>
        <activity
            android:label="@7F0B039E"
            android:name="com.sohu.inputmethod.settings.AccountList"
            android:excludeFromRecents="true"
            android:configChanges="0x000000A0"
            >
            <intent-filter
                >
                <action
                    android:name="android.intent.action.MAIN"
                    >
                </action>
            </intent-filter>
        </activity>
        ... ...
        <activity
            android:label="@7F0B0329"
            android:name="com.sohu.inputmethod.sogou.SogouIMESettings"
            android:excludeFromRecents="true"
            android:configChanges="0x000004A0"
            >
            <intent-filter
                >
                <action
                    android:name="android.intent.action.MAIN"
                    >
                </action>
            </intent-filter>
        </activity>
        <service
            android:name="com.sohu.inputmethod.sogou.push.PushReceiveService"
            >
            <intent-filter
                >
                <action
                    android:name="com.sogou.pushservice.action.message.RECEIVE"
                    >
                </action>
                ... ...
            </intent-filter>
        </service>
        <receiver
            android:name="com.sogou.udp.push.SystemReceiver"
            >
        </receiver>
        ... ...
        <service
            android:name="sogou.mobile.explorer.hotwords.floatingpopup.PushFloatingWindowService"
            android:exported="false"
            android:process="sogou.mobile.explorer.hotwords"
            >
        </service>
        <meta-data
            android:name="SdkVersion"
            android:value="3.7"
            >
        </meta-data>
        ... ...
        <meta-data
            android:name="QBSDKAppKey"
            android:value="ACR8D+367NCAy7ZECvRBVmMC"
            >
        </meta-data>
    </application>
</manifest>
```
# Step14: PackageParser::parseBaseApk(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:864
    private Package parseBaseApk(File apkFile, AssetManager assets, int flags)
            throws PackageParserException {
        final String apkPath = apkFile.getAbsolutePath();

        String volumeUuid = null;
        if (apkPath.startsWith(MNT_EXPAND)) {
            final int end = apkPath.indexOf('/', MNT_EXPAND.length());
            volumeUuid = apkPath.substring(MNT_EXPAND.length(), end);
        }
        ... ...
        final int cookie = loadApkIntoAssetManager(assets, apkPath, flags);

        Resources res = null;
        XmlResourceParser parser = null;
        ... ...
            res = new Resources(assets, mMetrics, null);
            assets.setConfiguration(0, 0, null, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    Build.VERSION.RESOURCES_SDK_INT);
            parser = assets.openXmlResourceParser(cookie, ANDROID_MANIFEST_FILENAME);

            final String[] outError = new String[1];
            // 🏁调用重载函数继续解析
            final Package pkg = parseBaseApk(res, parser, flags, outError); 
            ... ...
            pkg.volumeUuid = volumeUuid;
            pkg.applicationInfo.volumeUuid = volumeUuid;
            pkg.baseCodePath = apkPath;
            pkg.mSignatures = null;

            return pkg;
        ... ...
    }
```
# Step15: PackageParser::parseBaseApk(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:1354
    private Package parseBaseApk(Resources res, XmlResourceParser parser, int flags,
            String[] outError) throws XmlPullParserException, IOException {
        ... ...
            Pair<String, String> packageSplit = parsePackageSplitNames(parser, attrs, flags);
            pkgName = packageSplit.first;
            splitName = packageSplit.second;
        ... ...
        int type;
        ... ...
        final Package pkg = new Package(pkgName);
        boolean foundApp = false;
        // 解析manifest标签中的android:sharedUserId属性。如果设置了该属性，表示app
        // 要与其它应用程序共享一个LinuxUID。
        TypedArray sa = res.obtainAttributes(attrs,
                com.android.internal.R.styleable.AndroidManifest);
        ... ...
        String str = sa.getNonConfigurationString(
                com.android.internal.R.styleable.AndroidManifest_sharedUserId, 0);
        if (str != null && str.length() > 0) {
            ... ...
            pkg.mSharedUserId = str.intern(); // 将共享UID提取出来
            ... ...
        }
        ... ...
        sa.recycle();
        ... ...
        int outerDepth = parser.getDepth();
        // 解析uses-permission和application标签，它们均为manifest的子标签
        while ((type = parser.next()) != XmlPullParser.END_DOCUMENT
                && (type != XmlPullParser.END_TAG || parser.getDepth() > outerDepth)) {
            ... ...
            String tagName = parser.getName();
            if (tagName.equals("application")) {
                ... ...
                // 🏁 Step16: 解析每个app必须存在的application标签
                if (!parseBaseApplication(pkg, res, parser, attrs, flags, 
                outError)) { 
                    return null;
                }
            } ... ...
            else if (tagName.equals("uses-permission")) {
                // uses-permission对应资源访问权限，如果一个app申请了某资源访问权限，
                // 它就会获得一个对应的Linux用户组ID。一个app可以申请多个资源访问权限，
                // 故它的配置文件中可以存在多个uses-permission标签，这些标签有一个
                // name属性，用来描述对应的资源访问权限的名称。
                if (!parseUsesPermission(pkg, res, parser, attrs)) {
                    return null;
                }
            } ... ...
        }
        ... ...
        return pkg;
    }
```
# Step16: PackageParser::parseBaseApplication(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:2406
    private boolean parseBaseApplication(Package owner, Resources res,
            XmlPullParser parser, AttributeSet attrs, int flags, String[] outError)
        throws XmlPullParserException, IOException {
        ... ...
        final int innerDepth = parser.getDepth();
        int type;
        while ((type = parser.next()) != XmlPullParser.END_DOCUMENT
                && (type != XmlPullParser.END_TAG || parser.getDepth() > innerDepth)) {
            ... ...
            // 分别获得四大组件的配置信息
            String tagName = parser.getName();
            if (tagName.equals("activity")) {
                Activity a = parseActivity(owner, res, parser, attrs, flags, outError, false,
                        owner.baseHardwareAccelerated);
                ... ...
                owner.activities.add(a);

            } else if (tagName.equals("receiver")) {
                Activity a = parseActivity(owner, res, parser, attrs, flags, outError, true, false);
                ... ...
                owner.receivers.add(a);

            } else if (tagName.equals("service")) {
                Service s = parseService(owner, res, parser, attrs, flags, outError);
                ... ...
                owner.services.add(s);

            } else if (tagName.equals("provider")) {
                Provider p = parseProvider(owner, res, parser, attrs, flags, outError);
                ... ...
                owner.providers.add(p);

            } ... ...
        }
        ... ...
        return true;
    }
```
回到Step10中，在调用PackageParser::parsePackage(...)解析完应用程序的AndroidManifest.xml文件后，接下来调用PackageManagerService::scanPackageLI获得解析到的app的组件配置信息，并为app分配UID。
# Step17: PackageManagerService::scanPackageLI(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java
// :477
// 系统中已经安装的app都是用一个Package对象来描述，这些对象保存在mPackages这个HashMap中，
// 该HashMap是以Package的名称为关键字
    final ArrayMap<String, PackageParser.Package> mPackages =
            new ArrayMap<String, PackageParser.Package>();
// :528
// 每个已经安装的app都包含若干Activity、Broadcast Receiver、Service和
// Content Provider组件，这些组件信息分别保存在下面的变量中
    // All available activities, for your resolving pleasure.
    final ActivityIntentResolver mActivities =
            new ActivityIntentResolver();

    // All available receivers, for your resolving pleasure.
    final ActivityIntentResolver mReceivers =
            new ActivityIntentResolver();

    // All available services, for your resolving pleasure.
    final ServiceIntentResolver mServices = new ServiceIntentResolver();

    // All available providers, for your resolving pleasure.
    final ProviderIntentResolver mProviders = new ProviderIntentResolver();

    // Mapping from provider base names (first directory in content URI codePath)
    // to the provider information.
    final ArrayMap<String, PackageParser.Provider> mProvidersByAuthority =
            new ArrayMap<String, PackageParser.Provider>();

// :6466
    private PackageParser.Package scanPackageLI(PackageParser.Package pkg, int parseFlags,
            int scanFlags, long currentTime, UserHandle user) throws PackageManagerException {
        boolean success = false;
        ... ...
            // 🏁
            final PackageParser.Package res = scanPackageDirtyLI(pkg, parseFlags, scanFlags,
                    currentTime, user);
            success = true;
            return res;
        ... ...
    }
```
# Step18: PackageManagerService::scanPackageDirtyLI(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java : 6481
private PackageParser.Package scanPackageDirtyLI(PackageParser.Package pkg, int parseFlags,
            int scanFlags, long currentTime, UserHandle user) throws PackageManagerException {
        ... ...
        SharedUserSetting suid = null;
        PackageSetting pkgSetting = null;
        ... ...
        // 为pkg所描述的应用程序分配UID
        synchronized (mPackages) {
            if (pkg.mSharedUserId != null) {// 检查pkg是否指定了要与其它app共享UID
                // 🏁Step19 pkg.mSharedUserId是“shared-user name”，系统的
                // 共享用户信息保存在mSharedUser中，回顾
                // Step7 Settings::readSharedUserLPw(...)。此处根据name找到
                // SharedUserSetting对象
                suid = mSettings.getSharedUserLPw(pkg.mSharedUserId, 0, 0, true);
                ... ...
            }
            ... ...
            // 🏁Step20 为pkg描述的应用程序分配一个UID
            pkgSetting = mSettings.getPackageLPw(pkg, origPackage, realName, suid, destCodeFile,
                    destResourceFile, pkg.applicationInfo.nativeLibraryRootDir,
                    pkg.applicationInfo.primaryCpuAbi,
                    pkg.applicationInfo.secondaryCpuAbi,
                    pkg.applicationInfo.flags, pkg.applicationInfo.privateFlags,
                    user, false);
            ... ...
        }

        ... ...
        // writer
        synchronized (mPackages) {
            // We don't expect installation to fail beyond this point

            // Add the new setting to mSettings
            mSettings.insertPackageSettingLPw(pkgSetting, pkg);
            // Add the new setting to mPackages
            // 将pkg指向的Package对象保存在mPackages中
            mPackages.put(pkg.applicationInfo.packageName, pkg);
            ... ...
            // 将pkg描述的应用程序的Content Provider组件配置信息保存在mProvidersByAuthority
            int N = pkg.providers.size();
            StringBuilder r = null;
            int i;
            for (i=0; i<N; i++) {
                PackageParser.Provider p = pkg.providers.get(i);
                p.info.processName = fixProcessName(pkg.applicationInfo.processName,
                        p.info.processName, pkg.applicationInfo.uid);
                mProviders.addProvider(p);
                p.syncable = p.info.isSyncable;
                if (p.info.authority != null) {
                    String names[] = p.info.authority.split(";");
                    p.info.authority = null;
                    for (int j = 0; j < names.length; j++) {
                        if (j == 1 && p.syncable) {
                            // We only want the first authority for a provider to possibly be
                            // syncable, so if we already added this provider using a different
                            // authority clear the syncable flag. We copy the provider before
                            // changing it because the mProviders object contains a reference
                            // to a provider that we don't want to change.
                            // Only do this for the second authority since the resulting provider
                            // object can be the same for all future authorities for this provider.
                            p = new PackageParser.Provider(p);
                            p.syncable = false;
                        }
                        if (!mProvidersByAuthority.containsKey(names[j])) {
                            mProvidersByAuthority.put(names[j], p);
                            if (p.info.authority == null) {
                                p.info.authority = names[j];
                            } else {
                                p.info.authority = p.info.authority + ";" + names[j];
                            }
                            ... ...
                        } ... ...
                    }
                }
                ... ...
            }
            ... ...
            // 将pkg描述的应用程序的Service组件配置信息保存在mServices中
            N = pkg.services.size();
            r = null;
            for (i=0; i<N; i++) {
                PackageParser.Service s = pkg.services.get(i);
                s.info.processName = fixProcessName(pkg.applicationInfo.processName,
                        s.info.processName, pkg.applicationInfo.uid);
                mServices.addService(s);
                ... ...
            }
            ... ...
            // 将pkg描述的应用程序的Broadcast Receiver组件配置信息保存在mReceivers
            N = pkg.receivers.size();
            r = null;
            for (i=0; i<N; i++) {
                PackageParser.Activity a = pkg.receivers.get(i);
                a.info.processName = fixProcessName(pkg.applicationInfo.processName,
                        a.info.processName, pkg.applicationInfo.uid);
                mReceivers.addActivity(a, "receiver");
                ... ...
            }
            ... ...
            // 将pkg描述的应用程序的Activity组件配置信息保存在mActivities
            N = pkg.activities.size();
            r = null;
            for (i=0; i<N; i++) {
                PackageParser.Activity a = pkg.activities.get(i);
                a.info.processName = fixProcessName(pkg.applicationInfo.processName,
                        a.info.processName, pkg.applicationInfo.uid);
                mActivities.addActivity(a, "activity");
                ... ...
            }
            ... ...
        }

        return pkg;
    }
```
# Step19: Settings::getSharedUserLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:398
    SharedUserSetting getSharedUserLPw(String name,
            int pkgFlags, int pkgPrivateFlags, boolean create) {
        // name 描述共享的LinuxUID
        // create 当系统不存在名称为name的UID时，是否需要创建一个

        // 系统中所有共享的UID都保存在mSharedUsers，先到这里查找
        SharedUserSetting s = mSharedUsers.get(name);
        if (s == null) {
            if (!create) {
                return null;
            }
            s = new SharedUserSetting(name, pkgFlags, pkgPrivateFlags);
            s.userId = newUserIdLPw(s);
            ... ...
            if (s.userId >= 0) {
                mSharedUsers.put(name, s);
            }
        }

        return s;
    }
```
# Step20: Settings::getPackageLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:367
    PackageSetting getPackageLPw(PackageParser.Package pkg, PackageSetting origPackage,
            String realName, SharedUserSetting sharedUser, File codePath, File resourcePath,
            String legacyNativeLibraryPathString, String primaryCpuAbi, String secondaryCpuAbi,
            int pkgFlags, int pkgPrivateFlags, UserHandle user, boolean add) {
        final String name = pkg.packageName;
        PackageSetting p = getPackageLPw(name, origPackage, realName, sharedUser, codePath,
                resourcePath, legacyNativeLibraryPathString, primaryCpuAbi, secondaryCpuAbi,
                pkg.mVersionCode, pkgFlags, pkgPrivateFlags, user, add, true /* allowInstall */);
        return p;
    }
```
它又调用了重载函数。
## Step20.1 Settings::getPcakageLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:565
    private PackageSetting getPackageLPw(String name, PackageSetting origPackage,
            String realName, SharedUserSetting sharedUser, File codePath, File resourcePath,
            String legacyNativeLibraryPathString, String primaryCpuAbiString,
            String secondaryCpuAbiString, int vc, int pkgFlags, int pkgPrivateFlags,
            UserHandle installUser, boolean add, boolean allowInstall) {
        // mPackages中保存的是从packages.xml中读取的信息
        PackageSetting p = mPackages.get(name);
        ... ...
        if (p != null) {
            ... ...
            // packages.xml中记录的pkg使用的sharedUser和实际的包文件中指定的
            // sharedUser不一致
            if (p.sharedUser != sharedUser) { 
                ... ...
                p = null;
            } else ... ...
        }
        if (p == null) { // 为名称为name的app创建新的PackageSetting对象
            if (origPackage != null) { // 说明名称为name的app在系统中有一个旧版本
                // 为此旧版本的app的名称以及UID创建一个新PackageSetting对象
                // We are consuming the data from an existing package.
                p = new PackageSetting(origPackage.name, name, codePath, resourcePath,
                        legacyNativeLibraryPathString, primaryCpuAbiString, secondaryCpuAbiString,
                        null /* cpuAbiOverrideString */, vc, pkgFlags, pkgPrivateFlags);
                ... ...
                PackageSignatures s = p.signatures;
                p.copyFrom(origPackage);
                p.signatures = s;
                p.sharedUser = origPackage.sharedUser;
                p.appId = origPackage.appId;
                p.origPackage = origPackage;
                p.getPermissionsState().copyFrom(origPackage.getPermissionsState());
                mRenamedPackages.put(name, origPackage.name);
                name = origPackage.name;
                // Update new package state.
                p.setTimeStamp(codePath.lastModified());
            } else {
                // 说明名称为name的app是个全新安装的应用程序，使用本函数参数为之创
                // 建一个全新PackageSetting对象
                p = new PackageSetting(name, realName, codePath, resourcePath,
                        legacyNativeLibraryPathString, primaryCpuAbiString, secondaryCpuAbiString,
                        null /* cpuAbiOverrideString */, vc, pkgFlags, pkgPrivateFlags);
                p.setTimeStamp(codePath.lastModified());
                p.sharedUser = sharedUser;
                ... ...
                // 名称为name的app是否制定了要与其它app共享UID
                if (sharedUser != null) {
                    p.appId = sharedUser.userId;
                } else {
                    // Clone the setting here for disabled system packages
                    // 是否是一个禁用的系统应用
                    PackageSetting dis = mDisabledSysPackages.get(name);
                    if (dis != null) {//如果是，则不需要分配新的UID，直接使用原来的
                        ... ...
                        p.appId = dis.appId;
                        // Clone permissions
                        p.getPermissionsState().copyFrom(dis.getPermissionsState());
                        ... ...
                        // Add new setting to list of user ids
                        addUserIdLPw(p.appId, p, name);
                    } else {
                        // Assign new user id
                        // 🏁分配新UID
                        p.appId = newUserIdLPw(p);
                    }
                }
            }
            ... ...
            if (add) {
                // Finish adding new package by adding it and updating shared
                // user preferences
                addPackageSettingLPw(p, name, sharedUser);
            }
        } else {... ...}
        return p;
    }
```
# Step21: Settings::newUserIdLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:3736
    private int newUserIdLPw(Object obj) {
        // Let's be stupidly inefficient for now...
        final int N = mUserIds.size();
        for (int i = mFirstAvailableUid; i < N; i++) {
            // 如果为空，说明uid=FIRST_APPLICATION_UID+1的UID尚未分配
            if (mUserIds.get(i) == null) {
                mUserIds.set(i, obj);
                return Process.FIRST_APPLICATION_UID + i;
            }
        }

        // None left?
        if (N > (Process.LAST_APPLICATION_UID-Process.FIRST_APPLICATION_UID)) {
            return -1;
        }

        mUserIds.add(obj);
        return Process.FIRST_APPLICATION_UID + N;
    }
```
似曾相识，跟Step6 Settings::addUserIdLPw(...)的差异在于add指定了uid，而此处是在mUserIds的最末端生成一个新的uid。

接下来返回到Step2中，调用PackageManagerService::updatePermissionLPw(...)为前面安装的app分配用户组ID，即gid。授予它们所申请的资源的访问权限，尔后就可以调用Settings::writeLPr()将这些应用程序的安装信息保存在本地了。
# Step22: PackageManagerService::updatePermissionLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:8244
    private void updatePermissionsLPw(String changingPkg, PackageParser.Package pkgInfo,
            int flags) {
        final String volumeUuid = (pkgInfo != null) ? getVolumeUuidForPackage(pkgInfo) : null;
        updatePermissionsLPw(changingPkg, pkgInfo, volumeUuid, flags);
    }
```
调用了重载函数。
## Step22.1: PackageManagerService::updatePermissionLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:8250
    private void updatePermissionsLPw(String changingPkg,
            PackageParser.Package pkgInfo, String replaceVolumeUuid, int flags) {
        ... ...
            for (PackageParser.Package pkg : mPackages.values()) {
                if (pkg != pkgInfo) {
                    // Only replace for packages on requested volume
                    final String volumeUuid = getVolumeUuidForPackage(pkg);
                    final boolean replace = ((flags & UPDATE_PERMISSIONS_REPLACE_ALL) != 0)
                            && Objects.equals(replaceVolumeUuid, volumeUuid);
                    grantPermissionsLPw(pkg, replace, changingPkg);
                }
            }
        ... ...
    }
```
回顾Step15中的AndroidManifest.xml样例，它的user-permission部分如下：
``` xml
<uses-permission
        android:name="android.permission.READ_EXTERNAL_STORAGE">
</uses-permission>
```
他记录了app所需要的权限名称。系统在`/system/etc/permissions/platform.xml`中保存着系统中的资源访问权限列表，其内容主要形式为：
``` xml
    <permission name="android.permission.BLUETOOTH" >
        <group gid="net_bt" />
    </permission>
```
这两个表连接起来就知道app所需要的用户组名称，再通过getgrname函数就可以获得对应group id。<font color="red">但是我并没有在platform.xml中找到READ_EXTERNAL_STORAGE对应的grout gid标签，这是为什么？</font>

PackageManagerService会给AndroiManifest.xml中每个permission标签创建一个BasePermission对象，并且以标签中name属性作为关键字将对象们保存在mSettings.mPermissions这个HashMap中。
`/system/etc/permissions/platform.xml`中的内容：
``` xml
<permissions>
    <permission name="android.permission.BLUETOOTH_ADMIN" >
        <group gid="net_bt_admin" />
    </permission>

    <permission name="android.permission.BLUETOOTH" >
        <group gid="net_bt" />
    </permission>

    <permission name="android.permission.BLUETOOTH_STACK" >
        <group gid="net_bt_stack" />
    </permission>
    ... ...
    <assign-permission name="android.permission.MODIFY_AUDIO_SETTINGS" uid="media" />
    <assign-permission name="android.permission.ACCESS_SURFACE_FLINGER" uid="media" />
    ... ...
    <assign-permission name="android.permission.ACCESS_SURFACE_FLINGER" uid="graphics" />

    <library name="android.test.runner"
            file="/system/framework/android.test.runner.jar" />
    <library name="javax.obex"
            file="/system/framework/javax.obex.jar" />
    <library name="org.apache.http.legacy"
            file="/system/framework/org.apache.http.legacy.jar" />

    <allow-in-power-save-except-idle package="com.android.providers.downloads" />

</permissions>
```
# Step23: PackageManagerService::grantPermissionsLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:8338
    private void grantPermissionsLPw(PackageParser.Package pkg, boolean replace,
            String packageOfInterest) {
        // pkg描述的应用程序的安装信息就保存在mExtras中
        final PackageSetting ps = (PackageSetting) pkg.mExtras;
        ... ...
        PermissionsState permissionsState = ps.getPermissionsState();
        PermissionsState origPermissions = permissionsState;

        final int[] currentUserIds = UserManagerService.getInstance().getUserIds();
        ... ...
        // 将系统中所有应用程序都具备的默认资源访问权限赋给该应用
        permissionsState.setGlobalGids(mGlobalGids);

        // 依次检查pkg中所描述的每一个资源访问权限
        final int N = pkg.requestedPermissions.size();
        for (int i=0; i<N; i++) {
            final String name = pkg.requestedPermissions.get(i);
            // 每个资源访问权限都对应一个BasePermission对象，并且以name作为关键字
            // 此处取出该对象
            final BasePermission bp = mSettings.mPermissions.get(name);
            ... ...
            // 判断当前正在检查的资源访问权限是否合法
            final String perm = bp.name;
            boolean allowedSig = false;
            int grant = GRANT_DENIED;

            // Keep track of app op permissions.
            if ((bp.protectionLevel & PermissionInfo.PROTECTION_FLAG_APPOP) != 0) {
                ArraySet<String> pkgs = mAppOpPermissionPackages.get(bp.name);
                if (pkgs == null) {
                    pkgs = new ArraySet<>();
                    mAppOpPermissionPackages.put(bp.name, pkgs);
                }
                pkgs.add(pkg.packageName);
            }

            // 分析bp所描述的资源访问权限的保护级别
            final int level = bp.protectionLevel & PermissionInfo.PROTECTION_MASK_BASE;
            switch (level) {
                case PermissionInfo.PROTECTION_NORMAL: {
                    // For all apps normal permissions are install time ones.
                    grant = GRANT_INSTALL; // 合法
                } break;

                case PermissionInfo.PROTECTION_DANGEROUS: {
                    if (pkg.applicationInfo.targetSdkVersion <= Build.VERSION_CODES.LOLLIPOP_MR1) {
                        // For legacy apps dangerous permissions are install time ones.
                        grant = GRANT_INSTALL_LEGACY; // 合法
                    } else if (origPermissions.hasInstallPermission(bp.name)) {
                        // For legacy apps that became modern, install becomes runtime.
                        grant = GRANT_UPGRADE;
                    } else if (mPromoteSystemApps
                            && isSystemApp(ps)
                            && mExistingSystemPackages.contains(ps.name)) {
                        // For legacy system apps, install becomes runtime.
                        // We cannot check hasInstallPermission() for system apps since those
                        // permissions were granted implicitly and not persisted pre-M.
                        grant = GRANT_UPGRADE;
                    } else {
                        // For modern apps keep runtime permissions unchanged.
                        grant = GRANT_RUNTIME;
                    }
                } break;

                case PermissionInfo.PROTECTION_SIGNATURE: {
                    // For all apps signature permissions are install time ones.
                    // 需要结合pkg的签名来判断当前检查的资源访问权限是否合法
                    allowedSig = grantSignaturePermission(perm, pkg, bp, origPermissions);
                    if (allowedSig) {
                        grant = GRANT_INSTALL;
                    }
                } break;
            }
            ... ...
            if (grant != GRANT_DENIED) {
                if (!isSystemApp(ps) && ps.installPermissionsFixed) {
                    // If this is an existing, non-system package, then
                    // we can't add any new permissions to it.
                    if (!allowedSig && !origPermissions.hasInstallPermission(perm)) {
                        // Except...  if this is a permission that was added
                        // to the platform (note: need to only do this when
                        // updating the platform).
                        if (!isNewPlatformPermissionForPackage(perm, pkg)) {
                            grant = GRANT_DENIED;
                        }
                    }
                }
                // 将合法的资源访问权限对应的gid分配给pkg
                switch (grant) {
                    case GRANT_INSTALL: {
                        // Revoke this as runtime permission to handle the case of
                        // a runtime permission being downgraded to an install one.
                        for (int userId : UserManagerService.getInstance().getUserIds()) {
                            if (origPermissions.getRuntimePermissionState(
                                    bp.name, userId) != null) {
                                // Revoke the runtime permission and clear the flags.
                                origPermissions.revokeRuntimePermission(bp, userId);
                                origPermissions.updatePermissionFlags(bp, userId,
                                      PackageManager.MASK_PERMISSION_FLAGS, 0);
                                // If we revoked a permission permission, we have to write.
                                changedRuntimePermissionUserIds = ArrayUtils.appendInt(
                                        changedRuntimePermissionUserIds, userId);
                            }
                        }
                        // Grant an install permission.
                        if (permissionsState.grantInstallPermission(bp) !=
                                PermissionsState.PERMISSION_OPERATION_FAILURE) {
                            changedInstallPermission = true;
                        }
                    } break;

                    case GRANT_INSTALL_LEGACY: {
                        // Grant an install permission.
                        if (permissionsState.grantInstallPermission(bp) !=
                                PermissionsState.PERMISSION_OPERATION_FAILURE) {
                            changedInstallPermission = true;
                        }
                    } break;

                    case GRANT_RUNTIME: {
                        // Grant previously granted runtime permissions.
                        for (int userId : UserManagerService.getInstance().getUserIds()) {
                            PermissionState permissionState = origPermissions
                                    .getRuntimePermissionState(bp.name, userId);
                            final int flags = permissionState != null
                                    ? permissionState.getFlags() : 0;
                            if (origPermissions.hasRuntimePermission(bp.name, userId)) {
                                if (permissionsState.grantRuntimePermission(bp, userId) ==
                                        PermissionsState.PERMISSION_OPERATION_FAILURE) {
                                    // If we cannot put the permission as it was, we have to write.
                                    changedRuntimePermissionUserIds = ArrayUtils.appendInt(
                                            changedRuntimePermissionUserIds, userId);
                                }
                            }
                            // Propagate the permission flags.
                            permissionsState.updatePermissionFlags(bp, userId, flags, flags);
                        }
                    } break;

                    case GRANT_UPGRADE: {
                        // Grant runtime permissions for a previously held install permission.
                        PermissionState permissionState = origPermissions
                                .getInstallPermissionState(bp.name);
                        final int flags = permissionState != null ? permissionState.getFlags() : 0;

                        if (origPermissions.revokeInstallPermission(bp)
                                != PermissionsState.PERMISSION_OPERATION_FAILURE) {
                            // We will be transferring the permission flags, so clear them.
                            origPermissions.updatePermissionFlags(bp, UserHandle.USER_ALL,
                                    PackageManager.MASK_PERMISSION_FLAGS, 0);
                            changedInstallPermission = true;
                        }

                        // If the permission is not to be promoted to runtime we ignore it and
                        // also its other flags as they are not applicable to install permissions.
                        if ((flags & PackageManager.FLAG_PERMISSION_REVOKE_ON_UPGRADE) == 0) {
                            for (int userId : currentUserIds) {
                                if (permissionsState.grantRuntimePermission(bp, userId) !=
                                        PermissionsState.PERMISSION_OPERATION_FAILURE) {
                                    // Transfer the permission flags.
                                    permissionsState.updatePermissionFlags(bp, userId,
                                            flags, flags);
                                    // If we granted the permission, we have to write.
                                    changedRuntimePermissionUserIds = ArrayUtils.appendInt(
                                            changedRuntimePermissionUserIds, userId);
                                }
                            }
                        }
                    } break;
                    ... ...
                }
            } else { // 正在检查的资源访问权限不合法，将它从pkg的资源访问权限列表中删除
                if (permissionsState.revokeInstallPermission(bp) !=
                        PermissionsState.PERMISSION_OPERATION_FAILURE) {
                    // Also drop the permission flags.
                    permissionsState.updatePermissionFlags(bp, UserHandle.USER_ALL,
                            PackageManager.MASK_PERMISSION_FLAGS, 0);
                    changedInstallPermission = true;
                    ... ...
                } ... ...
            }
        }

        if ((changedInstallPermission || replace) && !ps.installPermissionsFixed &&
                !isSystemApp(ps) || isUpdatedSystemApp(ps)){
            // This is the first that we have heard about this package, so the
            // permissions we have now selected are fixed until explicitly
            // changed.
            ps.installPermissionsFixed = true;
        }

        // Persist the runtime permissions state for users with changes. If permissions
        // were revoked because no app in the shared user declares them we have to
        // write synchronously to avoid losing runtime permissions state.
        for (int userId : changedRuntimePermissionUserIds) {
            mSettings.writeRuntimePermissionsForUserLPr(userId, runtimePermissionsRevoked);
        }
    }
```
完成给pkg赋予需要的资源访问权限之后，回到前面Step2中，接下来调用Settings::writeLPr()将应用程序的安装信息保存在本地文件中。
# Step24: Settings::writeLPr()
``` java
    void writeLPr() {
        if (mSettingsFilename.exists()) {
            // 确保packages-backup.xml文件总是packages.xml的影子
            if (!mBackupSettingsFilename.exists()) {
                if (!mSettingsFilename.renameTo(mBackupSettingsFilename)) {
                    ... ...
                    return;
                }
            } else {
                mSettingsFilename.delete();
                ... ...
            }
        }

        mPastSignatures.clear();

        try {
            FileOutputStream fstr = new FileOutputStream(mSettingsFilename);
            BufferedOutputStream str = new BufferedOutputStream(fstr);

            // 初始化头部
            XmlSerializer serializer = new FastXmlSerializer();
            serializer.setOutput(str, StandardCharsets.UTF_8.name());
            serializer.startDocument(null, true);
            serializer.setFeature("http://xmlpull.org/v1/doc/features.html#indent-output", true);

            serializer.startTag(null, "packages");
            ... ...
            for (final SharedUserSetting usr : mSharedUsers.values()) {
                serializer.startTag(null, "shared-user");
                serializer.attribute(null, ATTR_NAME, usr.name);
                serializer.attribute(null, "userId",
                        Integer.toString(usr.userId));
                usr.signatures.writeXml(serializer, "sigs", mPastSignatures);
                writePermissionsLPr(serializer, usr.getPermissionsState()
                        .getInstallPermissionStates());
                serializer.endTag(null, "shared-user");
            }
            ... ...
            mKeySetManagerService.writeKeySetManagerServiceLPr(serializer);

            serializer.endTag(null, "packages");

            serializer.endDocument();

            str.flush();
            FileUtils.sync(fstr);
            str.close();

            // New settings successfully written, old ones are no longer
            // needed.
            mBackupSettingsFilename.delete();
            FileUtils.setPermissions(mSettingsFilename.toString(),
                    FileUtils.S_IRUSR|FileUtils.S_IWUSR
                    |FileUtils.S_IRGRP|FileUtils.S_IWGRP,
                    -1, -1);

            writePackageListLPr();
            writeAllUsersPackageRestrictionsLPr();
            writeAllRuntimePermissionsLPr();
            return;

        } catch(XmlPullParserException e) {... ...}
        ... ...
    }
```
至此，PackageManagerService就将每个应用程序使用的uid保存起来了，之后如果一个app重新安装，uid也是不会变的。
如果一个app是通过下载安装的，他调用PackageManagerService::installPackage(...)来启动安装，该函数最终也是通过调用PackageManagerService::scanPackageLI(...)来完成安装。

# 安装过程函数调用关系图
![安装过程函数调用关系图](1024Installer2/img01.png)