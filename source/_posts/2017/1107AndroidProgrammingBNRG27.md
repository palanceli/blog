---
layout: post
title: 《Android Programming BNRG》笔记二十七
date: 2017-11-07 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章在toolbar中放入了搜索框，输入关键词将向Flickr请求搜索结果图片：
![](1107AndroidProgrammingBNRG27/img01.png)
本章要点：
- Shared Preferences
- 使用SearchView
<!-- more -->

# Shared Preferences
Shared Preferences是指保存在文件系统，通过`SharedPreferences`类可以访问的数据。`SharedPreferences`提供了key-value的访问形式，和Bundle类似，不同点在于Bundle不保存在磁盘。Shared Preference的底层是通过XML文件来实现的，文件保存在应用的沙盒目录。

可以使用`Context.getSharedPreference(int)`来获得SharedPreferences实例，一般使用者并不关注使用具体哪一个实例，因此更常用的做法是通过`PreferenceManager.getDefaultSharedPreferences(Context)`来获得。具体使用如下：
``` java
private static final String PREF_SEARCH_QUERY = "searchQuery";

// 读取PREF_SEARCH_QUERY的值
String query = PreferenceManager.getDefaultSharedPreferences(context)
                .getString(PREF_SEARCH_QUERY, null);
...
// 设置PREF_SEARCH_QUERY的值
PreferenceManager.getDefaultSharedPreferences(context)
                .edit()
                .putString(PREF_SEARCH_QUERY,query)
                .apply();
    }
```
其中`SharedPreferences.edit()`返回`SharedPreferences.Editor`对象，在对象上可以进行多次`putString(...)`之类的操作，最后执行`apply()`可以确保写入的原子性。`apply()`通过后台线程完成文件写入。在[《笔记26·StrictMode》](/2017/11/06/2017/1106AndroidProgrammingBNRG26/#StrictMode)中曾提到过：不要在主线程中读写磁盘。

# 使用SearchView
SearchView是一个action view——可以包含在toolbar中的view。它展现出一个搜索栏的形态，并允许你输入关键词进行搜索。

## 1. 添加XML资源
右键res > New > Android resource file，资源类型选择Menu，添加菜单资源，`fragment_photo_gallery.xml`内容如下：
``` xml
<menu xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto">
    <item android:id="@+id/menu_item_search"
        android:title="@string/search"
        app:actionViewClass="android.support.v7.widget.SearchView"
        app:showAsAction="ifRoom"/>
    <item android:id="@+id/menu_item_clear"
        android:title="@string/clear_search"
        app:showAsAction="never"/>
</menu>
```
菜单中的第一个元素就是SearchView。

## 2.在Java代码中创建菜单
``` java
// PhotoGalleryFragment.java
public class PhotoGalleryFragment extends Fragment {
    ...
    
    @Override
    public void onCreate(Bundle savedInstanceState){
        ...
        setHasOptionsMenu(true); // ①
        ...
    }

    @Override
    public void onCreateOptionsMenu(Menu menu, MenuInflater menuInflater){
        // ②
        super.onCreateOptionsMenu(menu, menuInflater);
        menuInflater.inflate(R.menu.fragment_photo_gallery, menu);
        // ③
        MenuItem searchItem = menu.findItem(R.id.menu_item_search);
        final SearchView searchView = (SearchView)searchItem.getActionView();
        // ④
        searchView.setOnQueryTextListener(
                new SearchView.OnQueryTextListener(){
                    @Override
                    public boolean onQueryTextSubmit(String s){
                        Log.d(TAG, "QueryTextSubmit: " + s);
                        QueryPreferences.setStoredQuery(getActivity(), s);
                        updateItems();
                        return true;
                    }

                    @Override
                    public boolean onQueryTextChange(String s){
                        Log.d(TAG, "QueryTextChange: " + s);
                        return false;
                    }
                });
        // ⑤
        searchView.setOnSearchClickListener(new
        View.OnClickListener(){
            @Override
            public void onClick(View v){
                String query = QueryPreferences.getStoredQuery(getActivity());
                searchView.setQuery(query, false);
            }
        });
    }

    @Override // ⑥
    public boolean onOptionsItemSelected(MenuItem item){
        switch(item.getItemId()){
            case R.id.menu_item_clear:
                QueryPreferences.setStoredQuery(getActivity(), null);
                updateItems();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }
    ...
}
```
①和②在[《笔记13·怎么创建菜单》](http://localhost:4000/2017/10/24/2017/1024AndroidProgrammingBNRG13/#怎么创建菜单)已经讲过。
③ 拿到SearchView对象。
④ 通过设置Listener响应搜索事件，其中`onQueryTextSubmit(...)`响应搜索提交，`onQueryTextChange(...)`响应文字变化。
⑤ 当点击搜索框，将上次的搜索词展现在搜索框内。
⑥ 响应点击`×`按钮，清除关键词。