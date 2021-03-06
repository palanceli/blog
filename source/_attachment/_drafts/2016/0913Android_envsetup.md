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
文件开头定义了函数hmm()，它提供envsetup.sh的[Here Document](http://tldp.org/LDP/abs/html/here-docs.html)，执行如下命令即可看到输出结果：
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
此处使用sed是把envsetup.sh中的函数名解析出来。sed的用法参见[这里](#anchor-sed)。

# 一堆include
编译Android源码之前要做两个和环境设置相关的操作：
``` bash
$ source build/envsetup.sh
$ lunch aosp_arm-eng
```
前者主要执行位于envsetup.sh尾部的代码段，用来包含子目录中的sh文件。代码如下：
``` bash
# build/envsetup.sh:1500
# Execute the contents of any vendorsetup.sh files we can find.
for f in `test -d device && find -L device -maxdepth 4 -name 'vendorsetup.sh' 2> /dev/null | sort` \
         `test -d vendor && find -L vendor -maxdepth 4 -name 'vendorsetup.sh' 2> /dev/null | sort`
do
    echo "including $f"
    . $f
done
unset f
```
test命令的用法可参见[这里](#anchor-test)。上面的for循环中，分两部分，第一部分：
1. 判断文件夹device是否存在
2. 进入device目录下最多4层，查找所有vendorsetup.sh文件

第二部分和第一部分一样，只是把device换成vendor。因此这段代码就是查找目录device和vendor下所有的vendorsetup.sh文件，并执行。

即：它执行了device和vendor下最多4层子目录中所有的vendorsetup.sh。

## vendorsetup.sh
接下来看着一堆vendorsetup.sh里面都干了什么。例如，device/huawei/angler/vendorsetup.sh的内容如下：
``` bash
# device/huawei/angler/vendorsetup.sh:17
add_lunch_combo aosp_angler-userdebug
```
### add_lunch_combo

add_lunch_combo函数的定义如下：
``` bash
# build/envsetup.sh:450
function add_lunch_combo()
{
    local new_combo=$1                      # $1是要添加的菜单项
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
因此，这一对的include主要把编译选项字符串追加到数组LUNCH_MENU_CHOICES中。

需要注意，在调试envsetup.sh文件的时候，常用的手段是在里面插入echo语句，查看输出结果。要记得每次修改envsetup.sh文件之后都要重新执行`source build/envsetup.sh`，再调用内部的函数，如lunch。这是因为这些函数是在执行`source build/envsetup.sh`时把相关的代码加载到了内存，因此能够在命令行下直接调用。如果修改了这些函数，必须重新加载才能生效。

# lunch命令
来看环境设置的第二个重要操作，它会把前面记录的LUNCH_MENU_CHOICES列出来，供用户选择。确定了某个编译选项后，make即可按照该选项包含的配置启动编译。

``` bash
# build/envsetup.sh:489
function lunch()
{
    # ---------- ---------- ---------- ----------
    #  获取输入参数放入selection，如aosp_arm-eng
    # ---------- ---------- ---------- ----------
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
    # selection 应该符合<product>-<variant>的形式，
    # product为设备型号，如aosp_arm
    # variant为编译类型，如eng
    local product=$(echo -n $selection | sed -e "s/-.*$//")
    check_product $product  # 检查设备型号的合法性，后面会有介绍
    if [ $? -ne 0 ]
    then
        echo
        echo "** Don't have a product spec for: '$product'"
        echo "** Do you have the right repo manifest?"
        product=
    fi

    local variant=$(echo -n $selection | sed -e "s/^[^\-]*-//")
    check_variant $variant  # 检查编译类型的合法性，后面会有介绍
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
    if [ ! "$T" ]; then     # 找不到根目录就返回
        echo "Couldn't locate the top of the tree.  Try setting TOP." >&2
        return
    fi
        TARGET_PRODUCT=$1 \     # 把参数赋给TARGET_PRODUCT，如aosp_arm
        TARGET_BUILD_VARIANT= \
        TARGET_BUILD_TYPE= \
        TARGET_BUILD_APPS= \
        get_build_var TARGET_DEVICE > /dev/null
    # hide successful answers, but allow the errors to show
}

# build/envsetup.sh:51
function get_build_var()  # 检查由环境变量TARGET_PRODUCT指定的产品名称是否合法
{
    T=$(gettop)
    if [ ! "$T" ]; then     # 找不到根目录就返回
        echo "Couldn't locate the top of the tree.  Try setting TOP." >&2
        return
    fi
    # CALLED_FROM_SETUP=true    :接下来执行的make是用来初始化Android编译环境的
    # BUILD_SYSTEM=build/core   :Android编译系统的核心目录
    # 执行make命令:
    # make --no-print-directory -f build/core/config.mk dumpvar-TARGET_DEVICE
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

#### build/core/envsetup.mk
``` bash
# :135
include $(BUILD_SYSTEM)/product_config.mk
```

##### build/core/product_config.mk
Makefile相关知识请参见[这里](#anchor-make)。
``` bash
# build/core/product_config.mk:182
# TARGET_BUILD_APPS非空说明此次编译不是针对整个系统，只需加载核心产品相关的Makefile文件
ifneq ($(strip $(TARGET_BUILD_APPS)),)  
# An unbundled app build needs only the core product makefiles.
# 核心产品Makefile文件在$(SRC_TARGET_DIR)/product/AndroidProducts.mk
# 即build/target/product/AndroidProducts.mk中指定，
# 通过函数get-product-makefiles获得。
all_product_configs := $(call get-product-makefiles,\
    $(SRC_TARGET_DIR)/product/AndroidProducts.mk)
else    # 加载所有与产品相关的Makefile文件，使用lunch aosp_arm-eng，会走该分支
# Read in all of the product definitions specified by the AndroidProducts.mk
# files in the tree.
# 所有与产品相关的Makefile文件，通过函数get-all-product-makefiles获得。
all_product_configs := $(get-all-product-makefiles)
endif   
# 无论如何，最终获得的产品Makefie文件列表保存在变量all_product_configs中
# 在此处插入$(warning all_product_configs:$(get-all-product-makefiles))
# 会输出一堆mk文件。这里使用了函数get-product-makefiles和get-all-product-makefiles将在下面介绍。

# Find the product config makefile for the current product.
# all_product_configs consists items like:
# <product_name>:<path_to_the_product_makefile>
# or just <path_to_the_product_makefile> in case the product name is the
# same as the base filename of the product config makefile.
# 遍历变量all_product_configs所描述的产品Makefile列表，并且在这些Makefile文件中，
# 找到名称与环境变量TARGET_PRODUCT的值相同的文件，保存在另外一个变量
# current_product_makefile中，作为需要为当前指定的产品所加载的Makefile文件列表。
# 在这个过程当中，上一步找到的所有的产品Makefile文件也会保存在变量
# all_product_makefiles中。注意，环境变量TARGET_PRODUCT的值是在我们执行lunch命令的
# 时候设置并且传递进来的。
current_product_makefile :=
all_product_makefiles :=
# all_product_configs中每一项或为<product_name>:<path_to_the_product_makefile>
# 或为<path_to_the_product_makefile>，后者的product name就是makefile的文件名
$(foreach f, $(all_product_configs),\
    $(eval _cpm_words := $(subst :,$(space),$(f)))\ # 将冒号替换为空格
    $(eval _cpm_word1 := $(word 1,$(_cpm_words)))\  # 取冒号前的产品名称
    $(eval _cpm_word2 := $(word 2,$(_cpm_words)))\  # 取冒号后的makefile文件名
    $(if $(_cpm_word2),\                            # 如果有product_name
        $(eval all_product_makefiles += $(_cpm_word2))\
        $(if $(filter $(TARGET_PRODUCT),$(_cpm_word1)),\ # 产品名称包含$(TARGET_PRODUCT)
            $(eval current_product_makefile += $(_cpm_word2)),),\
        $(eval all_product_makefiles += $(f))\      # else以文件名为product_name
        $(if $(filter $(TARGET_PRODUCT),$(basename $(notdir $(f)))),\
            $(eval current_product_makefile += $(f)),)))
_cpm_words :=
_cpm_word1 :=
_cpm_word2 :=
current_product_makefile := $(strip $(current_product_makefile))
all_product_makefiles := $(strip $(all_product_makefiles))
# current_product_makefile为命中TARGET_PRODUCT的makefile列表
# all_product_makefiles为全部的makefile列表


# 指定的make目标等于product-graph或者dump-products，
# 对于lunch aosp_arm_eng来说，MAKECMDGOALS为dumpvar-TARGET_DEVICE，
# 因此进入else分支
ifneq (,$(filter product-graph dump-products, $(MAKECMDGOALS)))
# Import all product makefiles.
$(call import-products, $(all_product_makefiles)) # 加载所有产品相关的Makefile文件
else    # 走这里！
# Import just the current product.只加载与目标产品相关的Makefile文件
ifndef current_product_makefile
$(error Can not locate config makefile for product "$(TARGET_PRODUCT)")
endif
# 从前面的分析可以知道，此时的make目标为dumpvar-TARGET_DEVICE，
# 因此接下来只会加载与目标产品，即$(TARGET_PRODUCT)相关的Makefile文件，
# 这是通过调用另外函数import-products实现的。
ifneq (1,$(words $(current_product_makefile)))
$(error Product "$(TARGET_PRODUCT)" ambiguous: matches $(current_product_makefile))
endif
$(call import-products, $(current_product_makefile)) # 该函数在后面分析
endif  # Import all or just the current product makefile

# Sanity check
$(check-all-products)

ifneq ($(filter dump-products, $(MAKECMDGOALS)),)
$(dump-products)
$(error done)
endif

# 调用函数resolve-short-product-name解析环境变量TARGET_PRODUCT的值，将它变成一个Makefile文件路径。并且保存在变量INTERNAL_PRODUCT中。这里要求变量INTERNAL_PRODUCT和current_product_makefile的值相等，否则的话，就说明用户指定了一个非法的产品名称。
# Convert a short name like "sooner" into the path to the product
# file defining that product.
#
INTERNAL_PRODUCT := $(call resolve-short-product-name, $(TARGET_PRODUCT))
ifneq ($(current_product_makefile),$(INTERNAL_PRODUCT))
$(error PRODUCT_NAME inconsistent in $(current_product_makefile) and $(INTERNAL_PRODUCT))
endif
current_product_makefile :=
all_product_makefiles :=
all_product_configs :=

... ...
# 找到一个名称为PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_DEVICE的变量，并且将它的值保存另外一个变量TARGET_DEVICE中。变量PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_DEVICE是在加载产品Makefile文件的过程中定义的，用来描述当前指定的产品的名称。
# Find the device that this product maps to.
TARGET_DEVICE := $(PRODUCTS.$(INTERNAL_PRODUCT).PRODUCT_DEVICE)
```
在第16行插入`$(warning all_product_configs:$(all_product_configs))`即可查看all_product_configs的值：
``` bash
build/target/product/aosp_arm.mk 
build/target/product/aosp_arm64.mk 
... ...
device/asus/deb/aosp_deb.mk 
device/asus/flo/aosp_flo.mk 
... ...
device/generic/qemu/qemu_mips.mk 
device/generic/qemu/qemu_mips64.mk 
... ...
```

第41行则从这个文件列表中找到等于TARGET_PRODUCT的makefile文件，前面已经分析过，对于`lunch aosp_arm-eng`来说，TARGET_PRODUCT为aosp_arm。到第50行，得到所有名称等于TARGET_PRODUCT的makefile文件，可能是一个集合，放在current_product_makefile中。

###### 函数get-all-product-makefiles
``` bash
# build/core/product.mk : 59
define get-all-product-makefiles
$(call get-product-makefiles,$(_find-android-products-files))
endef

# : 30
# 返回Android源代码中的所有AndroidProducts.mk文件。他们定义在device或vendor最多6层的
# 子目录下，以及build/target/product/AndroidProducts.mk
define _find-android-products-files
$(shell test -d device && find device -maxdepth 6 -name AndroidProducts.mk) \
  $(shell test -d vendor && find vendor -maxdepth 6 -name AndroidProducts.mk) \
  $(SRC_TARGET_DIR)/product/AndroidProducts.mk
endef

# : 41
define get-product-makefiles
$(sort \
  $(foreach f,$(1), \   # 遍历参数$1所描述的AndroidProucts.mk文件列表
    $(eval PRODUCT_MAKEFILES :=) \ 
    $(eval LOCAL_DIR := $(patsubst %/,%,$(dir $(f)))) \ # 取f的目录名
    $(eval include $(f)) \
    $(PRODUCT_MAKEFILES) \
    # $(warning PRODUCT_MAKEFILES:$(PRODUCT_MAKEFILES)) \
   ) \
  $(eval PRODUCT_MAKEFILES :=) \
  $(eval LOCAL_DIR :=) \
 ) # 将定义在这些AndroidProucts.mk文件中的变量PRODUCT_MAKEFILES的值提取出来，形成一个列表返回给调用者
endef
```
函数`get-all-product-makefiles`调用了`get-product-makefiles`，并传入函数`_find-android-products-files`的返回值。

`_find-android-products-files`返回
``` bash
device/*/AndroidProducts.mk
vendor/*/AndroidProducts.mk
build/target/product/AndroidProduct.mk
```

`get-product-makefiles`函数则遍历这些AndroidProduct.mk文件，并将其中的变量PRODUCT_MAKEFILES提取出来，按字母排序。我在`foreach`循环中插入一段waning，可以看到输出的结果：
``` bash
device/asus/deb/aosp_deb.mk
device/asus/flo/aosp_flo.mk 
device/asus/flo/full_flo.mk
device/asus/fugu/aosp_fugu.mk 
device/asus/fugu/full_fugu.mk
device/generic/arm64/mini_arm64.mk
device/generic/armv7-a-neon/mini_armv7a_neon.mk
device/generic/mini-emulator-arm64/mini_emulator_arm64.mk
device/generic/mini-emulator-armv7-a-neon/m_e_arm.mk
... ...
```
###### 函数import-product
在build/core/product_config.mk中，得到了要使用的Makefile文件（current_product_makefile）后，调用import-products函数来处理该文件。
``` bash
# build/core/product.mk:157
define import-products
$(call import-nodes,PRODUCTS,$(1),$(_product_var_list))
endef
```
其中参数$(1)即current_product_makefile，对于lunch aosp_arm-eng来说就是build/target/product/aosp_arm.mk。
参数_product_var_list的定义如下，它描述产品Makefile文件中的各种变量：
``` bash
# build/core/product.mk:67
_product_var_list := \
    PRODUCT_NAME \
    PRODUCT_MODEL \
    PRODUCT_LOCALES \
    PRODUCT_AAPT_CONFIG \
    ... ...
```
####### 函数import-nodes
``` bash
# build/core/node_fns.mk:185
define _import-node
  # $(1)即"PRODUCTS"
  # $(2)即current_product_makefile，对于lunch aosp_arm-eng即
  # build/target/product/aosp_arm.mk
  # $(3)即_product_var_list
  $(eval _include_stack := $(2) $$(_include_stack))  
  $(call clear-var-list, $(3))  
  $(eval LOCAL_PATH := $(patsubst %/,%,$(dir $(2))))
  $(eval MAKEFILE_LIST :=)
  $(eval include $(2)) # $(2)里面肯定有MAKEFILE_LIST，记录一堆makefile文件
  $(eval _included := $(filter-out $(2),$(MAKEFILE_LIST))) # 过滤掉$(2)
  $(eval MAKEFILE_LIST :=)
  $(eval LOCAL_PATH :=)
  $(call copy-var-list, $(1).$(2), $(3))
  $(call clear-var-list, $(3))

  # 把PRODUCTS.$(current_product_makefile).inherited.$(3)中以$(INHERIT_TAG)打头的内容择出来，并把$(INHERIT_TAG)过滤掉
  $(eval $(1).$(2).inherited := \
      $(call get-inherited-nodes,$(1).$(2),$(3)))
  # 加载$($(1).$(2).inherited)文件列表，如果出错，该函数会生成更详细的msg以辅助调查
  $(call _import-nodes-inner,$(1),$($(1).$(2).inherited),$(3))

  $(call _expand-inherited-values,$(1),$(2),$(3))

  $(eval $(1).$(2).inherited :=)
  $(eval _include_stack := $(wordlist 2,9999,$$(_include_stack)))
endef
```
`clear-var-list`定义于build/core/node_fns.mk:17，注释说得很明白，清空参数列表中的每一项
``` makefile
#
# Clears a list of variables using ":=".
#
# E.g.,
#   $(call clear-var-list,A B C)
# would be the same as:
#   A :=
#   B :=
#   C :=
#
# $(1): list of variable names to clear
#
define clear-var-list
$(foreach v,$(1),$(eval $(v):=))
endef
```

`copy-var-list`定义于build/core/node_fns.mk:34，把一个列表拷贝到另一个列表，目标列表和源列表是一致的，只是多了一个用“.”隔开的前缀：
``` makefile
#
# Copies a list of variables into another list of variables.
# The target list is the same as the source list, but has
# a dotted prefix affixed to it.
#
# E.g.,
#   $(call copy-var-list, PREFIX, A B)
# would be the same as:
#   PREFIX.A := $(A)
#   PREFIX.B := $(B)
#
# $(1): destination prefix
# $(2): list of variable names to copy
#
define copy-var-list
$(foreach v,$(2),$(eval $(strip $(1)).$(v):=$($(v))))
endef
```

`get-inherited-nodes`定义于/build/core/node_fns.mk:109，遍历所有全局变量，把PREFIX.A，PREFIX.B中以INHERIT_TAG打头的内容择出来，并把INHERIT_TAG过滤掉，之后sort uniq。
``` makefile
INHERIT_TAG := @inherit:

#
# Walks through the list of variables, each qualified by the prefix,
# and finds instances of words beginning with INHERIT_TAG.  Scrape
# off INHERIT_TAG from each matching word, and return the sorted,
# unique set of those words.
#
# E.g., given
#   PREFIX.A := A $(INHERIT_TAG)aaa B C
#   PREFIX.B := B $(INHERIT_TAG)aaa C $(INHERIT_TAG)bbb D E
# Then
#   $(call get-inherited-nodes,PREFIX,A B)
# returns
#   aaa bbb
#
# $(1): variable prefix
# $(2): list of variables to check
#
define get-inherited-nodes
$(sort \
  $(subst $(INHERIT_TAG),, \
    $(filter $(INHERIT_TAG)%, \
      $(foreach v,$(2),$($(1).$(v))) \
 )))
endef
```

`_import-nodes-inner`定义于build/core/node_fns.mk:221，它用来家在指定的文件，只是额外做了“如果出错，会给出更多错误信息，以便调试”的工作。
``` makefile
#
# This will generate a warning for _included above
#  $(if $(_included), \
#      $(eval $(warning product spec file: $(2)))\
#      $(foreach _inc,$(_included),$(eval $(warning $(space)$(space)$(space)includes: $(_inc)))),)
#

#
# $(1): context prefix
# $(2): list of makefiles representing nodes to import
# $(3): list of node variable names
#
#TODO: Make the "does not exist" message more helpful;
#      should print out the name of the file trying to include it.
define _import-nodes-inner
  $(foreach _in,$(2), \
    $(if $(wildcard $(_in)), \
      $(if $($(1).$(_in).seen), \
        $(eval ### "skipping already-imported $(_in)") \
       , \
        $(eval $(1).$(_in).seen := true) \
        $(call _import-node,$(1),$(strip $(_in)),$(3)) \
       ) \
     , \
      $(error $(1): "$(_in)" does not exist) \
     ) \
   )
endef

#
# $(1): output list variable name, like "PRODUCTS" or "DEVICES"
# $(2): list of makefiles representing nodes to import
# $(3): list of node variable names
#
define import-nodes
$(if \
  $(foreach _in,$(2), \
    $(eval _node_import_context := _nic.$(1).[[$(_in)]]) \
    $(if $(_include_stack),$(eval $(error ASSERTION FAILED: _include_stack \
                should be empty here: $(_include_stack))),) \
    $(eval _include_stack := ) \
    $(call _import-nodes-inner,$(_node_import_context),$(_in),$(3)) \
    $(call move-var-list,$(_node_import_context).$(_in),$(1).$(_in),$(3)) \
    $(eval _node_import_context :=) \
    $(eval $(1) := $($(1)) $(_in)) \
    $(if $(_include_stack),$(eval $(error ASSERTION FAILED: _include_stack \
                should be empty here: $(_include_stack))),) \
   ) \
,)
endef
```
# 参考知识
## sed
<a name="anchor-sed"></a>sed的用法如下：
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


## test命令
<a name="anchor-test"></a>test命令的语法是：
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

## Makefile中的常用函数
<a name="anchor-make"></a>
调试Makefile文件，可以通过插入warning的方式，用来输出变量：
``` makefile
$(warning TARGET_BUILD_APPS:$(TARGET_BUILD_APPS))
```
但是很奇怪，只有输出"xxx:xxx"的形式才正常，如果只输出
``` makefile
$(warning helloworld!)
```
是会报错的，我还没弄明白怎么回事。
### dir
<a name="anchor-dir"></a>它的语法是：
`$(dir names)`
从文件名序列（一个或多个文件名）names中取出目录部分。目录部分是指最后一个斜杠”/”之前的部分，如果没有斜杠，则返回”./”。如：
``` bash
$(dir user/src/linux-2.4/Makefile hello.c)
```
返回`usr/src/linux-2.4` `./`

### eval
<a name="anchor-eval"></a>它的语法是：
`$(eval text)`
将text的内容将作为makefile的一部分被解析和执行。比如
`$(eval xd:xd.c a.c)`
将会产生一个这样的编译
`cc   xd.c a.c -o xd`

这样一个makefile:
``` bash
define MA
aa:aa.c
 gcc  -g -o aa aa.c
endef 

$(eval $(call MA) )
```
会产生一个这样的编译：
`gcc -g -o aa aa.c`

这样的makefile：
``` bash
OBJ=a.o b.o c.o d.o main.o

define MA
main:$(OBJ)
 gcc  -g -o main $$(OBJ)
endef 

$(eval $(call MA) )
```

会产生这样的编译过程：
``` bash
cc -c -o a.o a.c
cc -c -o b.o b.c
cc -c -o c.o c.c
g++ -c -o d.o d.cpp
cc -c -o main.o main.c
gcc -g -o main a.o b.o c.o d.o main.o
```
请注意$$(OBJ)，因为make要把这个作为makefile的一行，要让这个地方出现$，就要用两个$,因为两个$，make才把把作为$字符。

eval会做两次变量展开。`$(eval var)`首先会对var做一次变量展开，然后对展开后的结果，再执行一次变量展开。

再如，
``` bash
define import_target
    include $(1)
    _PREFIXID := $(if$2, $2, TARGET)
    $(_ PREFIXID)
endef
```
按上面定义的宏，当去计算a:=$(call  import_target)时，总是会报错。因为宏定义只是简单的做字符串替换,一经替换，原来看起来是一行语句，一下子就变成多行，从而导致makefile解析错误。于是只能使用“\”将各个语句连接为一行。
``` bash
define import_target
    include $(1) \
    _PREFIXID := $(if $2, $2,TARGET) \
    $(_ PREFIXID)
endef
```
这相当于
`include $(1) _PREFIXID := $(if $2, $2, TARGET)  $(_ PREFIXID)`
显然，肯定还是报解析错误。
最终解决方案，将各个子语句使用$(eval )包裹：
``` bash
define import_target
    $(eval include $(1)) \
    $(eval _PREFIXID := $(if $2,$2, TARGET)) \
    $(_ PREFIXID)
endef 
```
解析时，makefile先对$(1)做展开，假设结果为xxx，这是第一次；然后执行include xxx，这是第二次展开。这样解析错误解决了，而且 import_target的返回结果又正好是_ PREFIXID的值。

### filter
<a name="anchor-filter"></a>它的语法是：
`$(filter pattern..., text)`
以pattern模式过滤text字符串中的单词（可以有多个模式串），返回符合模式pattern的字串。如：
``` bash
sources := foo.c bar.c baz.s ugh.h 
foo: $(sources) 
cc $(filter %.c %.s,$(sources)) -o foo
```
`$(filter %.c %.s,$(sources))`返回的值是`foo.c bar.c baz.s`。

### filter-out
<a name="anchor-filter"></a>它的语法是：
`$(filter-out PATTERN..., TEXT)`
和"filter"函数实现的功能相反，过滤掉字串TEXT中所有符合模式串PATTERN的单词，保留所有不符合此模式串的单词。如：
``` bash
objects=main1.o foo.o main2.o bar.o
mains=main1.o main2.o
$(filter-out $(mains), $(objects))
```
它的返回值为"foo.o bar.o"。

### foreach
<a name="anchor-foreach"></a>它的语法是：
`$(foreach  var, list, text)`
从list中逐一取出每一项放到var中，然后再执行text所包含的表达式。每一次会返回一个字符串，循环过程中所返回的字符串会以空格分隔，最后返回这个以空格分割的整串。如：
``` bash
names := a b c d
files := $(foreach n, $(names), $(n).o)
```
$(name)中的单词被逐个取出，并存到变量“n”中，每次得到“$(n).o”，这些值以空格分隔，最后$(files)的值是“a.o b.o c.o d.o”。
注意，foreach中的参数是一个临时的局部变量，其作用域只在foreach函数当中。

### notdir
<a name="anchor-notdir"></a>它的语法是：
`$(notdir NAMES…)`
从序列“NAMES…”中取出非目录部分。目录部分是指最后一个斜线（“/”）（包括斜线）之前的部分。删除所有文件名中的目录部分，只保留非目录部分。如，
`$(notdir src/foo.c hacks)`
返回值为：
`foo.c hacks`。

### if
<a name="anchor-if"></a>它的语法是：
`$(if CONDITION,THEN-PART[,ELSE-PART])`
第一个参数"CONDITION"，在函数执行时忽略其前导和结尾空字符，如果包含对其他变量或者函数的引用则进行展开。如果"CONDITION"的展开结果非空，就将第二个参数"THEN_PATR"作为函数的计算表达式；"CONDITION"的展开结果为空，将第三个参数"ELSE-PART"作为函数的表达式，函数的返回结果为有效表达式的计算结果。如：
`SUBDIR += $(if $(SRC_DIR) $(SRC_DIR),/home/src)`
函数的结果是：如果“SRC_DIR”变量值不为空，则将变量“SRC_DIR”指定的目录作为子目录；否则将目录“/home/src”作为子目录。

### ifneq
<a name="anchor-ifneq"></a>它的语法是：
`ifneq(<arg1>,<arg2>)`
比较参数arg1和arg2的值是否相等，不相等时表达式值为真。

### include
<a name="anchor-include"></a>它的语法是：
`include FILENAMES...`
“include”指示符告诉 make 暂停读取当前的 Makefile,而转去读取“include”指定的一个或者多个文件,完成以后再继续当前 Makefile 的读取。

### patsubst
<a name="anchor-subst"></a>它的语法是：
`$(patsubst <pattern>, <replacement>, <text>)`
查找text中的单词是否符合模式pattern，如果匹配的话，则以replacement模式替换。
pattern可以包含通配符”%”，用来表示任意长度的字串。
如果replacement中也包含“%”，那么replacement中的这个“%”将是pattern中的“%”所代表的字串。
（可以用“\”来转义，以“\%”来表示真实含义的“%”字符）
返回：函数返回被替换过后的字符串。如：
`$(patsubst %.c, %.o, x.c.c bar.c) `
结果是：
`x.c.o bar.o`

### subst
<a name="anchor-subst"></a>它的语法是：
`$(subst from, to, text)`
把字串text中的from字符串替换成to。如：
``` bash
$(subst ee,EE,feet on the street)
```
把"feetonthestreet"中的"ee"替换成"EE"，返回结果是"fEEtonthestrEEt"。

### sort
<a name="anchor-sort"></a>它的语法是：
`$(sort list)`
将字符串list中的单词按照字母排序（升序）进行排序。遇到相同的单词时，sort函数会自动删除他们。返回排序后的字符串。如：
``` bash
$(sort program linux c program anxier)
```
返回值是anxier c linux program

### word
<a name="anchor-word"></a>它的语法是：
`$(word n, text)`
取字符串text中第n个单词，序号从1开始。如：
``` bash
$(word2,foobarbaz)
```
返回值是"bar"。

### words
<a name="anchor-words"></a>它的语法是：
`$(words text)`
统计text中的单词数。如：
``` bash
$(words, foo bar baz)
```
返回值为3.
