# !/bin/bash
# sh ln2android.sh <android-dir>

my_dir=$(cd "$(dirname "$0")"; pwd)
android_dir=$1
#slink=$android_dir/packages/experimental/HelloAndroid
slink=$android_dir/development/samples/HelloAndroid
echo "my_dir:     " $my_dir
echo "android_dir:" $android_dir
echo "slink:      " $slink

if [ -L $slink ]; then
	rm -fr $slink
fi

ln -s $my_dir $slink
