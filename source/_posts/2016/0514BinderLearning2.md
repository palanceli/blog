---
layout: post
title:  "Binder学习笔记（二）—— defaultServiceManager()返回了什么？"
date:   2016-05-07 00:39:48 +0800
categories: Android
tags:   binder
---
不管是客户端还是服务端，头部都要先调用
``` c++
sp < IServiceManager > sm = defaultServiceManager();
```
defaultServiceManager()都干了什么，它返回的是什么实例呢？
该函数定义在frameworks/native/libs/binder/IserviceManager.cpp:33
``` c++
sp<IServiceManager> defaultServiceManager()
{
    if (gDefaultServiceManager != NULL) return gDefaultServiceManager;
    
    {
        AutoMutex _l(gDefaultServiceManagerLock);
        while (gDefaultServiceManager == NULL) {
            gDefaultServiceManager = interface_cast<IServiceManager>(
                ProcessState::self()->getContextObject(NULL));  // 这里才是关键步骤
            if (gDefaultServiceManager == NULL)
                sleep(1);
        }
    }
    
    return gDefaultServiceManager;
}
```
关键步骤可以分解为几步：1、ProcessState::self()，2、ProcessState::getContextObject(…)，3、interface_cast<IserviceManager>(…)

# ProcessState::self()
frameworks/native/libs/binder/ProcessState.cpp:70 
``` c++
sp<ProcessState> ProcessState::self()  // 这又是一个进程单体
{
    Mutex::Autolock _l(gProcessMutex);
    if (gProcess != NULL) {
        return gProcess;
    }
    gProcess = new ProcessState;  // 首次创建在这里
    return gProcess;
}
```
ProcessState的构造函数很简单，frameworks/native/libs/binder/ProcessState.cpp:339
``` c++
ProcessState::ProcessState()
    : mDriverFD(open_driver())  // 这里打开了/dev/binder文件，并返回文件描述符
    , mVMStart(MAP_FAILED)
    , mThreadCountLock(PTHREAD_MUTEX_INITIALIZER)
    , mThreadCountDecrement(PTHREAD_COND_INITIALIZER)
    , mExecutingThreadsCount(0)
    , mMaxThreads(DEFAULT_MAX_BINDER_THREADS)
    , mManagesContexts(false)
    , mBinderContextCheckFunc(NULL)
    , mBinderContextUserData(NULL)
    , mThreadPoolStarted(false)
    , mThreadPoolSeq(1)
{
    if (mDriverFD >= 0) {
        // XXX Ideally, there should be a specific define for whether we
        // have mmap (or whether we could possibly have the kernel module
        // availabla).
#if !defined(HAVE_WIN32_IPC)
        // mmap the binder, providing a chunk of virtual address space to receive transactions.
        mVMStart = mmap(0, BINDER_VM_SIZE, PROT_READ, MAP_PRIVATE | MAP_NORESERVE, mDriverFD, 0);
        if (mVMStart == MAP_FAILED) {
            // *sigh*
            ALOGE("Using /dev/binder failed: unable to mmap transaction memory.\n");
            close(mDriverFD);
            mDriverFD = -1;
        }
#else
        mDriverFD = -1;
#endif
    }

    LOG_ALWAYS_FATAL_IF(mDriverFD < 0, "Binder driver could not be opened.  Terminating.");
}
```
ProcessState的构造函数主要完成两件事：1、初始化列表里调用opern_driver()，打开了文件/dev/binder；2、将文件映射到内存。ProcessState::self()返回单体实例。

