---
layout: post
title: Android App安装过程学习笔记（一）
date: 2016-10-23 20:01:42 +0800
categories: Android
tags: 安装过程
toc: true
comments: true
---
在Android下安装一个APP时，PackageManagerService会解析该APP的AndroidManifest.xml文件，以便获取它的安装信息，同时为该APP分配Linux用户ID和Linux用户组ID。

PackageManagerService是在SystemService启动的时候由该进程启动起来的：
<!-- more -->
``` java
// frameworks/base/services/java/com/android/server/SystemServer.java:366
public final class SystemServer {
... ...
    public static void main(String[] args) {    // 入口函数
        new SystemServer().run();
    }
    private void run() {
        ... ... 
        try { 
            startBootstrapServices();           // :268
            ... ...
        } catch (Throwable ex) {
            ... ...
        }
    }
    private void startBootstrapServices() {
    ... ...
    // Start the package manager.
    Slog.i(TAG, "Package Manager");             // :365
    // 🏁调用PackageManagerService的静态函数main(...)安装系统中的应用
    mPackageManagerService = PackageManagerService.main(mSystemContext, installer,
            mFactoryTestMode != FactoryTest.FACTORY_TEST_OFF, mOnlyCore);
    ... ...
} 
```
PackageManagerService在启动过程中会对系统中的应用程序进行安装，以它的main函数作为起点开启探索。
# Step1: PackageManagerService.main(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:1765
public static PackageManagerService main(Context context, Installer installer,
        boolean factoryTest, boolean onlyCore) {
    PackageManagerService m = new PackageManagerService(context, installer,
            factoryTest, onlyCore); // 🏁
    ServiceManager.addService("package", m);
    return m;
}
```
# Step2: PackageManagerService的构造函数
Android系统在启动时，会把已安装的app重新安装一遍，所谓的“安装”就是遍历各安装目录，解析各app的AndroidManifest.xml，记录它们的安装信息，并为各app分配uid和gid。
这里是系统启动时，安装app的逻辑起点。
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:1801
    public PackageManagerService(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore) {
        ... ...
        mSettings = new Settings(mPackages);
        ... ...            
            File dataDir = Environment.getDataDirectory();      // 目录/data
            mAppDataDir = new File(dataDir, "data");            // /data/data
            mAppInstallDir = new File(dataDir, "app");          // /data/app 
            mAppLib32InstallDir = new File(dataDir, "app-lib"); // /data/app-lib   
            mAsecInternalPath = new File(dataDir, "app-asec").getPath(); // /data/app-asec
            mUserAppDataDir = new File(dataDir, "user");        // /data/user
            mDrmAppPrivateInstallDir = new File(dataDir, "app-private"); // /data/app-private
            ... ...
            // 🏁系统中安装的应用程序信息会记录在配置文件中，此处读取该配置文件
            mRestoredSettings = mSettings.readLPw(this, sUserManager.getUsers(false),
                    mSdkVersion, mOnlyCore);

            File frameworkDir = new File(Environment.getRootDirectory(), "framework");
            ... ...

            // 🏁Step9: 调用scanDirLI(...)分别安装保存在几个目录下的应用程序
            // /vendor/overlay保存厂商提供的覆盖包
            File vendorOverlayDir = new File(VENDOR_OVERLAY_DIR);
            scanDirLI(vendorOverlayDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags | SCAN_TRUSTED_OVERLAY, 0);

            // /system/framework保存不含代码的资源包
            // Find base frameworks (resource packages without code).
            scanDirLI(frameworkDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR
                    | PackageParser.PARSE_IS_PRIVILEGED,
                    scanFlags | SCAN_NO_DEX, 0);

            // /system/priv-app 有特权的系统包
            // Collected privileged system packages.
            final File privilegedAppDir = new File(Environment.getRootDirectory(), "priv-app");
            scanDirLI(privilegedAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR
                    | PackageParser.PARSE_IS_PRIVILEGED, scanFlags, 0);

            // /system/app 系统自带的应用程序
            // Collect ordinary system packages.
            final File systemAppDir = new File(Environment.getRootDirectory(), "app");
            scanDirLI(systemAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            // /vendor/app 设备厂商提供的应用程序
            // Collect all vendor packages.
            File vendorAppDir = new File("/vendor/app");
            try {
                vendorAppDir = vendorAppDir.getCanonicalFile();
            } catch (IOException e) {...}
            scanDirLI(vendorAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            // /oem/app 所有OEM包
            // Collect all OEM packages.
            final File oemAppDir = new File(Environment.getOemDirectory(), "app");
            scanDirLI(oemAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            ... ...
            int updateFlags = UPDATE_PERMISSIONS_ALL;
            if (ver.sdkVersion != mSdkVersion) {
                ... ...
                updateFlags |= UPDATE_PERMISSIONS_REPLACE_PKG | UPDATE_PERMISSIONS_REPLACE_ALL;
            }
            // 🏁Step24: 为申请了特定资源访问权限的app分配相应的Linux用户组ID
            updatePermissionsLPw(null, null, StorageManager.UUID_PRIVATE_INTERNAL, updateFlags); 
            ver.sdkVersion = mSdkVersion;
            ... ...
            // can downgrade to reader
            mSettings.writeLPr();   // 把前面获得的app安装信息保存回配置文件
        ... ...
    }
```
# Step3: Settings.readLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java
// :346
    Settings(File dataDir, Object lock) {
        ... ...
        mSystemDir = new File(dataDir, "system");
        mSystemDir.mkdirs();
        ... ...
        mSettingsFilename = new File(mSystemDir, "packages.xml");
        mBackupSettingsFilename = new File(mSystemDir, "packages-backup.xml");
        ... ...
    }

