---
title: 使用hexo搭建博客并上传GitHub
date:   2016-05-12 10:28:48 +0800
categories: 环境、配置
tags:   hexo
---
之前在博客园、简书、CSDN等地儿都开过博，一篇文章写好了，我希望能在几个平台可以同步发布，可是操作起来成本不低。几个平台下的富文本编辑器比较起来还是博客园更顺手，看着更舒服，尤其是代码块的操作灵活、准确。而CSDN对代码块内的文字加粗、修改字色后就会出现html文无法解析的情况，混杂着代码和html文本实在太难看了，后来我知道原来是Markdown的代码块规则限制。而且CSDN刚刚才取消了提交文章要审核通过才能发布的限制，审核没有完成之前，连自己都看不到，且不能修改，这让我一度放弃CSDN平台。如果是写普通的文章写作体验最好的是简书，大气、简洁。但简书更适合一般的写作，比较技术化的中间掺杂大量代码的支持还不够好。
作为一名程序员，应该到GitHub上开博，这里是程序员的圣城。花了两天时间研究了一下，发现还蛮简单的，而且md格式也被博客园、简书、CSDN所支持，写完一份应该比较容易复制到这三个平台。我喜欢在本地编辑markdown文件，使用sublime 及其插件Markdown Editing 和 OmniMarkupPreviewer。完成后底稿、资源文件都悉数保存到GitHub，日后查找、修改都很容易。
我用hexo作为静态页面生成器，操作过程遇到不少问题，搞定之后留一份操作记录吧。

# 安装环境
* 安装node.js，去官网下载安装即可，我安装的是最新稳定版。
* 安装Hexo
`sudo npm install -g hexo`

* 创建hexo目录并初始化
```
$ mkdir hexo
$ cd hexo
$ hexo init
```

* 然后就可以生成网站，启动服务了：
```
$ hexo clean
$ hexo generate
$ hexo server
```
* hexo文件夹
先来看一下hexo文件夹下的内容：
```
hexo/
  |- node_modules/  # hexo需要的模块，不需要上传GitHub
  |- themes/        # 主题文件，需要上传GitHub的dev分支
  |- sources/       # 博文md文件，需要上传GitHub的dev分支
  |- public/        # 生成的静态页面，由hexo deploy自动上传到gh-page分支
  |- package.json   # 记录hexo需要的包信息，不需要上传GitHub
  |- _config.yml    # 全局配置文件，需要上传GitHub的dev分支
  |- .gitignore     # hexo生成默认的.gitignore，它已经配置好了不需要上传的hexo文件
```

# 关联GitHub
首次先创建GitHub工程blog，并且使用“Launch automatic page generator”生成页面，它会给该工程创建分支gh-pages。
手动为之创建dev分支，未来工程源码会放到dev分支下；hexo生成的网站静态页面会放到gh-pages分支。

* 首次创建GitHub工程后操作dev分支代码

如果是刚创建的GitHub工程，clone dev分支的代码到本地blog-dev/，然后把前面hexo/文件夹下的内容全部拷贝到blog-dev/，注意包括一个隐藏文件.gitignore。

* 已存在GitHub工程的恢复
仍是clone dev分支的代码到本地blog-dev/，然后把`hexo/node_modules/`拷贝到`blog-dev/`
再试试生成页面、启动服务，确保是正常的：
```
$ hexo clean
$ hexo generate
$ hexo server
```
网上有介绍把package.json文件同步到GitHub，以后每次恢复时执行
```
$ npm install hexo
$ npm install
$ npm install hexo-deployer-git --save
```
可是我在不同的机器上试总是出错。只好采取笨办法，每次先`hexo init`出一个完整文件夹，再把相关文件拷贝到GitHub目录下。千万不要先clone 了blog目录，再在该目录下执行`hexo init`，因为init会把.git信息删掉。

# 配置自己的_config.yml

按照如下内容修改blog-dev/_config.yml：
```
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
# 主题

这里有大量的主题`https://github.com/hexojs/hexo/wiki/Themes`
我非常喜欢Maupassant：https://www.haomwei.com/technology/maupassant-hexo.html，
简洁清晰，而且适配手机、PC各个平台。
* 安装方法
首次在blog-dev/目录下执行如下命令
```
$ git clone https://github.com/tufu9441/maupassant-hexo.git themes/maupassant
$ npm install hexo-renderer-jade --save
$ npm install hexo-renderer-sass --save
```
以后建议把blog-dev/themes/maupassant/.git文件夹删掉，把maupassant文件夹随自己的blog-dev上传到GitHub。
以后clone blog-dev后，执行完前面的安装操作步骤后记得执行
```
$ npm install hexo-renderer-jade --save
$ npm install hexo-renderer-sass --save
```

* 配置
在blog-dev/themes/maupassant/_config.yml中根据自己的情况修改，比如：
```
links:
  - title: 我的博客园
    url: http://www.cnblogs.com/palance/
  - title: 我的CSDN
    url: http://blog.csdn.net/zchongr
  - title: 我的简书
    url: http://www.jianshu.com/users/5e527164a8c2
```
在blog-dev/_config.yml中修改:
```
theme: maupassant
```

第一次的工作就完成了，可以提交github到blog-dev了。

# 上传生成页面
执行
```
$ cd blog-dev
$ npm install hexo-deployer-git --save
```
以后每次执行完
```
$ hexo clean
$ hexo generate
$ hexo server
```
生成了静态页面后就可以执行
```
hexo deploy
```
完成页面上传。

# 其它
## 图片

首先确认_config.yml中有：
```
post_asset_folder: true
```
然后在blog-dev/下执行
```
npm install https://github.com/CodeFalling/hexo-asset-image --save
```

确保在blog-dev/source/_posts下创建和md文件同名的目录，在里面放该md需要的图片，然后在md中插入
```
![](目录名/文件名.png)
```
即可在hexo generate时正确生成插入图片。比如：
```
_posts
    |- post1.md
    |_ post1
        |- pic1.png
```
在md文件中插入图片时只需写
```
![](post1/pic1.png)
```
即可。首次配置完了需要执行一次清除操作，再生成页面：
```
$ hexo clean
$ hexo generate
$ hexo server
```
如果没做清除，直接生成页面，在我这里会出现路径错误的情况。

## 视频
插入优酷视频很简单，在优酷点击视频下面的“分享”按钮，复制`通用代码`，直接粘贴到md文件中即可。

## 文章目录

参考[Maupassant作者对该主题的使用说明](https://www.haomwei.com/technology/maupassant-hexo.html)，只需要在文章的`front-matter`（即最头部写title、categories的部分）部分加入`toc: true`即可

## 评论

首先应该去http://disqus.com注册账号，并在设置中选择“Add DisqusTo Site”，然后填写自己的blog url以及shortname，注册成功后，才能在自己的主题配置文件中（themes/maupassant/_config.yml）填写disqus short name。我用的主题默认是开启评论功能的，如果要关掉，可以在`front-matter`中加入`comments: false`

## 隐藏文件
可以将文件生成到草稿目录下：
``` bash
$ hexo new draft "new draft"
```
或者直接在source/_drafts下新建md文件。如果希望在本地`hexo s`时文件可见，要么在md文件的`front-matter`中加入`render_drafts: true`，要么在启动server的时候使用`hexo server --drafts`


