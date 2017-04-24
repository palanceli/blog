---
layout: post
title: libGooglePinyin（二）查词
date: 2017-04-24 23:00:00 +0800
categories: 随笔笔记
tags: 输入法
toc: true
comments: true
---
查词的几个关键接口是加载`im_open_decoder`、查询`im_search`、获取结果`im_get_candidate`和关闭`im_close_decoder`，接下来继续深入研究。<!-- more -->
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
// pinyinime.cpp
size_t im_search(const char* pybuf, size_t pylen) {
  ...
  matrix_search->search(pybuf, pylen); // 🏁Step3
  return matrix_search->get_candidate_num();
}
```
# Step3 MatrixSearch::search(...)
``` c++
// matrixsearch.cpp
size_t MatrixSearch::search(const char *py, size_t py_len) {
  ...
  // Compare the new string with the previous one. Find their prefix to
  // increase search efficiency.
  size_t ch_pos = 0;
  for (ch_pos = 0; ch_pos < pys_decoded_len_; ch_pos++) {
    if ('\0' == py[ch_pos] || py[ch_pos] != pys_[ch_pos])
      break;
  }

  bool clear_fix = true;
  if (ch_pos == pys_decoded_len_)
    clear_fix = false;

  reset_search(ch_pos, clear_fix, false, false);

  // 将输入的字符追加到pys_
  memcpy(pys_ + ch_pos, py + ch_pos, py_len - ch_pos);
  pys_[py_len] = '\0';

  while ('\0' != pys_[ch_pos]) {
    if (!add_char(py[ch_pos])) { // 🏁Step4
      pys_decoded_len_ = ch_pos;
      break;
    }
    ch_pos++;
  }

  // Get spelling ids and starting positions.
  get_spl_start_id();

  // If there are too many spellings, remove the last letter until the spelling
  // number is acceptable.
  while (spl_id_num_ > 26) {
    py_len--;
    reset_search(py_len, false, false, false);
    pys_[py_len] = '\0';
    get_spl_start_id();
  }

  prepare_candidates();
  ...
  return ch_pos;
}
```
# Step4 MatrixSearch::add_char(...)
``` c++
// matrixsearch.cpp
bool MatrixSearch::add_char(char ch) {
  if (!prepare_add_char(ch)) // 🏁Step5 往pys_追加拼音，往matrix_追加一个数据块
    return false;
  return add_char_qwerty();
}
```
# Step5 MatrixSearch::prepare_add_char(...)
``` c++
bool MatrixSearch::prepare_add_char(char ch) {
  ...
  pys_[pys_decoded_len_] = ch; // 往pys_追加拼音
  pys_decoded_len_++;

  // 往matrix_追加一个数据块
  MatrixRow *mtrx_this_row = matrix_ + pys_decoded_len_;
  mtrx_this_row->mtrx_nd_pos = mtrx_nd_pool_used_;
  mtrx_this_row->mtrx_nd_num = 0;
  mtrx_this_row->dmi_pos = dmi_pool_used_;
  mtrx_this_row->dmi_num = 0;
  mtrx_this_row->dmi_has_full_id = 0;

  return true;
}
```