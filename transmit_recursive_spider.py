#! python3
# -*- coding: utf-8 -*-
import requests
import json
import time
import re
from pymongo import MongoClient
from pyquery import PyQuery as Pq
from dialogue.dumblog import dlog
from headers import headers, cookies
from decorators import pipe
from redis_queue import RedisQueue
from check_cookie import check_cookies_timeout
from login import execute
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logger = dlog(__name__, console='debug')


CLIENT = MongoClient('localhost', 27017)
DB = CLIENT['weibo_marriage']


class CommentRecursive(object):
    """
    寻找转发数不为0的评论，开始递归抓取
    核心递归树算法
    """
    def __init__(self):
        self.base_url = 'http://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id={}&page={}&__rnd={}'
        self.rnd = int(time.time() * 1000)

    def requester(self, father_mid, page_num):
        """
        发请求模块
        方便后续递归操作
        :return:
        """
        transmit_url = self.base_url.format(father_mid, page_num, self.rnd)
        logger.info(transmit_url)
        try:
            if check_cookies_timeout(cookies):
                # 如果cookie过期，需要重新登录
                execute()
            r = requests.get(transmit_url, verify=False, headers=headers, cookies=cookies, timeout=4)
            logger.info(r.status_code)
            r.encoding = 'utf8'
            resp_res = json.loads(r.text)
            return resp_res
        except TimeoutError as err:
            exception_url_queue = RedisQueue('exception_url', host='127.0.0.1', port='6379', password='', db=1)
            exception_url_queue.put(transmit_url)
            # 异常返回值
            return -1

    def parser(self, father_mid, resp_res, path=None):
        """
        转发信息解析模块
        :return:
        """
        html = resp_res['data']['html']
        current_page = int(resp_res['data']['page']['pagenum'])
        dollar = Pq(html)
        block = dollar('.list_li.S_line1.clearfix')
        result = []
        for elem in block.items():
            elem_outer_html = elem.outer_html()
            elem_outer_d = Pq(elem_outer_html)
            mid = elem_outer_d('.list_li.S_line1.clearfix').attr('mid')  # mid_id, 唯一标识
            logger.info(mid)
            user_id = re.findall(r'\d+', elem('.WB_face.W_fl a img').attr('usercard'))[0]  # user_id, 用户id
            logger.info(user_id)
            user_name = elem('.WB_text a:eq(0)').text().replace('\xa1', '').replace(' ¡ 查看图片', '')  # user_name
            logger.info(user_name)
            comment = elem('.WB_text span').text().replace('\xa0', '').replace('\xa1', '').replace('\xb4', '').replace(
                '\U0001f643', '').replace('U0001f644', '').replace('U0001f64a', '').replace('\U0001f649', '').replace(
                '\U0001f937', '').replace('\u1d98', '').replace('\u200d', '').replace('\ufe0f', '').replace(
                '\U0001f64a', '').replace('\U0001f644', '').replace('\u1d52', '')  # 转发评论
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
                transmit_url = re.findall('url=.+&mid', elem(
                    '.WB_func.clearfix .WB_handle.W_fr .clearfix li:eq(1) .line.S_line1 .S_txt1').attr('action-data'))[
                                   0].replace('url=', '').replace('&mid',
                                                                  '') + '?type=repost'
            logger.info(transmit_url)
            logger.info(relay_num)
            like_num = 0  # 点赞数
            like_list = re.findall(r'\d+', elem(
                '.WB_func.clearfix .WB_handle.W_fr .clearfix li:eq(2) .line.S_line1 a span em:eq(1)').text())  # 点赞数
            if len(like_list) != 0:
                like_num = like_list[0]
            logger.info(like_num)
            if path:
                propagate_path = path + mid + "->"
            else:
                propagate_path = "{}".format(father_mid) + "->" + "{}".format(mid) + "->"
            single_result = {'mid': int(mid), 'user_id': int(user_id), 'user_name': user_name, 'comment': comment,
                             'comment_time': comment_time, 'relay_num': int(relay_num), 'like_num': int(like_num),
                             'comment_img_src': comment_img_src, 'current_page': int(current_page),
                             'transmit_url': transmit_url, 'father_mid': int(father_mid),
                             'path': propagate_path}
            result.append(single_result)
        return result

    def gather(self, father_mid, path=None):
        """
        合并模块，第一页和剩余页面的内容
        方便后续递归操作
        :return:
        """
        total_result = []
        resp_page_one = self.requester(father_mid, 1)  # 第一页的原始内容
        if resp_page_one != -1:
            result_page_one = self.parser(father_mid, resp_page_one, path=path)  # 第一页的解析内容
            total_result.extend(result_page_one)
            total_page = int(resp_page_one['data']['page']['totalpage'])
            if total_page > 1:
                for index in range(2, total_page+1):
                    rest_resp_res = self.requester(father_mid, index)
                    if rest_resp_res != -1:
                        result_page_rest = self.parser(father_mid, rest_resp_res, path=path)
                        total_result.extend(result_page_rest)
            logger.info(total_result)
            return total_result

    @staticmethod
    def save(resp_res):
        collection = DB['transmit_comment']
        collection.insert_one(resp_res)
        logger.info('saving')

    def root_insert(self):
        """
        寻找根评论中有转发的数据，并放到redis队列中，叫root, 里面全是有转发的字典
        :return:
        """
        collection = DB['transmit_comment']
        test_root_res = collection.find_one({"mid": "4153419340041267"})  # 11个人转发的
        # test_root_res = collection.find_one({"mid": "4152039828718852"})  # 700多个人转发的
        logger.info(test_root_res)
        root = RedisQueue('root', host='127.0.0.1', port='6379', password='', db=1)
        root.put({'mid': test_root_res['mid'], 'user_id': test_root_res['user_id'], 'user_name': test_root_res['user_name'],
                  'comment': test_root_res['comment'], 'comment_time': test_root_res['comment_time'], 'relay_num': test_root_res['relay_num'],
                  'like_num': test_root_res['like_num'], 'comment_img_src': test_root_res['comment_img_src'], 'current_page': test_root_res['current_page'],
                  'transmit_url': test_root_res['transmit_url']})

        # collection = DB['transmit_comment']
        # root = RedisQueue('root', host='127.0.0.1', port='6379', password='', db=1)
        # transmit_res = collection.find({'relay_num': {'$gt': '0'}})
        # for i in transmit_res:
        #     logger.info(i)
        #     root.put({'mid': i['mid'], 'user_id': i['user_id'], 'user_name': i['user_name'], 'comment': i['comment'],
        #               'comment_time': i['comment_time'], 'relay_num': i['relay_num'], 'like_num': i['like_num'],
        #               'comment_img_src': i['comment_img_src'], 'current_page': i['current_page'],
        #               'transmit_url': i['transmit_url']})
            # break

    @pipe('root')
    def res_insert(self, param):
        """
        1. 从redis root队列中取出一个元素，存储一份到中间middle队列, db = 1
        2. 然后开始对转发链接进行解析，将结果放到res队列, db = 1
        3. 每次转发的结果都会放到res结果队列，每次都要遍历一遍转发结果队列
        :return:
        """
        root = RedisQueue('root', host='127.0.0.1', port='6379', password='', db=1)
        derivative = DB['transmit_comment_derivative']
        father_mid = param['mid']  # 从root队列里拿的元素肯定都是有转发的
        if 'path' in param:  # 如果是已经转发过一次的，应该有path, 要在原来的path基础上来继续增加
            logger.info(param['path'])
            derive_result = self.gather(father_mid, path=param['path'])  # 从有转发的产生出的结果
        else:
            derive_result = self.gather(father_mid)  # 从有转发的产生出的结果
        for element in derive_result:
            derivative.insert(element)  # 衍生出来的评论全部要放到数据库中
            element_relay_num = int(element['relay_num'])
            if element_relay_num != 0:
                root.put(
                    {'mid': element['mid'], 'user_id': element['user_id'],
                     'user_name': element['user_name'], 'comment': element['comment'],
                     'comment_time': element['comment_time'], 'relay_num': element['relay_num'],
                     'like_num': element['like_num'], 'comment_img_src': element['comment_img_src'],
                     'current_page': element['current_page'], 'transmit_url': element['transmit_url'],
                     'father_mid': element['father_mid'], 'path': element['path']})


if __name__ == '__main__':
    comment_recursive = CommentRecursive()
    comment_recursive.root_insert()
    comment_recursive.res_insert()
