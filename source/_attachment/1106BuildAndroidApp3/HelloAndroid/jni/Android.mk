LOCAL_PATH:=$(call my-dir)
include $(CLEAR_VARS)

LOCAL_MODULE := libhellojni
LOCAL_SRC_FILES := \
    palance_li_hello_MainActivity.c

LOCAL_C_INCLUDES += \
    $(JNI_H_INCLUDE)

include $(BUILD_SHARED_LIBRARY)