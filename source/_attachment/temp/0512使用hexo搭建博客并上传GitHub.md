---
title: 使用hexo搭建博客并上传GitHub
date:   2016-05-12 10:28:48 +0800
categories: 环境、配置
tags:   hexo
---
之前在博客园、简书、CSDN等地儿都开过博，一篇文章写好了，我希望能在几个平台可以同步发布，可是操作起来成本不低。几个平台下的富文本编辑器比较起来还是博客园更顺手，看着更舒服，尤其是代码块的操作灵活、准确。而CSDN对代码块内的文字加粗、修改字色后就会出现html文无法解析的情况，混杂着代码和html文本实在太难看了，后来我知道原来是Markdown的代码块规则限制。而且CSDN刚刚才取消了提交文章要审核通过才能发布的限制，审核没有完成之前，连自己都看不到，且不能修改，这让我一度放弃CSDN平台。如果是写普通的文章写作体验最好的是简书，大气、简洁。但简书更适合一般的写作，比较技术化的中间掺杂大量代码的支持还不够好。
<!-- more -->
作为一名程序员，应该到GitHub上开博，这里是程序员的圣城。花了两天时间研究了一下，发现还蛮简单的，而且md格式也被博客园、简书、CSDN所支持，写完一份应该比较容易复制到这三个平台。我喜欢在本地编辑markdown文件，使用sublime 及其插件Markdown Editing 和 OmniMarkupPreviewer。完成后底稿、资源文件都悉数保存到GitHub，日后查找、修改都很容易。
我用hexo作为静态页面生成器，操作过程遇到不少问题，搞定之后留一份操作记录吧。

# 安装环境
环境安装步骤可以参见[hexo 官方文档](https://hexo.io/zh-cn/docs)。这里还是记下一份操作路径，以后重新安装时，闭着眼睛操作就好了，呵呵呵~

安装Node.js
`$ curl https://raw.github.com/creationix/nvm/master/install.sh | sh`
`$ nvm install stable`

安装Hexo
`$ sudo npm install -g hexo-cli`

# 建站
`$ cd blog`
`$ hexo init`
`$ npm install`

将自己的`GitHub/blog.git`项目 Clone到本地`blog/blog`下。将主题Clone到`blog/themes/next`下，我使用的主题是[NexT](https://github.com/palanceli/hexo-theme-next)。

执行脚本`setup.sh`：
`$ cd blog`
`$ sh setup.sh`
该shell脚本的主要作用是：
删除文件(夹)：
`blog/source/`
`blog/_config.yml`
`blog/themes/next/_config.yml`
然后分别为它们创建软链：
`blog/source/ -> blog/blog/source`
`blog/_config.yml -> blog/blog/_config.yml`
`blog/themes/next/_config.yml -> blog/blog/_next-theme-config.yml`
注意：生成软链一定要使用绝对路径哦。

接下来就可以生成网页了：
`$ hexo clean`
`$ hexo generate`
`$ hexo server`

# 关联GitHub
安装hexo-delopyer-git：
`$ npm install hexo-deployer-git --save`

在`blog/_config.yml`中添加：
```
deploy:
  type: git
  repository: https://github.com/palanceli/palanceli.github.io.git
  branch: master
```

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

## 隐藏文件
可以将文件生成到草稿目录下：
``` bash
$ hexo new draft "new draft"
```
或者直接在source/_drafts下新建md文件。如果希望在本地`hexo s`时文件可见，要么在md文件的`front-matter`中加入`render_drafts: true`，要么在启动server的时候使用`hexo server --drafts`


