---
layout: post
title: 《Android Programming BNRG》笔记十
date: 2016-10-21 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章完成了点击list元素弹出details的业务逻辑。和Activity启动另一个Activity非常相似，稍有不同的是Fragment的Arguments机制。

本章要点：
- 在Fragment中启动Activity
- 在Fragment之间传递数据

<!-- more -->
# 在Fragment中启动另一个Activity
和Activity启动另一个Activity一样，Fragment启动另一个Activity也是调用startActivity(Intent intent)，传参的方式也是类似的：
``` java
// CrimeActivity 按照依赖倒置原则，被启动方负责创建Intent
public class CrimeActivity extends SingleFragmentActivity {
    public static final String EXTRA_CRIME_ID = "com.bnrg.bnrg07.crime_id";
    public static Intent newIntent(Context packageContext, UUID crimeId){
        Intent intent = new Intent(packageContext, CrimeActivity.class);
        intent.putExtra(EXTRA_CRIME_ID, crimeId);
        return intent;
    }
    ...
}
```

``` java
// CrimeListFragment.java
public class CrimeListFragment extends Fragment {
    ...
    private class CrimeHolder extends RecyclerView.ViewHolder
    implements View.OnClickListener{
        ...
        @Override
        public void onClick(View view){
            // 启动Activity并传入crimeId
            Intent intent = CrimeActivity.newIntent(getActivity(), mCrime.getId());
            startActivity(intent);
        }
     ...
    }
    ...
}
```

``` java
// CrimeFragment.java
public class CrimeFragment extends Fragment {
    ...
    @Override
    public void onCreate(Bundle savedInstance){
        super.onCreate(savedInstance);
        // 接收、解析crimeId，并由此创建crime
        UUID crimeId = (UUID)getActivity().getIntent().getSerializableExtra(CrimeActivity.EXTRA_CRIME_ID);
        mCrime = CrimeLab.get(getActivity()).getCrime(crimeId);
    }
    ...
}
```

# 解除Fragment 对Activity的依赖
在上面的例子中，Fragment启动后会向发起方Activity请求Extra参数，这会导致Fragment依赖于Activity，使得Fragment无法装配给任意的的Activity。解耦的方案是在创建Fragment的时候为它设定Argument，把传入的参数塞入Argument中。Argument其实是Bundle实例，它的使用方法如下：
``` java
Bundle args = new Bundle()          // 创建Bundle实例
args.putSerializable(key, value);   // 塞入key-value数据对
...
fragment.setArguments(args);        // 设置给Fragment
```

本节的操作步骤是：①在CrimeFragment中创建`newInstance(UUID crimeId)`函数，用来创建自身并传入Argument参数；②在CrimeActivity中的`createFragment()`函数中调用`CrimeFragment::newInstance(...)`生成Fragment；③在`CrimeFragment::onCreate(...)`函数中解析Argument参数

启动Fragment的一方总是需要传入crimeId，如果启动方是Activity，他还是需要知道传入什么参数，这是启动方必须知道的细节。但和前一种启动方案相比，这种方案的好处是Fragment不必再反过来依赖Activity了。

具体代码如下：
``` java
// CrimeFragment.java
public class CrimeFragment extends Fragment {
    private static final String ARG_CRIME_ID = "crime_id";
    ...
    //
    @Override
    public void onCreate(Bundle savedInstance){
        super.onCreate(savedInstance);
        // ③ 从自身的Argument中要参数，而不再问Activity
        UUID crimeId = (UUID)getArguments().getSerializable(ARG_CRIME_ID);
        mCrime = CrimeLab.get(getActivity()).getCrime(crimeId);
    }
    ...
    public static CrimeFragment newInstance(UUID crimeId){  // ①
	// 根据crimeId创建Argument，并置入Fragment
    Bundle args = new Bundle();	
    args.putSerializable(ARG_CRIME_ID, crimeId);
    CrimeFragment fragment = new CrimeFragment();
    fragment.setArguments(args);
    return fragment;
    }
}
```

