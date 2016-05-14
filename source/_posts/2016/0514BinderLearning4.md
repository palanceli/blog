---
layout: post
title:  "Binder学习笔记（四）—— ServiceManager如何响应checkService请求
"
date:   2016-05-09 00:32:48 +0800
categories: Android
tags:   binder
---
这要从frameworks/native/cmds/servicemanager/service_manager.c:347的main函数说起，该文件编译后生成servicemanager。
``` c++
int main(int argc, char **argv)
{
    struct binder_state *bs;

    bs = binder_open(128*1024);  // 打开/dev/binder文件，并映射到内存
    if (!bs) {
        ALOGE("failed to open binder driver\n");
        return -1;
    }

    //向/dev/binder写入BINDER_SET_CONTEXT_MGR命令
    if (binder_become_context_manager(bs)) { 
        ALOGE("cannot become context manager (%s)\n", strerror(errno));
        return -1;
    }

    selinux_enabled = is_selinux_enabled();
    sehandle = selinux_android_service_context_handle();
    selinux_status_open(true);

    if (selinux_enabled > 0) {
        if (sehandle == NULL) {
            ALOGE("SELinux: Failed to acquire sehandle. Aborting.\n");
            abort();
        }

        if (getcon(&service_manager_context) != 0) {
            ALOGE("SELinux: Failed to acquire service_manager context. Aborting.\n");
            abort();
        }
    }

    union selinux_callback cb;
    cb.func_audit = audit_callback;
    selinux_set_callback(SELINUX_CB_AUDIT, cb);
    cb.func_log = selinux_log_callback;
    selinux_set_callback(SELINUX_CB_LOG, cb);

    binder_loop(bs, svcmgr_handler);

    return 0;
}
```
接下来遇到se_xxx相关的数据结构和函数，未来我们还会遇到。他们是Android系统提供的安全机制，负责管理对资源的安全访问控制，通常只是回答某个资源是否有权限访问，而不会干涉业务逻辑，因此我们可以完全忽略。重点在binder_loop(…)，如下：
frameworks/native/cmds/servicemanager/binder.c:372
``` c++
void binder_loop(struct binder_state *bs, binder_handler func)
{
    int res;
    struct binder_write_read bwr;
    uint32_t readbuf[32];

    bwr.write_size = 0;
    bwr.write_consumed = 0;
    bwr.write_buffer = 0;

    readbuf[0] = BC_ENTER_LOOPER;
    binder_write(bs, readbuf, sizeof(uint32_t));

    for (;;) {
        bwr.read_size = sizeof(readbuf);
        bwr.read_consumed = 0;
        bwr.read_buffer = (uintptr_t) readbuf;

        res = ioctl(bs->fd, BINDER_WRITE_READ, &bwr);

        if (res < 0) {
            ALOGE("binder_loop: ioctl failed (%s)\n", strerror(errno));
            break;
        }

        res = binder_parse(bs, 0, (uintptr_t) readbuf, bwr.read_consumed, func);
        if (res == 0) {
            ALOGE("binder_loop: unexpected reply?!\n");
            break;
        }
        if (res < 0) {
            ALOGE("binder_loop: io error %d %s\n", res, strerror(errno));
            break;
        }
    }
}
```
它循环向/dev/binder读写内容，然后对读到的数据做解析，再深入binder_parse(…)
frameworks/native/cmds/servicemanager/binder.c:204
``` c++
int binder_parse(struct binder_state *bs, struct binder_io *bio,
                 uintptr_t ptr, size_t size, binder_handler func)
{
    int r = 1;
    uintptr_t end = ptr + (uintptr_t) size;

    while (ptr < end) {
        uint32_t cmd = *(uint32_t *) ptr;
        ptr += sizeof(uint32_t);
#if TRACE
        fprintf(stderr,"%s:\n", cmd_name(cmd));
#endif
        switch(cmd) {
        case BR_NOOP:
            break;
        case BR_TRANSACTION_COMPLETE:
            break;
        case BR_INCREFS:
        case BR_ACQUIRE:
        case BR_RELEASE:
        case BR_DECREFS:
#if TRACE
            fprintf(stderr,"  %p, %p\n", (void *)ptr, (void *)(ptr + sizeof(void *)));
#endif
            ptr += sizeof(struct binder_ptr_cookie);
            break;
        case BR_TRANSACTION: {
            struct binder_transaction_data *txn = (struct binder_transaction_data *) ptr;
            if ((end - ptr) < sizeof(*txn)) {
                ALOGE("parse: txn too small!\n");
                return -1;
            }
            binder_dump_txn(txn);
            if (func) {
                unsigned rdata[256/4];
                struct binder_io msg;
                struct binder_io reply;
                int res;

                bio_init(&reply, rdata, sizeof(rdata), 4);
                bio_init_from_txn(&msg, txn);
                res = func(bs, txn, &msg, &reply);
                binder_send_reply(bs, &reply, txn->data.ptr.buffer, res);
            }
            ptr += sizeof(*txn);
            break;
        }
        case BR_REPLY: {
            struct binder_transaction_data *txn = (struct binder_transaction_data *) ptr;
            if ((end - ptr) < sizeof(*txn)) {
                ALOGE("parse: reply too small!\n");
                return -1;
            }
            binder_dump_txn(txn);
            if (bio) {
                bio_init_from_txn(bio, txn);
                bio = 0;
            } else {
                /* todo FREE BUFFER */
            }
            ptr += sizeof(*txn);
            r = 0;
            break;
        }
        case BR_DEAD_BINDER: {
            struct binder_death *death = (struct binder_death *)(uintptr_t) *(binder_uintptr_t *)ptr;
            ptr += sizeof(binder_uintptr_t);
            death->func(bs, death->ptr);
            break;
        }
        case BR_FAILED_REPLY:
            r = -1;
            break;
        case BR_DEAD_REPLY:
            r = -1;
            break;
        default:
            ALOGE("parse: OOPS %d\n", cmd);
            return -1;
        }
    }

    return r;
}
```
重点在case BR_TRANSACTION里，它接收到的txn正是客户端发出的tr。首先初始化好reply数据结构
![](img01.png)
然后初始化msg，其中蓝色部分是客户端组织的数据，红色部分是ServiceManager端组织的数据：
![](img02.png)
接下来执行func(…)，这是一个函数指针，通过参数传进来，向上追溯binder_loop(…) – main(…)找到该函数指针的实参是svcmgr_handler
``` c++
frameworks/native/cmds/servicemanager/service_manager.c:244
int svcmgr_handler(struct binder_state *bs,
                   struct binder_transaction_data *txn,
                   struct binder_io *msg,
                   struct binder_io *reply)
{
    struct svcinfo *si;
    uint16_t *s;
    size_t len;
    uint32_t handle;
    uint32_t strict_policy;
    int allow_isolated;

    //ALOGI("target=%p code=%d pid=%d uid=%d\n",
    //      (void*) txn->target.ptr, txn->code, txn->sender_pid, txn->sender_euid);

    if (txn->target.ptr != BINDER_SERVICE_MANAGER)
        return -1;

    if (txn->code == PING_TRANSACTION)
        return 0;

    // Equivalent to Parcel::enforceInterface(), reading the RPC
    // header with the strict mode policy mask and the interface name.
    // Note that we ignore the strict_policy and don't propagate it
// further (since we do no outbound RPCs anyway).
// 从客户端发来的Parcel数据中取出InterfaceToken
    strict_policy = bio_get_uint32(msg);
    s = bio_get_string16(msg, &len);
    if (s == NULL) {
        return -1;
    }
    // svcmgr_id就是android.os.IserviceManager，定义在service_manager.c:164
    if ((len != (sizeof(svcmgr_id) / 2)) ||
        memcmp(svcmgr_id, s, sizeof(svcmgr_id))) {
        fprintf(stderr,"invalid id %s\n", str8(s, len));
        return -1;
    }

    if (sehandle && selinux_status_updated() > 0) {
        struct selabel_handle *tmp_sehandle = selinux_android_service_context_handle();
        if (tmp_sehandle) {
            selabel_close(sehandle);
            sehandle = tmp_sehandle;
        }
    }

    switch(txn->code) {
    case SVC_MGR_GET_SERVICE:
    case SVC_MGR_CHECK_SERVICE:
        s = bio_get_string16(msg, &len);  // 取出Parcel中的"service.testservice"字串
        if (s == NULL) {
            return -1;
        }
        handle = do_find_service(bs, s, len, txn->sender_euid, txn->sender_pid);
        if (!handle)
            break;
        bio_put_ref(reply, handle);
        return 0;

    case SVC_MGR_ADD_SERVICE:
        s = bio_get_string16(msg, &len);
        if (s == NULL) {
            return -1;
        }
        handle = bio_get_ref(msg);
        allow_isolated = bio_get_uint32(msg) ? 1 : 0;
        if (do_add_service(bs, s, len, handle, txn->sender_euid,
            allow_isolated, txn->sender_pid))
            return -1;
        break;

    case SVC_MGR_LIST_SERVICES: {
        uint32_t n = bio_get_uint32(msg);

        if (!svc_can_list(txn->sender_pid)) {
            ALOGE("list_service() uid=%d - PERMISSION DENIED\n",
                    txn->sender_euid);
            return -1;
        }
        si = svclist;
        while ((n-- > 0) && si)
            si = si->next;
        if (si) {
            bio_put_string16(reply, si->name);
            return 0;
        }
        return -1;
    }
    default:
        ALOGE("unknown code %d\n", txn->code);
        return -1;
    }

    bio_put_uint32(reply, 0);
    return 0;
}
```
继续找do_find_service(…)，frameworks/native/cmds/servicemanager/service_manager.c:170
``` c++
uint32_t do_find_service(struct binder_state *bs, const uint16_t *s, size_t len, uid_t uid, pid_t spid)
{
    struct svcinfo *si = find_svc(s, len); // 重点在这里

    if (!si || !si->handle) {
        return 0;
    }

    if (!si->allow_isolated) {
        // If this service doesn't allow access from isolated processes,
        // then check the uid to see if it is isolated.
        uid_t appid = uid % AID_USER;
        if (appid >= AID_ISOLATED_START && appid <= AID_ISOLATED_END) {
            return 0;
        }
    }

    if (!svc_can_find(s, len, spid)) {
        return 0;
    }

    return si->handle;
}
```
再到frameworks/native/cmds/servicemanager/service_manager.c:140
``` c++
struct svcinfo *find_svc(const uint16_t *s16, size_t len)
{
    struct svcinfo *si;

    for (si = svclist; si; si = si->next) {
        if ((len == si->len) &&
            !memcmp(s16, si->name, len * sizeof(uint16_t))) {
            return si;
        }
    }
    return NULL;
}
```
终于找到了尽头，svclist是一个链表，ServiceManager在收到checkService请求后，根据service name遍历svclist，返回命中的节点。之后再一路回到调用的原点：find_svc -> do_find_service，在这里它返回的是节点的handle成员变量。节点的数据类型定义在frameworks/native/cmds/servicemanager/service_manager.c:128
``` c++
struct svcinfo
{
    struct svcinfo *next;
    uint32_t handle;
    struct binder_death death;
    int allow_isolated;
    size_t len;
    uint16_t name[0];
};
```
从数据类型上来看，我们只能知道handle是一个整形数字，它是怎么来的？肯定是服务端先来这里注册的，然后ServiceManager把节点中的信息缓存到svclist链表里去，等待客户端过来请求，就把handle返回给客户端。
继续向调用原点返回，从do_find_service –> svcmgr_handle
frameworks/native/cmds/servicemanager/service_manager.c:296
``` c++
        handle = do_find_service(bs, s, len, txn->sender_euid, txn->sender_pid);
        if (!handle)
            break;
        bio_put_ref(reply, handle);
        return 0;
```
svcmgr_handle得到handle后，调用bio_put_ref把它塞到reply里。然后svcmgr_handle -> binder_parse，后者调用binder_send_reply把reply发送出去。这样ServiceManager就完成了一次checkService的响应。
不过还是有一些细节需要弄清楚，我们先回到svcmgr_handle的bio_put_ref(…)函数，看看他是怎么组织reply的，frameworks/native/cmds/servicemanager/binder.c:505
``` c++
void bio_put_ref(struct binder_io *bio, uint32_t handle)
{
    struct flat_binder_object *obj;

    if (handle)
        obj = bio_alloc_obj(bio);
    else
        obj = bio_alloc(bio, sizeof(*obj));

    if (!obj)
        return;

    obj->flags = 0x7f | FLAT_BINDER_FLAG_ACCEPTS_FDS;
    obj->type = BINDER_TYPE_HANDLE;
    obj->handle = handle;
    obj->cookie = 0;
}
```
还记得reply吧？上文在干活之前给它初始化成这样:
![](img03.png)
接下来进入bio_alloc_obj(…)，frameworks/native/cmds/servicemanager/binder.c:468
``` c++
static struct flat_binder_object *bio_alloc_obj(struct binder_io *bio)
{
    struct flat_binder_object *obj;

    obj = bio_alloc(bio, sizeof(*obj));

    if (obj && bio->offs_avail) {
        bio->offs_avail--; // 它记录offs区域还有多少容量
        // offs区域是一个size_t型数组，每个元素记录data区域中object相对于data0的偏移
        *bio->offs++ = ((char*) obj) - ((char*) bio->data0); 
        return obj;
    }

    bio->flags |= BIO_F_OVERFLOW;
    return NULL;
}
```
继续到bio_alloc(…)，frameworks/native/cmds/servicemanager/binder.c:437
``` c++
static void *bio_alloc(struct binder_io *bio, size_t size)
{   // size=sizeof(flat_binder_object)
    size = (size + 3) & (~3);
    if (size > bio->data_avail) {  // 溢出判断
        bio->flags |= BIO_F_OVERFLOW;
        return NULL;
    } else {  // 主干在这，原来是从bio->data中分配出的空间
        void *ptr = bio->data;
        bio->data += size;
        bio->data_avail -= size;
        return ptr;
    }
}
```
到bio_put_ref(…)函数返回时，他组织成的数据结构如下，我把被修改过的成员标橙色了：
![](img04.png)
binder_io只是一个数据索引，具体的数据是放在rdata中的，rdata又分两个区域：1、object指针索引区；2、数据区。数据区存放有基本数据类型，如int、string；也有抽象数据类型，如flat_binder_object。object指针索引区记录数据区中每一个抽象数据类型的偏移量。binder_io则记录rdata区域每个部分的起始位置、当前栈顶位置和所剩空间。
svcmgr_handle(…)调用bio_put_ref(…)组织完reply数据之后就返回到binder_parser(…)，然后调用binder_sendbinder_parse_raply(…)
frameworks/native/cmds/servicemanager/binder.c:245
``` c++
                res = func(bs, txn, &msg, &reply);
                binder_send_reply(bs, &reply, txn->data.ptr.buffer, res);
```
svcmgr_handle的返回值res为0，表示成功，该值被传入binder_send_reply(…)。一并被传入的还有txn的数据成员data.ptr.buffer，这是从客户端发来的请求数据，继续进入函数
frameworks/native/cmds/servicemanager/binder.c:170
``` c++
void binder_send_reply(struct binder_state *bs,
                       struct binder_io *reply,
                       binder_uintptr_t buffer_to_free,
                       int status)
{   // status=0
    struct {
        uint32_t cmd_free;
        binder_uintptr_t buffer;
        uint32_t cmd_reply;
        struct binder_transaction_data txn;
    } __attribute__((packed)) data;

    data.cmd_free = BC_FREE_BUFFER;
    data.buffer = buffer_to_free;
    data.cmd_reply = BC_REPLY;
    data.txn.target.ptr = 0;
    data.txn.cookie = 0;
    data.txn.code = 0;
    if (status) {
        data.txn.flags = TF_STATUS_CODE;
        data.txn.data_size = sizeof(int);
        data.txn.offsets_size = 0;
        data.txn.data.ptr.buffer = (uintptr_t)&status;
        data.txn.data.ptr.offsets = 0;
    } else {
        data.txn.flags = 0;
        data.txn.data_size = reply->data - reply->data0;
        data.txn.offsets_size = ((char*) reply->offs) - ((char*) reply->offs0);
        data.txn.data.ptr.buffer = (uintptr_t)reply->data0;
        data.txn.data.ptr.offsets = (uintptr_t)reply->offs0;
    }
    binder_write(bs, &data, sizeof(data));
}
```
这是在组织完整的响应数据。把完整的数据描绘出来如下，真是一盘大棋！客户端组织的数据用蓝色标出，ServiceManager组织的数据用红色标出。从图上可以清晰地看出原来reply并没有打到响应数据包里，只是作中间缓存之用。
![](img05.png)