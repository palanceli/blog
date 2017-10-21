---
layout: post
title: 《iOS Programming BNRG》笔记十九
date: 2017-08-07 23:00:00 +0800
categories: iOS Programming
tags: iOS BNRG笔记
toc: true
comments: true
---
本章在前一章基础上支持了对已经完成的直线的删除、拖动。
![](0807iOSProgrammingBNRG19/img01.png)
本章要点：
- UIGestureRecognizer
- UIMenuController
<!-- more -->

# 1 UIGestureRecognizer
## 1.1 UIGestureRecognizer和原始触屏事件之间的关系
所有的`UIGestureRecognizer`事件都以
``` objc
func action(_ gestureRecognizer: UIGestureRecognizer){}
```
的形式发出。参数是发生这个消息的手势实例，通过该实例可以得到比如手势发生位置等与此手势相关的信息。
当识别出是一种手势后，`UIGestureRecognizer`会拦截发往view的触屏事件，这会导致`UIResponder`事件不会再被发给该视图。

## 1.2 添加手势的基本步骤
一、添加手势实例。
``` objc
required init?(coder aDecoder: NSCoder) {
    super.init(coder: aDecoder)
        
    // 创建手势实例，一个手势实例连接target和action
    let doubleTapRecognizer = UITapGestureRecognizer(target: self, action: #selector(DrawView.doubleTap(_:)))
    doubleTapRecognizer.numberOfTapsRequired = 2	// 这是一个双击手势
    addGestureRecognizer(doubleTapRecognizer)		// 往视图添加手势
}
```
<font color=red>init函数后面的问号是啥意思？required关键字是啥意思？</font>

二、实现手势处理函数
``` objc
func doubleTap(_ gestureRecognizer: UIGestureRecognizer){
    currentLines.removeAll()	// 删除固化和正在绘制的直线
    finishedLines.removeAll()
    setNeedsDisplay()
}
```
## 1.3 如何避免一个完整的手势被识别前的原始UIResponder消息处理
在1.2中添加了一个双击消息，在单指触屏一次后，由于无法判断后面还会不会再击屏幕，因此会收到`touchesBegan(_:with:)`消息，如果继续完成了双击，才会收到`doubleTap(_:)`，并再收到单击的`touchesCancelled(_:with:)`，这样以后就不再收到`UIResponder`消息了。
这会导致第一次单击在view上绘制一小段线段，为了避免这种情况发生，可以将手势实例的`delaysToucesBagan`属性设为true：
``` objc
doubleTapRecognizer.delaysTouchesBegan = true
```
这样，手势实例会在判断当前动作是否为自己要处理的手势之后，再决定要不要把`UIResponder`消息发给View，不过代价是`UIResponder`消息会迟发一小段时间——在屏幕上单击后，过一会view才收到`touchesBegan(_:with:)`，视图上才出现小圆点。

## 1.4 如何设置两个手势的依赖关系
如果为一个视图既添加了单击手势，又添加了双击手势。一个双击动作会导致先收到单击消息，再收到双击消息，你肯定希望此时单击消息就不要处理了。通过设置手势的依赖关系可以解决这个问题。
``` objc
required init?(coder aDecoder: NSCoder) {
    super.init(coder: aDecoder)
    
    // 添加双击手势
    let doubleTapRecognizer = UITapGestureRecognizer(target: self, action: #selector(DrawView.doubleTap(_:)))
    doubleTapRecognizer.numberOfTapsRequired = 2
    doubleTapRecognizer.delaysTouchesBegan = true
    addGestureRecognizer(doubleTapRecognizer)
    // 添加单击手势
    let tapRecognizer = UITapGestureRecognizer(target: self, action: #selector(DrawView.tap(_:)))
    tapRecognizer.delaysTouchesBegan = true
    tapRecognizer.require(toFail: doubleTapRecognizer)	// 如果确认不是双击手势时再处理
    addGestureRecognizer(tapRecognizer)
}
```
需要在创建单击手势时，设置“确认不是双击手势才轮到自己处理”。当然代价和拦截`UIResponder`类似，这也会让单击消息延迟一会再处理。

## 1.5 连续型手势识别
手势识别分两种类型：一种是离散的，比如单击、双击，在识别完成后手势就结束了；另一种是连续的，比如长按，一个手势由多个阶段的识别结果组成。系统通过state属性来识别这些阶段。一个长按手势会分三个状态：
- 触屏，此时长按识别器判断这可能是一次长按的开始，但必须观察后续操作才能确认是不是一个长按。此时长按识别器的状态是`UIGestureRecognizerState.possible`
- 按住足够长的时间，此时长按识别器确认这是个长按开始，状态是`UIGestureRecognizerState.began`
- 手指从屏幕移开，手势结束。此时识别器的状态是`UIGestureRecognizerState.ended`

每次状态切换，手势识别器都会向target发送消息。

