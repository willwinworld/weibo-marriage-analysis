#! python3
# -*- coding: utf-8 -*-
import json
import datetime


cookie_expire_time = 23


def check_cookies_timeout(cookies):
    if cookies is None:
        return True
    print(cookies)
    print(type(cookies))
    login_time = datetime.datetime.fromtimestamp(int(cookies['LT']))
    if datetime.datetime.now() - login_time > datetime.timedelta(hours=cookie_expire_time):
        return True
    return False


# if __name__ == '__main__':
#     with open('cookie.json', 'r') as f:
#         test_cookies = f.read()
#     check_cookies_timeout(test_cookies)
#     res = check_cookies_timeout(test_cookies)
#     print(res)
__all__ = ['check_cookies_timeout']
