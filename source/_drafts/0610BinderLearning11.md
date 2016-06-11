---
title:  "Binder学习笔记（十）—— 智能指针"
date:   2016-06-10 00:07:23 +0800
categories: Android
tags:   binder
toc: true
comments: true
---
# 轻量级指针
Binder的学习历程爬到驱动的半山腰明显感觉越来越陡峭，停下业务层的学习，补补基础层知识吧，这首当其冲的就是智能指针了，智能指针的影子在Android源码中随处可见。打开frameworkds/rs/cpp/util，RefBase.h和StrongPointer.h两个文件，代码多读几遍都能读懂，可是串起来总感觉摸不到骨架，把不住主线。闭上眼零零星星的点串不成一条线。究其原因应该是此处使用了模式，最好先剔除掉业务层的皮肉，把模式的骨架摸个门清，再回来看代码就会势如破竹了。

不是多么高深的设计模式，智能指针和引用计数的混合而已。但，不要轻敌。翻开书，对这两个模式的描述竟有50页之多。我读的是Scott Meyers的《More Effective C++》，侯sir翻译的版本，十年前读这本书的时候囫囵吞枣很多读不懂，有一些概念依稀留下点印象。这些印象就构成了日后遇到问题时的路标，告诉我答案在哪里。这本书条款28、29讲的正是智能指针和引用计数，两章结尾处的代码几乎就是Android源码中LightRefBase和sp的原型。每一个条款都从一个简单的目标入手，不断地解决问题，再升级提出它的不足，再找答案，直到把这个问题打穿打透为止。这两个条款的内容就不赘述了，书里写的更精彩。接下来我把模式和Android源码的智能指针对接起来。

《More Effective C++》第203页，条款29描绘了具有引用计数功能的智能指针模式图如下：
![《More Effective C++》条款29](img01.png)
这张图还是把业务逻辑和模式框架混在一起了：
* String代表业务逻辑
* RCPtr是具备引用计数功能的智能指针
* RCObject用来履行引用计数的职责
* StringValue和HeapMemory又是局部的业务逻辑了

所以该模式本质上是由RCPtr和RCObject联袂完成，RCPtr负责智能指针，RCObject负责引用计数，如下：
![具备引用计数功能得智能指针](img02.png)
一个对象如果要配备引用计数和智能指针，则需要：
``` c++
class MyClass : public RCObject // 让该对象的类从RCObject派生
{...};
RCPtr<MyClass> pObj; // 声明对象
```
对应到Android源码中，LightRefBase就是RCObject，sp就是RCPtr：
![Android源码中的轻量级智能指针](img03.png)

我在初读Android源码的时候一直琢磨为什么搞得这么复杂，不能把智能指针封装在一个基类里。如果可以的话，MyClass只需要从这个类派生就好了。答案是不可以。因为RCPtr本质上要充当指针的角色，ptr1可以指向A，也可以指向B，当从A转向了B，应该让A的引用计数递减，让B的引用计数递增，这个计数只能是被指对象的属性，而不能是指针的。

我之所以会有合二为一的年头，是因为过去接触的智能指针大都是为了解决遇到Exception或错误返回时防止内存或资源泄露，又不想使用goto语句，比如：
``` c++
int fun(char * filename)
{
    FILE* fp = fopen(filename, "r");
    int result = 0
    ... ...
    if(error){
        result = -1;
        goto exit;
    }
exit:
    fclose(fp);
    return result;
}
```
如果在函数中打开了多种资源，则要么记住它们的状态，在exit中根据状态擦屁股；要么就得有多个goto标记。此时就可以使用智能指针的思想，给文件做个封装：
``` c++
void fun(char * filename)
{
    MyFile file;  // MyFile在析构的时候会自动关闭文件
    if(!file.open(filename, "r"))
        return -1;
    ... ...
}
```
这一类的智能指针可以看做“具备引用计数的智能指针”的特例，它的引用计数最多为1，且不存在所有权的转移，可以把引用计数RCObject模块退化掉，指针指向资源即代表引用计数为1，不指向任何资源则代表引用计数为0。因此这种情况可以让MyClass仅派生自RCPtr基类即可，一旦引用计数允许大于1，就必须带上RCObject的角色了。

回到Android源码上来，轻量级的智能指针：
* LightRefBase负责维护引用计数，并提供递增/递减的接口。
* sp履行智能指针的角色，负责构造析构、拷贝和赋值、提领。

