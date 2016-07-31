---
layout: post
title:  "深入浅出Binder（一）"
date:   2016-07-28 00:11:32 +0800
categories: Android
tags:   binder
toc: true
comments: true
---
# 取款机模型
Binder机制就像一个取款机，Client、Server、ServiceManager和驱动层分别就是客户、银行、取款机和每个银行的程序。
* 要想让取款机可以受理某个银行的卡，银行必须先向取款机注册，把自己的程序注册进去。这就是Server端要先调用addService完成注册，ServiceManager会保存服务名称以及对应的服务“实体”。
* 之后客户就可以把银行卡塞入取款机获取服务，取款机会根据银行卡找到对应的银行服务程序。Client调用checkService，ServiceManager查找之前保存的注册信息，找到和名称匹配的服务“实体”，并返回给客户端。
* 在客户看似是对自己的银行卡操作，而实际上操作的是银行的数据库。这张卡就是BPBinder，是代理；银行账户是BBinder，是服务本尊。在Client端和ServiceManager端拿到的服务“实体”实际上只是在自己进程空间内的UID，通过该UID可以提领到位于Server进程空间的Service对象。这也是前面给“实体”加引号的原因，我们称之为代理。通过BPBinder调用Binder接口看似是个本地函数调用，实际上是在Server端执行了一段代码。
* 对银行卡的存、取、查询都会被程序封装成银行可识别的账号+存、取、查询操作，银行完成对数据库的操作后，程序返回给客户的是客户名称+操作结果，它需要在客户可识别的客户名称和银行可识别的账户之间做转换。驱动程序也是一样的，Client端本质上操作的是handle，即前面的讲的UID，仅在Client进程空间内唯一，该操作到了驱动层，会把handle修改成在Server进程空间内唯一的Service的对象地址或影子对象的地址，然后再由Server端根据地址提领到Service对象，执行对应的操作。
* 传统的银行操作，需要客户填单子交给柜台，柜台再把信息誊写到银行账本上去（这个流程是我YY的~），而现在只需要客户录入一次信息，后面的数据流转都是在这份信息的基础上完成的，没有再做数据的复制。传统的进程间通信，需要先将由发起端拷贝到内核，再由内核拷贝到接收端；而Binder机制仅有一次数据拷贝，就是从Client端拷贝到内核驱动层，接下来驱动层直接把数据映射到Server的进程空间，而不是拷贝过去，因此性能更好。

