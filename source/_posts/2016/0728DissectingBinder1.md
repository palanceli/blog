---
layout: post
title:  "深度探索Binder（一）取款机模型"
date:   2016-07-28 00:11:32 +0800
categories: Android
tags:   深度探索binder
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










