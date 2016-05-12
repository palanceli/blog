---
title: 使用hexo搭建博客并上传GitHub
date:   2016-05-12 10:28:48 +0800
categories: 环境、配置
tags:   hexo
---
之前在博客园、简书、CSDN等地儿都开过博，一篇文章写好了，我希望能在几个平台可以同步发布，可是操作起来还是挺有难度，主要是成本太高。几个平台下的富文本编辑比较起来还是博客园更顺手，看着更舒服，尤其是代码块的操作灵活、准确。而CSDN对代码块内的文字加粗、修改字色后就会出现html文无法解析的情况，混杂着代码和html文本实在太难看了。后来我知道原来是Markdown的代码块规则限制。而且CSDN刚刚才取消了提交文章要审核通过才能发布的限制，审核没有完成之前，连自己都看不到，且不能修改，这让我一度放弃CSDN平台。如果是写普通的文章写作体验最好的是简书，大气、简洁。但简书更适合一般的写作，比较技术化的中间掺杂大量代码的支持还不够好。
我觉得作为一名技术狂，应该在GitHub上开博。花了两天时间研究了一下，发现还蛮简单的，而且md格式也被博客园、简书、CSDN所支持，写完一份应该比较容易复制到这三个平台。搞定之后留一份操作记录吧。
#安装环境
* 安装node.js，去官网下载安装即可，我安装的是最新稳定版。
* 安装Hexo

`sudo npm install -g hexo`

#第一次搭建Hexo
首次搭建和以后从github恢复的步骤不太一样，需要分开来讲。
创建blog目录

`$ mkdir blog`

并进入执行初始化
``` bash
$ cd blog
$ hexo init
```

然后就可以生成网站，启动服务了：
``` bash
$ hexo clean
$ hexo generate
$ hexo server
```
##上传GitHub
在github上创建工程blog，并且使用“Launch automatic page generator”生成页面，它会给该工程创建分支gh-pages。
手动为之创建dev分支，未来工程源码会放到dev分支下；hexo生成的网站静态页面会放到gh-pages分支。

* dev分支代码上传

clone dev分支的代码到本地blog-dev/，然后把
```
blog/
  |- _config.yml
  |- package.json
  |- source/
  |- scaffolds/
```
拷贝到blog-dev/下，并在blog-dev的.gitignore文件中追加如下内容：
``` bash
/public/           # 这是hexo的生成文件
/node_modules/     # 安装hexo的时候会下载
/db.json
```

* 配置blog-dev/_config.yml

按照如下内容修改：

``` bash
title: Palance's Blog   # 标题
subtitle:
description:
author: Palance Li
language: zh-CN         # 语言设置
url: http://palanceli.github.io/blog
root: /blog/
```
翻到最下面，改成：
```
deploy:
  type: git
  repository: https://github.com/<自己的github账号>/blog.git
  branch: gh-pages
```
* 主题

这里有大量的主题`https://github.com/hexojs/hexo/wiki/Themes`
我选了Maupassant：https://www.haomwei.com/technology/maupassant-hexo.html
安装方法：
``` bash
$ git clone https://github.com/tufu9441/maupassant-hexo.git themes/maupassant
$ npm install hexo-renderer-jade --save
$ npm install hexo-renderer-sass --save
```

在blog-dev/_config.yml中修改:
``` bash
theme: maupassant
```
第一次的工作就完成了，可以提交github到blog-dev了。

# 从GitHub恢复hexo

首先从GitHub上clone blog的blog-dev分支到本地blog-dev/下
``` bash
$ cd blog-dev
$ npm install hexo
$ npm install
$ npm install hexo-deployer-git
```
**千万不要执行hexo init，它会把blog-dev的git信息冲掉。**
以后每次修改完执行deploy，将代码上传到blog-dev分支下：

`hexo deploy`

# 其它
## 图片

首先确认_config.yml中有：
```
post_asset_folder: true
```
然后在blog-dev/下执行
``` bash
npm install https://github.com/CodeFalling/hexo-asset-image --save
```

确保在blog-dev/source/_posts下创建和md文件同名的目录，在里面放该md需要的图片，然后在md中插入
```
![](目录名/文件名.png)
```
即可在hexo generate时正确生成插入图片。比如：
``` bash
_posts
    |- post1.md
    |_ post1
        |- pic1.png
```
在md文件中插入图片时只需写
```
![](post1/pic1.png)
```
即可