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