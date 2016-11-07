#include <string.h>
#include "palance_li_hello_MainActivity.h"
JNIEXPORT jstring JNICALL Java_palance_li_hello_MainActivity_stringFromJNI(JNIEnv* env, jobject _this)
{
    return (*env)->NewStringUTF(env, "This is from JNI!");
}