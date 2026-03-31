import hashlib
import json
import os
import re
import logging

import requests
from requests.utils import cookiejar_from_dict
from retrying import retry
from urllib.parse import quote
from dotenv import load_dotenv

# ✅ 新增导入
from weread2notionpro.cookie_manager import CookieManager, CookieUtil

load_dotenv()

logger = logging.getLogger(__name__)

WEREAD_URL = "https://weread.qq.com/"
WEREAD_NOTEBOOKS_URL = "https://i.weread.qq.com/user/notebooks"
WEREAD_BOOKMARKLIST_URL = "https://i.weread.qq.com/book/bookmarklist"
WEREAD_CHAPTER_INFO = "https://i.weread.qq.com/book/chapterInfos"
WEREAD_READ_INFO_URL = "https://i.weread.qq.com/book/readinfo"
WEREAD_REVIEW_LIST_URL = "https://i.weread.qq.com/review/list"
WEREAD_BOOK_INFO = "https://i.weread.qq.com/book/info"
WEREAD_READDATA_DETAIL = "https://i.weread.qq.com/readdata/detail"
WEREAD_HISTORY_URL = "https://i.weread.qq.com/readdata/summary?synckey=0"


class WeReadApi:
    def __init__(self):
        # ✅ 使用新的 Cookie 管理器
        self.cookie_manager = CookieManager()
        self.cookie = self.cookie_manager.get_cookies_string()
        self.session = requests.Session()
        self.session.cookies = self.cookie_manager.get_cookiejar()

    # ✅ 删除旧的 try_get_cloud_cookie、get_cookie、parse_cookie_string 方法

    def refresh_cookie(self) -> bool:
        """
        刷新 Cookie

        返回: True 表示 Cookie 有效，False 表示失效
        """
        logger.info('开始刷新 Cookie...')

        # 强制从 CookieCloud 获取新 Cookie
        cookies = self.cookie_manager.get_cookies(force_refresh=True)

        if not cookies:
            logger.error('无法获取新 Cookie')
            return False

        # 更新 cookie 字符串
        self.cookie = self.cookie_manager.get_cookies_string()

        # 更新 session
        self.session.cookies = self.cookie_manager.get_cookiejar()

        # 验证 Cookie 有效性
        if self.cookie_manager.is_cookie_valid():
            logger.info('Cookie 刷新成功')
            return True
        else:
            logger.warning('刷新后的 Cookie 仍然无效')
            return False

    def get_bookshelf(self):
        self.session.get(WEREAD_URL)
        r = self.session.get(
            "<https://i.weread.qq.com/shelf/sync?synckey=0&teenmode=0&album=1&onlyBookid=0>"
        )
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get bookshelf {r.text}")

    def handle_errcode(self, errcode):
        """处理 WeRead API 错误码"""
        if errcode in [-2012, -2010]:
            # Cookie 过期
            logger.error('微信读书 Cookie 过期了，开始自动刷新...')
            if self.refresh_cookie():
                logger.info('Cookie 刷新成功，请重试')
            else:
                print(f"::error::微信读书Cookie过期了，无法自动刷新。请参考文档重新设置。"
                      f"<https://mp.weixin.qq.com/s/B_mqLUZv7M1rmXRsMlBf7A>")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_notebooklist(self):
        """获取笔记本列表"""
        self.session.get(WEREAD_URL)
        r = self.session.get(WEREAD_NOTEBOOKS_URL)
        if r.ok:
            data = r.json()
            books = data.get("books")
            books.sort(key=lambda x: x["sort"])
            return books
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get notebook list {r.text}")

    # ... 其他方法保持不变 ...