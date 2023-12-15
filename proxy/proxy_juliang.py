import hashlib
import logging
import copy

import requests

from .proxy import Proxy

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class ProxyJuliang(Proxy):
    # 获取代理IP接口
    __GET_IP_API = "http://v2.api.juliangip.com/dynamic/getips"
    # 校验代理IP接口
    __CHECK_IP_API = "http://v2.api.juliangip.com/dynamic/check"

    __PARAMS_KEY_TRADE_NO = "trade_no"

    __PARAMS_KEY_NUM = "num"

    __PARAMS_KEY_KEY = "key"

    def __init__(self, username: str, password: str, params: dict):
        super().__init__()

        if username is None or len(username.strip()) == 0:
            raise ValueError("username is none")

        self.username = username

        if password is None or len(password.strip()) == 0:
            raise ValueError("password is none")

        self.password = password

        if params is None:
            raise ValueError("params is none")

        if params.get(self.__PARAMS_KEY_TRADE_NO) is None:
            raise ValueError(f"params {self.__PARAMS_KEY_TRADE_NO} is none")

        if params.get(self.__PARAMS_KEY_KEY) is None:
            raise ValueError(f"params {self.__PARAMS_KEY_KEY} is none")

        if params.get(self.__PARAMS_KEY_NUM) is None:
            raise ValueError(f"params {self.__PARAMS_KEY_NUM} is none")

        self.params = params

        self.__key = self.params.get(self.__PARAMS_KEY_KEY)

        self.__current_proxy_ip = ""

    def __get_proxy_ip(self):

        if self.__current_proxy_ip is not None and len(self.__current_proxy_ip) != 0:
            # __current_ip is not None
            if self.__check_proxy_ip(self.__current_proxy_ip):
                # check proxy ip, if check is True, return current proxy ip
                return self.__current_proxy_ip

        logging.info("get juliang proxy ip not use, request new proxy ip")

        copy_params = copy.deepcopy(self.params)
        del copy_params[self.__PARAMS_KEY_KEY]
        p_str = self.__get_request_params(copy_params)
        copy_params["sign"] = self.__md5(p_str)

        logging.info(f"start to get juliang proxy ip, url is {self.__GET_IP_API}")

        resp = requests.get(self.__GET_IP_API, params=copy_params)

        if resp.status_code != 200:
            raise ValueError(f"get juliang proxy ip failed, status_code is {resp.status_code}")

        if resp.headers.get('Content-Type') == 'application/json':
            if resp.json()['code'] != 200:
                raise ValueError(f"get juliang proxy ip failed, code is {resp.json()['code']}")

        self.__current_proxy_ip = resp.text

        logging.info(f"get juliang proxy ip success, proxy ip is {self.__current_proxy_ip}")

    def __check_proxy_ip(self, _proxy_ip: str) -> bool:

        _params = {
            'trade_no': self.params[self.__PARAMS_KEY_TRADE_NO],
            'proxy': _proxy_ip
        }
        _params['sign'] = self.__md5(self.__get_request_params(_params))

        logging.info(f"start to check proxy ip, url is {self.__GET_IP_API}")

        resp = requests.post(self.__CHECK_IP_API, params=_params)
        if resp.status_code != 200:
            raise ValueError(f"check proxy ip failed, status_code is {resp.status_code}")
        if resp.json() is None or resp.json()['data'] is None:
            raise ValueError(f"check proxy ip failed, data is None")

        use = resp.json()['data'][_proxy_ip]

        logging.info(f"check proxy ip success, {_proxy_ip} is {use}")

        return use

    # 110.82.167.3:41072
    def get_proxies(self) -> dict:
        self.__get_proxy_ip()
        return {
            'http': "http://{}:{}@{}".format(self.username, self.password, self.__current_proxy_ip),
            'https': "http://{}:{}@{}".format(self.username, self.password, self.__current_proxy_ip),
        }

    def __get_request_params(self, _params: dict) -> str:
        sorted_keys = sorted(_params.keys())
        return '&'.join([f'{k}={_params[k]}' for k in sorted_keys])

    def __md5(self, p_str: str) -> str | None:
        if len(p_str.strip()) == 0:
            raise ValueError("p_str is empty")
        nps = f"{p_str}&key={self.__key}"
        md5 = hashlib.md5(nps.encode('UTF-8'))
        return md5.hexdigest()
