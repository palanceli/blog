---
title: Mac下的定时自动运行
date:   2016-08-19 20:17:37 +0800
categories: 随笔笔记
tags: Mac操作配置
toc: true
comments: true
---
终于被Mac的launchctl打败了，每次配置都要花好长时间摆弄这个玩意，每次都得出点什么状况，还有那个谜一样的返回码，每次都要查半天。干脆下载一个GUI程序[LaunchControl](http://www.soma-zone.com/LaunchControl/)，直接上配置如下：
<!-- more -->
![LaunchControl配置](0819AutoRunOnMac/img01.png)
公司的机器经常重起后ip就变了，这会让我在家里vpn不到这台机器。我让这台机器每隔一段时间向server发http请求，server的ip是固定的，因此从server的http log上就能找到这台机器的ip了。
LaunchControl背后还是调用了launchctl，只是它能把错误信息更直观地展现出来。再来看看它生成的plist文件：
``` xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>KeepAlive</key>
        <false/>
        <key>Label</key>
        <string>com.palanceli.ipmonitor.plist</string>
        <key>ProgramArguments</key>
        <array>
            <string>curl</string>
            <string>http://10.134.29.201/rmbp</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardErrorPath</key>
        <string>/tmp/com.palanceli.ipmonitor.plist.err</string>
        <key>StandardOutPath</key>
        <string>/tmp/com.palanceli.ipmonitor.plist.out</string>
        <key>StartInterval</key>
        <integer>60</integer>
</dict>
</plist>
```