// :2500
    boolean readLPw(PackageManagerService service, List<UserInfo> users, int sdkVersion,
            boolean onlyCore) {
        FileInputStream str = null;
        if (mBackupSettingsFilename.exists()) { 
            try {   // 优先读取配置的备份文件/data/system/packages-backup.xml
                str = new FileInputStream(mBackupSettingsFilename);
                ... ...
            } catch (java.io.IOException e) {...}
        }
        ... ...
        try {        // 🏁读取配置文件/data/system/packages.xml
            if (str == null) {                 
                ... ... 
                str = new FileInputStream(mSettingsFilename);
            }
            XmlPullParser parser = Xml.newPullParser(); // 解析配置文件
            parser.setInput(str, StandardCharsets.UTF_8.name());

            int type;
            ... ...
            int outerDepth = parser.getDepth();
            while ((type = parser.next()) != XmlPullParser.END_DOCUMENT
                    && (type != XmlPullParser.END_TAG || parser.getDepth() > outerDepth)) {
                ... ...
                String tagName = parser.getName();
                // 此处只关注与app的Linux用户ID相关的信息
                if (tagName.equals("package")) { 
                    // 🏁Step4: 该标签描述上一次安装的app信息
                    readPackageLPw(parser);
                } else if (tagName.equals("shared-user")) { 
                    // 🏁Step5: 描述上一次安装app时分配的共享Linux用户ID
                    readSharedUserLPw(parser);
                } 
                ... ...
            }
            str.close();
        } catch ...
        ... ...
        // 解析完app安装信息中的共享Linux用户信息后，再为它们保留上一次所使用的Linux UID
        final int N = mPendingPackages.size();

        for (int i = 0; i < N; i++) { // 遍历mPendingPackage
            final PendingPackage pp = mPendingPackages.get(i);
            Object idObj = getUserIdLPr(pp.sharedId);
            // 如果sharedId存在相应的SharedUserSetting记录，说明pp所描述的app上次
            // 所使用的LinuxUID是有效的
            if (idObj != null && idObj instanceof SharedUserSetting) {
                // 🏁为它创建一个PackageSetting对象，并保存在mPackage中
                PackageSetting p = getPackageLPw(pp.name, null, pp.realName,
                        (SharedUserSetting) idObj, pp.codePath, pp.resourcePath,
                        pp.legacyNativeLibraryPathString, pp.primaryCpuAbiString,
                        pp.secondaryCpuAbiString, pp.versionCode, pp.pkgFlags, pp.pkgPrivateFlags,
                        null, true /* add */, false /* allowInstall */);
                ... ...
                p.copyFrom(pp);
            } ... ...
        }
        mPendingPackages.clear();
        ... ...
        return true;
    }
