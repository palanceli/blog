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
    size_t nr = im_search(szLine, strlen(szLine)); // 🏁Step2查询
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
  return add_char_qwerty();   // 🏁 Step6
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

# Step6 MatrixSearch::add_char_qwerty()
``` c++
bool MatrixSearch::add_char_qwerty() {
  matrix_[pys_decoded_len_].mtrx_nd_num = 0;

  bool spl_matched = false;
  uint16 longest_ext = 0;
  // Extend the search matrix, from the oldest unfixed row. ext_len means
  // extending length.
  for (uint16 ext_len = kMaxPinyinSize + 1; ext_len > 0; ext_len--) {
    if (ext_len > pys_decoded_len_ - spl_start_[fixed_hzs_])
      continue;

    // Refer to the declaration of the variable dmi_has_full_id for the
    // explanation of this piece of code. In one word, it is used to prevent
    // from the unwise extending of "shoud ou" but allow the reasonable
    // extending of "heng ao", "lang a", etc.
    if (ext_len > 1 && 0 != longest_ext &&
        0 == matrix_[pys_decoded_len_ - ext_len].dmi_has_full_id) {
      if (xi_an_enabled_)
        continue;
      else
        break;
    }

    uint16 oldrow = pys_decoded_len_ - ext_len;

    // 0. If that row is before the last fixed step, ignore.
    if (spl_start_[fixed_hzs_] > oldrow)
      continue;

    // 1. Check if that old row has valid MatrixNode. If no, means that row is
    // not a boundary, either a word boundary or a spelling boundary.
    // If it is for extending composing phrase, it's OK to ignore the 0.
    if (0 == matrix_[oldrow].mtrx_nd_num && !dmi_c_phrase_)
      continue;

    // 2. Get spelling id(s) for the last ext_len chars.
    uint16 spl_idx;
    bool is_pre = false;
    spl_idx = spl_parser_->get_splid_by_str(pys_ + oldrow,
                                            ext_len, &is_pre);
    if (is_pre)
      spl_matched = true;

    if (0 == spl_idx)
      continue;

    bool splid_end_split = is_split_at(oldrow + ext_len);

    // 3. Extend the DMI nodes of that old row
    // + 1 is to extend an extra node from the root
    for (PoolPosType dmi_pos = matrix_[oldrow].dmi_pos;
         dmi_pos < matrix_[oldrow].dmi_pos + matrix_[oldrow].dmi_num + 1;
         dmi_pos++) {
      DictMatchInfo *dmi = dmi_pool_ + dmi_pos;
      if (dmi_pos == matrix_[oldrow].dmi_pos + matrix_[oldrow].dmi_num) {
        dmi = NULL;  // The last one, NULL means extending from the root.
      } else {
        // If the dmi is covered by the fixed arrange, ignore it.
        if (fixed_hzs_ > 0 &&
            pys_decoded_len_ - ext_len - dmi->splstr_len <
            spl_start_[fixed_hzs_]) {
          continue;
        }
        // If it is not in mode for composing phrase, and the source DMI node
        // is marked for composing phrase, ignore this node.
        if (dmi->c_phrase != 0 && !dmi_c_phrase_) {
          continue;
        }
      }

      // For example, if "gao" is extended, "g ao" is not allowed.
      // or "zh" has been passed, "z h" is not allowed.
      // Both word and word-connection will be prevented.
      if (longest_ext > ext_len) {
        if (NULL == dmi && 0 == matrix_[oldrow].dmi_has_full_id) {
          continue;
        }

        // "z h" is not allowed.
        if (NULL != dmi && spl_trie_->is_half_id(dmi->spl_id)) {
          continue;
        }
      }

      dep_->splids_extended = 0;
      if (NULL != dmi) {
        uint16 prev_ids_num = dmi->dict_level;
        if ((!dmi_c_phrase_ && prev_ids_num >= kMaxLemmaSize) ||
            (dmi_c_phrase_ && prev_ids_num >=  kMaxRowNum)) {
          continue;
        }

        DictMatchInfo *d = dmi;
        while (d) {
          dep_->splids[--prev_ids_num] = d->spl_id;
          if ((PoolPosType)-1 == d->dmi_fr)
            break;
          d = dmi_pool_ + d->dmi_fr;
        }
        assert(0 == prev_ids_num);
        dep_->splids_extended = dmi->dict_level;
      }
      dep_->splids[dep_->splids_extended] = spl_idx;
      dep_->ext_len = ext_len;
      dep_->splid_end_split = splid_end_split;

      dep_->id_num = 1;
      dep_->id_start = spl_idx;
      if (spl_trie_->is_half_id(spl_idx)) {
        // Get the full id list
        dep_->id_num = spl_trie_->half_to_full(spl_idx, &(dep_->id_start));
        assert(dep_->id_num > 0);
      }

      uint16 new_dmi_num;

      new_dmi_num = extend_dmi(dep_, dmi);

      if (new_dmi_num > 0) {
        if (dmi_c_phrase_) {
          dmi_pool_[dmi_pool_used_].c_phrase = 1;
        }
        matrix_[pys_decoded_len_].dmi_num += new_dmi_num;
        dmi_pool_used_ += new_dmi_num;

        if (!spl_trie_->is_half_id(spl_idx))
          matrix_[pys_decoded_len_].dmi_has_full_id = 1;
      }

      // If get candiate lemmas, try to extend the path
      if (lpi_total_ > 0) {
        uint16 fr_row;
        if (NULL == dmi) {
          fr_row = oldrow;
        } else {
          assert(oldrow >= dmi->splstr_len);
          fr_row = oldrow - dmi->splstr_len;
        }
        for (PoolPosType mtrx_nd_pos = matrix_[fr_row].mtrx_nd_pos;
             mtrx_nd_pos < matrix_[fr_row].mtrx_nd_pos +
             matrix_[fr_row].mtrx_nd_num;
             mtrx_nd_pos++) {
          MatrixNode *mtrx_nd = mtrx_nd_pool_ + mtrx_nd_pos;

          extend_mtrx_nd(mtrx_nd, lpi_items_, lpi_total_,
                         dmi_pool_used_ - new_dmi_num, pys_decoded_len_);
          if (longest_ext == 0)
            longest_ext = ext_len;
        }
      }
    }  // for dmi_pos
  }  // for ext_len
  mtrx_nd_pool_used_ += matrix_[pys_decoded_len_].mtrx_nd_num;

  if (dmi_c_phrase_)
    return true;

  return (matrix_[pys_decoded_len_].mtrx_nd_num != 0 || spl_matched);
}
```