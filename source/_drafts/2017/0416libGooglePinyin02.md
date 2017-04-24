---
layout: post
title: libGooglePinyin（二）查词
date: 2017-04-24 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
查词的几个关键接口是加载`im_open_decoder`、查询`im_search`、获取结果`im_get_candidate`和关闭`im_close_decoder`，接下来继续深入研究。
# Step1 main函数
``` c++
int main(int argc, char* argv[])
{
  setlocale(LC_ALL, "");
  char* szSysDict = "../build/data/dict_pinyin.dat";
  char* szUserDict = "";
  if (argc >= 3) {
    szSysDict = argv[1];
    szUserDict = argv[2];
  }

  bool ret = im_open_decoder(szSysDict, szUserDict);  // 加载
  assert(ret);
  im_set_max_lens(32, 16);
  char szLine[256];
```
此处将前文生成词库时使用4个`save`保存的数据结构依次使用4个`load`加载到内存：![系统词库](http://palanceli.com/2017/04/16/2017/0416libGooglePinyin01/img21.png)
``` c++
  ...
    wprintf(L"\n.拼音 >");
    gets_s(szLine, 256);
    if (strlen(szLine) == 0)
      break;
    
    im_reset_search();
    size_t nr = im_search(szLine, 8); // 🏁Step2查询
    size_t size = 0;
    printf("%s\n", im_get_sps_str(&size));  // 获取查询结果个数
    char16 str[64] = { 0 };
    for (auto i = 0; i < nr; i++)
    {
      im_get_candidate(i, str, 32);         // 获取查询候选
      const wchar_t* szCand = (const wchar_t*)str;
      wprintf(L"%s\n", szCand);
      int j = 0;
      j++;
    }
  ...
  im_close_decoder();                 // 关闭

  return 0;
}
```
# Step2 im_search(...)
``` c++
```