---
layout: post
title: Android App安装过程笔记
date: 2016-10-15 15:14:42 +0800
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
    mPackageManagerService = PackageManagerService.main(mSystemContext, installer,
            mFactoryTestMode != FactoryTest.FACTORY_TEST_OFF, mOnlyCore);
    mFirstBoot = mPackageManagerService.isFirstBoot();
    mPackageManager = mSystemContext.getPackageManager();
    ... ...
} 
```
PackageManagerService在启动过程中会对系统中的应用程序进行安装，因此可以它的main函数作为起点。
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
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:1801
    public PackageManagerService(Context context, Installer installer,
            boolean factoryTest, boolean onlyCore) {
        ... ...
        mSettings = new Settings(mPackages);
        ... ...            
            File dataDir = Environment.getDataDirectory();      // 目录/data
            mAppDataDir = new File(dataDir, "data");            // /data/data
            // /data/app 保存有用户自己安装的app
            mAppInstallDir = new File(dataDir, "app");             
            mAppLib32InstallDir = new File(dataDir, "app-lib"); // /data/app-lib   
            mAsecInternalPath = new File(dataDir, "app-asec").getPath(); // /data/app-asec
            mUserAppDataDir = new File(dataDir, "user");        // /data/user
            // /data/app-private 保存受DRM保护的私有app
            mDrmAppPrivateInstallDir = new File(dataDir, "app-private"); 
            ... ...
            // /system/framework保存的应用程序是资源型的，资源型应用程序是用来打包资源文件的，不包含执行代码
            File frameworkDir = new File(Environment.getRootDirectory(), "framework");
            ... ...
            // 🏁Step10: 安装保存在/system/framework、/system/app、/vendor/app、
            // /data/app和/data/app-private的app
            // Collect vendor overlay packages.
            // (Do this before scanning any apps.)
            // For security and version matching reason, only consider
            // overlay packages if they reside in VENDOR_OVERLAY_DIR.
            File vendorOverlayDir = new File(VENDOR_OVERLAY_DIR);
            scanDirLI(vendorOverlayDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags | SCAN_TRUSTED_OVERLAY, 0);

            // Find base frameworks (resource packages without code).
            scanDirLI(frameworkDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR
                    | PackageParser.PARSE_IS_PRIVILEGED,
                    scanFlags | SCAN_NO_DEX, 0);

            // Collected privileged system packages.
            final File privilegedAppDir = new File(Environment.getRootDirectory(), "priv-app");
            scanDirLI(privilegedAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR
                    | PackageParser.PARSE_IS_PRIVILEGED, scanFlags, 0);

            // Collect ordinary system packages.
            // /system/app 系统自带的应用程序
            final File systemAppDir = new File(Environment.getRootDirectory(), "app");
            scanDirLI(systemAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            // Collect all vendor packages.
            // /vendor/app 设备厂商提供的应用程序
            File vendorAppDir = new File("/vendor/app");
            try {
                vendorAppDir = vendorAppDir.getCanonicalFile();
            } catch (IOException e) {
                // failed to look up canonical path, continue with original one
            }
            scanDirLI(vendorAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            // Collect all OEM packages.
            final File oemAppDir = new File(Environment.getOemDirectory(), "app");
            scanDirLI(oemAppDir, PackageParser.PARSE_IS_SYSTEM
                    | PackageParser.PARSE_IS_SYSTEM_DIR, scanFlags, 0);

            ... ...

            //look for any incomplete package installations
            ArrayList<PackageSetting> deletePkgsList = mSettings.getListOfIncompleteInstallPackagesLPr();
            //clean up list
            for(int i = 0; i < deletePkgsList.size(); i++) {
                //clean up here
                cleanupInstallFailedPackage(deletePkgsList.get(i));
            }
            //delete tmp files
            deleteTempPackageFiles();

            // Remove any shared userIDs that have no associated packages
            mSettings.pruneSharedUsersLPw();

            ... ...

            // Now that we know all of the shared libraries, update all clients to have
            // the correct library paths.
            updateAllSharedLibrariesLPw();

            ... ...
            // Now that we know all the packages we are keeping,
            // read and update their last usage times.
            mPackageUsage.readLP();
            ... ...
            // If the platform SDK has changed since the last time we booted,
            // we need to re-grant app permission to catch any new ones that
            // appear.  This is really a hack, and means that apps can in some
            // cases get permissions that the user didn't initially explicitly
            // allow...  it would be nice to have some better way to handle
            // this situation.
            int updateFlags = UPDATE_PERMISSIONS_ALL;
            if (ver.sdkVersion != mSdkVersion) {
                Slog.i(TAG, "Platform changed from " + ver.sdkVersion + " to "
                        + mSdkVersion + "; regranting permissions for internal storage");
                updateFlags |= UPDATE_PERMISSIONS_REPLACE_PKG | UPDATE_PERMISSIONS_REPLACE_ALL;
            }
            // 为申请了特定资源访问权限的app分配相应的Linux用户组ID
            updatePermissionsLPw(null, null, StorageManager.UUID_PRIVATE_INTERNAL, updateFlags); 
            ver.sdkVersion = mSdkVersion;
            ... ...
            // can downgrade to reader
            mSettings.writeLPr();   // 把前面获得的app安装信息保存在本地
        ... ...
    }
```
# Step3: Settings.readLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings/java
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
        try {        // 🏁Step4: 如果没有备份，则读取配置文件/data/system/packages.xml
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
                    // 🏁Step5: 该标签描述上一次安装的app信息
                    readPackageLPw(parser);
                } else if (tagName.equals("shared-user")) { 
                    // 🏁Step8: 描述上一次安装app时分配的共享Linux用户ID
                    readSharedUserLPw(parser);
                } 
                ... ...
                } ... ...
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
# Step4: packages.xml内容
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
    <!-- package部分，描述上一次安装的app的信息 -->
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
    <!-- shared-user部分，描述上一次安装app时分配的共享UID -->
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
# Step5: Settings::readPackageLPw(...)
这里关注标签"package"的三个属性：
* name 描述上一次安装的app的Package名称
* userId 描述该app所使用的独立Linux用户ID
* sharedUserId 描述该app所使用的共享Linux用户ID
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
            // 上次安装的app的Package名称
            name = parser.getAttributeValue(null, ATTR_NAME); 
            ... ...
            // 该app所使用的独立Linux用户ID
            idStr = parser.getAttributeValue(null, "userId"); 
            ... ...
            // 该app所使用的共享Linux用户ID
            sharedIdStr = parser.getAttributeValue(null, "sharedUserId");
            ... ...
            int userId = idStr != null ? Integer.parseInt(idStr) : 0;
            ... ...
            if (name == null) {     // 该字段必须存在
                ... ...
            }... ...
            else if (userId > 0) {
                packageSetting = addPackageLPw(name.intern(), realName, new File(codePathStr),
                        new File(resourcePathStr), legacyNativeLibraryPathStr, primaryCpuAbiString,
                        secondaryCpuAbiString, cpuAbiOverrideString, userId, versionCode, pkgFlags,
                        pkgPrivateFlags); // 🏁将上次安装时分配的Linux用户ID保留下来
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
            } else {
                ... ...
            }
        } catch (NumberFormatException e) {
            ... ...
        }
        ... ...
    }