```
# /data/system/packages.xml内容
/data/system/packages.xml的内容如下：
``` xml
<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<packages>
    <version sdkVersion="23" databaseVersion="3" fingerprint="Android/aosp_arm/generic:6.0.1/MMB29Q/palance09252259:eng/debug,test-keys" />
    <version volumeUuid="primary_physical" sdkVersion="23" databaseVersion="3" fingerprint="Android/aosp_arm/generic:6.0.1/MMB29Q/palance09252259:eng/debug,test-keys" />
    <permission-trees />
    <permissions>
        <item name="android.permission.REAL_GET_TASKS" package="android" protection="18" />
        ... ...
        <item name="android.permission.REMOTE_AUDIO_PLAYBACK" package="android" protection="2" />
    </permissions>
    <!-- package部分，描述app的信息 -->
    <!-- name: package名称 -->
    <!-- userId: app的独立UID -->
    <!-- sharedUserId: app的共享UID -->
    <package name="com.android.providers.telephony" codePath="/system/priv-app/TelephonyProvider" nativeLibraryPath="/system/priv-app/TelephonyProvider/lib" publicFlags="940064261" privateFlags="8" ft="15761def440" it="15761def440" ut="15761def440" version="23" sharedUserId="1001">
        <sigs count="1">
            <cert index="0" key="308204a... ..." />
        </sigs>
        <perms>
            <item name="android.permission.WRITE_SETTINGS" granted="true" flags="0" />
            <item name="android.permission.MODIFY_AUDIO_SETTINGS" granted="true" flags="0" />
            ... ...
        </perms>
        <proper-signing-keyset identifier="1" />
    </package>
    ... ...
    <package name="com.sohu.inputmethod.sogou" codePath="/data/app/com.sohu.inputmethod.sogou-1" nativeLibraryPath="/data/app/com.sohu.inputmethod.sogou-1/lib" primaryCpuAbi="armeabi" publicFlags="940064324" privateFlags="0" ft="157cd4e7e80" it="157cd4ea0d6" ut="157cd4ea0d6" version="590" userId="10053">
        <sigs count="1">
            <cert index="3" key="308202... ..." />
        </sigs>
        <perms>
            <item name="android.permission.EXPAND_STATUS_BAR" granted="true" flags="0" />
            <item name="com.android.launcher.permission.UNINSTALL_SHORTCUT" granted="true" flags="0" />
            <item name="android.permission.INTERNET" granted="true" flags="0" />
            ... ...
        </perms>
        <proper-signing-keyset identifier="5" />
    </package>
    ... ...    
    <!-- shared-user部分，描述安装app时分配的共享UID -->
    <!-- name: 共享的Linux用户名称 -->
    <!-- userId: 共享的Linux UID -->
    <!-- system: 该UID是分配给一个系统类型的app使用，还是用户类型的app使用 -->
    <shared-user name="android.media" userId="10006">
        <sigs count="1">
            <cert index="2" />
        </sigs>
        <perms>
            <item name="android.permission.ACCESS_CACHE_FILESYSTEM" granted="true" flags="0" />
            <item name="android.permission.WRITE_SETTINGS" granted="true" flags="0" />
            ... ...
        </perms>
    </shared-user>
    <shared-user name="android.uid.shared" userId="10002">
        <sigs count="1">
            <cert index="4" />
        </sigs>
        <perms>
            <item name="android.permission.WRITE_SETTINGS" granted="true" flags="0" />
            <item name="android.permission.USE_CREDENTIALS" granted="true" flags="0" />
            ... ...
        </perms>
    </shared-user>
    <keyset-settings version="1">
        <keys>
            <public-key identifier="1" value="MIIBI... ..." />
            <public-key identifier="2" value="MIIBIDANBg... ..." />
            ... ...
        </keys>
        <keysets>
            <keyset identifier="1">
                <key-id identifier="1" />
            </keyset>
            <keyset identifier="2">
                <key-id identifier="2" />
            </keyset>
            ... ...
        </keysets>
        <lastIssuedKeyId value="5" />
        <lastIssuedKeySetId value="5" />
    </keyset-settings>
