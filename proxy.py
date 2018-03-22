#! python3
# -*- coding: utf-8 -*-
import os
import json
import requests
import subprocess
from random import choice
from haipproxy.client.py_cli import ProxyFetcher
from headers import headers, cookies
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


args = dict(host='127.0.0.1', port=6379, password='', db=0)
fetcher = ProxyFetcher('zhihu', strategy='greedy', length=5, redis_args=args)


class Proxy(object):
    @staticmethod
    def trigger_proxy():
        base_path = os.path.abspath(os.path.dirname(__file__))
        subprocess.Popen(['py', '-3', 'run.py'], cwd='%s' % base_path)

    @staticmethod
    def get_proxy():
        five_fastest_proxy = requests.get(
            'http://127.0.0.1:8000/proxy?count=5&anonymity=anonymous&protocol=https').content
        five_fastest_proxy_list = json.loads(five_fastest_proxy)
        usable = []
        for proxy in five_fastest_proxy_list:
            proxy_ip_address = 'https://' + proxy[0] + ':' + proxy[1]
            proxies = {"https": "{}".format(proxy_ip_address)}
            weibo_test_url = 'http://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id=4151542729073845&max_id=4207260944678477&page=1&__rnd=1520929138466'
            try:
                test_status_code = requests.get(weibo_test_url, proxies=proxies, headers=headers, cookies=cookies, verify=False)
                if test_status_code == 200:
                    usable.append(proxies)
            except Exception as err:
                print(err)
        if len(usable) != 0:
            return choice(usable)
        else:
            return 0

    @staticmethod
    def weibo_get_proxy():
        proxy_list = fetcher.get_proxies()
        print(proxy_list)
        usable = []
        for i in proxy_list:
            proxy = {"http": "{}".format(i)}
            weibo_test_url = 'http://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id=4151542729073845&max_id=4207260944678477&page=1&__rnd=1520929138466'
            try:
                test_status_code = requests.get(weibo_test_url, proxies=proxy, headers=headers, cookies=cookies, verify=False, timeout=0.2).status_code
                if test_status_code == 200:
                    print(proxy)
                    usable.append(proxy)
            except Exception as err:
                pass
        if len(usable) != 0:
            return choice(usable)
        else:
            return 0


__all__ = [Proxy]