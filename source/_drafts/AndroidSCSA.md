---
title: Android系统源代码情景分析 - Binder驱动程序
date:   2016-04-12 10:28:49 +0800
tags:
toc: true
description: 未完成
---
# Binder设备文件的内存映射过程
kernel/goldfish/drivers/staging/android/binder.c:2883
``` c
static int binder_mmap(struct file *filp, struct vm_area_struct *vma)
{   // vma描述用户地址空间
    int ret;
    struct vm_struct *area; // area描述内核地址空间
    struct binder_proc *proc = filp->private_data;
    const char *failure_string;
    struct binder_buffer *buffer;

    // Binder驱动程序最多为进程分配4M内核缓冲区来传输进程间通信数据
    if ((vma->vm_end - vma->vm_start) > SZ_4M)  
        vma->vm_end = vma->vm_start + SZ_4M;

    binder_debug(BINDER_DEBUG_OPEN_CLOSE,
             "binder_mmap: %d %lx-%lx (%ld K) vma %lx pagep %lx\n",
             proc->pid, vma->vm_start, vma->vm_end,
             (vma->vm_end - vma->vm_start) / SZ_1K, vma->vm_flags,
             (unsigned long)pgprot_val(vma->vm_page_prot));

    // 如果进程指定要映射的用户地址空间可写，将出错。
    if (vma->vm_flags & FORBIDDEN_MMAP_FLAGS) {
        ret = -EPERM;
        failure_string = "bad vm_flags";
        goto err_bad_arg;
    }
    // 不可拷贝，不可写
    vma->vm_flags = (vma->vm_flags | VM_DONTCOPY) & ~VM_MAYWRITE; 

    mutex_lock(&binder_mmap_lock);
    if (proc->buffer) {  // 文件已经被映射，则返回
        ret = -EBUSY;
        failure_string = "already mapped";
        goto err_already_mapped;
    }
    // 在进程的内核地址空间分配内存
    area = get_vm_area(vma->vm_end - vma->vm_start, VM_IOREMAP);
    if (area == NULL) {
        ret = -ENOMEM;
        failure_string = "get_vm_area";
        goto err_get_vm_area_failed;
    }
    proc->buffer = area->addr;  // 内核地址空间起始地址
    // 用户空间起址和内核空间起址差值
    proc->user_buffer_offset = vma->vm_start - (uintptr_t)proc->buffer;  
    mutex_unlock(&binder_mmap_lock);

#ifdef CONFIG_CPU_CACHE_VIPT
    if (cache_is_vipt_aliasing()) {
        while (CACHE_COLOUR((vma->vm_start ^ (uint32_t)proc->buffer))) {
            printk(KERN_INFO "binder_mmap: %d %lx-%lx maps %p bad alignment\n", proc->pid, vma->vm_start, vma->vm_end, proc->buffer);
            vma->vm_start += PAGE_SIZE;
        }
    }
#endif
    // 创建物理页面结构体指针数组
    proc->pages = kzalloc(sizeof(proc->pages[0]) * ((vma->vm_end - vma->vm_start) / PAGE_SIZE), GFP_KERNEL);
    if (proc->pages == NULL) {
        ret = -ENOMEM;
        failure_string = "alloc page array";
        goto err_alloc_pages_failed;
    }
    proc->buffer_size = vma->vm_end - vma->vm_start;

    vma->vm_ops = &binder_vm_ops;
    vma->vm_private_data = proc;
    // 为虚拟地址空间area分配一个物理页面
    if (binder_update_page_range(proc, 1, proc->buffer, proc->buffer + PAGE_SIZE, vma)) {
        ret = -ENOMEM;
        failure_string = "alloc small buf";
        goto err_alloc_small_buf_failed;
    }
    buffer = proc->buffer;
    INIT_LIST_HEAD(&proc->buffers);
    list_add(&buffer->entry, &proc->buffers); // 将刚申请的物理页面加入内核缓冲区列表
    buffer->free = 1;
    binder_insert_free_buffer(proc, buffer); // 将buffer加入proc空闲内核缓冲区红黑树
    // 将进程最大可用于异步事务的内核缓冲区大小设为总内核缓冲区大小的一半，
    // 防止内核事务消耗过多内核缓冲区，影响同步事务的执行
    proc->free_async_space = proc->buffer_size / 2;
    barrier();
    proc->files = get_files_struct(proc->tsk);
    proc->vma = vma;
    proc->vma_vm_mm = vma->vm_mm;

    /*printk(KERN_INFO "binder_mmap: %d %lx-%lx maps %p\n",
         proc->pid, vma->vm_start, vma->vm_end, proc->buffer);*/
    return 0;

err_alloc_small_buf_failed:
    kfree(proc->pages);
    proc->pages = NULL;
err_alloc_pages_failed:
    mutex_lock(&binder_mmap_lock);
    vfree(proc->buffer);
    proc->buffer = NULL;
err_get_vm_area_failed:
err_already_mapped:
    mutex_unlock(&binder_mmap_lock);
err_bad_arg:
    printk(KERN_ERR "binder_mmap: %d %lx-%lx %s failed %d\n",
           proc->pid, vma->vm_start, vma->vm_end, failure_string, ret);
    return ret;
}
```
binder_update_page_range(...)：为一段指定的虚拟地址空间分配或者释放物理页面，kernel/goldfish/drivers/staging/android/binder.c:627
``` c
static int binder_update_page_range(struct binder_proc *proc, int allocate,
                    void *start, void *end,
                    struct vm_area_struct *vma)
{   // allocate=0表示要释放物理页面，否则表示要分配物理页面
    // start、end制定了要操作的内核地址空间起始和结束地址
    // vma指向要映射的用户地址空间
    void *page_addr;
    unsigned long user_page_addr;
    struct vm_struct tmp_area;
    struct page **page;
    struct mm_struct *mm;

    binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
             "binder: %d: %s pages %p-%p\n", proc->pid,
             allocate ? "allocate" : "free", start, end);

    if (end <= start)
        return 0;

    trace_binder_update_page_range(proc, allocate, start, end);

    if (vma)
        mm = NULL;
    else
        mm = get_task_mm(proc->tsk);

    if (mm) {
        down_write(&mm->mmap_sem);
        vma = proc->vma;
        if (vma && mm != proc->vma_vm_mm) {
            pr_err("binder: %d: vma mm and task mm mismatch\n",
                proc->pid);
            vma = NULL;
        }
    }

    if (allocate == 0)  // 分配 or 释放
        goto free_range;

    if (vma == NULL) {
        printk(KERN_ERR "binder: %d: binder_alloc_buf failed to "
               "map pages in userspace, no vma\n", proc->pid);
        goto err_no_vma;
    }
    // start~end可能包含多个页面，因此需要遍历，为每个虚拟地址页面分配物理页面
    for (page_addr = start; page_addr < end; page_addr += PAGE_SIZE) {
        int ret;
        struct page **page_array_ptr;
        page = &proc->pages[(page_addr - proc->buffer) / PAGE_SIZE];

        BUG_ON(*page);
        // 分配物理页面
        *page = alloc_page(GFP_KERNEL | __GFP_HIGHMEM | __GFP_ZERO);
        if (*page == NULL) {
            printk(KERN_ERR "binder: %d: binder_alloc_buf failed "
                   "for page at %p\n", proc->pid, page_addr);
            goto err_alloc_page_failed;
        }
        // 映射内核地址空间
        tmp_area.addr = page_addr;
        // 实际映射了2个内核地址空间页面。Linux内核规定，在（3G+896M+8M)~4G范围
        // 内的任意一块内核地址空间都必须要在后面保留一块空的地址空间来作为安全保护区
        // 用来检测非法指针
        tmp_area.size = PAGE_SIZE + PAGE_SIZE /* guard page? */;
        page_array_ptr = page;
        ret = map_vm_area(&tmp_area, PAGE_KERNEL, &page_array_ptr);
        if (ret) {
            printk(KERN_ERR "binder: %d: binder_alloc_buf failed "
                   "to map page at %p in kernel\n",
                   proc->pid, page_addr);
            goto err_map_kernel_failed;
        }
        // 映射用户地址空间
        user_page_addr =
            (uintptr_t)page_addr + proc->user_buffer_offset;
        ret = vm_insert_page(vma, user_page_addr, page[0]);
        if (ret) {
            printk(KERN_ERR "binder: %d: binder_alloc_buf failed "
                   "to map page at %lx in userspace\n",
                   proc->pid, user_page_addr);
            goto err_vm_insert_page_failed;
        }
        /* vm_insert_page does not seem to increment the refcount */
    }
    if (mm) {
        up_write(&mm->mmap_sem);
        mmput(mm);
    }
    return 0;

free_range: // 依次为每个虚拟地址空间页面释放物理页面
    for (page_addr = end - PAGE_SIZE; page_addr >= start;
         page_addr -= PAGE_SIZE) {
        page = &proc->pages[(page_addr - proc->buffer) / PAGE_SIZE];
        if (vma) // 解除物理页面在用户空间的映射
            zap_page_range(vma, (uintptr_t)page_addr +
                proc->user_buffer_offset, PAGE_SIZE, NULL);
err_vm_insert_page_failed:  // 解除物理页面在内核空间的映射
        unmap_kernel_range((unsigned long)page_addr, PAGE_SIZE);
err_map_kernel_failed:
        __free_page(*page); // 释放该物理页面
        *page = NULL;
err_alloc_page_failed:
        ;
    }
err_no_vma:
    if (mm) {
        up_write(&mm->mmap_sem);
        mmput(mm);
    }
    return -ENOMEM;
}
```
binder_insert_free_buffer(...)，它将一个空闲的内核缓冲区加入到进程的空闲内核缓冲区红黑树中。binder_proc::free_buffers用来描述一个红黑树，他按照大小来组织进程中的空闲内核缓冲区。因此将内核缓冲区new_buffer加入到目标进程proc的空闲内核缓冲区红黑树之前，先调用binder_buffer_size(...)来计算它的大小。

