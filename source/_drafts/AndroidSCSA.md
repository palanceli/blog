---
title: Android系统源代码情景分析 - Binder驱动程序
tags:
toc: true
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
>书签

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