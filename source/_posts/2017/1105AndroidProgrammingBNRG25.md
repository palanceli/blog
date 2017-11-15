---
layout: post
title: 《Android Programming BNRG》笔记二十五
date: 2017-11-05 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章搭起了一个简单框架，通过http请求flickr图片数据，并展现出来。

本章要点：
- 联网操作
- json数据解析
- 主线程和后台线程
<!-- more -->

# 联网操作
## 权限申请
联网操作被Android视为一般性权限，大部分app都需要改权限。只需要在AndroidManifest.xml中声明该权限即可，在安装app的时候会询问用户是否允许，更加隐私的权限常常需要在运行时申请的。`AndroidManifest.xml`的声明如下：
``` xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET"/>

    <application ...>
        ...
    </application>

</manifest>
```

## 请求数据
很程式化的步骤，直接在代码里注释了：
``` java
// FlickrFetchr.java
public byte[] getUrlBytes(String urlSpec) throws IOException{
    URL url = new URL(urlSpec);
    // ① 创建连接对象
    HttpURLConnection connection = (HttpURLConnection)url.openConnection();
    try{
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        // ② 发起连接，对于POST可以调用getOutputStream()
        InputStream in = connection.getInputStream();   
        // ③ 获得响应码
        if(connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
            throw new IOException(connection.getResponseMessage() + ": with " + urlSpec);
        }
        int bytesRead = 0;
        byte[] buffer = new byte[1024];
        while((bytesRead = in.read(buffer)) > 0){ // ④ 读取数据
            out.write(buffer, 0, bytesRead);
        }
        out.close();
        return out.toByteArray();
    }finally {
        connection.disconnect();    // ⑤ 关闭连接
    }
}
```

## 组织URL
需要吧域名、参数组织在一起：
``` java
// FlickrFetchr.java
public void fetchItems(){
    try{
        String url = Uri.parse("https://api.flickr.com/services/rest/")
                .buildUpon()
                .appendQueryParameter("method", "flickr.photos.getRecent")
                .appendQueryParameter("api_key", API_KEY)
                .appendQueryParameter("format", "json")
                .appendQueryParameter("nojsoncallback", "1")
                .appendQueryParameter("extras", "url_s")
                .build().toString();
        String jsonString = getUrlString(url);
        ...
    }...
}
```
它组织起来的url为：
`https://api.flickr.com/services/rest/?method=flickr.photos.getRecent&api_key=<API_KEY>&format=json&nojsoncallback=1`

# 解析Json数据
返回的json数据形如：
``` json
{"photos":{
    "page":1,
    "pages":10,
    "perpage":100,
    "total":1000,
    "photo":[
        {
            "id":"24560174998", "owner":"140909859@N05",
            "secret":"bb960eabc6", "server":"4530",
            "farm":5, "title":"imsi20171115033551",
            "ispublic":1, "isfriend":0, "isfamily":0
        },...,
        {
            "id":"38431317441", "owner":"153803854@N08",
            "secret":"7851f9d792", "server":"4581",
            "farm":5,"title":"\u6797\u90c1\u8ed2_3",
            "ispublic":1, "isfriend":0, "isfamily":0
        }
    ]
    },
"stat":"ok"
}
```
解析这段数据的代码如下：
``` java
// FlickrFetchr.java
private void parseItems(List<GalleryItem> items, JSONObject jsonBody)
                        throws IOException, JSONException{
    // 解析根部字典
    JSONObject photosJsonObject = jsonBody.getJSONObject("photos");
    // 解析photo数组
    JSONArray photoJsonArray = photosJsonObject.getJSONArray("photo");
    for(int i=0; i<photoJsonArray.length(); i++){ // 解析数组中每一项
        JSONObject photoJsonObject = photoJsonArray.getJSONObject(i);
        GalleryItem item = new GalleryItem();
        item.setId(photoJsonObject.getString("id"));
        item.setCaption(photoJsonObject.getString("title"));
        if(!photoJsonObject.has("url_s")){
            continue;
        }
        item.setUrl(photoJsonObject.getString("url_s"));
        items.add(item);
    }
}
```

# 主线程和工作线程
Android不允许在主线程中做长程操作，例如在主线程长时间的网络阻塞会导致`NetworkOnMainThreadException`异常。主线程负责运行所有与UI响应、更新相关的代码，包括响应不同的UI事件——启动Activity、按钮按下等等。主线程也常常被称为UI线程。

当Android的watchdog发现应用程序的主线程失去响应，将会触发ANR。所以需要创建一个后台工作现成来完成诸如网络操作这类的长程操作。

通过如下代码实现后台线程：
``` java
// PhotoGalleryFragment.java
// ① 定义后台线程类
private class FetchItemsTask extends AsyncTask<Void, Void, Void>{
    @Override
    protected Void doInBackground(Void ... params){ // ② 实现工作接口
        try{
            String result = new FlickrFetchr()
                    .getUrlString("https://www.bignerdranch.com");
            ...
        }...
        return null;
    }
}

@Override
public void onCreate(Bundle savedInstanceState){
    ...
    new FetchItemsTask().execute(); // ③ 执行
}
```

