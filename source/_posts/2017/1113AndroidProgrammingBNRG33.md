---
layout: post
title: 《Android Programming BNRG》笔记三十三
date: 2017-11-13 20:00:00 +0800
categories: Android Programming
tags: Android BNRG笔记
toc: true
comments: true
---
本章
本章要点：
- Play Services
<!-- more -->

# Play Services
除了随Android系统带的标准库外，Android还通过Google Play Service下发和更新API，以确保这类功能的更新速度更快，location service就属于这一类型，被称为`Fused Location Provider`。如果使用这类API，就要求设备必须安装了Google Play Service。

# 在模拟器上安装Play Services
Android Studio菜单Tools > Android > SDK Manager，勾选“Show Package Details”，确保和模拟器对应版本的“Google APIs Intel x86 Atom System Imange”被勾选：
![](1113AndroidProgrammingBNRG33/img01.png)
来到Android Virutal Device Manager，确保模拟器Target里有“Google APIs”字样：
![](1113AndroidProgrammingBNRG33/img02.png)

# 使用Google Play Services
## 1.添加依赖
在AndroidStudio中，⌘+; > Project Structure > app > Dependencies > + > Library dependency
![](1113AndroidProgrammingBNRG33/img03.png)
输入com.agoogle.android.gms，注意我们需要的是com.agoogle.android.gms:play-services-location:11.6.0这在搜索结果里没有，需要自己补上完整的名称：
![](1113AndroidProgrammingBNRG33/img04.png)
<font color=red>如果不知道完整的写法该如何是好？</font>

## 2.检查Google Play Services是否可用
我们在Activity即将弹出时检查服务是否可用，如果不可用则弹出提示。
``` java
// LocatrActivity.java
public class LocatrActivity extends SingleFragmentActivity {
    private static final int REQUEST_ERROR = 0;
    ...
    @Override
    protected void onResume(){
        super.onResume();

        GoogleApiAvailability apiAvailability = GoogleApiAvailability.getInstance();

        int errorCode = apiAvailability.isGooglePlayServicesAvailable(this);
        if(errorCode != ConnectionResult.SUCCESS){ // 如果服务不可用，则弹提示
            Dialog errorDialog = apiAvailability.getErrorDialog(this,
                    errorCode, REQUEST_ERROR,
                    new DialogInterface.OnCancelListener() {
                        @Override
                        public void onCancel(DialogInterface dialogInterface) {
                            finish();
                        }
                    });
            errorDialog.show();
        }
    }
}
```
## 3.申请权限
在`AndroidManifest.xml`中声明权限：
``` xml
<manifest ...>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
    <uses-permission android:name="android.permission.INTERNET"/>
    <application.../>
</manifest>
```
其中FINE_LOCATION来自GPS信号更精准，COARSE_LOCATION来自基站或WiFi信号精度较差。二者都属于`dangerous`类型的权限，这类权限仅在`AndroidManifest.xml`里声明是不够的，必须在运行时，再实时申请。

``` java
// LocatrFragment.java
public class LocatrFragment extends Fragment {
    private static final String TAG = "LocatrFragment";
    private static final String[] LOCATION_PERMISSIONS = new String[]{
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
    };
    private static final int REQUEST_LOCATION_PERMISSION = 0;
    private ImageView mImageView;
    private GoogleApiClient mClient;

    public static LocatrFragment newInstance(){
        return new LocatrFragment();
    }

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setHasOptionsMenu(true);
        mClient = new GoogleApiClient.Builder(getActivity())
                .addApi(LocationServices.API)
                .addConnectionCallbacks(
                        new GoogleApiClient.ConnectionCallbacks() {
                            @Override
                            public void onConnected(@Nullable Bundle bundle) {
                                getActivity().invalidateOptionsMenu();
                            }

                            @Override
                            public void onConnectionSuspended(int i) {

                            }
                        })
                .build();
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState){
        View v = inflater.inflate(R.layout.fragment_locatr, container,
                false);
        mImageView = (ImageView)v.findViewById(R.id.image);
        return v;
    }

    @Override
    public void onStart(){
        super.onStart();
        getActivity().invalidateOptionsMenu();
        mClient.connect();
    }

    @Override
    public void onStop(){
        super.onStop();
        mClient.disconnect();
    }

    @Override
    public void onCreateOptionsMenu(Menu menu, MenuInflater inflater){
        super.onCreateOptionsMenu(menu, inflater);
        inflater.inflate(R.menu.fragment_locatr, menu);
        MenuItem searchItem = menu.findItem(R.id.action_locate);
        searchItem.setEnabled(mClient.isConnected());
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item){
        switch (item.getItemId()){
            case R.id.action_locate:
                if(hasLocationPermission()) {
                    findImage();
                }else {
                    requestPermissions(LOCATION_PERMISSIONS, REQUEST_LOCATION_PERMISSION);
                }
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permission,
                                          int[] grantResults){
        switch (requestCode){
            case REQUEST_LOCATION_PERMISSION:
                if(hasLocationPermission()){
                    findImage();
                }
                default:
                    super.onRequestPermissionsResult(requestCode, permission,
                            grantResults);
        }
    }

    private void findImage(){
        LocationRequest request = LocationRequest.create();
        request.setPriority(LocationRequest.PRIORITY_HIGH_ACCURACY);
        request.setNumUpdates(1);
        request.setInterval(0);

        LocationServices.FusedLocationApi
                .requestLocationUpdates(mClient, request,
                        new LocationListener() {
                            @Override
                            public void onLocationChanged(Location location) {
                                Log.i(TAG, "Got a fix: " + location);
                            }
                        });
    }

    private boolean hasLocationPermission(){
        int result = ContextCompat.checkSelfPermission(getActivity(),
                LOCATION_PERMISSIONS[0]);
        return result == PackageManager.PERMISSION_GRANTED;
    }
}
```