import os
import time
import json
import argparse
from json import JSONDecodeError
import random
import pandas as pd
import requests
from requests import Session

# from fake_useragent import UserAgent

pool = []


class Proxy:
    # PROXY_POOL_API = "http://82.157.149.211:5010/get"
    api = "http://webapi.http.zhimacangku.com/getip?num=400&type=2&pro=&city=0&yys=0&port=1&pack=193957&ts=0&" \
          "ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions="

    @classmethod
    def get_proxy(cls):
        # s = f"http://{requests.get(cls.PROXY_POOL_API).json()['proxy']}"
        r = requests.get(cls.api)
        print(r.text)
        r = json.loads(r.text)["data"]
        r = [f"http://{a['ip']}:{a['port']}" for a in r]
        return r


class Spider:
    SLEEP_TIME = 0.7
    U_A = [
        "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 "
        "Safari/534.16 ",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4688.0 "
        "Safari/537.36 Edg/97.0.1069.0",
    ]
    HEADERS = {
        "Host": "jyhpt.tj.gov.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/97.0.4688.0 Safari/537.36 Edg/97.0.1069.0",
        "Origin": "http://www.tj.gov.cn",
        "Referer": "http://www.tj.gov.cn/"
    }
    META_API = "http://jyhpt.tj.gov.cn/zmljl/list"
    DETAIL_API = "http://jyhpt.tj.gov.cn/zmljl/view"
    # proxies = Proxy.get_proxy()
    # print(proxies)

    def __init__(self, save_file: str = "./tj_result.csv"):
        self.sess = Session()
        # self.proxy = Proxy.get_proxy()
        self.save_file = save_file
        self.file_inited = False

    def _flush_session(self):
        self.sess = Session()
        # self.HEADERS["User-Agent"] = random.choice(self.U_A)
        # self._reset_proxy()

    def start(self, start_page_index=1, end_page_index=10, page_size=10):
        for i in range(start_page_index, end_page_index + 1):
            print(f"parsing page: {i}")
            # proxy = Proxy.get_proxy()
            # print(proxy)
            self._flush_session()
            # proxy = self._get_proxy()
            proxy = ""

            meta_info = self._parse_meta_info(page_index=i, page_size=page_size, proxy=proxy)
            details = [self._parse_detail(m, proxy) for m in meta_info]
            details = [d for d in details if d]

            # 增量写入文件
            df = pd.DataFrame(details)
            df.to_csv(self.save_file, mode='a', encoding="utf-8", index=False, header=False, sep="|")
            time.sleep(self.SLEEP_TIME)

    def _parse_meta_info(self, page_index: int, page_size: int, proxy: str = "") -> list:
        params = {
            "resultDeptType": 1,
            "pageIndex": page_index,
            "pageSize": page_size,
            "_": int(time.time() * 1000)
        }
        r = self.sess.get(self.META_API, params=params, headers=self.HEADERS, proxies={"http": proxy})
        r = json.loads(r.text)

        meta_info: list = r["datas"]["data"]
        return meta_info

    def _parse_detail(self, info: dict, proxy: str = "") -> dict:
        """ 解析单条元数据
        :param info:
        :return: dict
        """
        time.sleep(self.SLEEP_TIME)
        res = {
            "类型": info["questionType"],
            "留言标题": info["title"],
            "留言内容": "",
            "留言时间": info["createTime"],
            "答复内容": "",
            "答复部门": "",
            "答复时间": info["replyTime"],
            "主题分类": f"{info['keyword2']},{info['keyword3']}",
            "行政区域": info["deptName"]
        }
        id_ = info["id"]
        q_text, a_text, reply_department = self._get_text(id_=id_, proxy=proxy)

        res["留言内容"] = q_text.strip()
        res["答复内容"] = a_text.strip()
        res["答复部门"] = reply_department
        if q_text:
            return res
        else:
            return {}

    def _get_text(self, id_: int, proxy: str = ""):
        """解析单条元数据中的 问/答 文本"""
        params = {"id": id_, "_": int(time.time() * 1000)}

        r = self.sess.get(self.DETAIL_API, params=params, headers=self.HEADERS, proxies={"http": proxy})
        r = json.loads(r.text)
        r = r["datas"]
        q_text = r["content"]  # question
        a_text = r["replyContent"]  # answer
        reply_department = r["lkDeptName"]  # 答复部门
        print(q_text)
        return q_text, a_text, reply_department

    def _reset_proxy(self):
        self.proxy = Proxy.get_proxy()

    def _get_proxy(self):
        global pool
        return random.choice(pool)


if __name__ == '__main__':
    # with open("./pool.json", 'r') as f:
    #     info = json.load(f)["data"]
    #     pool = [f"http://{i['ip']}:{i['port']}" for i in info]

    spider = Spider(save_file="./tj_result_test_3.csv")
    start = 15001
    end = 28664
    # end = start + 100
    spider.start(start_page_index=start, end_page_index=end)