接下来以使用Binder的关键步骤为主线，阐述framework层和驱动层是怎样共同完成Binder机制的。本文采用的Android源码是基于6.0.1_r11，所有调试代码都可在[palanceli/androidex/external-testservice](https://github.com/palanceli/androidex/tree/master/external-testservice)获取。

# 注册服务
无论是服务端还是客户端，在使用Binder机制之前都必须找到取款机，即ServiceManager：
``` c
sp < ProcessState > proc(ProcessState::self());
sp < IServiceManager > sm = defaultServiceManager(); 
```
智能指针在本系列中不再赘述，参见[《Binder学习笔记（十一）—— 智能指针》](http://palanceli.github.io/blog/2016/06/10/2016/0610BinderLearning11/)，在framework层所有Binder相关的智能指针`sp <XXX> pObj`都可以当`XXX *pObj`来看。

sm是什么？为什么defaultServiceManager()就能返回ServiceManager？本质上ServiceManager也是Binder服务，位于另一个进程空间，为什么这么一行调用就能获取另一个进程空间的服务？这个“服务”具体是什么，实体？handle？
我们先给出答案，再逐步求证。

Binder Service对象只存在于Server的进程空间里，当Client端请求Service时，驱动程序会分配一个在该Client进程空间内唯一的整形数又叫handle，并将该handle和Service对象地址的对应关系缓存在内核空间。Client端的BPBinder本质上是对该handle的封装，所有对远程Binder的调用都会通过BPBinder被封装成一坨数据通过驱动层到达Server，驱动层在这坨数据到达Server前把handle改成Service地址，Server通过改地址提领到Service对象，执行请求。

ServiceManager是handle=0的Binder，它保存着系统内所有注册的Binder，只有通过它才能找到其他Binder。它是一切Binder的起点，因此必须hard code一个固定值，以便所有进程都能直接得到它，很自然这个固定值是0。
sm是handle=0的BPBinder，为什么对它的调用可以被转到进程ServiceManager呢？因为BPBinder会把调用打包成数据写入文件`/dev/binder`。每个进程都可以通过BPBinder打开这个文件，但驱动层确保每个进程打开的该文件是不同的，其内容是各进程一份的。如果一个进程打开两次呢？首先驱动层确保实际打开的是同一份数据，其次应用层的ProcessState以进程单体的方式确保进程内只打开一次。数据包进入驱动层后，驱动层会根据目标handle找到对应的Server进程，把数据包交由Server处理。

## 初始化proc
proc指向ProcessState::self()，这是一个进程单体，它返回一个ProcessState实例。在ProcessState的构造函数中有两个关键步骤：1、打开`/dev/binder`文件；2、将该文件映射到自己的地址空间。
``` c++
// frameworks/native/libs/binder/ProcessState.cpp 井号+数字表示行号
// #70
sp<ProcessState> ProcessState::self()  // 进程单体
{
    ... ...
    if (gProcess != NULL) {
        return gProcess;
    }
    gProcess = new ProcessState;  // 首次创建在这里
    return gProcess;
}

// #339
ProcessState::ProcessState()
    : mDriverFD(open_driver())  // 这里打开了/dev/binder文件，并返回文件描述符
    ... ...
{
    ... ...
    mVMStart = mmap(0, BINDER_VM_SIZE, PROT_READ, MAP_PRIVATE | MAP_NORESERVE, mDriverFD, 0);
    ... ...
}

// #311
static int open_driver()
{
    int fd = open("/dev/binder", O_RDWR);
    ... ...
    return fd;
}
```
通常打开一个磁盘上的文件，不管是由谁打开的，只要路径相同，所指的就是同一个文件，读写的也是同一坨数据。可是Binder不一样，规定统一的路径`dev/binder`只是为了让所有端获取Binder的方式一致，实际上每个进程获取的内容是不同的。就好像大家都通过同一个电话号码95555获得招商银行的客服，但实际上每个人分配到的客服小妹是不同的。只是在Binder的世界更极端，每个进程打开文件`dev/binder`都是不同的。可以进入到驱动层来证实这一点。

### 打开/dev/binder
应用层调用`open("/dev/binder")`最终对落地到驱动层的`binder_open(...)`调用上来，中间的流转过程是驱动层的知识，可以参见《Linux设备驱动程序》，我们直接进入`binder_open(...)`函数：
``` c++
// kernel/drivers/staging/android/binder.c
// #2979
static int binder_open(struct inode *nodp, struct file *filp)
{
    struct binder_proc *proc;
    ......
    proc = kzalloc(sizeof(*proc), GFP_KERNEL); // 创建binder_proc结构体
    ......
    filp->private_data = proc;
    ......
    return 0;
}
```
结构体`struct file`表示进程已打开的文件，包含访问模式、当前偏移等信息（参见《Linux内核设计与实现（第三版）》第13章11节），这说明对于同一个文件`struct file`是每进程一份的。
`binder_open(...)`函数创建了结构体`struct binder_proc`并将之保存在文件对象的private_data成员中。[struct binder_proc](http://palanceli.github.io/blog/2016/06/14/2016/0614BinderLearning12/#struct-binder-proc)描述一个正在使用Binder的进程。

### 映射/dev/binder
ProcessState在初始化列表中打开`/dev/binder`后，在构造函数体内立刻调用`mmap`完成映射，该函数最终落地在驱动层的`binder_mmap(...)`函数：
``` c++
// kernel/goldfish/drivers/staging/android/binder.c
// #2883
static int binder_mmap(struct file *filp, struct vm_area_struct *vma)
{
    int ret;
    struct vm_struct *area;
    struct binder_proc *proc = filp->private_data;
    const char *failure_string;
    struct binder_buffer *buffer;
    ... ...
    // 分配内核地址空间
    area = get_vm_area(vma->vm_end - vma->vm_start, VM_IOREMAP);
    ... ...
    proc->buffer = area->addr;
    proc->user_buffer_offset = vma->vm_start - (uintptr_t)proc->buffer;
    ... ...
    // 分配物理页面结构体指针数组
    proc->pages = kzalloc(sizeof(proc->pages[0]) * ((vma->vm_end - vma->vm_start) / PAGE_SIZE), GFP_KERNEL);
    ... ...
    proc->buffer_size = vma->vm_end - vma->vm_start;

    vma->vm_ops = &binder_vm_ops;
    vma->vm_private_data = proc;
    // 为proc->pages数组的每个元素创建物理页面，并将之同时映射到用户和内核地址空间
    if (binder_update_page_range(proc, 1, proc->buffer, proc->buffer + PAGE_SIZE, vma)) {
        ... ...
    }
    buffer = proc->buffer;
    INIT_LIST_HEAD(&proc->buffers);
    list_add(&buffer->entry, &proc->buffers);
    buffer->free = 1;
    binder_insert_free_buffer(proc, buffer);
    proc->free_async_space = proc->buffer_size / 2;
    barrier();
    proc->files = get_files_struct(proc->tsk);
    proc->vma = vma;
    proc->vma_vm_mm = vma->vm_mm;
    ... ...
    return 0;
... ...
}
```
该映射操作为Binder分配物理页面，并将页面同时映射到内核和用户地址空间。
这块内存空间就为未来数据包传输铺设的轨道，只是这条轨道对于Client或Server端来说都通往一个时光隧道，这个时光隧道就是驱动层。数据包里注明了数据要发往何处，数据进入隧道后就不见了，驱动层会根据数据包里的目的地址把数据包列车放到目的端的时光隧道出口，这样目的端就能源源不断地看到数据列车从隧道口驶来。
将页面同时映射到内核和用户地址空间的目的是为了提升效率。出于安全的考虑，从用户空间发往内核空间的数据应该使用`copy_from_user(...)`函数拷贝到内核空间，在内核驱动层处理完数据后没有必要再用`copy_to_user(...)`拷贝到对端，因此双重映射使得数据可被对端访问，且减少一次数据拷贝的开销。

## 初始化sm
完成轨道铺设后，就要建设跑在上面的火车了，其实火车原本都是一样的，但是客户端会根据发往的目的地不同给他们做成不同的封装，例如发往ServiceManager号的会被封装成sp<IServiceManager>，发往TestService号的会被封装成sp<ITestService>等等。接下来看`sp<IServiceManager> sm`，它是函数`defaultServiceManager()`的返回值：
``` c++
// frameworks/native/libs/binder/IServiceManager.cpp
// #33
sp<IServiceManager> defaultServiceManager()
{   // 又是个进程单体
    if (gDefaultServiceManager != NULL) return gDefaultServiceManager;
        ... ...
    gDefaultServiceManager = interface_cast<IServiceManager>(
        ProcessState::self()->getContextObject(NULL));  
        ... ...
    
    return gDefaultServiceManager;
}
```
### ProcessState::getContextObject(NULL)装配成火车
函数`ProcessState::self()`已经讲过了，来看它的`getContextObject(NULL)`函数：
``` c++
// frameworks/native/libs/binder/ProcessState.cpp
// #85
sp<IBinder> ProcessState::getContextObject(const sp<IBinder>& /*caller*/)
{
    return getStrongProxyForHandle(0);
}
// #179
sp<IBinder> ProcessState::getStrongProxyForHandle(int32_t handle)
{
    sp<IBinder> result;
    ... ...
    handle_entry* e = lookupHandleLocked(handle); //正常情况下总会返回一个非空实例
        ... ...
        IBinder* b = e->binder; 
        if (b == NULL || !e->refs->attemptIncWeak(this)) {// 如果首次创建，b==NULL
            ... ...
            b = new BpBinder(handle); // 即BpBinder(0)
            e->binder = b;
            if (b) e->refs = b->getWeakRefs();
            result = b;
        } 
        ... ...

    return result;
}
// #166
ProcessState::handle_entry* ProcessState::lookupHandleLocked(int32_t handle)
{
    const size_t N=mHandleToObject.size();  // 这是个以handle为下标的数组
    if (N <= (size_t)handle) {              // 如果没有则插入
        handle_entry e;
        e.binder = NULL;
        e.refs = NULL;
        status_t err = mHandleToObject.insertAt(e, N, handle+1-N);
        if (err < NO_ERROR) return NULL;
    }
    return &mHandleToObject.editItemAt(handle);
}
```
函数`getContextObject(NULL)`只是返回了`BpBinder(0)`的实例而已。

### interface_cast(...)把普通火车封装成XX号
其实前面`BpBinder(0)`已经是在普通火车上装配了目的地数据，参数0就是，接下来的转型操作是进一步把它刷成`XX号`。
``` c++
// frameworks/native/include/binder/IInterface.h
// #41
template<typename INTERFACE>
inline sp<INTERFACE> interface_cast(const sp<IBinder>& obj)
{   // INTERFACE=IServiceManager
    // obj=ProcessState::self()->getContextObject(NULL)，即
    // new BpBinder(0)

    return INTERFACE::asInterface(obj);
    // 代入模板参数即：
    // return IServiceManager::asInterface(new BpBinder(0));
}
```
`IServiceManager::asInterface(...)`函数的定义隐藏在一个宏里：
``` c++
// frameworks/native/libs/binder/IServiceManager.cpp
// #185
IMPLEMENT_META_INTERFACE(ServiceManager, "android.os.IServiceManager");
```
该宏定义在`frameworks/native/include/binder/IInterface.h:83`展开后为：
``` c++
const android::String16 IServiceManager::descriptor("android.os.IServiceManager");
const android::String16& IServiceManager::getInterfaceDescriptor() const {
    return IServiceManager::descriptor;
}
android::sp< IServiceManager > IServiceManager::asInterface(
            const android::sp<android::IBinder>& obj)
    {   // obj=new BpBinder(0)
        android::sp< IServiceManager > intr;
        if (obj != NULL) {
            intr = static_cast< IServiceManager *>( 
                obj->queryLocalInterface(IServiceManager::descriptor).get());
            if (intr == NULL) {  // 对于BpBinder类型的智能指针来说总为NULL
                intr = new BpServiceManager(obj);
            }
        }
        return intr;
    }
```
`BpBinder`继承自`IBinder`，
``` c++
// frameworks/native/libs/binder/Binder.cpp
// #42
sp<IInterface>  IBinder::queryLocalInterface(const String16& /*descriptor*/)
{
    return NULL;
}
```
也就是说`obj->queryLocalInterface(IServiceManager::descriptor)`返回NULL，又怎么能调用其get()成员函数呢？注意，此处需要考虑智能指针，obj实际上是指向空的智能指针，参见`system/core/include/utils/StrongPointer.h:89`，其`get()`函数就返回实际指向的对象，即为NULL。
所以`asInterface(...)`的返回值即`new BpServiceManager(new BpBinder(0))`这不就是拿SM号封装的普通火车嘛。`class BpServiceManager`定义在`frameworks/native/libs/IServiceManager.cpp:126`，沿着派生族谱层层向上追溯构造函数：
``` c++
// frameworks/natvie/libs/binder/IServiceManager.cpp:129
BpServiceManager(const sp<IBinder>& impl)       // impl=new BpBinder(0) 
    : BpInterface<IServiceManager>(impl)
{
}
// frameworks/native/include/binder/IInterface.h:134
template<typename INTERFACE>
inline BpInterface<INTERFACE>::BpInterface(const sp<IBinder>& remote)
    : BpRefBase(remote)                         // remote = new BpBinder(0)
{
}
// frameworks/native/libs/binder/Binder.cpp:241
BpRefBase::BpRefBase(const sp<IBinder>& o)
    : mRemote(o.get()), mRefs(NULL), mState(0)  // mRemote = new BpBinder(0)
{
    ... ...
}
```
来看看`class BpServiceManager`的定义：
``` c++
// frameworks/native/libs/binder/IServiceManager.cpp:126
class BpServiceManager : public BpInterface<IServiceManager>
{
public:
    BpServiceManager(const sp<IBinder>& impl)
        : BpInterface<IServiceManager>(impl)
    {}

    virtual sp<IBinder> getService(const String16& name) const
    {... ...}

    virtual sp<IBinder> checkService( const String16& name) const
    {... ...}

    virtual status_t addService(const String16& name, const sp<IBinder>& service, bool allowIsolated)
    {... ...}

    virtual Vector<String16> listServices()
    {... ...}
};
```
该类封装了ServiceManager的逻辑，其实很少，主要就是`addService(...)`和`addService(...)`两个函数，它们分别封装了ServiceManager注册服务和查找服务的数据包，然后使用“普通火车”`remote()`把数据包发出去。
> sm就是给BpBinder(0)加了薄薄一层封装成为BpServiceManager。

<font color="red">未完待续...</font>
## addService(...)添加服务

## ProcessState::startThreadPool()时刻等待着接客

# 查找服务

# 调用服务接口