## 从后台工作线程回归到前台
在本节，Fragment被加载后，首先启动工作线程，需要等待该线程完成数据下载后再更新界面，怎么完成由后台到前台的通知呢？在`AsyncTask::doInBackground(...)`完成后，`AsyncTask::onPostExecute(...)`将被执行，而且是在主线程里执行，这正符合我们的诉求。接下来贴出PhotoGalleryFragment.java的完整代码，涉及到RecyclerView的配合，我们使用①②③来标出逻辑顺序：
``` java
// PhotoGalleryFragment.java
public class PhotoGalleryFragment extends Fragment {
    private static final String TAG = "PhotoGalleryFragment";
    private RecyclerView mPhotoRecyclerView;
    private List<GalleryItem> mItems = new ArrayList<>();

    private class FetchItemsTask extends AsyncTask<Void, Void, List<GalleryItem>>{
        @Override
        protected List<GalleryItem> doInBackground(Void ... params){
            return new FlickrFetchr().fetchItems(); // ② 下载数据
        }

        @Override
        protected void onPostExecute(List<GalleryItem> items){
            mItems = items;
            setupAdapter(); // ③ 返回数据，并在主线程中更新界面
        }
    }

    public static PhotoGalleryFragment newInstance(){
        return new PhotoGalleryFragment();
    }

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setRetainInstance(true);
        new FetchItemsTask().execute();// ①启动后台线程
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View v = inflater.inflate(R.layout.fragment_photo_gallery,
                container, false);
        mPhotoRecyclerView = (RecyclerView)v.findViewById(R.id.photo_recycler_view);
        mPhotoRecyclerView.setLayoutManager(new GridLayoutManager(getActivity(), 3));
        setupAdapter();
        return v;
    }

    private void setupAdapter(){
        if(isAdded()){  // ④ 设置adapter
            mPhotoRecyclerView.setAdapter(new PhotoAdapter(mItems));
        }
    }

    private class PhotoHolder extends RecyclerView.ViewHolder{
        private TextView mTitleTextView;

        public PhotoHolder(View itemView){
            super(itemView);
            mTitleTextView = (TextView)itemView;
        }

        public void bindGalleryItem(GalleryItem itme){
            mTitleTextView.setText(itemView.toString());
        }
    }

    private class PhotoAdapter extends RecyclerView.Adapter<PhotoHolder>{
        private List<GalleryItem> mGalleryItems;

        public PhotoAdapter(List<GalleryItem> galleryItems){
            mGalleryItems = galleryItems;
        }

        @Override
        public PhotoHolder onCreateViewHolder(ViewGroup viewGroup, int viewType){
            TextView textView = new TextView(getActivity());
            return new PhotoHolder(textView);
        }

        @Override
        public void onBindViewHolder(PhotoHolder photoHolder, int position){
            GalleryItem galleryItem = mGalleryItems.get(position);
            photoHolder.bindGalleryItem(galleryItem);
        }

        @Override
        public int getItemCount(){
            return mGalleryItems.size();
        }
    }
}
```
有几处需要说明：
- FetchItemsTask类的第1个模板参数表示传入`execute()`的参数，该参数将被传入`doInBackground(...)`。使用方法为：
``` java
AsyncTask<String, Void, Void> task = new AsyncTask<String, Void, Void>(){
    public Void doInBackground(String ... params){
        for(String parameter : params){
            Log.i(TAG, "Received parameter:" + parameter);
        }
    }
}
...
task.execute("First parameter", "Second parameter", "Etc.");
```
- FetchItemsTask类的第2个模板参数用来表示进度的类型。如下面的代码，在工作线程中调用`publishProgress(...)`设置进度，UI线程将调用`onProgressUpdate(...)`显示进度：
``` java
final ProgressBar gestationProgressBar = gestationProgressBar.setMax(42);
AsyncTask<Void, Integer, Void> task = new AsyncTask<Void, Integer, Void>(){
    public Void doInBackground(Void ... params){
        for(int i=0; i<10; i++){
            Integer progress = new Integer(i);
            publishProgress(progress);
            sleep(1000);
        }
    }
    public void onProgressUpdate(Integer ... params){
        int progress = params[0];
        gestationProgressBar.setProgress(progress);
    }
}
...
task.execute();
```
- FetchItemsTask类的第3个模板参数表示`doInBackground(...)`的返回值以及`onPostExecute(...)`的输入参数，当`doInBackground(...)`被执行完成后，把返回值传入`onPostExecute(...)`。
- ④ 在设置adapter之前先调用了`isAdded()`，用来判断Fragment是否被attach到Activity，只有activity就绪了，才能设置adapter。之前没有做过此判断是因为以前fragment的函数都是被activity回调的，之所以能被会调说明activity一定已经加载了。而本章引入了后台线程，fragment的函数有可能被该线程调用，那就不能保证activity一定就绪，所以需要有`isAdded()`的判断。

## 结束后台线程
调用`AsyncTask::cancel(boolean)`可以终止后台线程，有两种方式：
- `AsyncTask::cancel(false)`是一种更柔和的方式，它将`isCancelled()`置为true，在`doInBackground(...)`会根据这个值判断是否退出。
- `AsyncTask::cancel(true)`则更粗暴，它直接终止线程，应尽量避免这么使用。

<font color=red>本节的最后简单提到了AsyncTaskLoader，当系统配置发生变化而导致重建时，LoaderManager会确保loader不会因此导致重建，因此它有更好的数据延续性。此处需要进一步确认：普通的AsyncTask也不会被重建吧？</font>