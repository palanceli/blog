package com.palanceli.demo.msgloopdemo;

import android.os.AsyncTask;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import org.w3c.dom.Text;

public class MainActivity extends AppCompatActivity {
    private HandlerThread mDataThread;
    private Handler mDataThreadHandler;
    private int mManualWorkNum = 0;

    // 定义在数据线程中的工作任务
    public class DataTask implements Runnable{
        private int mWorkNum;
        private boolean mAutoWork = true; // 手动还是自动
        public DataTask(int workNum, boolean autoWork){
            mWorkNum = workNum;
            mAutoWork = autoWork;
        }
        public void run(){
            int tid = android.os.Process.myTid();
            try {
                Thread.sleep(2000);       // 假设需要一段时间保存数据
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            if(mAutoWork)
                System.out.printf("[Data Thread %d] Save auto work %d\n", tid, mWorkNum);
            else
                System.out.printf("[Data Thread %d] Save manual work %d\n", tid, mWorkNum);
        }
    }

    public class WorkThread extends Thread{
        private int mWorkNum;
        public WorkThread(String name){
            super(name);
        }

        public void run(){
            int tid = android.os.Process.myTid();
            for (; mWorkNum<10; mWorkNum++){
                try {
                    Thread.sleep(1000);  // 工作线程完成每次工作
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                System.out.printf("[Work Thread %d] Complete Work %d.\n", tid, mWorkNum);

                // 向数据线程发送消息
                mDataThreadHandler.post(new DataTask(mWorkNum, true));
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        int tid = android.os.Process.myTid();
        System.out.printf("[UI Thread %d]\n", tid);

        mManualWorkNum = 0;
        final Button clickMeButton = (Button)findViewById(R.id.ManualWorkButton);
        clickMeButton.setOnClickListener(new View.OnClickListener() {
                                             @Override
                                             public void onClick(View view) {
                                                 mManualWorkNum++;
                                                 mDataThreadHandler.post(new DataTask(mManualWorkNum, false));
                                             }
                                         });
        initBackThread();
    }

    private void initBackThread() {
        // 启动工作线程
        WorkThread workThread = new WorkThread("Work Thread");
        workThread.start();
        // 创建数据线程
        mDataThread = new HandlerThread("Data Thread");
        mDataThread.start();
        // 保存数据线程的Handler
        mDataThreadHandler = new Handler(mDataThread.getLooper());

        // 定义AsyncTask，
        // public abstract class AsyncTask<Params, Progress, Result> 三个模板参数分别为：
        //   Params：  doInBackground方法的参数类型
        //   Progress：AsyncTask所执行的后台任务的进度类型
        //   Result：  后台任务的返回结果类型
        AsyncTask<Integer, Integer, Integer> task =
                new AsyncTask<Integer, Integer, Integer>() {
            @Override
            protected Integer doInBackground(Integer... integers) {
                Integer asyncTaskNum = integers[0];
                int tid = android.os.Process.myTid();

                for(; asyncTaskNum<10; asyncTaskNum++){
                    try {
                        Thread.sleep(1000);
                        System.out.printf("[Async Task Thread %d] Complete async task%d.\n", tid, asyncTaskNum);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                    publishProgress(asyncTaskNum);
                }
                return asyncTaskNum;
            }
            protected void updateAsyncTextInfo(Integer val){
                TextView tv = (TextView)findViewById(R.id.aysncTextInfo);
                int tid = android.os.Process.myTid();
                tv.setText("Completed " + val + " async tasks.(tid=" + tid + ")");
            }
            @Override
            protected void onProgressUpdate(Integer... integers){
                super.onProgressUpdate(integers);
                updateAsyncTextInfo(integers[0]);
            }
            @Override
            protected void onPostExecute(Integer integer){
                updateAsyncTextInfo(integer);
            }
        };
        // 启动
        task.execute(0);
    }
}