## 1.6 什么情况下两个手势识别器要同时工作
如果视图同时注册了长按和拖动，通过长按选中某条线，然后拖动改变它的位置。长按began之后的拖动，就需要它和拖动同时工作，因为在手离开屏幕之前，长按没有结束。正常情况下，长按会独占手势识别器，这会令其他的手势识别器不工作。

## 1.7 怎么解决两个手势识别器需要同时工作的问题
还以长按和拖动为例，拖动可能发生在长按的时间窗口内，当时别到拖动手势时，该手势会向其委托代理发送
``` objc
optional func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, 
                        shouldRecognizeSimultaneouslyWith 
                        otherGestureRecognizer: UIGestureRecognizer) -> Bool
```
消息，询问是否可以同时处理处理多个手势，如果该消息返回true，拖动手势就可以正常工作了。这个委托代理必须遵循UIGestureRecognizerDelegate协议

代码如下：
``` objc
// 令View遵循UIGestureRecognizerDelegate协议
class DrawView: UIView ,UIGestureRecognizerDelegate{	
    ……
    required init?(coder aDecoder: NSCoder) {
        super.init(coder: aDecoder)
       ……
        let longPressRecognizer = UILongPressGestureRecognizer(target: self, action: #selector(DrawView.longPress(_:)))
        addGestureRecognizer(longPressRecognizer)
        
        moveRecognizer = UIPanGestureRecognizer(target: self, action: #selector(DrawView.moveLine(_:)))
        moveRecognizer.delegate = self  // 将拖动手势的代理设为DrawView
        moveRecognizer.cancelsTouchesInView = false
        addGestureRecognizer(moveRecognizer)
    }

    func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldRecognizeSimultaneouslyWith otherGestureRecognizer: UIGestureRecognizer) -> Bool{
        return true	// 同时识别的询问总是返回true
    }
    ……
}
```
<font color=red>我的问题是：在长按尚未完成之前，应该是长按吃掉了手势吧，如果成立，那么在另外一个手势识别器里做任何的设置和操作怎么就能让它获得手势了呢？我认为应该在longPressRecognizer里设置个什么属性才能达到效果呀。</font>

## 1.8 怎么完成拖动
拖动`UIPanGestureRecognizer`也是一个连续型手势：当手指开始移动，它的状态为began，首次向target发送消息；当手指持续移动，它的状态为changed，并持续向target发送消息；当手指离开屏幕，状态为ended，最后一次向target发送消息。在不断发送changed消息时，调用他的`translation(in:)`方法可以得到和前一次之间的相对位移：
``` objc
func moveLine(_ gestureRecognizer: UIPanGestureRecognizer){
    print(#function)
    if let index = selectedLineIndex{
        if gestureRecognizer.state == .changed{
            let translation = gestureRecognizer.translation(in: self)
            // 移动被选中的直线
            finishedLines[index].begin.x += translation.x   
            finishedLines[index].begin.y += translation.y
            finishedLines[index].end.x += translation.x
            finishedLines[index].end.y += translation.y
            // 给位移清零，以便下次接收到的仅是针对这次的位移
            gestureRecognizer.setTranslation(CGPoint.zero, in: self)	
            
            setNeedsDisplay()
        }
    }else{
        return
    }
}
```
# 2 UIMenuController
## 2.1 创建UIMenuController的基本步骤
一、获取`UIMenuController`实例，组装菜单项，设置`UIMenuController`实例的位置，如果是令它可见，需要先将响应视图设置为first responder。
``` objc
func tap(_ gestureRecognizer: UIGestureRecognizer){
    ……
    let menu = UIMenuController.shared	// 获取UIMenuController实例
    ……
    becomeFirstResponder()	// 设置为first responder
    // 组装菜单项
    let deleteItem = UIMenuItem(title: "Delete", action: #selector(DrawView.deleteLine(_:)))
    menu.menuItems = [deleteItem]
    // 设置弹出位置，令其可见
    let targetRect = CGRect(x: point.x, y: point.y, width: 2, height: 2)
    menu.setTargetRect(targetRect, in: self)
    menu.setMenuVisible(true, animated: true)
    ……
}
```
`UIMenuController`实例是进程内全局唯一的，因此这里是获取，而不是创建。
二、设置`canBecomeFirstResponder`属性为true，令其可以成为first responder：
``` objc
override var canBecomeFirstResponder: Bool{
    return true
}
```
<font color=red>这种写法很奇怪，它是一个属性而不是函数，也可以被覆盖？那么在声明此属性的时候是怎么声明的呢？</font>

三、实现菜单项响应函数
``` objc
func deleteLine(_ sender: UIMenuController){
    ……
}
```
书中P562说到：菜单在显示之前会遍历每个菜单项，并检查first responder是否实现了该菜单项关联的方法，如果没实现，则不显示此菜单项，如果所有菜单项关联的方法都没实现，则整个菜单都不会展现。
<font color=red>问题是：如果没有实现菜单项绑定的方法，既在创建菜单项时，传入action参数没有对应的函数实现，会在`#selector()`处会编译不通过吧？</font>