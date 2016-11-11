---
title: Shell 脚本
date:   2016-11-10 22:37:56 +0800
categories: 随笔笔记
tags: Android开发环境
toc: true
comments: true
---
在学习Android源码和Gradle编译时，都会遇到大量的Shell脚本和命令，本文的目的是要把在这过程中遇到的问题和知识点全部记录下来，以便未来在遇到的时候可以很方便地查看。
<!-- more -->
# ls
用法如下：
``` 
ls [-ABCFGHLOPRSTUW@abcdefghiklmnopqrstuwx1] [file ...]
选项与参数
-a 列出目录下的所有文件，包括以 . 开头的隐含文件。
-b 把文件名中不可输出的字符用反斜杠加字符编号(就象在C语言里一样)的形式列出。
-c 输出文件的 i 节点的修改时间，并以此排序。
-d 将目录象文件一样显示，而不是显示其下的文件。
-e 输出时间的全部信息，而不是输出简略信息。
-f -U 对输出的文件不排序。
-i 输出文件的 i 节点的索引信息。
-k 以 k 字节的形式表示文件的大小。
-l 列出文件的详细信息。
-m 横向输出文件名，并以“，”作分格符。
-n 用数字的 UID,GID 代替名称。
-o 显示文件的除组信息外的详细信息。
-p -F 在每个文件名后附上一个字符以说明该文件的类型，“*”表示可执行的普通
文件；“/”表示目录；“@”表示符号链接；“|”表示FIFOs；“=”表示套
接字(sockets)。
-q 用?代替不可输出的字符。
-r 对目录反向排序。
-s 在每个文件名后输出该文件的大小。
-t 以时间排序。
-u 以文件上次被访问的时间排序。
-x 按列输出，横向排序。
-A 显示除 “.”和“..”外的所有文件。
-B 不输出以 “~”结尾的备份文件。
-C 按列输出，纵向排序。
-G 输出文件的组的信息。
-L 列出链接文件名而不是链接到的文件。
-N 不限制文件长度。
-Q 把输出的文件名用双引号括起来。
-R 列出所有子目录下的文件。
-S 以文件大小排序。
-X 以文件的扩展名(最后一个 . 后的字符)排序。
-1 一行只输出一个文件。
```
# expr
评估一个表达式的值，用法如下
``` 
expr expression
expression的格式如下：
expr1 | expr2   相当于
      if (expr1 != "" && expr1 != 0)
        return expr1;
      else if (expr2 != "" && expr2 != 0)
        return expr2;
      else return 0;

 expr1 : expr2  将expr1和正则表达式expr2作比较
             The ``:'' operator matches expr1 against expr2, which must be a basic regular
             expression.  The regular expression is anchored to the beginning of the
             string with an implicit ``^''.

             If the match succeeds and the pattern contains at least one regular expres-
             sion subexpression ``\(...\)'', the string corresponding to ``\1'' is
             returned; otherwise the matching operator returns the number of characters
             matched.  If the match fails and the pattern contains a regular expression
             subexpression the null string is returned; otherwise 0.
```
# sed
sed的用法如下：
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


# test命令
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