</packages>
```
# Step4: Settings::readPackageLPw(...)
这里关注标签"package"的三个属性：
* name 描述app的Package名称
* userId 描述该app所使用的uid
* sharedUserId 描述该app所使用的shared uid
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java
// :336
    private final ArrayList<PendingPackage> mPendingPackages = new ArrayList<PendingPackage>();
// :3256
    private void readPackageLPw(XmlPullParser parser) throws XmlPullParserException, IOException {
        String name = null;
        ... ...
        String idStr = null;
        String sharedIdStr = null;
        ... ...
        try {
            // app的Package名称
            name = parser.getAttributeValue(null, ATTR_NAME); 
            ... ...
            // 该app所使用的uid
            idStr = parser.getAttributeValue(null, "userId"); 
            ... ...
            // 该app所使用的shared uid
            sharedIdStr = parser.getAttributeValue(null, "sharedUserId");
            ... ...
            int userId = idStr != null ? Integer.parseInt(idStr) : 0;
            ... ...
            if (name == null) {  ... }  // 该字段必须存在
            ... ...
            else if (userId > 0) {
                packageSetting = addPackageLPw(name.intern(), realName, new File(codePathStr),
                        new File(resourcePathStr), legacyNativeLibraryPathStr, primaryCpuAbiString,
                        secondaryCpuAbiString, cpuAbiOverrideString, userId, versionCode, pkgFlags,
                        pkgPrivateFlags); // 🏁将读取到的安装信息和uid信息保存到内存数据结构
                ... ...
                    packageSetting.setTimeStamp(timeStamp);
                    packageSetting.firstInstallTime = firstInstallTime;
                    packageSetting.lastUpdateTime = lastUpdateTime;
                ... ...
            } else if (sharedIdStr != null) {
                // 如果sharedIdStr非空，说明上次并没有给他分配独立Linux用户ID，
                // 而是让它与其它app共享同一个Linux用户ID。此时不能马上为它保留上次使用的
                // Linux用户ID，因为该ID实际是别的app所有，此时可能是无效的。
                userId = sharedIdStr != null ? Integer.parseInt(sharedIdStr) : 0;
                if (userId > 0) {
                    // 为之创建一个PendingPackage，表示该Linux用户ID还未确定
                    // 需要等到PackageManagerService解析完成之后，才能才能确认保存在
                    // mPendingPackages中的ID是否有效，如果有效，
                    // PackageManagerService才会为它们保留上一次所使用的Linux用户ID
                    packageSetting = new PendingPackage(name.intern(), realName, new File(
                            codePathStr), new File(resourcePathStr), legacyNativeLibraryPathStr,
                            primaryCpuAbiString, secondaryCpuAbiString, cpuAbiOverrideString,
                            userId, versionCode, pkgFlags, pkgPrivateFlags);
                    packageSetting.setTimeStamp(timeStamp);
                    packageSetting.firstInstallTime = firstInstallTime;
                    packageSetting.lastUpdateTime = lastUpdateTime;
                    mPendingPackages.add((PendingPackage) packageSetting);
                    ... ...
                } ... ...
            } else {...}
        } catch (NumberFormatException e) {...}
        ... ...
    }
```
# Step5: Settings::addPackageLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:474
    PackageSetting addPackageLPw(String name, String realName, File codePath, File resourcePath,
            String legacyNativeLibraryPathString, String primaryCpuAbiString, String secondaryCpuAbiString,
            String cpuAbiOverrideString, int uid, int vc, int pkgFlags, int pkgPrivateFlags) {
        PackageSetting p = mPackages.get(name); // 根据包名找到已记录的安装信息
        if (p != null) {
            if (p.appId == uid) {
                return p;
            }
            ... ...
            return null;
        }
        // 如果没有找到则创建，并使用指定的uid
        p = new PackageSetting(name, realName, codePath, resourcePath,
                legacyNativeLibraryPathString, primaryCpuAbiString, secondaryCpuAbiString,
                cpuAbiOverrideString, vc, pkgFlags, pkgPrivateFlags);
        p.appId = uid;
        if (addUserIdLPw(uid, p, name)) { // 🏁保存uid信息
            mPackages.put(name, p); // 将安装信息保存到mPackages
            return p;
        }
        return null;
    }
```
# Step6: Settings::addUserIdLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:967
    private boolean addUserIdLPw(int uid, Object obj, Object name) {
        // 检查uid的合法性
        if (uid > Process.LAST_APPLICATION_UID) {
            return false;
        }

        if (uid >= Process.FIRST_APPLICATION_UID) {
            // mUserIds是以UID为索引的列表，如果指定uid比它的容量大，则用null填充
            int N = mUserIds.size();
            final int index = uid - Process.FIRST_APPLICATION_UID;
            while (index >= N) {
                mUserIds.add(null);
                N++;
            }
            if (mUserIds.get(index) != null) { // 指定uid已存在
                ... ...
                return false;
            }
            mUserIds.set(index, obj);
        } else {
            // mOtherUserIds是已分配给特权用户的UID的稀疏数组
            if (mOtherUserIds.get(uid) != null) { // 如果已分配，则返回
                ... ...
                return false;
            }
            mOtherUserIds.put(uid, obj);
        }
        return true;
    }
```
区间
`[FIRST_APPLICATION_UID, FIRST_APPLICATION_UID + MAX_APPLICATION_UIDS)`
中的UID是保留给应用程序的，
`(0, FIRST_APPLICATION_UID)`是留给特权用户的。
`FIRST_APPLICATION_UID=10000`,
`MAX_APPLICATION_UIDS=1000`。

