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

## addService(...)添加服务
### Server端把addService(...)的调用封装成一个数据包
对于Server端，添加服务的调用简单明了，传入服务的名字以及提供服务的对象；客户端查找服务时只需提供服务名字，即可获得服务的（代理）对象。添加服务的代码在TestService.cpp:30
`sm->addService(String16("service.testservice"), new BnTestService());`
上一节已经分析过sm是`BpServiceManager`的实例，其`mRemote`成员即`BpBinder(0)`。
`BpServiceManager::addService(...)`定义如下：
``` c++
// frameworks/native/libs/binder/IServiceManager.cpp
// #155
virtual status_t addService(const String16& name, const sp<IBinder>& service,
        bool allowIsolated)
{   // name="service.testservice", service=new BnTestService()
    // allowIsolated 默认值为 false，定义在IserviceManager.h:49
    Parcel data, reply;
    data.writeInterfaceToken(IServiceManager::getInterfaceDescriptor());
    data.writeString16(name);
    data.writeStrongBinder(service);
    data.writeInt32(allowIsolated ? 1 : 0);
    status_t err = remote()->transact(ADD_SERVICE_TRANSACTION, data, &reply);
    return err == NO_ERROR ? reply.readExceptionCode() : err;
}
```
Parcel的封装细节可参见[《Binder学习笔记（五）—— Parcel是怎么打包的？》](http://palanceli.github.io/blog/2016/05/10/2016/0514BinderLearning5/)。data中携带的重要数据还是服务名称以及服务对象。remote()返回的是BpBinder(0)，因此来看`BpBinder::transact(...)`
``` c++
// frameworks/native/libs/binder/BpBinder.cpp:159
status_t BpBinder::transact(
    uint32_t code, const Parcel& data, Parcel* reply, uint32_t flags)
{   // code = ADD_SERVICE_TRANSACTION
    // data 携带服务名称和服务对象
    // reply 一个清白的Parcel
    // flags 默认为0，定义在Binder.h:37
    ... ...
    status_t status = IPCThreadState::self()->transact(
            mHandle, code, data, reply, flags);  // mHandle=0
    ... ...
}

// frameworks/native/libs/binder/IPCThreadState.cpp:548
status_t IPCThreadState::transact(int32_t handle,
                                  uint32_t code, const Parcel& data,
                                  Parcel* reply, uint32_t flags)
{   // handle   0
    // code     ADD_SERVICE_TRANSACTION
    // data     携带服务名称和服务对象
    // reply    指向一个清白的Parcel
    // flags    0
    ... ...
    flags |= TF_ACCEPT_FDS;     // flags = TF_ACCEPT_FDS
    ... ...
    err = writeTransactionData(BC_TRANSACTION, flags, handle, code, data, NULL);
    ... ...
    if ((flags & TF_ONE_WAY) == 0) {  // 为真
        ... ...
        if (reply) {    // 非空
            err = waitForResponse(reply);
        } 
        ... ...
    } 
    ... ...
    return err;
}

// frameworks/native/libs/binder/IPCThreadState.cpp:904
status_t IPCThreadState::writeTransactionData(int32_t cmd, uint32_t binderFlags,
    int32_t handle, uint32_t code, const Parcel& data, status_t* statusBuffer)
{   // cmd          BC_TRANSACTION
    // binderFlags  TF_ACCEPT_FDS
    // handle       0
    // code         ADD_SERVICE_TRANSACTION
    // data         携带服务名称和服务对象
    // statusBuffer NULL
    binder_transaction_data tr;

    tr.target.ptr = 0; 
    tr.target.handle = handle;  // 0
    tr.code = code;             // ADD_SERVICE_TRANSACTION
    tr.flags = binderFlags;     // TF_ACCEPT_FDS
    tr.cookie = 0;
    tr.sender_pid = 0;
    tr.sender_euid = 0;
    ... ...
        tr.data_size = data.ipcDataSize();
        tr.data.ptr.buffer = data.ipcData();
        tr.offsets_size = data.ipcObjectsCount()*sizeof(binder_size_t);
        tr.data.ptr.offsets = data.ipcObjects();
    ... ...
    
    mOut.writeInt32(cmd);
    mOut.write(&tr, sizeof(tr));
    
    return NO_ERROR;
}
```
![Server端为addService组织的请求数据](http://palanceli.github.io/blog/2016/05/11/2016/0514BinderLearning6/img02.png)
这个数据结构很重要，它表达了Server端本次请求的具体内容，即把addService(...)封装成的数据包。其中tr记录定长的控制信息，data记录变长的数据信息。本次的控制信息的核心内容就是ADD_SERVICE_TRANSACTION，数据信息的核心内容是服务名称和服务实体。

组织完数据接下来显然要发出去，
![Server端addService的调用关系](0728DissectingBinder1/img01.png)
沿着调用关系，我们来看具体发送数据的`IPCThreadState::waitForResponse(...)`
``` c++
// frameworks/native/libs/binder/IPCThreadState.cpp:712
status_t IPCThreadState::waitForResponse(Parcel *reply, status_t *acquireResult)
{   // reply            指向一个清白的Parcel
    // acquireResult    NULL
    uint32_t cmd;
    int32_t err;

    while (1) {
        if ((err=talkWithDriver()) < NO_ERROR) break;
        ... ...
        cmd = (uint32_t)mIn.readInt32();
        // 接下来根据ServiceManager应答数据中的cmd分别处理，具体怎么处理暂且不表
        ... ...
    }
... ...
}

// frameworks/natvie/libs/binder/IPCThreadState.cpp:803
status_t IPCThreadState::talkWithDriver(bool doReceive)
{   // doReceive    默认参数为true，定义在IPCThreadState.h:98
    ... ...
    binder_write_read bwr;
    ... ...

    bwr.write_size = outAvail;
    bwr.write_buffer = (uintptr_t)mOut.data();
    ... ...
    bwr.read_size = mIn.dataCapacity();
    bwr.read_buffer = (uintptr_t)mIn.data();
    ... ...
    status_t err;
    do {
        ... ...
        // 对/dev/binder完成一次读写操作
        if (ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &bwr) >= 0)
            err = NO_ERROR;
        ... ...
    } while (err == -EINTR);
    ... ...
    return err;
}
```
这两个函数砍掉细枝末节主要完成两个事：1、从/dev/binder完成一次读写操作，把前面组好的数据包mOut发出去，把读入响应数据放到mIn中；2、根据响应数据中的cmd做相应的处理。我们先看1，因为只有分析过ServiceManager如何组织响应数据才能分析2中怎么处理。
1中数据通过ioctl(...)函数发向/dev/binder，接下来应该去看驱动层怎么处理了。

### 驱动层怎么处理Server端的addService数据包
承接`ioctl(m_Process->mDriverFD, BINDER_WRITE_READ, &bwr)`的驱动层函数是`binder_ioctl(...)`，这个函数的大框架比较简单：
* 将用户空间的数据拷贝到内核空间
* 根据cmd的值，对数据做不同处理。这里只涉及了BINDER_WRITE_READ命令，它的处理又分两部分
    - 调用binder_thread_write(...)来处理bwr中写缓冲区里用户写入的数据
    - 调用binder_thread_read(...)将用户要读出的数据放到bwr中读缓冲区里
* 将处理完的数据拷贝回用户空间
<font color=red>需要确定binder_get_thread(proc)都干了什么</font>
``` c++
// kernel/goldfish/drivers/staging/android/binder.c:2716
static long binder_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{   // cmd      BINDER_WRITE_READ
    // arg      指向bwr的地址
    int ret;
    struct binder_proc *proc = filp->private_data;
    struct binder_thread *thread;
    unsigned int size = _IOC_SIZE(cmd);
    void __user *ubuf = (void __user *)arg;

    ... ...
    thread = binder_get_thread(proc);
    ... ...
    switch (cmd) {
    case BINDER_WRITE_READ: {
        struct binder_write_read bwr;
        ... ...
        // 将用户空间的bwr拷贝到内核空间
        if (copy_from_user(&bwr, ubuf, sizeof(bwr))) { 
            ... ...
        }
        ... ...

        if (bwr.write_size > 0) {  // 表明bwr的写缓冲区有数据，将数据发送到目标
            ret = binder_thread_write(proc, thread, (void __user *)bwr.write_buffer, bwr.write_size, &bwr.write_consumed);
            ... ...
        }
        if (bwr.read_size > 0) {    // 表明bwr的读缓冲区有空间，读取数据
            ret = binder_thread_read(proc, thread, (void __user *)bwr.read_buffer, bwr.read_size, &bwr.read_consumed, filp->f_flags & O_NONBLOCK);
            ... ...
            if (!list_empty(&proc->todo))
                wake_up_interruptible(&proc->wait);
            ... ...
        }
        ... ...
        // 将处理后的数据拷贝回用户空间
        if (copy_to_user(ubuf, &bwr, sizeof(bwr))) {
            ... ...
        }
        break;
    }
    ... ...
    }
... ...
    return ret;
}
```
先来看写入的部分，bwr的write_buffer是一个cmd跟着一个`binder_transaction_data`结构体。函数的大框架是根据cmd做不同的处理，addService请求对应的cmd是BC_TRANSACTION，我们先只看这部分。它把`binder_trsansction_data`结构体拷贝到内核空间，然后调用binder_transaction(...)来处理该结构体：
``` c++
// kernel/goldfish/drivers/staging/android/binder.c:1837
int binder_thread_write(struct binder_proc *proc, struct binder_thread *thread,
            void __user *buffer, int size, signed long *consumed)
{   // buffer   bwr.write_buffer
    // size     brw.write_size
    // consumed brw.write_confumed
    uint32_t cmd;
    void __user *ptr = buffer + *consumed;
    void __user *end = buffer + size;

    while (ptr < end && thread->return_error == BR_OK) {
        if (get_user(cmd, (uint32_t __user *)ptr))  // 从用户空间拿到cmd
            return -EFAULT;
        ptr += sizeof(uint32_t);
        ... ...
        switch (cmd) {
        ... ...
        case BC_TRANSACTION:
        case BC_REPLY: {
            struct binder_transaction_data tr;
            if (copy_from_user(&tr, ptr, sizeof(tr)))// 将用户空间的tr拷贝到内核空间
                return -EFAULT;
            ptr += sizeof(tr);
            binder_transaction(proc, thread, &tr, cmd == BC_REPLY); // 处理tr
            break;
        }
        ... ...
        }
        *consumed = ptr - buffer;
    }
    return 0;
}
```
`binder_transaction(...)`函数是处理写入数据的核心代码，在深入分析代码之前，让我们再温习一下已经从用户空间拷贝到内核空间的Server端为addService组织的请求数据：
![Server端为addService组织的请求数据](http://palanceli.github.io/blog/2016/05/11/2016/0514BinderLearning6/img02.png)
``` c++
kernel/goldfish/drivers/staging/android/binder.c:1402
static void binder_transaction(struct binder_proc *proc,
                   struct binder_thread *thread,
                   struct binder_transaction_data *tr, int reply)
{   // reply    (cmd==BC_REPLY)即false
    struct binder_transaction *t;
    struct binder_work *tcomplete;
    size_t *offp, *off_end;
    struct binder_proc *target_proc;
    struct binder_thread *target_thread = NULL;
    struct binder_node *target_node = NULL;
    struct list_head *target_list;
    wait_queue_head_t *target_wait;
    struct binder_transaction *in_reply_to = NULL;

    ... ...
        if (tr->target.handle) {                    // 从上图上查到handle为0
            ... ...
        } else {
            target_node = binder_context_mgr_node;  // 发往ServiceManager
            ... ...
        }
        ... ...
        // 这是ServiceManager在打开/dev/binder时，驱动层为该进程创建的内核数据结构
        target_proc = target_node->proc;
        ... ...
        if (!(tr->flags & TF_ONE_WAY) && thread->transaction_stack) {
            struct binder_transaction *tmp;
            tmp = thread->transaction_stack;
            ... ...
            while (tmp) {
                if (tmp->from && tmp->from->proc == target_proc)
                    target_thread = tmp->from;
                tmp = tmp->from_parent;
            }
        }

    if (target_thread) {
        e->to_thread = target_thread->pid;
        target_list = &target_thread->todo;
        target_wait = &target_thread->wait;
    } else {
        target_list = &target_proc->todo;
        target_wait = &target_proc->wait;
    }
    ... ...

    t = kzalloc(sizeof(*t), GFP_KERNEL);
    ... ...

    tcomplete = kzalloc(sizeof(*tcomplete), GFP_KERNEL);
    ... ...

    if (!reply && !(tr->flags & TF_ONE_WAY))        // 为真
        t->from = thread;
    ... ...
    t->sender_euid = proc->tsk->cred->euid;
    t->to_proc = target_proc;
    t->to_thread = target_thread;
    t->code = tr->code;
    t->flags = tr->flags;
    t->priority = task_nice(current);

    ... ...

    t->buffer = binder_alloc_buf(target_proc, tr->data_size,
        tr->offsets_size, !reply && (t->flags & TF_ONE_WAY));
    ... ...
    t->buffer->allow_user_free = 0;
    t->buffer->debug_id = t->debug_id;
    t->buffer->transaction = t;
    t->buffer->target_node = target_node;
    ... ...
    if (target_node)
        binder_inc_node(target_node, 1, 0, NULL);

    offp = (size_t *)(t->buffer->data + ALIGN(tr->data_size, sizeof(void *)));

    if (copy_from_user(t->buffer->data, tr->data.ptr.buffer, tr->data_size)) {
        ... ...
    }
    if (copy_from_user(offp, tr->data.ptr.offsets, tr->offsets_size)) {
        ... ...
    }
    ... ...
    off_end = (void *)offp + tr->offsets_size;
    for (; offp < off_end; offp++) {
        struct flat_binder_object *fp;
        ... ...
        fp = (struct flat_binder_object *)(t->buffer->data + *offp);
        switch (fp->type) {
        case BINDER_TYPE_BINDER:
        case BINDER_TYPE_WEAK_BINDER: {
            struct binder_ref *ref;
            struct binder_node *node = binder_get_node(proc, fp->binder);
            if (node == NULL) {
                node = binder_new_node(proc, fp->binder, fp->cookie);
                ... ...
                node->min_priority = fp->flags & FLAT_BINDER_FLAG_PRIORITY_MASK;
                node->accept_fds = !!(fp->flags & FLAT_BINDER_FLAG_ACCEPTS_FDS);
            }
            ... ...
            ref = binder_get_ref_for_node(target_proc, node);
            ... ...
            if (fp->type == BINDER_TYPE_BINDER)
                fp->type = BINDER_TYPE_HANDLE;
            else
                fp->type = BINDER_TYPE_WEAK_HANDLE;
            fp->handle = ref->desc;
            binder_inc_ref(ref, fp->type == BINDER_TYPE_HANDLE,
                       &thread->todo);

            ... ...
        } break;
        ... ...
    }
    if (reply) {                            // 为假
        ... ...
    } else if (!(t->flags & TF_ONE_WAY)) {  // 为真
        ... ...
        t->need_reply = 1;
        t->from_parent = thread->transaction_stack;
        thread->transaction_stack = t;
    } ... ...
    t->work.type = BINDER_WORK_TRANSACTION;
    list_add_tail(&t->work.entry, target_list);
    tcomplete->type = BINDER_WORK_TRANSACTION_COMPLETE;
    list_add_tail(&tcomplete->entry, &thread->todo);
    if (target_wait)
        wake_up_interruptible(target_wait);
    return;

... ...
}
```

<font color="red">未完待续...</font>
### ServiceManager端如何等待响应
### 驱动层怎么处理ServiceManager响应的addService数据
## ProcessState::startThreadPool()时刻等待着接客

# 查找服务

# 调用服务接口