# ProcessState::getContextObject(…)
该函数定义在frameworks/native/libs/binder/ProcessState.cpp:85
``` c++
sp<IBinder> ProcessState::getContextObject(const sp<IBinder>& /*caller*/)
{
    return getStrongProxyForHandle(0);
}
```
继续深入，frameworks/native/libs/binder/ProcessState/cpp:179
``` c++
sp<IBinder> ProcessState::getStrongProxyForHandle(int32_t handle)
{
    sp<IBinder> result;

    AutoMutex _l(mLock);

    handle_entry* e = lookupHandleLocked(handle);  //正常情况下总会返回一个非空实例

    if (e != NULL) {
        // We need to create a new BpBinder if there isn't currently one, OR we
        // are unable to acquire a weak reference on this current one.  See comment
        // in getWeakProxyForHandle() for more info about this.
        IBinder* b = e->binder;
        if (b == NULL || !e->refs->attemptIncWeak(this)) {
            if (handle == 0) {  // 首次创建b为NULL，handle为0
                // Special case for context manager...
                // The context manager is the only object for which we create
                // a BpBinder proxy without already holding a reference.
                // Perform a dummy transaction to ensure the context manager
                // is registered before we create the first local reference
                // to it (which will occur when creating the BpBinder).
                // If a local reference is created for the BpBinder when the
                // context manager is not present, the driver will fail to
                // provide a reference to the context manager, but the
                // driver API does not return status.
                //
                // Note that this is not race-free if the context manager
                // dies while this code runs.
                //
                // TODO: add a driver API to wait for context manager, or
                // stop special casing handle 0 for context manager and add
                // a driver API to get a handle to the context manager with
                // proper reference counting.

                Parcel data;
                status_t status = IPCThreadState::self()->transact(
                        0, IBinder::PING_TRANSACTION, data, NULL, 0);
                if (status == DEAD_OBJECT)
                   return NULL;
            }

            b = new BpBinder(handle); 
            e->binder = b;
            if (b) e->refs = b->getWeakRefs();
            result = b;  // 返回的是BpBinder(0)
        } else {
            // This little bit of nastyness is to allow us to add a primary
            // reference to the remote proxy when this team doesn't have one
            // but another team is sending the handle to us.
            result.force_set(b);
            e->refs->decWeak(this);
        }
    }

    return result;
}
```
因此getStrongProxyForHandle(0)返回的就是new BpBinder(0)。有几处细节可以再回头关注一下：
## ProcessState::lookupHandleLocked(int32_t handle)
该函数定义在frameworks/native/libs/binder/ProcessState.cpp:166
``` c++
ProcessState::handle_entry* ProcessState::lookupHandleLocked(int32_t handle)
{
    const size_t N=mHandleToObject.size();
    if (N <= (size_t)handle) {
        handle_entry e;
        e.binder = NULL;
        e.refs = NULL;
        status_t err = mHandleToObject.insertAt(e, N, handle+1-N);
        if (err < NO_ERROR) return NULL;
    }
    return &mHandleToObject.editItemAt(handle);
}
```
成员变量mHandleToObject是一个数组
``` c++
Vector<handle_entry>mHandleToObject;
```
该函数遍历数组查找handle，如果没找到则会向该数组中插入一个新元素，handle是数组下标。新元素的binder、refs成员默认均为NULL，在getStrongProxyForHandle(…)中会被赋值。
# interface_cast<IserviceManager>(…)
interface_cast(…)函数在binder体系中非常常用，后面还会不断遇见。该函数定义在frameworks/native/include/binder/IInterface.h:41
``` c++
template<typename INTERFACE>
inline sp<INTERFACE> interface_cast(const sp<IBinder>& obj)
{
    return INTERFACE::asInterface(obj);
}
```
代入模板参数及实参后为：
``` c++
IServiceManager::asInterface(new BpBinder(0));
```
该函数藏在宏IMPLEMENT_META_INTERFACE中，frameworks/native/libs/binder/IServiceManager.cpp:185
``` c++
IMPLEMENT_META_INTERFACE(ServiceManager, "android.os.IServiceManager");
```
展开后为：
``` c++
android::sp< IServiceManager > IServiceManager::asInterface(
            const android::sp<android::IBinder>& obj)
    {
        android::sp< IServiceManager > intr;
        if (obj != NULL) {
            intr = static_cast< IServiceManager *>( 
                obj->queryLocalInterface(IServiceManager::descriptor).get());
            if (intr == NULL) {  // 首次会走这里
                intr = new BpServiceManager(obj);
            }
        }
        return intr;
    }
```
因此它返回的就是new BpServiceManager(new BpBinder(0))。
> 经过层层抽丝剥茧之后，defaultServiceManager()的返回值即为new BpServiceManager(new BpBinder(0))。
> 

我们再顺道看一下BpServiceManager的继承关系以及构造函数，frameworks/native/libs/binder/IServiceManager.cpp:126
``` c++
class BpServiceManager : public BpInterface<IServiceManager>
```
frameworks/native/libs/binder/IInterface.h:62
``` c++
template<typename INTERFACE>
class BpInterface : public INTERFACE, public BpRefBase
```
BpServiceManager继承自BpInterface，后者继承自BpRefBase。
frameworks/native/libs/binder/IServiceManager.cpp:129
``` c++
    BpServiceManager(const sp<IBinder>& impl)
        : BpInterface<IServiceManager>(impl)
    {
    }
```
frameworks/native/include/binder/IInterface.h:134
``` c++
template<typename INTERFACE>
inline BpInterface<INTERFACE>::BpInterface(const sp<IBinder>& remote)
    : BpRefBase(remote)
{
}
```
frameworks/native/libs/binder/Binder.cpp:241
``` c++
BpRefBase::BpRefBase(const sp<IBinder>& o)
    : mRemote(o.get()), mRefs(NULL), mState(0)
{
    extendObjectLifetime(OBJECT_LIFETIME_WEAK);

    if (mRemote) {
        mRemote->incStrong(this);           // Removed on first IncStrong().
        mRefs = mRemote->createWeak(this);  // Held for our entire lifetime.
    }
}
```
BpServiceManager通过构造函数，沿着继承关系一路将impl参数传递给基类BpRefBase，基类将它赋给数据成员mRemote。在defaultServiceManager()中传给BpServiceManager构造函数的参数是new BpBinder(0)。

