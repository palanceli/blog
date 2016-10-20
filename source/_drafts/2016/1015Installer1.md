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
            // 🏁Step24: 为申请了特定资源访问权限的app分配相应的Linux用户组ID
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

        for (File file : files) { // 遍历dir下的每个文件
            final boolean isPackage = (isApkFile(file) || file.isDirectory())
                    && !PackageInstallerService.isStageName(file.getName());
            if (!isPackage) {
                // Ignore entries which are not packages
                continue;
            }
            try {
                scanPackageLI(file, parseFlags | PackageParser.PARSE_MUST_BE_APK,
                        scanFlags, currentTime, null); // 🏁继续解析Package
            } catch (PackageManagerException e) {
                ... ...
                // Delete invalid userdata apps
                // 如果解析失败则表明不是真正的应用程序文件，如果不在系统目录下，则删除
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
# Step11: PackageManagerService::scanPackageLI(...)
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
        // 🏁Step12: 解析scanFile所描述的文件
        pkg = pp.parsePackage(scanFile, parseFlags); 
        ... ...
        // 🏁Step19: 安装pkg描述的应用程序文件，以便获得它的组件信息，并为它分配LinuxUID
        PackageParser.Package scannedPkg = scanPackageLI(pkg, parseFlags, scanFlags
                | SCAN_UPDATE_SIGNATURE, currentTime, user);

        ... ...
        return scannedPkg;
    }
```
# Step12: PackageParser::parsePackage(...)
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

# Step13: PackageParser::parseMonollithicPackage(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:827
    public Package parseMonolithicPackage(File apkFile, int flags) throws PackageParserException {
        if (mOnlyCoreApps) {
            final PackageLite lite = parseMonolithicPackageLite(apkFile, flags);
            ... ...
        }

        final AssetManager assets = new AssetManager();
        ... ...
            final Package pkg = parseBaseApk(apkFile, assets, flags);
            pkg.codePath = apkFile.getAbsolutePath(); // 🏁Step16
            return pkg;
        ... ...
    }
```
# Step14: PackageParser::parseMonolithicPackageLite(...)
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
## Step14.1: PackageParser::parseApkLite(...)
`parseApkLite(...)`是一个获取APK轻量级信息的方法，比如package name, split name, install location等。
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
## Step14.2: PackageParser::parseApkLite(...)
``` java
// frameworks/base/core/java/android/content/pm/PackageParser.java:1155
    private static ApkLite parseApkLite(String codePath, Resources res, XmlPullParser parser,
            AttributeSet attrs, int flags, Signature[] signatures) throws IOException,
            XmlPullParserException, PackageParserException {
        final Pair<String, String> packageSplit = parsePackageSplitNames(parser, attrs, flags); // 🏁解析并生成<package, split>的pair

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
## Step 14.3: PackageParser::parsePackageSplitNames(...)
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
# Step15: 一个AndroidManifest.xml的样例
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
# Step16: PackageParser::parseBaseApk(...)
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
# Step17: PackageParser::parseBaseApk(...)
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
        pkg.mVersionCode = pkg.applicationInfo.versionCode = sa.getInteger(
                com.android.internal.R.styleable.AndroidManifest_versionCode, 0);
        pkg.baseRevisionCode = sa.getInteger(
                com.android.internal.R.styleable.AndroidManifest_revisionCode, 0);
        pkg.mVersionName = sa.getNonConfigurationString(
                com.android.internal.R.styleable.AndroidManifest_versionName, 0);
        if (pkg.mVersionName != null) {
            pkg.mVersionName = pkg.mVersionName.intern();
        }
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
        // 解析uses-permission和application标签，它们均未manifest子标签
        while ((type = parser.next()) != XmlPullParser.END_DOCUMENT
                && (type != XmlPullParser.END_TAG || parser.getDepth() > outerDepth)) {
            ... ...
            String tagName = parser.getName();
            if (tagName.equals("application")) {
                ... ...
                if (!parseBaseApplication(pkg, res, parser, attrs, flags, 
                outError)) { // 🏁解析每个app必须存在的application标签
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
            } else if (tagName.equals("uses-permission-sdk-m")
                    || tagName.equals("uses-permission-sdk-23")) {
                if (!parseUsesPermission(pkg, res, parser, attrs)) {
                    return null;
                }
            } ... ...
        }
        ... ...
        final int NP = PackageParser.NEW_PERMISSIONS.length;
        StringBuilder implicitPerms = null;
        for (int ip=0; ip<NP; ip++) {
            final PackageParser.NewPermissionInfo npi
                    = PackageParser.NEW_PERMISSIONS[ip];
            if (pkg.applicationInfo.targetSdkVersion >= npi.sdkVersion) {
                break;
            }
            if (!pkg.requestedPermissions.contains(npi.name)) {
                if (implicitPerms == null) {
                    implicitPerms = new StringBuilder(128);
                    implicitPerms.append(pkg.packageName);
                    implicitPerms.append(": compat added ");
                } else {
                    implicitPerms.append(' ');
                }
                implicitPerms.append(npi.name);
                pkg.requestedPermissions.add(npi.name);
            }
        }
        if (implicitPerms != null) {
            Slog.i(TAG, implicitPerms.toString());
        }

        final int NS = PackageParser.SPLIT_PERMISSIONS.length;
        for (int is=0; is<NS; is++) {
            final PackageParser.SplitPermissionInfo spi
                    = PackageParser.SPLIT_PERMISSIONS[is];
            if (pkg.applicationInfo.targetSdkVersion >= spi.targetSdk
                    || !pkg.requestedPermissions.contains(spi.rootPerm)) {
                continue;
            }
            for (int in=0; in<spi.newPerms.length; in++) {
                final String perm = spi.newPerms[in];
                if (!pkg.requestedPermissions.contains(perm)) {
                    pkg.requestedPermissions.add(perm);
                }
            }
        }
        ... ...
        return pkg;
    }
```
# Step18: PackageParser::parseBaseApplication(...)
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
回到Step11中，在调用PackageParser::parsePackage(...)解析完应用程序后，接下来调用PackageManagerService::scanPackageLI获得将前面解析到的app的组件配置信息，并为app分配UID。
# Step19: PackageManagerService::scanPackageLI(...)
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
            final PackageParser.Package res = scanPackageDirtyLI(pkg, parseFlags, scanFlags,
                    currentTime, user);
            success = true;
            return res;
        ... ...
    }
