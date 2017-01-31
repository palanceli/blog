package com.palanceli.demo.msgloopdemo;

import android.os.Handler;
import android.os.HandlerThread;
import android.os.Message;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;

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
        WorkThread workThread = new WorkThread("Work Thread");
        workThread.start();

    }
}
