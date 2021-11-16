import re
import time
import json
import random
import pandas as pd
from requests import Session
from bs4 import BeautifulSoup


class GovSpider:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/97.0.4688.0 Safari/537.36 Edg/97.0.1069.0",
        "Host": "www.beijing.gov.cn",
        "Referer": "http://www.beijing.gov.cn/hudong/hdjl/com.web.search.mailList.flow",
        "Proxy-Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    search_data = {
        "PageCond/begin": 600,
        "PageCond/length": 600,
        "PageCond/isCount": "true",
        "keywords": "",
        "orgids": "",
        "startDate": "",
        "endDate": "",
        "letterType": "",
        "letterStatue": ""
    }
    mail_list_url = "http://www.beijing.gov.cn/hudong/hdjl/com.web.search.mailList.flow"
    search_api = "http://www.beijing.gov.cn/hudong/hdjl/com.web.search.mailList.mailList.biz.ext"
    # 咨询 api
    consult_detail_api = "http://www.beijing.gov.cn/hudong/hdjl/com.web.consult.consultDetail.flow"
    # 建议 api
    suggest_detail_api = "http://www.beijing.gov.cn/hudong/hdjl/com.web.suggest.suggesDetail.flow"

    def __init__(self):
        self.sess = Session()

    def parse(self):
        # 获取 cookie, 不需要 response
        self.sess.get(self.mail_list_url, headers=self.headers)

        # 向 search api POST, 获得总共 反馈数, 用于分批查询
        meta, _ = self._post_search_api()
        total_len = int(meta["count"])
        # total_len = 30
        # total_len = 1

        # 批量方式爬取
        res = []
        batch_size = 16
        for start in range(0, total_len, batch_size):
            # 这一批量反馈, 各自的元数据
            _, meta_infos = self._post_search_api(start=start, length=batch_size)
            infos = [self._parse_one_detail(info) for info in meta_infos]
            infos = [e for e in infos if e]  # 过滤空值
            res += infos
            time.sleep(0.1)

        # 保存为 csv 文件
        df = pd.DataFrame(res)
        print(len(df))
        df.to_csv("./result.csv", encoding="utf-8", index=False, sep="|")

        # with open("./result.json", "w", encoding="utf-8") as f:
        #     json.dump(res, f, indent=2, ensure_ascii=False)

        # print(self._parse_one_detail(_[0]))
        # id_ = first["original_id"]
        # v = "06081196458731493"
        # self.headers["Referer"] = "http://www.beijing.gov.cn/hudong/hdjl/com.web.suggest.suggesDetail." \
        #                           "flow?originalId=AH21111000024"
        # self.sess.get("http://www.beijing.gov.cn/hudong/yonghu/uSpace/myUserName",
        #               params={"v": v}, headers=self.headers)
        # self.parse_one_detail(id_="AH21111000024")

    def _post_search_api(self, start: int = 0, length: int = 1) -> (dict, list):
        """ 查询一批反馈的元数据
        :param start:
        :param length:
        :return: dict, dict["PageCond"] 为这一批的大小等, dict["mailList"]: list, 是每一条反馈的元数据
        """
        self.search_data["PageCond/begin"] = start
        self.search_data["PageCond/length"] = length
        r = self.sess.post(self.search_api, headers=self.headers, data=self.search_data)
        r = json.loads(r.text)
        return r["PageCond"], r["mailList"]

    def _parse_one_detail(self, info: dict):
        """
        爬取一条反馈的文本信息
        :param info
        :return:
        """
        type_ = info["letter_type"]  # 反馈类型
        id_ = info["original_id"]  # 反馈 ID
        title = info["letter_title"]  # 反馈标题
        q_date = info["create_date"]  # 问题时间
        is_reply = info["isReply"]  # 是否已回复

        catalog_id = info["catalog_id"]  # 类型 ?
        response_department = info["org_id"]  # 回复的部门

        res = {
            "类型": type_,
            "留言标题": title,
            "留言内容": "NaN",
            "留言时间": q_date,

            "答复内容": "NaN",
            "答复部门": response_department,
            "答复时间": "NaN",
            "主题分类": catalog_id,
            "行政区域": "NaN"
        }
        if is_reply:
            q_text, a_text, a_date = self._get_qa_text(id_=id_)
            if q_text:
                res["留言内容"] = q_text
                res["答复内容"] = a_text
                res["答复时间"] = a_date
            else:
                return {}
        return res

    def _get_qa_text(self, id_):
        r = self.sess.get(self.suggest_detail_api, params={"originalId": id_}, headers=self.headers)
        if r.status_code != 200:
            return None, None, None

        soup = BeautifulSoup(r.content, "lxml")
        container = soup.select("div.container > div")[-1]
        # 问 和 答, 各自的 DOM 块
        question, answer = container.find_all("div", attrs={"class": "row clearfix my-5 o-border p-2"})
        # 解析 问部分
        q_text = question.select("div")[-1].get_text().strip()

        # 解析 答部分
        answer = answer.div.div

        a_date = answer.div.select("div")[-1].get_text()
        a_date = a_date.split("：")[-1]

        a_text = answer.find("div", attrs={"class": 'col-xs-12 col-md-12 column p-4 text-muted my-3'}). \
            get_text().strip()

        return q_text, a_text, a_date

    # def parse_one_detail(self, id_: str):
    #     self.headers["Referer"] = "http://www.beijing.gov.cn/hudong/hdjl/com.web.search.mailList.flow"
    #     # self.headers["Proxy-Connection"] = "keep-alive"
    #     # self.headers["Upgrade-Insecure-Requests"] = "1"
    #
    #     # old_va_id = self.sess.cookies["_va_id"].split('.')
    #     # self.sess.cookies["_va_id"] = f"e79c8bab65f7135c.1637038114.1.{int(time.time())}.1637038114."
    #     # self.sess.cookies["_va_ses"] = "*"
    #     # self.sess.cookies["route"] = "74cee48a71a9ef78636a55b3fa493f67"


if __name__ == '__main__':
    spider = GovSpider()
    spider.parse()
