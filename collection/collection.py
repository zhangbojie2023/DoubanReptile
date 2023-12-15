import requests
import re
from fake_useragent import UserAgent
import logging
from proxy import Proxy
import utils
import config as cfg
import bs4

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DOUBAN_MOVIE_SHORT_COMMENT = "douban_movie_short_comment"


class Collection:
    _PAGE_LIMIT = 120

    _MAX_COMMENT_TOTAL = 600

    def __init__(self, m_id: str, proxy: Proxy):

        if m_id is None:
            raise ValueError("movie_id is none, collection over.")

        if proxy is None:
            raise ValueError("proxy is none, collection over.")

        self._proxy = proxy

        self._movie_id = m_id

        self.collections = cfg.get_mongo_database()[DOUBAN_MOVIE_SHORT_COMMENT]

        self._page_base_url = "https://movie.douban.com/subject/{}/comments?percent_type=&start={}&limit={}&status=P&sort=new_score&comments_only=1&ck=YCHn"

        self._start_url = "https://movie.douban.com/subject/{}/comments?status=P"

        self._pattern = re.compile(r'看过\((\d*)\)')

        self._ua = UserAgent()

        self._page_urls = []

        self._comment_total = self._get_comment_total()

        self._initial_page_urls()

    # 定义一个函数，用于获取评论总数，返回类型为int
    def _get_comment_total(self):

        start_url = self._start_url.format(self._movie_id)

        # 输出提示信息
        logging.info(f"start to get comment total, start_url is {start_url}")

        # 设置请求头
        headers = {
            "User-Agent": self._ua.random,
        }
        # 发起get请求
        resp = requests.get(start_url, headers=headers)

        # 如果请求状态码不是200，则输出警告信息，并抛出ValueError异常
        if resp.status_code != 200:
            raise ValueError(f"get comment total failed, status_code is {resp.status_code}")

        # 如果响应内容为空，则输出警告信息，并抛出ValueError异常
        if resp.text is None:
            logging.warning("get comment total failed, response content is none")
            raise ValueError("get comment total failed, response content is none")

        # 使用正则表达式搜索响应内容
        res = self._pattern.search(resp.text)

        # 如果搜索失败，则输出警告信息，并抛出ValueError异常
        if res is None:
            logging.warning("get comment total failed, pattern search failed")
            raise ValueError("get comment total failed, pattern search failed")

        # 将搜索到的结果转换为int类型
        comment_total = int(res.group(1))

        comment_total = comment_total if comment_total <= self._MAX_COMMENT_TOTAL else self._MAX_COMMENT_TOTAL

        # 输出提示信息
        logging.info(f"get comment total is {comment_total}")

        # 返回评论总数
        return comment_total

    # 定义_initial_page_urls函数，用于初始化所有页面的url
    def _initial_page_urls(self):

        # 判断comment_total是否为空或者小于等于0
        if self._comment_total is None or self._comment_total <= 0:
            logging.warning("comment total is none or lt zero. ")
            raise ValueError("comment total is none or lt zero. ")

        # 打印comment_total的值
        logging.info(f"comment total is {self._comment_total}, calculate and initial all page url. ")

        # 判断comment_total是否小于page_limit
        if self._comment_total <= self._PAGE_LIMIT:
            for_count = 1
        else:
            # 计算page_urls的个数
            if self._comment_total % self._PAGE_LIMIT == 0:
                for_count = int(self._comment_total / self._PAGE_LIMIT)
            else:
                for_count = int(self._comment_total % self._PAGE_LIMIT) + 1

        # 打印page_urls的个数
        logging.info(f"page url count is {for_count}")

        # 遍历page_urls的个数
        for i in range(for_count):
            # 计算每一页的url
            page_url = self._page_base_url.format(self._movie_id, (i * self._PAGE_LIMIT), self._PAGE_LIMIT)
            # 打印每一页的url
            logging.info(f"append {page_url} to page url list. ")
            # 将每一页的url添加到page_urls列表中
            self._page_urls.append(page_url)

    def _pull_page_url(self):
        return self._page_urls.pop()

    def collection(self):

        headers = {
            "User-Agent": self._ua.random,
            "Cookies": f"bid={utils.random_string(11)}"
        }

        contents = []

        for page_url in self._page_urls:

            logging.info(f"start collection {page_url} is html")

            resp = requests.get(url=page_url, headers=headers, proxies=self._proxy.get_proxies())

            if resp.status_code != 200:
                logging.warning(f"collection {page_url} html failed, status_code is {resp.status_code}")
                continue

            if resp.json() is None or resp.json()['html'] is None:
                logging.warning(f"collection {page_url} html failed, data is None")
                continue

            contents.append({
                "page": page_url,
                "html": resp.json()['html']
            })

        for c in contents:
            soup = bs4.BeautifulSoup(c['html'], "lxml")
            spans = soup.find_all("span", class_="short")
            for span in spans:
                self.collections.insert_one({
                    "mid": self._movie_id,
                    "page": c['page'],
                    "comment": span.string
                })

        logging.info(f"collection {self._movie_id} data and into database success")