Step5把从/data/system/packages.xml中读取到的安装信息保存到mPackageSetting对象中，并将此对象以包名为key保存到mPackages中；Step6把此包使用的uid保存到mUserIds中，并关联到对应的PackageSetting对象。

在Step4中，如果配置文件记录安装包被分配了独立的uid，就走以上的逻辑分支；如果没有独立uid，而是被分配了shared uid，则走另一个逻辑分支，将安装信息暂时封装为PendingPackage对象，保存到mPendingPackages，后面还会用到。

回到Step3中，通过`readPackageLPw(...)`读取了app安装信息之后，接下来调用`readSharedUserLPw(...)`读取系统分配的shared uid。

# Step7: Settings::readSharedUserLPw(...)
这里关注标签“shared-user”的三个属性：
* name: shared uid的名称
* userId: shared uid
* system: 此uid是否分配给了一个系统应用程序使用
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:3605
    private void readSharedUserLPw(XmlPullParser parser) throws XmlPullParserException,IOException {
        String name = null;
        String idStr = null;
        int pkgFlags = 0;
        int pkgPrivateFlags = 0;
        SharedUserSetting su = null;
        try {
            name = parser.getAttributeValue(null, ATTR_NAME); // shared uid对应的名称
            idStr = parser.getAttributeValue(null, "userId"); // shared uid
            int userId = idStr != null ? Integer.parseInt(idStr) : 0;//shared uid=>int
            // 此uid是否分配给了一个系统类型的应用程序使用
            if ("true".equals(parser.getAttributeValue(null, "system"))) {
                pkgFlags |= ApplicationInfo.FLAG_SYSTEM;
            }
            if (name == null) { ... }// name和uid都必须存在
            else if (userId == 0) { ... } 
            else {
                // 🏁保存shared uid信息
                if ((su = addSharedUserLPw(name.intern(), userId, pkgFlags, pkgPrivateFlags))
                        == null) { ... }
            }
        } catch (NumberFormatException e) { ... }
        ... ...
    }
```
# Step8: Settings::addSharedUserLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:497
    SharedUserSetting addSharedUserLPw(String name, int uid, int pkgFlags, int pkgPrivateFlags) {
        // 每个共享Linux用户都由一个SharedUserSetting来描述，以name为key保存在mSharedUsers
        SharedUserSetting s = mSharedUsers.get(name);
        if (s != null) {
            if (s.userId == uid) {
                return s; // 说明已经为该name的用户分配了指定的uid
            }
            ... ...
            return null;
        }
        // 不存在指定名称的共享用户，则创建
        s = new SharedUserSetting(name, pkgFlags, pkgPrivateFlags);
        s.userId = uid;
        if (addUserIdLPw(uid, s, name)) {   // 见Step6，把uid保存到mUserIds，并关联到s
            mSharedUsers.put(name, s);      // 将s保存到mSharedUsers
            return s;
        }
        return null;
    }
```
Step8将从/data/system/packages.xml中读取到的shared-user信息封装为`SharedUserSetting`对象，并以shared uid的名称为key保存到mSharedUser中；将shared uid保存到mUserIds中，并关联到该SharedUserSetting对象。

至此就完成了packages.xml文件的加载：
* 对于“package”标签记录的app安装信息，有独立uid的app信息，封装为PackageSetting对象，保存到mPackages中；有shareduid的app，封装为PendingPackage对象，保存到mPendingPackages中
* 对于“shared-user”标签记录的shared uid信息，封装为SharedUserSetting对象，保存到mSharedUser中
* 在此过程中遇到的uid和shared uid都保存在mUserIds中，并让每个uid指向与之关联的PackageSetting对象或SharedUserSetting对象。

本步完成后回到Step3，完成共享Linux用户信息的读取。接下来就可以为保存在mPendingPackage中的app保留他们上一次所使用的Linux UID了。然后返回到Step2，readLPw(...)完成恢复上一次应用程序安装信息的读取。接下来调用scanDirLI来安装保存在/system/framework、/system/app、/vendor/app、/data/app和/data/app-private的应用程序。
