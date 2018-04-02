#! python3
# -*- coding: utf-8 -*-
import re
import json
import time
import requests
import redis
from pyquery import PyQuery as Pq
from pymongo import MongoClient
from dialogue.dumblog import dlog
from headers import headers, cookies
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# https://weibo.com/5861369000/FlCRqC4wl?type=repost#_rnd1520924717136

logger = dlog(__name__, console='debug')


CLIENT = MongoClient('localhost', 27017)
DB = CLIENT['weibo_marriage']


class CommentTransmit(object):
    """
    存储原始76页数据
    """
    def __init__(self):
        self.base_url = 'http://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id={}&max_id={}&page={}&__rnd={}'
        self.id = '4151542729073845'
        self.max_id = '4207260944678477'
        self.page = 76  # 一共有76页
        self.rnd = int(time.time() * 1000)
        self.session = requests.Session()

    @staticmethod
    def save(resp_res):
        collection = DB['transmit_response']
        collection.insert_one(resp_res)
        logger.info('saving')

    def send_request(self):
        for i in range(1, self.page+1):
            logger.info('current page: {}'.format(i))
            url = self.base_url.format(self.id, self.max_id, i, self.rnd)
            logger.info(url)
            r = requests.get(url, verify=False, headers=headers, cookies=cookies)
            r.encoding = 'utf8'
            url_resp_res = json.loads(r.text)
            CommentTransmit.save(url_resp_res)
            # break


class CommentParser(object):
    """
    拆分原始评论
    """
    @staticmethod
    def save(resp_res):
        collection = DB['transmit_comment']
        collection.insert_one(resp_res)
        logger.info('saving')

    def parse_resp(self):
        collection = DB['transmit_response']
        logger.info(collection.count())
        document_length = collection.count()
        for i in range(1, document_length+1):
            logger.info(i)
            document = collection.find_one({"data.page.pagenum": i})  # 按页数顺序解析
            html = document['data']['html']
            dollar = Pq(html)
            block = dollar('.list_li.S_line1.clearfix')
            for elem in block.items():
                elem_outer_html = elem.outer_html()
                elem_outer_d = Pq(elem_outer_html)
                mid = elem_outer_d('.list_li.S_line1.clearfix').attr('mid')  # mid_id, 唯一标识
                logger.info(mid)
                user_id = re.findall(r'\d+', elem('.WB_face.W_fl a img').attr('usercard'))[0]  # user_id, 用户id
                logger.info(user_id)
                user_name = elem('.WB_text a:eq(0)').text().replace('\xa1', '').replace(' ¡ 查看图片', '')  # user_name
                logger.info(user_name)
                comment = elem('.WB_text span').text().replace('\xa0', '').replace('\xa1', '').replace('\xb4', '').replace('\U0001f643', '').replace('U0001f644', '').replace('U0001f64a', '').replace('\U0001f649', '').replace('\U0001f937', '').replace('\u1d98', '').replace('\u200d', '').replace('\ufe0f', '').replace('\U0001f64a', '').replace('\U0001f644', '').replace('\u1d52', '')  # 转发评论
                logger.info(comment)
                comment_img_src = [i.attr('src') for i in elem('.WB_text span img').items()]  # 评论表情url, 这个url可能决定了情感倾向
                logger.info(comment_img_src)
                comment_time = elem('.WB_from.S_txt2').text()  # 转发时间
                logger.info(comment_time)
                transmit_url = ''
                relay_num = 0  # 转发数
                relay_list = re.findall(r'\d+', elem(
                    '.WB_func.clearfix .WB_handle.W_fr .clearfix li:eq(1) .line.S_line1 .S_txt1').text())  # 转发数
                if len(relay_list) != 0:
                    relay_num = relay_list[0]
                    transmit_url = re.findall('url=.+&mid', elem('.WB_func.clearfix .WB_handle.W_fr .clearfix li:eq(1) .line.S_line1 .S_txt1').attr('action-data'))[0].replace('url=', '').replace('&mid', '') + '?type=repost'  # 如果有转发，就要将转发链接抓下来，但是这只是第一层原本的评论的链接，还没有进行递归
                logger.info(transmit_url)
                logger.info(relay_num)
                like_num = 0  # 点赞数
                like_list = re.findall(r'\d+', elem(
                    '.WB_func.clearfix .WB_handle.W_fr .clearfix li:eq(2) .line.S_line1 a span em:eq(1)').text())  # 点赞数
                if len(like_list) != 0:
                    like_num = like_list[0]
                logger.info(like_num)
                result = {'mid': mid, 'user_id': user_id, 'user_name': user_name, 'comment': comment,
                          'comment_time': comment_time, 'relay_num': relay_num, 'like_num': like_num,
                          'comment_img_src': comment_img_src, 'current_page': i, 'transmit_url': transmit_url}
                CommentParser.save(result)
                # break
            # break


if __name__ == '__main__':
    comment_transmit = CommentTransmit()
    comment_transmit.send_request()
    comment_parser = CommentParser()
    comment_parser.parse_resp()


