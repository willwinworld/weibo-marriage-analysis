#! python3
# -*- coding: utf-8 -*-
import json
import time
import requests
from pyquery import PyQuery as Pq
from pymongo import MongoClient
from dialogue.dumblog import dlog
from headers import headers, cookies
from proxy import Proxy
from haipproxy.client.py_cli import ProxyFetcher
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# https://weibo.com/5861369000/FlCRqC4wl?filter=hot&root_comment_id=0&type=comment#_rnd1520924660779

logger = dlog(__name__, console='debug')


CLIENT = MongoClient('localhost', 27017)
DB = CLIENT['weibo_marriage']
args = dict(host='127.0.0.1', port=6379, password='', db=0)
fetcher = ProxyFetcher('weibo', strategy='greedy', length=5, redis_args=args)


class CommentResp(object):
    """
    存储原始评论响应(按时间)
    """
    def __init__(self):
        self.base_url = 'http://weibo.com/aj/v6/comment/big?ajwvr=6&id={}&root_comment_max_id={}&page={}&__rnd={}'
        self.id = '4151542729073845'
        self.max_id = '4151542909555851'  # 一直点击页面达到的最大页面
        self.rnd = int(time.time() * 1000)
        self.session = requests.Session()

    @staticmethod
    def save(resp_res):
        collection = DB['comment_response']
        collection.insert_one(resp_res)

    def send_request(self):
        page_one_url = self.base_url.format(self.id, self.max_id, 1, self.rnd)
        page_one_resp = self.session.get(page_one_url, headers=headers, cookies=cookies, verify=False)
        page_one_resp_res = json.loads(page_one_resp.text)
        CommentResp.save(page_one_resp_res)
        current_page = page_one_resp_res['data']['page']['pagenum']  # 当前页面
        logger.info(current_page)
        total_page = int(page_one_resp_res['data']['page']['totalpage'])  # 一共有多少页
        logger.info(total_page)
        for i in range(2, total_page+1):
            logger.info(i)  # 当前页面
            page_rest_url = self.base_url.format(self.id, self.max_id, i, self.rnd)
            proxies = Proxy.get_proxy()
            logger.info(proxies)
            page_rest_resp = self.session.get(page_rest_url, headers=headers, cookies=cookies, verify=False, proxies=proxies)
            page_rest_resp_res = json.loads(page_rest_resp.text)
            CommentResp.save(page_rest_resp_res)


class CommentParser(object):
    """
    拆分原始评论,一共有71条记录, 所以设了一个默认值
    """
    def parse_resp(self, document_length=71):
        collection = DB['comment_response']
        for i in range(1, document_length+1):
            document = collection.find_one({"data.page.pagenum": i})  # 按页数顺序解析
            html = document['data']['html']
            d = Pq(html)
            block = d('.list_ul .list_li.S_line1.clearfix')
            for elem in block.items():
                comment_id = elem('.list_li.S_line1.clearfix').attr('comment_id')  # ok
                logger.info(comment_id)
                user_id = elem('.WB_text a').attr('usercard').replace('id=', '')  # ok
                logger.info(user_id)
                # user_name = elem('.WB_text a').text()  # 用户名称不固定要后续处理
                # logger.info(user_name)  # ok
                comment_content = elem('.WB_text').text().replace('\xa0', '')  # ok
                try:
                    logger.info(comment_content)
                except UnicodeEncodeError as err:
                    print('ln:99 INFO :: {}'.format(comment_content))
                comment_time = elem('.WB_from.S_txt2').text()  # ok
                logger.info(comment_time)
                up_vote_num = elem('.S_txt1 em:eq(1)').text().replace('赞', '0')  # ok
                logger.info(up_vote_num)
                result = {'comment_id': comment_id, 'user_id': user_id,
                          'comment_content': comment_content, 'comment_time': comment_time,
                          'up_vote_num': up_vote_num}
                comment_without_username = DB['comment_without_username']
                comment_without_username.insert_one(result)
            # break


class AddUserName(object):
    """
    由于评论数据缺乏稳定的用户名选择器，要去用户主页去爬取用户名，增加至mongodb中
    """
    comment_without_username = DB['comment_without_username']
    comment_with_username = DB['comment_with_username']

    def add_username(self):
        for record in self.comment_without_username.find():
            user_id = record['user_id']
            user_page_url = 'https://weibo.com/u/' + user_id
            logger.info(user_page_url)
            proxies = {"http": "{}".format(fetcher.get_proxy())}
            logger.info(proxies)
            r = requests.get(user_page_url, verify=False, headers=headers, cookies=cookies, proxies=proxies)
            r.encoding = 'utf8'  # 解决异常编码
            d = Pq(r.text)
            # print(r.text)
            user_name = d('title').text().replace('的微博_微博', '')
            logger.info(user_name)
            # result = {'comment_id': record['comment_id'], 'user_id': record['user_id'],
            #           'comment_content': record['comment_content'], 'comment_time': record['comment_time'],
            #           'up_vote_num': record['up_vote_num'], 'user_name': user_name}
            # comment_with_username = DB['comment_with_username']
            # comment_with_username.insert_one(result)
            # break


if __name__ == '__main__':
    comment_resp = CommentResp()
    comment_resp.send_request()

    # add_user_name = AddUserName()
    # add_user_name.add_username()
    # fetcher.get_proxy()
"""
comment_response: 原始响应
comment_without_username: 没有用户名的
comment_with_username: 有用户名的
"""


#     comment_resp = CommentResp()
#     comment_resp.send_request()
#     client = MongoClient('localhost', 27017)
#     db = client['weibo_marriage']
#     collection = db['comment_response']
#     # res = collection.find_one({'code': '100000'})
#     res = collection.find_one({"data.page.pagenum": 1})  # mongodb多层结构嵌套查询
#     print(res)