``` java
// CrimeActivity.java
public class CrimeActivity extends SingleFragmentActivity {
    ...
    @Override
    protected Fragment createFragment(){    // ②
        UUID crimeId = (UUID)getIntent().getSerializableExtra(EXTRA_CRIME_ID);
        return CrimeFragment.newInstance(crimeId); // 调用新的方案创建Fragment
    }
}
```

# 退出details后更新list
在[笔记五·从启动的Activity返回数据](/2016/10/16/2017/1016AndroidProgrammingBNRG05/#从启动的Activity返回数据)中，讲到了Activity启动Activity时，通过`startActivityForResult(...)`启动Activity，被启动方调用`setResult(...)`设置返回数据，启动方收到回调`onActivityResult(...)`接收返回数据。

在传递数据的机制上，Fragment和Activity只有一点点不同，Fragment有`Fragment::startActivityForResult(...)`和`Fragment::onActivityResult(...)`，但是没有`setResult(...)`函数，它需要调用它所在的Activity的该函数来设置返回值：
``` java
public class CrimeFragment extends Fragment{
    ...
    public void returnResult(){
        getActivity().setResult(Activty.RESULT_OK, null);
    }
}
```

而在本节，其实并没有需要返回的数据，因为启动Activity时传入的只是crimeId，被启动的Fragment是在其onCreateView(...)函数内获得了crimeId对应的Crime对象，在Fragment上都是直接修改CrimeLab单体中的元素，也就是直接更新了Model层。因此当在Fragment按下Back而返回时，只需要通知启动方，令其更新即可。

书中是在`CrimeListFragment::onResume()`回调中刷新了界面。当点击list中的某个元素，弹出CrimeActivity，CrimeListActivity被压栈进入Paused状态；在CrimeActivity点击Back后，该Activity被销毁，CrimeListActivity又成为栈顶组件而进入Resumed状态，因此会回调它的onResume()函数，它在调用其内部Fragment的`onResume()`函数。

具体代码如下：
``` java
// CrimeListFragment.java
public class CrimeListFragment extends Fragment {
    ...
    @Override
    public void onResume(){
        super.onResume();
        updateUI();	// 更新界面
    }
    private void updateUI(){
        CrimeLab crimeLab = CrimeLab.get(getActivity());
        List<Crime> crimes = crimeLab.getCrimes();
        if(mAdapter == null) {
            mAdapter = new CrimeAdapter(crimes);
            mCrimeRecyclerView.setAdapter(mAdapter);
        }else{
            mAdapter.notifyDataSetChanged();
        }
    }
}
```
在updateUI()函数中，首次更新需要创建mAdapter实例，之后再更新，只需要调用它的`notifyDataSetChanged()`函数，它会通知每一个“集装箱”更新数据。

一个activity从无到有再到展现，经历了Nonexistent > Stopped > Paused > Resumed四个状态，如果Activity是被其它的Activity覆盖，它会进入到Paused状态，而未必进入Stopped状态，所以在`onResume()`中更新界面是个比较安全的时机。

# 为什么使用Arguments而不是传参？
在[笔记七·向创建的Fragment传入参数](http://localhost:4000/2016/10/18/2017/1018AndroidProgrammingBNRG07/#向创建的Fragment传入参数)中已经提到过了。我们在创建Fragment实例时，并没有在构造函数中传入crimeId参数，而是在实例构造完成后通过调用`setArguments(...)`传入crimeId的主要原因是：当系统配置发生变化或者由于低内存而引发内存回收时，会导致fragment重建。使用构造函数传参，把参数保存在成员变量中的做法会导致在重建时，该数据丢失，除非你始终记得在fragment的`onSaveInstanceState(...)`函数中回写，在`onCreate(...)`函数中读入，这样很麻烦；而使用Arguments的方式，会在重建时，自动保存/读入参数数据。

