---
title: Android源码envsetup学习笔记
date:   2016-09-13 22:37:56 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
本文分析build/envsetup.sh脚本。该文件是编译Android源码的起点，用于设置各种环境变量。
<!-- more -->

# 帮助函数hmm
该文件以函数hmm()的定义开头，该函数提供了envsetup.sh的[Here Document](http://tldp.org/LDP/abs/html/here-docs.html)，执行如下命令即可看到输出结果：
``` bash
$ source build/envsetup.sh
$ hmm
```
来看hmm()的定义：
``` bash
# build/envsetup.sh : 1
function hmm() {
# 定义EOF为cat的结尾标志
cat <<EOF
Invoke ". build/envsetup.sh" from your shell to add the following functions to your environment:
- lunch:   lunch <product_name>-<build_variant>
- tapas:   tapas [<App1> <App2> ...] [arm|x86|mips|armv5|arm64|x86_64|mips64] [eng|userdebug|user]
- croot:   Changes directory to the top of the tree.
- m:       Makes from the top of the tree.
- mm:      Builds all of the modules in the current directory, but not their dependencies.
- mmm:     Builds all of the modules in the supplied directories, but not their dependencies.
           To limit the modules being built use the syntax: mmm dir/:target1,target2.
- mma:     Builds all of the modules in the current directory, and their dependencies.
- mmma:    Builds all of the modules in the supplied directories, and their dependencies.
- cgrep:   Greps on all local C/C++ files.
- ggrep:   Greps on all local Gradle files.
- jgrep:   Greps on all local Java files.
- resgrep: Greps on all local res/*.xml files.
- mangrep: Greps on all local AndroidManifest.xml files.
- sepgrep: Greps on all local sepolicy files.
- sgrep:   Greps on all local source files.
- godir:   Go to the directory containing a file.

Environemnt options:
- SANITIZE_HOST: Set to 'true' to use ASAN for all host modules. Note that
                 ASAN_OPTIONS=detect_leaks=0 will be set by default until the
                 build is leak-check clean.

Look at the source to view more functions. The complete list is:
EOF
    T=$(gettop)     # 函数gettop获得Android源码的根目录
    local A
    A=""
    # 遍历envsetup.sh中的函数名，把它们用空格串起来存到A里
    for i in `cat $T/build/envsetup.sh | sed -n "/^[ \t]*function /s/function \([a-z_]*\).*/\1/p" | sort | uniq`; do
      A="$A $i"
    done
    echo $A
}
```
## sed
此处使用sed把envsetup.sh中的函数名解析出来。sed的用法如下：
```
sed [-nefr] [action]
选项与参数：
-n ：使用安静(silent)模式。在一般 sed 的用法中，所有来自 STDIN 的数据一般都会被列出到终端上。但如果加上 -n 参数后，则只有经过sed 特殊处理的那一行(或者动作)才会被列出来。
-e ：直接在命令列模式上进行 sed 的动作编辑；
-f ：直接将 sed 的动作写在一个文件内， -f filename 则可以运行 filename 内的 sed 动作；
-r ：sed 的动作支持的是延伸型正规表示法的语法。(默认是基础正规表示法语法)
-i ：直接修改读取的文件内容，而不是输出到终端。

action说明： [n1[,n2]]function
n1, n2 ：不见得会存在，一般代表『选择进行动作的行数』，举例来说，如果我的动作是需要在 10 到 20 行之间进行的，则『 10,20[动作行为] 』

function说明：
a ：新增， a 的后面可以接字串，而这些字串会在新的一行出现(目前的下一行)～
c ：取代， c 的后面可以接字串，这些字串可以取代 n1,n2 之间的行！
d ：删除， d 后面通常不接任何内容；
i ：插入， i 的后面可以接字串，而这些字串会在新的一行出现(目前的上一行)；
p ：列印，将某个选择的数据印出。通常 p 会与参数 sed -n 一起运行～
s ：取代，可以直接进行取代的工作哩！通常这个 s 的动作可以搭配正规表示法！例如 1,20s/old/new/g 就是啦！
```
命令
`sed -n "/^[ \t]*function /s/function \([a-z_]*\).*/\1/p"`
是在function中跟了2个操作：
1. `"[ \t]*function /p"`表示查找所有以function打头的行
2. `"/^[ \t]*function /s/function \([a-z_]*\).*/\1/p"`则把这些行中的`function 函数名`替代为`函数名`