还有一个问题：LightRefBase和《More Effective C++》条款29中的RCObject相比多出一个模板参数，在该类的定义中几乎没有用到这个模板参数，这是为什么？我分析应该是出于性能的考虑——这样做可以省去虚表的开销：
``` c++
RCObject::removeReference()
{if(--refCount == 0) delete this;}
```
这里要经由基类的指针删除派生类的对象，在《Effecive C++（第三版）》（刚刚发现这本书的第二版和第三版调整很大！）第7条中说到:
> 当派生类的对象经由基类指针被删除时，基类必须有虚析构函数，否则会导致未定义的行为，通常是对象的devrived成分没被销毁。

RCObject确实声明了析构函数为virtual，也因此不得不引入虚表。再看LightRefBase：
``` c++
template <class T>
class LightRefBase
{
... ...
    inline void decStrong(const Void* id) const{
        if(android_atomic_dec(&mCount) == 1){
            // 这里并没有delete this，而是先转成子类再delete，这就不再是
            // “经由基类指针删除子类对象”，而是“由子类指针删除子类对象”了，
            // 怎么得到子类指针？模板参数T呀！为这段代码拍案叫绝！
            delete static_cast<const T*>(this);
        }
    }
};
```
## 情景分析
Android智能指针的代码不多，且比较独立，我把它们抽取出来，再写一些测试用例，对这块代码的理解大有裨益。我在Anrdoid源码中每个函数头部都打了Log，标示函数名。代码可以到这里下载[androidex/host-smartptr](https://github.com/palanceli/androidex/tree/master/host-smartptr)。这里的Android源码取自android-6.0.1_r11。
* StrongPointer.h
来自`frameworks/rs/cpp/util/StrongPointer.h`
* RefBase.h
来自`frameworks/rs/cpp/util/RefBase.h`
* RefBase.cpp
来自`system/core/libutils/RefBase.cpp`
* meyers.h
来自《More Effective C++》条款29，是带有引用计数功能的智能指针的实现
* testlightptr.cpp和testweightptr.cpp
是对Android轻量级智能指针和强、弱智能指针的测试用例，
* logger.h
是一个log工具，
* smartptr.cpp
是主入口函数，该文件包含若干测试用例，函数名为tc01、tc02...

该程序的使用方法为：
``` bash
smartptr <tcname>
```
例如：
``` bash
smartptr tc01  # 它执行例程函数tc01
```
一下是对轻量级指针的测试代码：
``` c++
#include <stdio.h>
#include "RefBase.h"
#include "logger.h"

class LightClass : public LightRefBase <LightClass>
{
public:
    LightClass(){}
    ~LightClass(){}
};

int testlightptr(int argc, char const * argv[])
{
    // 初始lpLightClass的引用计数为0
    LightClass * pLightClass = new LightClass();
    // 调用sp的复制构造函数sp::sp(T* other)，使得pLightClass的引用计数为1。
    sp<LightClass> lpOut = pLightClass;
    Logging("Light Ref Count: %d.", pLightClass->getStrongCount());
    {
        // 调用sp的赋值构造函数sp::sp(const sp<T>& other)，
        // 使得pLightClass的引用计数累加为2
        sp<LightClass> lpInner = lpOut;
        Logging("Light Ref Count: %d.", pLightClass->getStrongCount());
        // lpInner析构，pLightClass的引用计数递减为1
    }
    Logging("Light Ref Count:%d.", pLightClass->getStrongCount());
    return 0;
    // lpOut析构，pLightClass引用计数递减为0，在decStrong(...)中delete pLightClass
}
```
执行结果如下：
``` bash
$ ./smartptr tc01
[StrongPointer.h:41] sp::sp(T*)
[testlightptr.cpp:16] Light Ref Count: 1.
[StrongPointer.h:47] sp::sp(const sp<T>&)
[testlightptr.cpp:19] Light Ref Count: 2.
[StrongPointer.h:53] sp::~sp()
[testlightptr.cpp:21] Light Ref Count:1.
[StrongPointer.h:53] sp::~sp()
```
# 强/弱智能指针
强/弱指针把我折腾的七荤八素的，因为没有原型可参考了，我相信这个设计必有出处，只是自己没有找到，于是只好啃代码。强/弱智能指针的代码比轻量级智能指针复杂很多，静态代码研究很容易陷入“每句代码都明白，就是抓不住灵魂”的境地，我发现最好的应对方法是从需求出发，找到一两个使用场景代入走查一下。好在这块代码比较独立，前面我已经把他们抽取出来，情景分析是比较容易的。

## 强/弱智能指针的目的
轻量级智能指针可以完成对目标对象的引用计数的记录，并在没有没有任何指针指向目标对象的时候自动销毁对象，防止内存泄漏。但是当遇到循环引用的时候，该手段就失效了，如下图：
![当智能指针遇上循环引用](img04.png)
当p不再指向objectA，其引用计数由2变为1，相互指向的objectA和objectB就变成悬浮的两座孤岛，再也没有路径可以访问到它们，于是造成了内存泄漏。

解决方案是给循环引用的双方定义主从关系，由主指向从的智能指针就称为强指针，由从指向主的指针就称为弱指针，强/弱指针仍然都是具备引用计数功能的智能指针，只是当一个对象没有强指针指向的时候就可以销毁掉了。如下图：
![强弱指针解决循环引用的问题](img05.png)
实线代表强指针，虚线代表弱指针。当p不再指向objectA，其强引用计数递减为0，于是objectA可以销毁，它指向objectB的强指针也被销毁，于是objectB的强引用计数递减为0，objectB也可以销毁。

## 强/弱智能指针的使用
强/弱智能指针的定义和使用形式如下：
``` c++
// 对象实体必须从RefBase派生，该类在`RefBase.h`和`RefBase.cpp`中声明和定义
class MyClass : public RefBase
{
......
};
......
sp<MyClass> pStrong(new MyClass);   // 定义强指针
wp<MyClass> pWeak(new MyClass);     // 定义弱指针
```
我们来看看RefBase，frameworks/rs/cpp/util/RefBase.h
``` c++
class RefBase
{
........

    class weakref_type
    {
        ........
    };

......

    virtual                 ~RefBase();

    enum {
        OBJECT_LIFETIME_STRONG  = 0x0000,
        OBJECT_LIFETIME_WEAK    = 0x0001,
        OBJECT_LIFETIME_MASK    = 0x0001
    };

......

private:
    ......
    class weakref_impl;
        
    weakref_impl* const mRefs;
};
```
和LightRefBase相比有三个明显的差异：
1. 没有模板参数，前文已经分析过LightRefBase使用模板参数是出于性能的考虑，省去一个虚表的开销，而RefBase定义了virtual的析构函数，可见继承关系可能是在所难免的，于是再用模板参数就没有任何意义了。
2. RefBase没有像LightRefBase那样直接用成员变量记录引用计数，而是又定义了一个weakref_impl*类型的成员，由它来记录强/弱引用计数。这是为什么？从前面模型图上就能找到答案：
![强弱指针解决循环引用的问题](img05.png)
继续前面的推演，objectA被销毁后，objectB还有一个弱指针指向objectA的。objectA在销毁的时刻，只能处理由自己发出的指针，而无法知道都有谁指向了自己。于是objectA被销毁后，来自objectB的弱指针也就成了野指针。为了解决这个问题，可以让引用计数和对象实体分离，如下图：
![引用计数与对象实体分离](img06.png)
于是就有了weakref_impl* mRefs成员，该成员被称为他所记录的实体对象的影子对象，影子和本尊之间有指针指向对方，但影子的生存周期可能比本尊还要长。因为影子负责记录本尊的强/弱引用计数，当强引用计数为0时，本尊被销毁，影子继续记录其弱引用计数，直到两个引用计数分别为0，影子才被销毁掉。
3. 枚举类型OBJECT_LIFETIME_xxx。这本不算和LightRefBase之间的差异，但在阅读RefBase代码时这三种类型左右着实体对象的生命周期策略。这也是最让我疑惑的地方：既然强引用计数决定实体的生命周期，为什么还要在reakref_impl中用一个成员变量mFlags来记录实体的生命周期受哪个引用计数控制呢？试想如下这种情况：
![](img07.png)
当p1不再指向objectA，它的强引用计数就为0了，于是可以被销毁。可此时还有p2指向objectB，两个实体对象并没有成为孤岛，还有可能要通过p2再访问objectA和objectB组成的循环链表，在objectA和objectB之间定义主从关系仅仅是为了避免孤岛导致的内存泄漏。所以尽管objectA此时的强引用计数已为0，只要弱引用计数还在，还是先留objectA一条小命，让它再苟延残喘一段时间，直到其弱引用计数也为0，说明彻底没用了，到那时候再真地干掉。这就是mFlags和这三个枚举类型的作用：
 * 当mFlags为OBJECT_LIFETIME_STRONG，实体对象的生命周期遵循强/弱指针最初始的规则：强引用计数为0，就销毁；
 * 当mFlags为OBJECT_LIFETIME_WEAK，如果强引用计数为0，实体对象暂时不要销毁，等到弱引用计数也为0时再销毁

## 情景分析

