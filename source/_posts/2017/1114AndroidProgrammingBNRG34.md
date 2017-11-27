---
layout: post
title: 《Android Programming BNRG》笔记三十四
date: 2017-11-14 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章会把附近图片的经纬度标到地图上。
本章要点：
- 获取Google地图API key
- 显示Google地图
- 在Google地图上标注位置
<!-- more -->

# 获取地图API key
使用Map API需要在AndroidManifest.xml文件中配置一个API key，该API key是用来证明此app已经获得了Google Map Service的授权。在[《Google Maps API》](https://developers.google.com/maps/documentation/)有官方说明。具体操作步骤可以follow AndroidStudio的指示，包名右键 > New > Activity > Gallery
![](1114AndroidProgrammingBNRG34/img01.png)
选择Google Maps Activity：
![](1114AndroidProgrammingBNRG34/img02.png)
这会生成`MapsActivity.java`和`google_maps_api.xml`两个文件，打开后者：
``` xml
<resources>
    <!--
    TODO: Before you run your application, you need a Google Maps API key.

    To get one, follow this link, follow the directions and press "Create" at the end:

    https://console.developers.google.com/flows/enableapi?apiid=maps_android_backend&keyType=CLIENT_SIDE_ANDROID&r=84:99:B8:6F:79:C0:48:5E:A0:3D:F5:2B:3A:E3:EC:ED:A3:BE:A6:A8%3Bcom.bnrg.locatr
    ...
    -->
    <string name="google_maps_key" templateMergeStrategy="preserve" 
    translatable="false">AIzaSyBFYVpfsIF7k4MJa3vxDHZDpbmKNS9UPxA</string>
</resources>
```
按照提示生成`API密钥`，将其填入`google_maps_key`，注意要设置`密钥限制`为`Android应用`。我在运行的时候还是出现了如下错误：
```
E/Google Maps Android API: Authorization failure.  
    Please see https://developers.google.com/maps/documentation/android-api/start for how to correctly set up the map.
E/Google Maps Android API: In the Google Developer Console (https://console.developers.google.com)
    Ensure that the "Google Maps Android API v2" is enabled.
    Ensure that the following Android Key exists:
    API Key: xxxxxx
    Android Application (<cert_fingerprint>;<package_name>):xx:xx:xx:xx....;com.bnrg.locatr
```
可以将提示中指出的证书指纹和包名添加到服务端即可：
![](1114AndroidProgrammingBNRG34/img03.png)

> 书中提到：引入MapsActivity会自动添加依赖`com.google.android.gms:pla-services`，这玩意儿会带来巨大的代码量，导致method limit爆表。因为Android app支持的最大方法数是65536个，如果要多于这个方法数，就必须使用multidex。本节给出的方法是在app/build.gradle中删除`compile 'com.google.android.gms:play.services:11.6.0'`。但是我在引入MapsActivity之后并没有在gradle文件中找到这么一行。

# 显示地图
可以使用`MapView`来显示地图，使用它和普通的View最大的差别在于：必须要把所有生命周期回调函数转发给它，例如：
``` java
@Override
public void onCreate(Bundle savedInstanceState){
    super.onCreate(savedInstanceState);
    ...
    mMapView.onCreate(savedInstanceState);
}
```
好烦！可以使用`SupportMapFragment`让它完成这些转发，我们要做的只是让我们的Fragment成为它的子类即可，`SupportMapFragment`内部维护着一个MapView实例。

## 从Flickr获取返回的位置数据
在前一节中，请求Flickr数据时，会带上当前所在位置：
``` java
// FlickrFetchr.java
    private String buildUrl(Location location){
        return ENDPOINT.buildUpon()
                .appendQueryParameter("method", SEARCH_METHOD)
                .appendQueryParameter("lat", "" + location.getLatitude())   
                .appendQueryParameter("lon", "" + location.getLongitude())
                .build().toString();    // lat和lon为当前位置
    }
```
现在还需要告诉服务器端：请在返回数据中包含每张图片所在的位置：
``` java
// FlickrFetchr.java
    private static final Uri ENDPOINT = Uri.parse("https://api.flickr.com/services/rest/")
            .buildUpon()
            .appendQueryParameter("api_key", API_KEY)
            .appendQueryParameter("format", "json")
            .appendQueryParameter("nojsoncallback", "1")
            .appendQueryParameter("extras", "url_s,geo")  // geo要求返回图片位置
            .build();
```
当请求收到应答数据后，解析并获取图片的位置信息：
``` java
// FlickrFetchr.java
    private void parseItems(List<GalleryItem> items, JSONObject jsonBody)...{
        JSONObject photosJsonObject = jsonBody.getJSONObject("photos");
        JSONArray photoJsonArray = photosJsonObject.getJSONArray("photo");
        for(int i=0; i<photoJsonArray.length(); i++){
            JSONObject photoJsonObject = photoJsonArray.getJSONObject(i);
            GalleryItem item = new GalleryItem();
            ...
            item.setLat(photoJsonObject.getDouble("latitude"));
            item.setLon(photoJsonObject.getDouble("longitude"));
            items.add(item);
        }
    }
```
把前面的机制层串在一起：带着当前位置请求Flickr，得到距离当前位置最近的item，并获取图片：
``` java
// FlickrFetchr.java
    private class SearchTask extends AsyncTask<Location, Void, Void>{
        private GalleryItem mGalleryItem;
        private Bitmap mBitmap;
        private Location mLocation;

        @Override
        protected Void doInBackground(Location ... params){
            mLocation = params[0]; // 传入的当前位置
            FlickrFetchr fetchr = new FlickrFetchr();
            List<GalleryItem> items = fetchr.searchPhotos(params[0]);
            ...
            mGalleryItem = items.get(0); // 离当前位置最近的item
            try{ // 获取最近的item包含的图片
                byte[] bytes = fetchr.getUrlBytes(mGalleryItem.getUrl());
                mBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            }...
        }

        @Override
        protected void onPostExecute(Void result){
            // 将成功下载到的数据更新给宿主类LocatrFragment
            mMapImage = mBitmap;
            mMapItem = mGalleryItem;
            mCurrentLocation = mLocation; 
            updateUI();
        }
    }
```
## 显示地图并标注位置
`SupportMapFragment`内部维护一个`MapView`实例，但要想提领到该实例，需要使用异步函数`getMapAsync(...)`：
``` java
// LocatrFragment.java
public class LocatrFragment extends SupportMapFragment {
    @Override
    public void onCreate(Bundle savedInstanceState){
        ...
        getMapAsync(new OnMapReadyCallback() {
            @Override
            public void onMapReady(GoogleMap googleMap) {
                mMap = googleMap; // ① 当得到ViewMap的实例，会通过回调赋给mMap。
                updateUI(); // ②a
            }
        });
    }

    private class SearchTask extends AsyncTask<Location, Void, Void>{
        ...
        @Override
        protected void onPostExecute(Void result){
            mMapImage = mBitmap;
            mMapItem = mGalleryItem;
            mCurrentLocation = mLocation;
            updateUI(); // ②b
        }
    }
}

    private void updateUI(){
        ...
        LatLng itemPoint = new LatLng(mMapItem.getLat(),
                mMapItem.getLon()); // 附近图片经纬度
        LatLng myPoint = new LatLng(mCurrentLocation.getLatitude(),
                mCurrentLocation.getLongitude()); // 当前所在经纬度

        BitmapDescriptor itemBitmap =
                BitmapDescriptorFactory.fromBitmap(mMapImage);
        MarkerOptions itemMarker = new MarkerOptions()
                .position(itemPoint)
                .icon(itemBitmap); // 附近图片直接显示在地图上
        MarkerOptions myMarker = new MarkerOptions()
                .position(myPoint); // 当前所在经纬度显示图钉
        mMap.clear();
        mMap.addMarker(itemMarker);
        mMap.addMarker(myMarker);   // ③添加定位点

        LatLngBounds bounds = new LatLngBounds.Builder()
                .include(itemPoint)
                .include(myPoint)
                .build();           // ④
        int margin = getResources().getDimensionPixelOffset(
                R.dimen.map_inset_margin); // ⑤
        CameraUpdate update =
                CameraUpdateFactory.newLatLngBounds(bounds, margin);
        mMap.animateCamera(update); // ⑥
    }
    ...
}
```
②当初始化完成或者当下到新的附近图片的信息，将刷新地图界面。
③在地图上添加两个定位点，一个是当前位置，用图钉表示；另一个是附近图片，直接在对应位置上显示图片。
④构造一个LatLngBounds实例，它的作用是圈定地图显示的范围，可以把你关心的点include到LatLngBounds里，`build()`会生成包含这些点的矩形区域。
⑤指定LatLngBounds区域距离MapView的边距。④和⑤共同组成了地图当前显示的位置和比例尺。
⑥可以通过两种方式更新地图：`moveCamera(CameraUpdate)`或`animateCamera(CameraUpdate)`

运行后的结果如下：
![](1114AndroidProgrammingBNRG34/img04.png)
可以在模拟器的Extended control中设置当前位置。宇宙中心的经纬度是：东经116.332°, 北纬39.993°。