kernel/goldfish/drivers/staging/android/binder.c:545
``` c
static void binder_insert_free_buffer(struct binder_proc *proc,
                      struct binder_buffer *new_buffer)
{
    struct rb_node **p = &proc->free_buffers.rb_node;
    struct rb_node *parent = NULL;
    struct binder_buffer *buffer;
    size_t buffer_size;
    size_t new_buffer_size;

    BUG_ON(!new_buffer->free);
    // 将内核缓冲区new_buffer加入到目标进程proc的空闲内核缓冲区红黑树之前，先计算它的大小
    new_buffer_size = binder_buffer_size(proc, new_buffer);

    binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
             "binder: %d: add free buffer, size %zd, "
             "at %p\n", proc->pid, new_buffer_size, new_buffer);

    while (*p) {
        parent = *p;
        buffer = rb_entry(parent, struct binder_buffer, rb_node);
        BUG_ON(!buffer->free);

        buffer_size = binder_buffer_size(proc, buffer);

        if (new_buffer_size < buffer_size)
            p = &parent->rb_left;
        else
            p = &parent->rb_right;
    }
    rb_link_node(&new_buffer->rb_node, parent, p);
    rb_insert_color(&new_buffer->rb_node, &proc->free_buffers);
}
```
# 分配内核缓冲区
当进程使用命令协议BC_TRANSACTION或BC_REPLY向另一个进程传递数据时，Binder驱动程序需要将这些数据从用户空间拷贝到内核空间，然后再传递给目标进程。此时Binder驱动程序就需要在目标进程的内存池中分配出一小块内核缓冲区来保存这些数据，以便可以传递给它使用。此操作由binder_alloc_buf来实现。
kernel/goldfish/drivers/staging/android/binder.c:732
``` c
static struct binder_buffer *binder_alloc_buf(struct binder_proc *proc,
                          size_t data_size,
                          size_t offsets_size, int is_async)
{   // proc描述目标进程；data_size描述数据缓冲区大小；
    // offsets_size描述偏移数组缓冲区大小；
    // is_async描述所请求的内核缓冲区是用于同步事务还是异步事务
    struct rb_node *n = proc->free_buffers.rb_node;
    struct binder_buffer *buffer;
    size_t buffer_size;
    struct rb_node *best_fit = NULL;
    void *has_page_addr;
    void *end_page_addr;
    size_t size;
    ......
    // 分别将data_size和offset_size对齐到一个void指针大小边界，
    // 然后相加得到要分配的内核缓冲区大小
    size = ALIGN(data_size, sizeof(void *)) +
        ALIGN(offsets_size, sizeof(void *));
    // 是否发生溢出
    if (size < data_size || size < offsets_size) {
        binder_user_error("binder: %d: got transaction with invalid "
            "size %zd-%zd\n", proc->pid, data_size, offsets_size);
        return NULL;
    }
    // 如果是异步事务 && 请求分配的内核缓冲区大小大于目标进程剩余可用于
    // 异步事务的内核缓冲区大小，则出错返回
    if (is_async &&
        proc->free_async_space < size + sizeof(struct binder_buffer)) {
        binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
                 "binder: %d: binder_alloc_buf size %zd"
                 "failed, no async space left\n", proc->pid, size);
        return NULL;
    }
    // 使用最佳适配算法在目标进程的空闲内核缓冲区红黑树中检查有没有最合适的内核缓冲区可用
    // 如果有则保存在best_fit中
    while (n) {
        buffer = rb_entry(n, struct binder_buffer, rb_node);
        BUG_ON(!buffer->free);
        buffer_size = binder_buffer_size(proc, buffer);

        if (size < buffer_size) {
            best_fit = n;
            n = n->rb_left;
        } else if (size > buffer_size)
            n = n->rb_right;
        else {
            best_fit = n;
            break;
        }
    }
    if (best_fit == NULL) { // 没有找到，则出错返回
        printk(KERN_ERR "binder: %d: binder_alloc_buf size %zd failed, "
               "no address space\n", proc->pid, size);
        return NULL;
    }
    // 没有找到大小刚刚合适的，但找到一块较大的内核缓冲区，将实际大小保存在buffer_size中
    if (n == NULL) { 
        buffer = rb_entry(best_fit, struct binder_buffer, rb_node);
        buffer_size = binder_buffer_size(proc, buffer);
    }

    binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
             "binder: %d: binder_alloc_buf size %zd got buff"
             "er %p size %zd\n", proc->pid, size, buffer, buffer_size);
    // 计算空闲内核缓冲区buffer的结束地址所在页面的起始地址
    has_page_addr =
        (void *)(((uintptr_t)buffer->data + buffer_size) & PAGE_MASK);
    // 如果找到了一块较大的内核缓冲区，则裁剪
    if (n == NULL) {
        // 如果裁剪后剩下的小块小于等于4字节，就不裁减了
        if (size + sizeof(struct binder_buffer) + 4 >= buffer_size)
            buffer_size = size; /* no room for other buffers */
        else
            buffer_size = size + sizeof(struct binder_buffer);
    }
    // 得到最终要分配的内核缓冲区大小，并将其结束地址对齐到页面边界
    end_page_addr =
        (void *)PAGE_ALIGN((uintptr_t)buffer->data + buffer_size);
    // 对齐后的end_page_addr可能大于原来的空闲内核缓冲区
    // buffer结束地址所在的页面起始地址had_page_addr，此时需要修正end_page_addr
    if (end_page_addr > has_page_addr)
        end_page_addr = has_page_addr;
    // 分配物理页面
    if (binder_update_page_range(proc, 1,
        (void *)PAGE_ALIGN((uintptr_t)buffer->data), end_page_addr, NULL))
        return NULL;
    // 将空闲内核缓冲区从目标进程的空闲内核缓冲区红黑树中删除
    rb_erase(best_fit, &proc->free_buffers);
    buffer->free = 0;
    // 将前面分配的内核缓冲区加入到目标进程的已分配物理页面的内核缓冲区红黑树中
    binder_insert_allocated_buffer(proc, buffer);
    // 从原来的空闲内核缓冲区中分配出来一块新的内核缓冲区之后，是否还有剩余。
    if (buffer_size != size) {  
        // 如果有，将剩余的内核缓冲区封装成另外一个新的空闲内核缓冲区new_buffer，
        // 并将它添加到目标进程的内核缓冲区列表，以及空闲内核缓冲区红黑树中
        struct binder_buffer *new_buffer = (void *)buffer->data + size;
        list_add(&new_buffer->entry, &buffer->entry);
        new_buffer->free = 1;
        binder_insert_free_buffer(proc, new_buffer);
    }
    binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
             "binder: %d: binder_alloc_buf size %zd got "
             "%p\n", proc->pid, size, buffer);
    // 对新分配的内核缓冲区执行初始化操作
    buffer->data_size = data_size;          // 数据缓冲区大小
    buffer->offsets_size = offsets_size;    // 偏移数组缓冲区大小
    buffer->async_transaction = is_async;
    if (is_async) {//如果用于异步事务，则减少目标进程proc可用于异步事务的内核缓冲区大小
        proc->free_async_space -= size + sizeof(struct binder_buffer);
        binder_debug(BINDER_DEBUG_BUFFER_ALLOC_ASYNC,
                 "binder: %d: binder_alloc_buf size %zd "
                 "async free %zd\n", proc->pid, size,
                 proc->free_async_space);
    }

    return buffer;
}
```
# 释放内核缓冲区
当一个进程处理完成Binder驱动程序给它发送的返回协议BR_TRANSACTION或BR_REPLY之后，它就会使用命令协议BC_FREE_BUFFER来通知Binder驱动程序释放响应的内核缓冲区，以免浪费内存。
``` c
static void binder_free_buf(struct binder_proc *proc,
                struct binder_buffer *buffer)
{
    size_t size, buffer_size;
    // 计算要释放的内核缓冲区buffer的大小
    buffer_size = binder_buffer_size(proc, buffer);
    // 计算数据缓冲区以及偏移数组缓冲区的大小之和
    size = ALIGN(buffer->data_size, sizeof(void *)) +
        ALIGN(buffer->offsets_size, sizeof(void *));

    binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
             "binder: %d: binder_free_buf %p size %zd buffer"
             "_size %zd\n", proc->pid, buffer, size, buffer_size);

    BUG_ON(buffer->free);
    BUG_ON(size > buffer_size);
    BUG_ON(buffer->transaction != NULL);
    BUG_ON((void *)buffer < proc->buffer);
    BUG_ON((void *)buffer > proc->buffer + proc->buffer_size);
    // 如果用于异步事务，将它所占用的大小增加到目标进程proc可用于
    // 异步事务的内核缓冲区大小free_async_space中
    if (buffer->async_transaction) {
        proc->free_async_space += size + sizeof(struct binder_buffer);

        binder_debug(BINDER_DEBUG_BUFFER_ALLOC_ASYNC,
                 "binder: %d: binder_free_buf size %zd "
                 "async free %zd\n", proc->pid, size,
                 proc->free_async_space);
    }
    // 释放内核缓冲区buffer用来保存数据的那一部分地址空间所占用的物理页面
    binder_update_page_range(proc, 0,
        (void *)PAGE_ALIGN((uintptr_t)buffer->data),
        (void *)(((uintptr_t)buffer->data + buffer_size) & PAGE_MASK),
        NULL);
    // 从目标进程proc已分配物理页面的内核缓冲区红黑树中删除
    rb_erase(&buffer->rb_node, &proc->allocated_buffers);
    buffer->free = 1;
    // 如果要释放的内核缓冲区buffer不是目标进程proc的内核缓冲区列表中的最后一个元素，
    // 并且它前后的内核缓冲区也是空闲的，那么就需要将它们合并成一个更大的空闲内核缓冲区
    if (!list_is_last(&buffer->entry, &proc->buffers)) {
        struct binder_buffer *next = list_entry(buffer->entry.next,
                        struct binder_buffer, entry);
        if (next->free) {
            rb_erase(&next->rb_node, &proc->free_buffers);
            binder_delete_free_buffer(proc, next);
        }
    }
    if (proc->buffers.next != &buffer->entry) {
        struct binder_buffer *prev = list_entry(buffer->entry.prev,
                        struct binder_buffer, entry);
        if (prev->free) {
            binder_delete_free_buffer(proc, buffer);
            rb_erase(&prev->rb_node, &proc->free_buffers);
            buffer = prev;
        }
    }
    // 将回收的buffer添加到目标进程proc空闲内核缓冲区红黑树中
    binder_insert_free_buffer(proc, buffer);
}
```
# 删除binder_buffer结构体的函数binder_delete_free_buffer
调用该函数时，必须保证它指向的内核缓冲区不是目标进程proc的第一个内核缓冲区，
并且该内核缓冲区以及它前面的内核缓冲区都是空闲的；否则，函数就会报错。
kerne/goldfish/drivers/staging/android/binder.c:848
``` c
static void binder_delete_free_buffer(struct binder_proc *proc,
                      struct binder_buffer *buffer)
{
    struct binder_buffer *prev, *next = NULL;
    int free_page_end = 1;
    int free_page_start = 1;

    BUG_ON(proc->buffers.next == &buffer->entry);
    prev = list_entry(buffer->entry.prev, struct binder_buffer, entry);
    BUG_ON(!prev->free);
    // 检查binder_buffer结构体buffer和prev的位置关系
    // 如果binder_buffer结构体buffer的第一个虚拟地址页面和binder_buffer结构体
    // prev的第二个虚拟地址页面是同一个页面
    if (buffer_end_page(prev) == buffer_start_page(buffer)) {
        // binder_buffer结构体buffer所在的第一个虚拟地址页面所对应的物理页面就不可以释放
        free_page_start = 0; 
        // 如果binder_buffer结构体buffer的第二个虚拟地址页面和binder_buffer
        // 结构体prev的第二个虚拟地址页面也是同一个页面
        if (buffer_end_page(prev) == buffer_end_page(buffer))
            free_page_end = 0;  // 第二个虚拟地址页面所对应的物理页面也不可释放
        binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
                 "binder: %d: merge free, buffer %p "
                 "share page with %p\n", proc->pid, buffer, prev);
    }

    if (!list_is_last(&buffer->entry, &proc->buffers)) {
        next = list_entry(buffer->entry.next,
                  struct binder_buffer, entry);
        // 检查binder_buffer结构体buffer和next的位置关系
        // 如果 buffer第二个虚拟地址页面和next第一个虚拟地址页面是同一个页面
        if (buffer_start_page(next) == buffer_end_page(buffer)) {
            // buffer所在的第二个虚拟地址页面所对应的物理页面就不可以释放
            free_page_end = 0;  
            // 如果buffer第一个虚拟地址页面和next的第一个虚拟地址页面也是同一个页面
            // 则buffer所在的第一个虚拟地址页面所对应的物理页面也不可释放
            if (buffer_start_page(next) ==
                buffer_start_page(buffer))
                free_page_start = 0; 
            binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
                     "binder: %d: merge free, buffer"
                     " %p share page with %p\n", proc->pid,
                     buffer, prev);
        }
    }
    // 将buffer所描述的内核缓冲区从目标进程proc的内核缓冲区列表中删除
    list_del(&buffer->entry);
    if (free_page_start || free_page_end) { // 是否需要释放buffer所占用的物理页面
        binder_debug(BINDER_DEBUG_BUFFER_ALLOC,
                 "binder: %d: merge free, buffer %p do "
                 "not share page%s%s with with %p or %p\n",
                 proc->pid, buffer, free_page_start ? "" : " end",
                 free_page_end ? "" : " start", prev, next);
        // 释放它所在的虚拟地址页面所对应的物理页面
        binder_update_page_range(proc, 0, free_page_start ?
            buffer_start_page(buffer) : buffer_end_page(buffer),
            (free_page_end ? buffer_end_page(buffer) :
            buffer_start_page(buffer)) + PAGE_SIZE, NULL);
    }
}
```
# 函数Binder_buffer_lookup根据一个用户空间地址来查询一个内核缓冲区
``` c
static struct binder_buffer *binder_buffer_lookup(struct binder_proc *proc,
                          void __user *user_ptr)
{
    struct rb_node *n = proc->allocated_buffers.rb_node;
    struct binder_buffer *buffer;
    struct binder_buffer *kern_ptr;
    // 用户空间地址user_ptr所对应的binder_buffer结构体的内核空间地址
    kern_ptr = user_ptr - proc->user_buffer_offset
        - offsetof(struct binder_buffer, data);

    // 在目标进程proc已分配内核缓冲区红黑树allocated_buffers中查找与
    // 内核空间地址kern_ptr对应的节点
    while (n) {
        buffer = rb_entry(n, struct binder_buffer, rb_node);
        BUG_ON(buffer->free);

        if (kern_ptr < buffer)
            n = n->rb_left;
        else if (kern_ptr > buffer)
            n = n->rb_right;
        else
            return buffer;  // 返回该节点所对应的一个binder_buffer结构体
    }
    return NULL;  // 找不到与用户空间地址user_ptr对应的内核缓冲区
}
```