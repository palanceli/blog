---
title: Binder学习笔记（十三）—— 小结？
date:   2016-07-09 18:23:50 +0800
categories: Android
tags:   binder
toc: true
comments: true
layout: post
---
先给出这张图：
![binder_transaction(...)完成后的数据结构]()
上图中标红的部分需要重点考虑一下，为什么驱动层要篡改这两个字段呢？我们结合前面的文章或许可以找出端倪。在[Binder学习笔记（七）—— ServiceManager如何响应addService请求 ？](http://localhost:4000/blog/2016/05/12/2016/0514BinderLearning7/)一文中其实留下了挺多疑问。
server端调用addService向ServiceManager注册该Service，ServiceManager保存Service的(name, binder)二元对以备后用，但其中最不可理解的是在函数`bio_get_ref(struct binder_io *bio)`中判断当Service的type==BINDER_TYPE_HANDLE时，binder为0。这个疑团现在就可以打开了：因为ServiceManager收到的service的type不可能为BINDER_TYPE_BINDER！尽管在Server端组织的数据结构中type=BINDER_TYPE_BINDER，但在驱动层被上图的红色部分过了一手，把它改成了BINDER_TYPE_HANDLE。
也就是说一个binder在由Server端发给ServiceManager时，binder在Server端是实体，到了ServiceManager端就要变成引用，因为实体并不在自己的进程空间。同理，我推断当Client端调用Server端的Binder服务时，Client端使用的是引用，到了Server端会变成实体。我们看`binder_transaction(...)`函数中case BINDER_TYPE_HANDLE和case BINDER_TYPE_WEAK_HANDLE的代码，确实是有这样的修改。
flat_binder_object的binder字段和handle字段公用一个联合，在实体端使用binder，在引用端使用handle，在驱动层完成binder<-->handle的转换，使之对实体/引用端透明，这是驱动层的职责。那么为什么要有这种转换呢？这个字段的作用就是为了提领到binder，使用一个唯一标识不就行了么？问题就在于这个“唯一标识”不好搞，binder是跨进程的调用，所以这个“唯一标识”必须要系统全局唯一。binder在Server端就是BnService的影子对象的地址，这个地址在Server进程中是全局唯一的；但是到了ServiceManager一端却不唯一，为了确保它在这一端的唯一性，驱动为它生成了在ServiceManager中的唯一id，即haneld，也即ref->desc，可是它仅在ServiceManager内唯一。于是驱动层需要做这个转化，确保在阴阳两界各自唯一，到了对端就不唯一的两个id之间建立关联，使得一端向另一端的binder喊话时，对端对应的binder能收到。



