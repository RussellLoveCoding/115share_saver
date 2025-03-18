#!/usr/bin/python3
#coding:  utf-8
import requests
import json
import sys
import sqlite3
import re
import codecs
import os
from time import sleep
from p115client import P115Client
from pathlib import Path
import argparse
import sys
import traceback
import logging
import time

class SharedLinksDB:
    def __init__(self, db_file):
        self.netdisk_115_client = None
        self.conn = self.create_connection(db_file)
        if self.conn is not None:
            self.create_table('''CREATE TABLE IF NOT EXISTS shared_link
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 share_code TEXT,
                                 receive_code TEXT,
                                 snap_id INTEGER,
                                 file_size INTEGER,
                                 share_title TEXT,
                                 share_state INTEGER,
                                forbid_reason INTEGER,
                                    create_time INTEGER,
                                    receive_count INTEGER,
                                    expire_time INTEGER,
                                    file_category INTEGER,
                                    auto_renewal INTEGER,
                                    auto_fill_recvcode INTEGER,
                                    can_report INTEGER,
                                    can_notice INTEGER,
                                    have_vio_file INTEGER,
                                 status INTEGER)''')

            self.create_table('''CREATE TABLE IF NOT EXISTS saved_data
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 n TEXT,
                                 cid TEXT)''')

    def __del__(self):
        self.close_connection()

    # 创建数据库连接
    def create_connection(self, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except:
            logging.error("[x] 无法创建数据库连接")
        return conn

    # 创建数据表
    def create_table(self, create_table_sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
        except:
            logging.error("[x] 无法创建数据表")

    # 插入分享链接信息
    def insert_shared_link(self, share_code, receive_code,share_info, status):
        sql = '''INSERT INTO shared_link (share_code, receive_code, snap_id, file_size, share_title, share_state, forbid_reason, create_time, receive_count, expire_time, file_category, auto_renewal, auto_fill_recvcode, can_report, can_notice, have_vio_file, status)'''
        sql += '''VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        cursor = self.conn.cursor()
        if share_info:
            cursor.execute(sql, (share_code, receive_code, share_info['snap_id'], share_info['file_size'], share_info['share_title'], share_info['share_state'], share_info['forbid_reason'], share_info['create_time'], share_info['receive_count'], share_info['expire_time'], share_info['file_category'], share_info['auto_renewal'], share_info['auto_fill_recvcode'], share_info['can_report'], share_info['can_notice'], share_info['have_vio_file'], status))
        else:
            cursor.execute(sql, (share_code, receive_code, 0, 0, '', 0, '', 0, 0, 0, 0, 0, 0, 0, 0, 0, status))
        self.conn.commit()

    # 检查分享链接信息是否存在
    def check_shared_link(self, share_code, receive_code):
        sql = '''SELECT 1 FROM shared_link WHERE share_code = ? AND receive_code = ?'''
        cursor = self.conn.cursor()
        cursor.execute(sql, (share_code, receive_code))
        rows = cursor.fetchall()
        return len(rows) > 0

    # 插入data_list中的n值和cid值
    def insert_saved_data(self, data_list):
        cursor = self.conn.cursor()
        for i, data in enumerate(data_list):
            sql = '''INSERT INTO saved_data (n, cid)
                    VALUES (?, ?)'''
            cursor.execute(sql, (str(data['n']), data['cid']))
        self.conn.commit()

    # 检查saved_data表中是否已经存在n值
    def check_saved_data(self, n):
        sql = '''SELECT * FROM saved_data WHERE n = ?'''
        cursor = self.conn.cursor()
        cursor.execute(sql, (n,))
        rows = cursor.fetchall()
        return len(rows) > 0

    # 关闭数据库连接
    def close_connection(self):
        if self.conn is not None:
            self.conn.close()

class Fake115Client(object):

    def __init__(self,  cookies, cliHelper:P115Client):
        self.cookies = cookies
        self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        self.content_type = 'application/x-www-form-urlencoded'
        self.header = {"User-Agent":  self.ua,
                       "Content-Type":  self.content_type,  "Cookie": self.cookies}
        self.db = SharedLinksDB('shared_links.db')
        # self.root_cid = root_cid
        self.get_userid()
        self.cliHelper=cliHelper

    # 获取UID
    def get_userid(self):
        try:
            self.user_id = ''
            url = "https://my.115.com/?ct=ajax&ac=get_user_aq" ############
            p = requests.get(url, headers=self.header)
            if p:
                rootobject = p.json()
                if not rootobject.get("state"):
                    self.err = "[x] 获取 UID 错误：{}".format(rootobject.get("error_msg"))
                    return False
                self.user_id = rootobject.get("data").get("uid")
                return True
        except Exception as result:
            logging.error("[x] 异常错误：{}".format(result))
        return False

    def request_datalist(self,share_code,receive_code):
        url = f"https://webapi.115.com/share/snap?share_code={share_code}&offset=0&limit=20&receive_code={receive_code}&cid="
        data_list = []
        share_info = {}
        try:
            response = requests.get(url, headers=self.header)
            response_json = json.loads(response.content.decode())
            share_info = response_json['data'].get('shareinfo')
            if response_json['state'] == False:
                logging.error('error:',response_json['error'])
                return share_info,[]
            count = response_json['data']['count']
            data_list.extend(response_json['data']['list'])
            while len(data_list) < count:
                offset = len(data_list)
                response = requests.get(f"{url}&offset={offset}")
                response_json = json.loads(response.content.decode())
                data_list.extend(response_json['data']['list'])
        except:
            data_list = []
        return share_info,data_list

    def post_save(self, share_code, receive_code, file_ids, pid='', req_delay=2):
        time.sleep(req_delay)
        # logging.info('[√]正在转存 %s:%s 中的 %d 项' % (share_code,receive_code, len(file_ids)))
        # 将 file_ids 用逗号拼接为一个字符串
        file_id_str = ','.join(file_ids)
        # 构造 POST 请求的 payload
        if pid == '':
            payload = {
                'user_id': self.user_id,
                'share_code': share_code,
                'receive_code': receive_code,
                'file_id': file_id_str
            }
        else:
            payload = {
                'user_id': self.user_id,
                'share_code': share_code,
                'receive_code': receive_code,
                'file_id': file_id_str,
                'cid': pid
            }
        # 发送 POST 请求
        try:
            response = requests.post('https://webapi.115.com/share/receive', data=payload, headers=self.header)
        except:
            sleep(5)
            response = requests.post('https://webapi.115.com/share/receive', data=payload, headers=self.header)
        result = response.json()
        if not result['state']:
            logging.error('[x]转存 %s:%s 失败，原因：%s' % (share_code,receive_code,result['error']))
        response.close()
        return result['state']

    def create_dir(self,cname, pid):
        '''
        pid:父目录id
        cname:目录名
        '''
        if not cname:
            return self.target_dir_cid
        if pid == "":
            pid = 0
        data = {'pid': pid ,'cname':cname}
        try:
            response=requests.post('http://web.api.115.com/files/add',data=data,headers=self.header)
            data=response.json()
            if data['state']:
                return data['cid']
            else:
                logging.error('[x]'+'新建文件夹失败,错误信息:'+data['error'])
                return self.target_dir_cid
        except:
                logging.error('[x]'+'新建文件夹失败')
                return self.target_dir_cid

    def share_link_parser(self, link) -> tuple:
        match = re.search(r'https?:\/\/(115|115cdn|anxia)\.com\/s\/(\w+)\?password\=(\w+)', link, re.IGNORECASE |re.DOTALL)
        if not match:
            logging.info(f'链接格式错误, link={link}')
            return None
        share_code=match.group(2)
        receive_code=match.group(3)
        return (share_code,receive_code)

        
    def save_link(self, share_item, pid="") -> bool:
        """
        将数据转存于 目录pid 中,
        
        特别地，对于一个含有多项条目的分享，则需要在 pid 下创建一个新的目录，并将文件转存于该新的目录中
        """

        share_code=share_item[0]
        receive_code=share_item[1]

        # 获取data_list
        share_info,data_list = self.request_datalist(share_code, receive_code)
        # 总数0就存share_code, receive_code到数据库 非0发送转存请求
        if len(data_list) == 0:
            self.db.insert_shared_link(share_code, receive_code,share_info,0)
            return True

        self.db.insert_shared_link(share_code, receive_code,share_info,1)
        file_ids = []
        for data in data_list:
            n = data['n']
            cid = data['cid']
            fid = data.get('fid')
            if fid:
                cid = fid
            # 检查数据库中是否存在n值
            if self.db.check_saved_data(n):
                print('[x]转存 %s:%s 中的 %s 已存在' % (share_code,receive_code, n))
                continue
            file_ids.append(cid)
        
        # 如果一个分享有多个文件的话，则需要创建一个新的目录去包括他们，然后再转存
        # if len(data_list) > 1:

        #     # 首先检查是否存在同名目录
        #     res = cliHelper.fs_files({
        #         "cid":pid,
        #         "limit":32,
        #         "cur":1,
        #         "show_dir":1,
        #         "nf":1,
        #     })
        #     subdirs_map = {}
        #     if res["state"]:
        #         for i in res["data"]:
        #             subdirs_map[i["n"]] = i
        #         if share_info["share_title"] in subdirs_map:
        #             pid = subdirs_map[share_info["share_title"]]["cid"]
            
        #     # 需要创建一个目录
        #     if not res["state"] or share_info["share_title"] not in subdirs_map:
        #         payload={ "cname": share_info['share_title'], "pid":pid}
        #         res = self.cliHelper.fs_mkdir(payload)
        #         if res["state"] == True:
        #             pid = res["cid"]

        if self.post_save(share_code=share_code, receive_code=receive_code, file_ids=file_ids, pid=pid):
            self.db.insert_saved_data(data_list)
            return True
        return False

    def batch_save_share_link_from_file(self, pid="", filepath=""):
        
        with open(filepath, 'r', encoding='utf-8') as f:
            share_items = [
                self.share_link_parser(l.strip())
                for l in f.readlines()
                if self.share_link_parser(l.strip()) is not None
            ]

        if len(share_items) == 0 and filepath != "":
            print(f'{os.path.basename(filepath)} 是个空文件，没有链接可转存\n')
            return

        saved = [ i for i in share_items if self.db.check_shared_link(i[0],i[1])]
        not_yet = [ i for i in share_items if not self.db.check_shared_link(i[0],i[1])]
        
        msg = f"""
--------------------------------
{os.path.basename(filepath)} 文件 合法分享连接数: {len(share_items)} 

已经转存数目：{len(saved)}

本轮需要转存数目: {len(not_yet)}

"""
        print(msg)
        logging.info(msg)
        
        cur_succ_cnt = 0
        for i in not_yet:
            res = self.save_link(i, pid)
            if res:
                cur_succ_cnt += 1   
                logging.info(f'成功转存 https://115cdn.com/s/{i[0]}?password={i[1]}')
                logging.info(f'【当前链接文件转存进度】: {(cur_succ_cnt/len(not_yet)) *100:.2f}%, 转存总进度')
            else:
                logging.info(f'转存失败 https://115cdn.com/s/{i[0]}?password={i[1]}')
        # saved_res = [ self.save_link(i, pid) for i in not_yet ]

        msg = f"""
本轮共转存数目: {len(not_yet)}

成功转存数目: {cur_succ_cnt}

失败转存数目: {len(not_yet)-cur_succ_cnt}
"""

        print(msg)
        logging.info(msg)


def get_cookies_interactively():
    """获取单行cookies输入（Chrome抓包格式）"""
    
    try:
        if not os.path.exists("./cookies.txt"):
            print("\n请粘贴从Chrome获取的完整cookies字符串（单行）：")
            print("示例：key1=value1; key2=value2; key3=value3\n")
            cookies = input("Cookies > ").strip()
            with open('./cookies.txt', 'w', encoding='utf-8') as f:
                f.write(cookies)
        else:
            with open('./cookies.txt', 'r') as f:
                cookies = f.read()
    except KeyboardInterrupt:
        sys.stderr.write("\n操作已取消\n")
        sys.exit(1)
    
    if not cookies:
        sys.stderr.write("\n错误：未检测到cookies输入，请重新操作\n")
        sys.stderr.write("提示：请完整复制Chrome抓包中的Cookie请求头内容\n")
        sys.exit(1)
    
    return cookies

def parse_arguments():
    """解析命令行参数（与之前相同）"""
    parser = argparse.ArgumentParser(description='网盘文件转存工具')
    parser.add_argument('-c', '--cid', required=True, help='CID目录标识')
    parser.add_argument('-d', '--dir', action='append', default=[], 
                       help='目标目录名，需与-l参数成对出现')
    parser.add_argument('-l', '--links_path', action='append', default=[], 
                       help='分享链接文件路径，需与-d参数成对出现')

    args = parser.parse_args()
    
    if len(args.dir) != len(args.links_path):
        parser.error("错误：每个 -d 参数必须对应一个 -l 参数\n")
    if not args.dir:
        parser.error("错误：至少需要一组 -d 和 -l 参数\n")
    for i in args.links_path:
        if not os.path.exists(i):
            parser.error(f"错误：{i} 文件不存在")
        if not i.endswith('.txt'):
            parser.error(f"错误：{i} 文件不是文本文件")
    return args

if __name__ == '__main__':
    logging.basicConfig(
        filename="115.share.link.save.log",  # 日志文件名
        level=logging.INFO,  # 日志级别
        format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    )

    args = parse_arguments()
    user_cookies = get_cookies_interactively()

    to_save_items = [
        {"dir_name":dir_name, "filepath":links_path} for dir_name, links_path in zip(args.dir, args.links_path)
    ]
    # print(to_save_items)

    cliHelper = P115Client(user_cookies)

    # 获取 cid 下的目录信息, 以检查是否需要创建 指定的目录， 用来存储 分享的文件
    res = cliHelper.fs_files({
        "cid":args.cid,
        "limit":32,
        "cur":1,
        "show_dir":1,
        "nf":1,
    })
    if res["state"] == False:
        logging.error(f'无法获取 cid {args.cid} 下的子文件夹信息, 请检查 cid 是否正确, error={res["error"]}')
        os._exit(0)

    subdirs_map = {}
    for i in res["data"]:
        subdirs_map[i["n"]] = i

    # 解析文件，提取分享链接
    for i in range(len(to_save_items)):

        dir_name = to_save_items[i]["dir_name"]
        if dir_name in subdirs_map:
            to_save_items[i]["cid"] = subdirs_map[dir_name]["cid"]
            logging.info(f'cid {args.cid} 下的目录 {dir_name} 已存在, 无须创建\n')
            continue

        to_save_items[i]["cid"] = args.cid # 这里如果创建目录失败的话，分享的文件将会转存到 指定的 cid 根目录
        payload={ "cname": dir_name, "pid":int(args.cid)}
        res = cliHelper.fs_mkdir(payload)
        if res["state"] == True:
            to_save_items[i]['cid'] = res['cid']
            logging.info(f'cid {args.cid} 下的目录 {to_save_items[i]["dir_name"]} 创建成功\n')

    # 开始转存
    cli = Fake115Client(cookies=user_cookies, cliHelper=cliHelper)
    for item in to_save_items:
        cli.batch_save_share_link_from_file(item["cid"], item["filepath"])
