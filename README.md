# 115share_saver

115批量转存助手

## 意义

有时候遇到很多的 115 分享链接，需要手动来逐个转存是很累人的，因此在 [AAlexDing的115sharebatchsave](https://github.com/AAlexDing/115sharebatchsave) 和 [ChenyangGao的p115client](https://github.com/ChenyangGao/p115client) 的基础上将转存功能封装成一个 cli 工具

功能包括：
1. 解析分享链接，排除非法链接，合法的分享链接包含 115 的几个域名的分享，例如 115.com, anxia.com, 115cdn.com, 也包括 http 链接
2. cli 通过参数化的方式，可以指定父目录，并且在父目录下创建不同新目录 以转存 不同类型的分享链接，具体以命令参看命令用法
3. 重复检查，不会转存已经转存过的分享链接

## 依赖安装

安装依赖 `pip install -U p115client`


## 命令用法

1. 首先分好类，将不同的分享链接归类到不同的文件当中。例如本例子当中有 电影.txt 存储着 很多电影的 115分享链接，剧集同理。
2. 在 115网盘 新创建个文件夹，并进入该文件夹，中网址 URL 中复制 `cid` 数值。要是使用根目录 直接用 0 即可。
3. 按如下命令例子开始转存，在执行命令后需要输入从浏览器调试工具拷贝到的 115 Cookies， 接着程序会保存到同目录下的 cookies.txt的文件，后续不需要重新输入，同时也会创建一个 share_links.db 的文件以记录转存过的链接，避免重复转存。
4. 命令转存时，会在  cid 目录下自动创建 几个子目录，并将 对应的文件中的分享转存到其中，转存请求每两秒转存一个，避免触发风控。注意 -d 和 -l 参数是成对出现的。
5. 打开同目录下的 `115.share.link.save.log` 查看转存日志，包括 成功转存的、失败转存的、转存进度、转存统计等信息。可以通过命令 `tail -f 115.share.link.save.log` 监控转存情形。

```shell
python 115share_saver.py -c "3113388667951906219" -d "电影" -l "电影.txt" -d "剧集" -l "剧集.txt"
```

或者 

```bash
python 115share_saver.py --cid "3113388667951906219" --dir "电影" --links_path "电影.txt" --dir "剧集" --links_path "剧集.txt"
```

