package palance.li.hello;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

public class HelloAndroid extends Activity{
    private final static String LOG_TAG = "palance.li.hello.HelloAndroid";

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        Log.i(LOG_TAG, "OnCreate OK.");
    }
}