```
# Step6: Settings::addPackageLPw(...)
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
        if (addUserIdLPw(uid, p, name)) { // 🏁在系统中保留指定的uid
            mPackages.put(name, p);
            return p;
        }
        return null;
    }
```
# Step7: Settings::addUserIdLPw(...)
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
在区间[FIRST_APPLICATION_UID, FIRST_APPLICATION_UID + MAX_APPLICATION_UIDS)中的UID是保留给应用程序的，(0, FIRST_APPLICATION_UID)是留给特权用户的。FIRST_APPLICATION_UID=10000, MAX_APPLICATION_UIDS=1000。

回到Step3中，通过readPackageLPw(...)读取了上次安装的app信息之后，接下来调用readSharedUserLPw(...)读取上次安装app时分配的共享UID。

# Step8: Settings::readSharedUserLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:3605
    private void readSharedUserLPw(XmlPullParser parser) throws XmlPullParserException,IOException {
        String name = null;
        String idStr = null;
        int pkgFlags = 0;
        int pkgPrivateFlags = 0;
        SharedUserSetting su = null;
        try {
            name = parser.getAttributeValue(null, ATTR_NAME); // 获取用户名
            idStr = parser.getAttributeValue(null, "userId"); // 获取用户ID
            int userId = idStr != null ? Integer.parseInt(idStr) : 0;//UID=>int
            // 此uid是否分配给了一个系统类型的应用程序使用
            if ("true".equals(parser.getAttributeValue(null, "system"))) {
                pkgFlags |= ApplicationInfo.FLAG_SYSTEM;
            }
            if (name == null) { // name和uid一定存在
                ... ...
            } else if (userId == 0) {
                ... ...
            } else {
                // 🏁在系统中为名称为name的共享Linux用户保留一个职位userId的Linux用户ID
                if ((su = addSharedUserLPw(name.intern(), userId, pkgFlags, pkgPrivateFlags))
                        == null) {
                    ... ...
                }
            }
        } catch (NumberFormatException e) {
            ... ...
        }
        ... ...
    }
```
# Step9: Settings::addSharedUserLPw(...)
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
        if (addUserIdLPw(uid, s, name)) {   // 在系统中保留uid
            mSharedUsers.put(name, s);      // 将s保存到mSharedUsers
            return s;
        }
        return null;
    }
```
本步完成后回到Step3，完成共享Linux用户信息的读取。接下来就可以为保存在mPendingPackage中的app保留他们上一次所使用的Linux UID了。然后返回到Step2，readLPw(...)完成恢复上一次应用程序安装信息的读取。接下来调用scanDirLI来安装保存在/system/framework、/system/app、/vendor/app、/data/app和/data/app-private的应用程序。
# Step10: PackageManagerService::scanDirLI(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:5624
    private void scanDirLI(File dir, int parseFlags, int scanFlags, long currentTime) {
        final File[] files = dir.listFiles();
        ... ...

        for (File file : files) {
            final boolean isPackage = (isApkFile(file) || file.isDirectory())
                    && !PackageInstallerService.isStageName(file.getName());
            if (!isPackage) {
                // Ignore entries which are not packages
                continue;
            }
            try {
                scanPackageLI(file, parseFlags | PackageParser.PARSE_MUST_BE_APK,
                        scanFlags, currentTime, null);
            } catch (PackageManagerException e) {
                ... ...
                // Delete invalid userdata apps
                if ((parseFlags & PackageParser.PARSE_IS_SYSTEM) == 0 &&
                        e.error == PackageManager.INSTALL_FAILED_INVALID_APK) {
                    ... ...
                    if (file.isDirectory()) {
                        mInstaller.rmPackageDir(file.getAbsolutePath());
                    } else {
                        file.delete();
                    }
                }
            }
        }
    }
```

