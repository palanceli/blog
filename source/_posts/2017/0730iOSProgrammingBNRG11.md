---
layout: post
title: 《iOS Programming BNRG》笔记十一
date: 2017-07-30 23:00:00 +0800
categories: iOS Programming
tags: BNRG笔记
toc: true
comments: true
---
![](0730iOSProgrammingBNRG11/img04.png)
本章要点：
- UITableView的编辑模式
- Alerts的使用
<!-- more -->
# TableView的整体构造
## 1 Header和Footer
TableView的Header有Table Header和Section Header；同样，Footer有Table Footer和Section Footer：
![](0730iOSProgrammingBNRG11/img01.png)
## 2 如何为TableView创建Table Header？
只有一步：在Interface Builder中向TableView的顶部拖入一个View，然后就可以在这个View里放置按钮了
![](0730iOSProgrammingBNRG11/img02.png)
因此所谓的Table Header只是在TableView的上面放了一个普通的View，他并不是TableView体系的一部分。Table Footer也一样。
<font color=red>Section Header应该会不同，因为它要显示到TableView的内部。</font>


## 3 如何进入Editing模式
UITableViewController有一个属性isEditing表示当前是否处于Editing模式，
有一个函数func setEditing(_ editing: Bool, animated: Bool)设置当前模式
因此Edit按钮的响应函数如下：
``` objc
@IBAction func toggleEditingMode(_ sender: UIButton) { 
if isEditing { 	// 当前处于editing模式
sender.setTitle("Edit", for: .normal)	// 把Edit按钮的文字改回“Edit”
setEditing(false, animated: true) 	// 撤销Edit模式
} else {		// 当前不是Editing模式
sender.setTitle("Done", for: .normal)	// 把Edit按钮的文字改成“Done”
setEditing(true, animated: true) 		// 进入Edit模式
}
}
```
<font color=red>这里只是设置了一个数据标志，之后系统会划入/划出右侧的图标。系统刷新app界面的策略是什么？为什么数据标志的修改会导致界面的变化？如果是类似Windows，定期调用onDraw函数，在onDraw内部判断当前的状态，决定怎么绘制界面，那么这个划入划出的动画又是怎么驱动的呢？</font>
![](0730iOSProgrammingBNRG11/img03.png)
## 4 如何删除一条记录
进入Editing后的界面交互，是TableView默认提供的。
![](0730iOSProgrammingBNRG11/img04.png)
可以点击左边红色按钮触发删除，这些不需要程序员控制。但是根据第10章介绍的TableView运行原理，一旦点击了删除按钮，需要数据源将该数据删除，M和V配合才能共同完成数据删除。具体需要两步：
一、在data source中实现tableView(_:commit:forRow:)方法，该方法属于TableViewDataSource协议的一部分，如果没有实现该方法，点击Delete按钮是没响应的
二、在tableView(_:commit:forRow:)方法中删除数据源中的数据，这是对M操作；调用TableView的tableView(_:commit:forRowAt:)方法删除一行，这是对V操作

代码如下：
``` objc
override func tableView(_ tableView: UITableView, commit editingStyle: UITableViewCellEditingStyle, forRowAt indexPath: IndexPath) {
    if editingStyle == .delete {	// 如果执行的是删除操作
        let item = itemStore.allItems[indexPath.row]
        itemStore.removeItem(item)		// M操作，删除数据源中的数据
        tableView.deleteRows(at: [indexPath], with: .automatic)	// V操作，删除视图中的一行
    } else if editingStyle == .insert {
        ...
    }    
}
```
tableView(_:commit:forRow:)方法从命名上就能判断，它不止用于处理删除，还可以处理其他的编辑操作，具体是哪种操作视editingStyle而定

## 5 如何调整TableView中记录的顺序
默认生成的TableView，进入Editing模式后是不能调整顺序的，由1.4不难猜测肯定是因为没有实现data source协议的某个接口。是的，这个接口的名字叫
tableView(_:moveRowAt:to:)
和1.4类似，实现该接口只需要操作数据源，调整数据的顺序即可。这里不需要通知TableView进行V操作，因为操作是通过用户在TableView上交互自然完成的。代码如下：
``` objc
override func tableView(_ tableView: UITableView, moveRowAt fromIndexPath: IndexPath, to destinationIndexPath: IndexPath) {
    itemStore.moveItem(from: fromIndexPath.row, to: destinationIndexPath.row) // M操作，只需要操作数据源即可
}
```
当然在此之前需要自己添加itemStore的mvoeItem方法

## 6 如何向TableView添加一行数据
按照第10章给出的TableView原理，添加记录应该只需要操作数据源，添加一条记录就可以了，但这只完成了一半，在运行中途动态添加数据还需要通知TableView更新：
一、向数据源添加一条数据
二、通知TableView添加一行
``` objc
@IBAction func addNewItem(_ sender: UIButton){
    let newItem = itemStore.createItem()		// 往数据源添加一条数据
    
    if let index = itemStore.allItems.index(of: newItem){
        let indexPath = IndexPath(row: index, section: 0)
        tableView.insertRows(at:[indexPath], with:.automatic)		// 通知TableView增加一行
    }
}
```

## 7 如何跳到另一个页面？如何返回？

## 8 如何为TableView创建Section Header？

# 显示Alerts
## 1 Alerts的两种风格
可以通过UIAlertControllerStyle来指定Alert的显示风格
![](0730iOSProgrammingBNRG11/img05.png)
## 2 使用actionSheet Alert的操作步骤
先来看这种风格界面的完整展现：
![](0730iOSProgrammingBNRG11/img06.png)
实现这种提示共分三步：
一、构造UIAlertController实例，并指定Title和Message。上图中第一行粗体灰字就是Title，第二行灰字就是Message。
二、构造用户可以选择的UIAlertAction实例，指定Title、风格和操作，并将这些实例添加到UIAlertController实例中。上图中的Delete和Cancel分别对应一个UIAlertAction实例。
三、调用VC的present方法，并传入UIAlertController实例完成显示。

代码如下：
``` objc
let item = itemStore.allItems[indexPath.row]

// 第一步：构造UIAlertController实例
let title = "Delete \(item.name)?"
let message = "Are you sure you want to delete this item?"
let ac = UIAlertController(title: title, message:message, preferredStyle:.actionSheet)

// 第二步：分别构造两个UIAlertAction实例，并添加到ac
let cancelAction = UIAlertAction(title: "Cancel", style: .cancel, handler: nil)
ac.addAction(cancelAction)

let deleteAction = UIAlertAction(title: "Delete", style: .destructive, 
handler: {(action) -> Void in			// 原先的删除操作作为闭包传入AA的handler参数
    self.itemStore.removeItem(item)		
    self.tableView.deleteRows(at: [indexPath], with: .automatic)
})
ac.addAction(deleteAction)
// 第三步：弹出提示框
present(ac, animated: true, completion: nil)
```
## 3 使用alert Alert的操作步骤
