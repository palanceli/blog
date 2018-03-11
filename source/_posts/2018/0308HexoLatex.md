---
layout: post
title: 在Hexo中通过Mathjax支持数学公式
date: 2018-03-08 10:00:00 +0800
categories: 环境、配置
tags: hexo
toc: true
comments: true
mathjax: true
---
数学公式在博客里用得越来越频繁，找到hexo的插件可以完美支持，安装过程如下：
<!-- more -->

# 安装插件
```
npm uninstall hexo-renderer-marked --save
npm install hexo-renderer-mathjax --save
npm install hexo-renderer-pandoc --save
npm install hexo-renderer-kramed --save
```

打开`/node_modules/hexo-renderer-mathjax/mathjax.html`，把`<script>`更改为：
``` html
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-MML-AM_CHTML"></script>
```
# 修改配置
在hexo配置文件`_config.yml`中添加：
```
# MathJax Support
mathjax:
  enable: true
  per_page: true
```
在主题文件`_next-theme-config.yml`中修改：
```
mathjax:
  enable: true
```

# 修改转义策略
找到`node_modules\kramed\lib\rules\inline.js`，把第11行的escape变量的值做相应的修改：
```
//  escape: /^\\([\\`*{}\[\]()#$+\-.!_>])/,
```
修改为：
```
  escape: /^\\([`*\[\]()# +\-.!_>])/,
```
这一步是在原基础上取消了对\,{,}的转义(escape)。同时把第20行的em变量也要做相应的修改。
```
//  em: /^\b_((?:__|[\s\S])+?)_\b|^\*((?:\*\*|[\s\S])+?)\*(?!\*)/,
```
修改为：
```
  em: /^\*((?:\*\*|[\s\S])+?)\*(?!\*)/,
```

更改`/node_modules/hexo-renderer-kramed/lib/renderer.js`：
```
// Change inline math rule
function formatText(text) {
    // Fit kramed's rule: $$ + \1 + $$
    return text.replace(/`\$(.*?)\$`/g, '$$$$$1$$$$');
}
```
修改为：
```
// Change inline math rule
function formatText(text) {
    return text;
}
```