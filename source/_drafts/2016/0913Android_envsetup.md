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

# 一堆include
``` bash
# Execute the contents of any vendorsetup.sh files we can find.
for f in `test -d device && find -L device -maxdepth 4 -name 'vendorsetup.sh' 2> /dev/null | sort` \
         `test -d vendor && find -L vendor -maxdepth 4 -name 'vendorsetup.sh' 2> /dev/null | sort`
do
    echo "including $f"
    . $f
done
unset f
```
## test命令
其中test命令格式：
`test condition`
通常在if-then-else中，用[]代替，即[ condition ]，注意：方括号两边都要有空格。test命令可用于多种类型的比较。
* 文件比较，condition格式如下：
``` bash
-d file 检查file是否存在并是一个目录 
-e file 检查file是否存在 
-f file 检查file是否存在并是一个文件 
-r file 检查file是否存在并可读 
-s file 检查file是否存在并非空 
-w file 检查file是否存在并可写 
-x file 检查file是否存在并可执行 
-O file 检查file是否存在并属当前用户所有 
-G file 检查file是否存在并且默认组与当前用户相同 
file1 -nt file2 检查file1是否比file2新 
file1 -ot file2 检查file1是否比file2旧 
```
* 字符串比较，condition格式如下：
``` bash
str1 = str2 检查str1是否和str2相同 
str1 != str2 检查str1是否和str2不同 
str1 < str2 检查str1是否比str2小 
str1 > str2 检查str1是否比str2大 
-n str1 检查str1的长度是否非0 
-z str1 检查str1的长度是否为0 
```

所以，上面的for循环中，分两部分，第一部分：
1. 判断文件夹device是否存在
2. 进入device目录下最多4层，查找所有vendorsetup.sh文件

第二部分和第一部分一样，只是把device换成vendor。因此这段代码就是查找目录device和vendor下所有的vendorsetup.sh文件，并执行。

## vendorsetup.sh
例如，device/huawei/angler/vendorsetup.sh的内容如下：
``` bash
add_lunch_combo aosp_angler-userdebug
```
### add_lunch_combo

``` bash
add_lunch_combo函数的定义如下：
# build/envsetup.sh:450
function add_lunch_combo()
{
    local new_combo=$1  # $1是要添加的菜单项
    local c
    for c in ${LUNCH_MENU_CHOICES[@]} ; do  # 如果要添加的菜单项已经存在，则返回
        if [ "$new_combo" = "$c" ] ; then
            return
        fi
    done
    LUNCH_MENU_CHOICES=(${LUNCH_MENU_CHOICES[@]} $new_combo)    # 添加
}

# add the default one here
add_lunch_combo aosp_arm-eng
add_lunch_combo aosp_arm64-eng
add_lunch_combo aosp_mips-eng
add_lunch_combo aosp_mips64-eng
add_lunch_combo aosp_x86-eng
add_lunch_combo aosp_x86_64-eng

```
# lunch命令
``` bash
# build/envsetup.sh:489
function lunch()
{
    local answer

    if [ "$1" ] ; then  # 是否有参数
        answer=$1
    else
        print_lunch_menu
        echo -n "Which would you like? [aosp_arm-eng] "
        read answer     # 如果没有则读入
    fi

    local selection=

    if [ -z "$answer" ]     # answer长度为0
    then
        selection=aosp_arm-eng
    elif (echo -n $answer | grep -q -e "^[0-9][0-9]*$") # answer为数字
    then
        if [ $answer -le ${#LUNCH_MENU_CHOICES[@]} ]
        then
            selection=${LUNCH_MENU_CHOICES[$(($answer-1))]} # 得到菜单项内容
        fi
    elif (echo -n $answer | grep -q -e "^[^\-][^\-]*-[^\-][^\-]*$") # 为字串
    then
        selection=$answer
    fi

    if [ -z "$selection" ]
    then
        echo
        echo "Invalid lunch combo: $answer"
        return 1
    fi

    export TARGET_BUILD_APPS=
    # selection 应该符合<product>-<variant>的形式，product为设备型号，variant为编译类型
    local product=$(echo -n $selection | sed -e "s/-.*$//")
    check_product $product  # 检查设备型号的合法性
    if [ $? -ne 0 ]
    then
        echo
        echo "** Don't have a product spec for: '$product'"
        echo "** Do you have the right repo manifest?"
        product=
    fi

    local variant=$(echo -n $selection | sed -e "s/^[^\-]*-//")
    check_variant $variant  # 检查编译类型的合法性
    if [ $? -ne 0 ]
    then
        echo
        echo "** Invalid variant: '$variant'"
        echo "** Must be one of ${VARIANT_CHOICES[@]}"
        variant=
    fi

    if [ -z "$product" -o -z "$variant" ]
    then
        echo
        return 1
    fi

    export TARGET_PRODUCT=$product
    export TARGET_BUILD_VARIANT=$variant
    export TARGET_BUILD_TYPE=debug

    echo

    set_stuff_for_environment   # 配置环境
    printconfig                 # 显示编译环境参数
}
```
其中主要步骤已经在代码中注释出来，接下来继续分析子函数。
## check_product函数
``` bash
# build/envsetup.sh:63
function check_product()
{
    T=$(gettop)
    if [ ! "$T" ]; then     # 找不到根目录就返回吧
        echo "Couldn't locate the top of the tree.  Try setting TOP." >&2
        return
    fi
        TARGET_PRODUCT=$1 \     # 把参数赋给TARGET_PRODUCT
        TARGET_BUILD_VARIANT= \
        TARGET_BUILD_TYPE= \
        TARGET_BUILD_APPS= \
        get_build_var TARGET_DEVICE > /dev/null
    # hide successful answers, but allow the errors to show
}

function get_build_var()
{
    T=$(gettop)
    if [ ! "$T" ]; then
        echo "Couldn't locate the top of the tree.  Try setting TOP." >&2
        return
    fi
    # CALLED_FROM_SETUP=true ：接下来执行的make命令是用来初始化Android编译环境的
    # BUILD_SYSTEM=build/core ：Android编译系统的核心目录
    # 执行make命令，当前目录为Android源码根目录，mk文件为build/core/config.mk
    # 目标为dumpvar-TARGET_DEVICE
    (\cd $T; CALLED_FROM_SETUP=true BUILD_SYSTEM=build/core \
      command make --no-print-directory -f build/core/config.mk dumpvar-$1)
}
```
继续深入build/core/config.mk
### build/core/config.mk
``` bash
# :158
include $(BUILD_SYSTEM)/envsetup.mk # build/core/envsetup.mk

# :688
include $(BUILD_SYSTEM)/dumpvar.mk  # build/core/dumpvar.mk
```
