MY_ANDROID_JAR=~/Library/Android/sdk/platforms/android-25/android.jar
MY_PACKAGEPATH=palance/li/hello
MY_APKNAME=HelloAndroid
MY_JAVA_FILES=src/$MY_PACKAGEPATH/MainActivity.java
MY_PROJDIR=$(cd "$(dirname "$0")"; pwd)

##  **** 打包脚本 ****
echo "**** 1. 将工程的资源编译到R.java ****"
if [ -d "gen" ]; then
	echo "rm [gen]"
	rm -rf gen
fi
mkdir gen

aapt package -f -m -J gen -S res -I $MY_ANDROID_JAR -M AndroidManifest.xml

echo "**** 2. 编译java源文件 ****"
if [ -d "bin" ]; then
	echo "rm [bin]"
	rm -rf bin
fi
echo "mkdir [bin] [bin/classes]"
mkdir bin
mkdir bin/classes
javac -encoding utf-8 -source 1.6 -target 1.6 -bootclasspath $MY_ANDROID_JAR \
	-d bin/classes $MY_JAVA_FILES gen/$MY_PACKAGEPATH/R.java

echo "**** 3. 将编译好的文件打包成dex格式 ****"
dx --dex --output=bin/classes.dex bin/classes

echo "**** 4. 创建未签名的apk文件 ****"
if [ -d "assets" ]; then
	echo "rm [assets]"
	rm -rf assets
fi
echo "mkdir [assets]"
mkdir assets
echo "aapt package -f -M AndroidManifest.xml -S res -A assets -I $MY_ANDROID_JAR -F bin/"$MY_APKNAME"_unsigned.apk"
aapt package -f -M AndroidManifest.xml -S res -A assets -I $MY_ANDROID_JAR -F bin/$MY_APKNAME"_unsigned.apk"

echo "**** 4.1 添加dex文件 ****"
cd $MY_PROJDIR"/bin"
aapt add $MY_APKNAME"_unsigned.apk" classes.dex
cd $MY_PROJDIR

echo "**** 4.2 添加so文件 ****"
if [ ! -f "libs/x86_64/libhellojni.so" ]; then
	echo '.so not found, exit!'
	exit
fi
mv libs lib
aapt add bin/$MY_APKNAME"_unsigned.apk" lib/x86_64/libhellojni.so
mv lib libs

echo "**** 5. 对apk文件签名 ****"
jarsigner -verbose -keystore ~/.android/debug.keystore -keypass android -storepass android \
	-signedjar bin/$MY_APKNAME"_signed.apk" bin/$MY_APKNAME"_unsigned.apk" androiddebugkey

echo "**** 6. 优化对齐 ****"
zipalign -f 4 bin/$MY_APKNAME"_signed.apk" bin/$MY_APKNAME".apk"

rm -f bin/$MY_APKNAME"_signed.apk"
rm -f bin/$MY_APKNAME"_unsigned.apk"
