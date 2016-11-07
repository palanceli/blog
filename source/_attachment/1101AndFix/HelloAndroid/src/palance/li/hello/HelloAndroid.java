package palance.li.hello;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

public class HelloAndroid extends Activity{
    private final static String LOG_TAG = "palance.li.hello.HelloAndroid";

    @Override
    public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        TextView tv = (TextView)findViewById(R.id.tv);
        tv.setText("I'm a bug !v_v!");
        Log.i(LOG_TAG, "OnCreate OK.");
    }
}
