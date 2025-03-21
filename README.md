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

1. **将分享链接分类保存到不同文件中**。将例如本例子当中有 电影.txt 存储着 很多电影的 115分享链接，剧集同理。
2. **拷贝 转存目标文件夹的 cid**.  例如我要将本轮转存的所有分享到转存到 根目录中，则 cid 为 `0`. 否则在浏览器中打开115网盘的该文件夹，然后复制网址中的cid
3. **填写参数执行命令**。`-c cid`, `-d 电影 -l 电影.txt` 并执行。这几个参数的意思是：在 cid 目录下 创建 电影子目录，并在电影子目录转存所有 电影.txt 中的分享链接、
    1. **输入 Cookies**. 在执行命令后需要输入从浏览器调试工具拷贝到的 115 Cookies， 接着程序会保存到同目录下的 cookies.txt的文件，后续不需要重新输入。
    2. **链接检查**：非法分享链接会直接跳过。只有符合 115 合法域名和合法分享链接的才会接收，如 115.com/s/xxxx?password=1234#沙丘2 [90G] 原盘
    3. **转存逻辑**：在 cid 目录下 根据 `-d 电影 -l 电影.txt` 参数对 创建子文件夹（如果有则不重建直接用），并转存对应的分享链接到 子文件夹中。
    4. **去重逻辑**：重复转存过的链接不会再转存，会跳过. 如果想转存，则需要 先删掉 执行脚本文件的目录下的 share_links.db, 同时删掉 115网盘中接收中的转存记录。
4. **查看转存日志**。打开同目录下的 `115.share.link.save.log` 查看转存日志，包括 成功转存的、失败转存的、转存进度、转存统计等信息。可以通过命令 `tail -f 115.share.link.save.log` 监控转存情形。

命令例子

```shell
python 115share_saver.py -c "3113388667951906219" -d "电影" -l "电影.txt" -d "剧集" -l "剧集.txt"
```

或者 

```bash
python 115share_saver.py --cid "3113388667951906219" --dir "电影" --links_path "电影.txt" --dir "剧集" --links_path "剧集.txt"
```


转存统计例子
```txt
--------------------------------
电影-韩国.txt 文件 合法分享连接数: 6

已经转存数目：0

本轮需要转存数目: 6



本轮共转存数目: 6

成功转存数目: 6

失败转存数目: 0

```

转存日志例子
```
...

2025-03-18 01:45:28,662 - INFO - 成功转存 https://115cdn.com/s/swzjjw73h0m?password=zc39
2025-03-18 01:45:28,662 - INFO - 【当前链接文件转存进度】: 27.66%, 转存总进度
2025-03-18 01:45:30,948 - ERROR - [x]转存 swhm2og33dn:3993 失败，原因：链接已过期或接收人次超过上限

...

2025-03-18 01:46:50,515 - INFO - 成功转存 https://115cdn.com/s/sw6cugn33t0?password=gr4k
2025-03-18 01:46:50,515 - INFO - 【当前链接文件转存进度】: 95.74%, 转存总进度
2025-03-18 01:46:52,879 - INFO - 成功转存 https://115cdn.com/s/swzx5m93wrb?password=n221
2025-03-18 01:46:52,879 - INFO - 【当前链接文件转存进度】: 97.87%, 转存总进度
2025-03-18 01:46:52,879 - INFO -
本轮共转存数目: 47

成功转存数目: 46

失败转存数目: 1

```
