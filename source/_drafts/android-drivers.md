---
title: android drivers
tags:
---
# module_init和device_initcall宏
kernel/goldfish/include/linux/init.h:267
``` c
    #define module_init(x)  __initcall(x);
```
kernel/goldfish/include/linux/init.h:213
``` c
    #define __initcall(fn) device_initcall(fn)
```
kernel/goldfish/include/linux/init.h:208
``` c
    #define device_initcall(fn)     __define_initcall("6",fn,6)
```
kernel/goldfish/include/linux/init.h:178
``` c
#define __define_initcall(level,fn,id) \
    static initcall_t __initcall_##fn##id __used \
    __attribute__((__section__(".initcall" level ".init"))) = fn
```
于是展开`device_initcall(binder_init)`为
`__define_initcall("6", binder_init, 6)`，
再展开为
``` c
static initcall_t __initcall_binder_init6 __used 
    __attribute__((__section__(".initcall6.init")) = binder_init
```