```
# Step20: PackageManagerService::scanPackageDirtyLI(...)
``` java
private PackageParser.Package scanPackageDirtyLI(PackageParser.Package pkg, int parseFlags,
            int scanFlags, long currentTime, UserHandle user) throws PackageManagerException {
        ... ...
        SharedUserSetting suid = null;
        PackageSetting pkgSetting = null;
        ... ...
        // 为pkg所描述的应用程序分配UID
        synchronized (mPackages) {
            if (pkg.mSharedUserId != null) {// 检查pkg是否指定了要与其它app共享UID
                // 🏁Step21 获得被共享的UID
                suid = mSettings.getSharedUserLPw(pkg.mSharedUserId, 0, 0, true);
                ... ...
            }
            ... ...
            // 🏁Step22 为pkg描述的应用程序分配一个UID
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
# Step21: Settings::getSharedUserLPw(...)
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
# Step22: Settings::getPackageLPw(...)
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
## Step22.1 Settings::getPcakageLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/Settings.java:3565
    private PackageSetting getPackageLPw(String name, PackageSetting origPackage,
            String realName, SharedUserSetting sharedUser, File codePath, File resourcePath,
            String legacyNativeLibraryPathString, String primaryCpuAbiString,
            String secondaryCpuAbiString, int vc, int pkgFlags, int pkgPrivateFlags,
            UserHandle installUser, boolean add, boolean allowInstall) {
        // 系统所有应用程序的安装信息都保存在mPackages中
        PackageSetting p = mPackages.get(name);
        UserManagerService userManager = UserManagerService.getInstance();
        if (p != null) {
            ... ...
            // p是否与其他app共享同一个UID，且其sharedUser是否与sharedUser相同
            // 如果不相同，p就不能用来描述名称为name的应用程序的安装信息
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
# Step23: Settings::newUserIdLPw(...)
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
接下来返回到Step2中，调用PackageManagerService::updatePermissionLPw(...)为前面安装的app分配用户组ID，授予它们所申请的资源的访问权限，尔后就可以调用Settings::writeLPr()将这些应用程序的安装信息保存在本地了。
# Step24: PackageManagerService::updatePermissionLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:8244
    private void updatePermissionsLPw(String changingPkg, PackageParser.Package pkgInfo,
            int flags) {
        final String volumeUuid = (pkgInfo != null) ? getVolumeUuidForPackage(pkgInfo) : null;
        updatePermissionsLPw(changingPkg, pkgInfo, volumeUuid, flags);
    }
```
调用了重载函数。
## Step24.1: PackageManagerService::updatePermissionLPw(...)
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
系统在`/system/etc/permissions/platform.xml`中保存着系统中的资源访问权限列表，内容如下：
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

    <permission name="android.permission.NET_TUNNELING" >
        <group gid="vpn" />
    </permission>

    <permission name="android.permission.INTERNET" >
        <group gid="inet" />
    </permission>

    <permission name="android.permission.READ_LOGS" >
        <group gid="log" />
    </permission>

    <permission name="android.permission.WRITE_MEDIA_STORAGE" >
        <group gid="media_rw" />
        <group gid="sdcard_rw" />
    </permission>

    <permission name="android.permission.ACCESS_MTP" >
        <group gid="mtp" />
    </permission>

    <permission name="android.permission.NET_ADMIN" >
        <group gid="net_admin" />
    </permission>

    <permission name="android.permission.ACCESS_CACHE_FILESYSTEM" >
        <group gid="cache" />
    </permission>

    <permission name="android.permission.DIAGNOSTIC" >
        <group gid="input" />
        <group gid="diag" />
    </permission>

    <permission name="android.permission.READ_NETWORK_USAGE_HISTORY">
        <group gid="net_bw_stats" />
    </permission>

    <permission name="android.permission.MODIFY_NETWORK_ACCOUNTING">
        <group gid="net_bw_acct" />
    </permission>

    <permission name="android.permission.LOOP_RADIO" >
        <group gid="loop_radio" />
    </permission>

    <permission name="android.permission.MANAGE_VOICE_KEYPHRASES">
        <group gid="audio" />
    </permission>

    <permission name="android.permission.ACCESS_FM_RADIO" >
        <group gid="media" />
    </permission>

    <assign-permission name="android.permission.MODIFY_AUDIO_SETTINGS" uid="media" />
    <assign-permission name="android.permission.ACCESS_SURFACE_FLINGER" uid="media" />
    <assign-permission name="android.permission.WAKE_LOCK" uid="media" />
    <assign-permission name="android.permission.UPDATE_DEVICE_STATS" uid="media" />
    <assign-permission name="android.permission.UPDATE_APP_OPS_STATS" uid="media" />

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
# Step25: PackageManagerService::grantPermissionsLPw(...)
``` java
// frameworks/base/services/core/java/com/android/server/pm/PackageManagerService.java:8338
    private void grantPermissionsLPw(PackageParser.Package pkg, boolean replace,
            String packageOfInterest) {
        // IMPORTANT: There are two types of permissions: install and runtime.
        // Install time permissions are granted when the app is installed to
        // all device users and users added in the future. Runtime permissions
        // are granted at runtime explicitly to specific users. Normal and signature
        // protected permissions are install time permissions. Dangerous permissions
        // are install permissions if the app's target SDK is Lollipop MR1 or older,
        // otherwise they are runtime permissions. This function does not manage
        // runtime permissions except for the case an app targeting Lollipop MR1
        // being upgraded to target a newer SDK, in which case dangerous permissions
        // are transformed from install time to runtime ones.

        final PackageSetting ps = (PackageSetting) pkg.mExtras;
        if (ps == null) {
            return;
        }

        PermissionsState permissionsState = ps.getPermissionsState();
        PermissionsState origPermissions = permissionsState;

        final int[] currentUserIds = UserManagerService.getInstance().getUserIds();

        boolean runtimePermissionsRevoked = false;
        int[] changedRuntimePermissionUserIds = EMPTY_INT_ARRAY;

        boolean changedInstallPermission = false;

        if (replace) {
            ps.installPermissionsFixed = false;
            if (!ps.isSharedUser()) {
                origPermissions = new PermissionsState(permissionsState);
                permissionsState.reset();
            } else {
                // We need to know only about runtime permission changes since the
                // calling code always writes the install permissions state but
                // the runtime ones are written only if changed. The only cases of
                // changed runtime permissions here are promotion of an install to
                // runtime and revocation of a runtime from a shared user.
                changedRuntimePermissionUserIds = revokeUnusedSharedUserPermissionsLPw(
                        ps.sharedUser, UserManagerService.getInstance().getUserIds());
                if (!ArrayUtils.isEmpty(changedRuntimePermissionUserIds)) {
                    runtimePermissionsRevoked = true;
                }
            }
        }

        permissionsState.setGlobalGids(mGlobalGids);

        final int N = pkg.requestedPermissions.size();
        for (int i=0; i<N; i++) {
            final String name = pkg.requestedPermissions.get(i);
            final BasePermission bp = mSettings.mPermissions.get(name);

            if (DEBUG_INSTALL) {
                Log.i(TAG, "Package " + pkg.packageName + " checking " + name + ": " + bp);
            }

            if (bp == null || bp.packageSetting == null) {
                if (packageOfInterest == null || packageOfInterest.equals(pkg.packageName)) {
                    Slog.w(TAG, "Unknown permission " + name
                            + " in package " + pkg.packageName);
                }
                continue;
            }

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

            final int level = bp.protectionLevel & PermissionInfo.PROTECTION_MASK_BASE;
            switch (level) {
                case PermissionInfo.PROTECTION_NORMAL: {
                    // For all apps normal permissions are install time ones.
                    grant = GRANT_INSTALL;
                } break;

                case PermissionInfo.PROTECTION_DANGEROUS: {
                    if (pkg.applicationInfo.targetSdkVersion <= Build.VERSION_CODES.LOLLIPOP_MR1) {
                        // For legacy apps dangerous permissions are install time ones.
                        grant = GRANT_INSTALL_LEGACY;
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
                    allowedSig = grantSignaturePermission(perm, pkg, bp, origPermissions);
                    if (allowedSig) {
                        grant = GRANT_INSTALL;
                    }
                } break;
            }

            if (DEBUG_INSTALL) {
                Log.i(TAG, "Package " + pkg.packageName + " granting " + perm);
            }

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

                    default: {
                        if (packageOfInterest == null
                                || packageOfInterest.equals(pkg.packageName)) {
                            Slog.w(TAG, "Not granting permission " + perm
                                    + " to package " + pkg.packageName
                                    + " because it was previously installed without");
                        }
                    } break;
                }
            } else {
                if (permissionsState.revokeInstallPermission(bp) !=
                        PermissionsState.PERMISSION_OPERATION_FAILURE) {
                    // Also drop the permission flags.
                    permissionsState.updatePermissionFlags(bp, UserHandle.USER_ALL,
                            PackageManager.MASK_PERMISSION_FLAGS, 0);
                    changedInstallPermission = true;
                    Slog.i(TAG, "Un-granting permission " + perm
                            + " from package " + pkg.packageName
                            + " (protectionLevel=" + bp.protectionLevel
                            + " flags=0x" + Integer.toHexString(pkg.applicationInfo.flags)
                            + ")");
                } else if ((bp.protectionLevel&PermissionInfo.PROTECTION_FLAG_APPOP) == 0) {
                    // Don't print warning for app op permissions, since it is fine for them
                    // not to be granted, there is a UI for the user to decide.
                    if (packageOfInterest == null || packageOfInterest.equals(pkg.packageName)) {
                        Slog.w(TAG, "Not granting permission " + perm
                                + " to package " + pkg.packageName
                                + " (protectionLevel=" + bp.protectionLevel
                                + " flags=0x" + Integer.toHexString(pkg.applicationInfo.flags)
                                + ")");
                    }
                }
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