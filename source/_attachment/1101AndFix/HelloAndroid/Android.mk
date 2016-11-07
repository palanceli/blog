
TOP_LOCAL_PATH:= $(call my-dir)

LOCAL_PATH:= $(TOP_LOCAL_PATH)
include $(CLEAR_VARS)

LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := $(call all-subdir-java-files)
LOCAL_PACKAGE_NAME := HelloAndroid
LOCAL_JNI_SHARED_LIBRARIES := andfix
LOCAL_PROGUARD_ENABLED := disabled

LOCAL_SDK_VERSION := current
include $(BUILD_PACKAGE)

# ============================================================

# Also build all of the sub-targets under this one: the shared library.
include $(call all-makefiles-under,$(LOCAL_PATH))