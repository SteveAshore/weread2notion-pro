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
WEREAD_NOTEBOOKS_URL = "https://weread.qq.com/api/user/notebook"
WEREAD_BOOKMARKLIST_URL = "https://weread.qq.com/web/book/bookmarklist"
WEREAD_CHAPTER_INFO = "https://weread.qq.com/web/book/chapterInfos"
WEREAD_READ_INFO_URL = "https://weread.qq.com/web/book/readinfo"
WEREAD_REVIEW_LIST_URL = "https://weread.qq.com/web/review/list"
WEREAD_BOOK_INFO = "https://weread.qq.com/web/book/info"
WEREAD_READDATA_DETAIL = "https://weread.qq.com/web/readdata/detail"
WEREAD_HISTORY_URL = "https://weread.qq.com/web/readdata/summary?synckey=0"
WEREAD_READ_TIME_URL = "https://weread.qq.com/web/readdata"


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
    
    def get_headers(self):
        cookies = self.cookie_manager.get_cookies()

        # 根据平台选择合适的 User-Agent（与原代码一致的短 UA）
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'

        headers = {
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }

        return headers


    def get_bookshelf(self):
        """获取书架（从 /web/shelf 页面解析 window.__INITIAL_STATE__）"""
        import re
        import json
        
        self.session.get(WEREAD_URL)
        r = self.session.get("https://weread.qq.com/web/shelf")
        
        if not r.ok:
            errcode = r.json().get("errcode", 0) if r.text else 0
            self.handle_errcode(errcode)
            raise Exception(f"Could not get bookshelf {r.text}")
        
        # 从 HTML 中解析 window.__INITIAL_STATE__
        html = r.text
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', html, re.DOTALL)
        
        if not match:
            logger.error('无法从页面中解析 window.__INITIAL_STATE__')
            raise Exception("Could not parse shelf data from HTML")
        
        try:
            initial_state = json.loads(match.group(1))
            shelf_data = initial_state.get('shelf', {})
            
            # 从 booksAndArchives 提取书籍（books 和 bookProgress 可能为空）
            books_and_archives = shelf_data.get('booksAndArchives', [])
            # 过滤出书籍类型（type 为 book 或有 bookId 的项）
            books = [item for item in books_and_archives 
                     if item.get('type') == 'book' or 'bookId' in item]
            
            # 构建 bookProgress（从书籍数据中提取阅读进度）
            book_progress = []
            for book in books:
                progress = {
                    'bookId': book.get('bookId'),
                    'readingTime': book.get('readingTime', 0),
                }
                # 添加其他可能的进度字段
                if 'readUpdateTime' in book:
                    progress['readUpdateTime'] = book.get('readUpdateTime')
                if 'finishReading' in book:
                    progress['finishReading'] = book.get('finishReading')
                book_progress.append(progress)
            
            # 转换为与原来 API 一致的格式
            result = {
                'books': books,
                'archive': shelf_data.get('archive', []),
                'bookProgress': book_progress,
            }
            
            logger.info(f"成功获取书架: {len(result['books'])} 本书, {len(result['archive'])} 个分类")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f'解析 window.__INITIAL_STATE__ 失败: {e}')
            raise Exception(f"Failed to parse shelf JSON: {e}")

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

    def get_read_time_history(self, year: int = None) -> dict:
        """
        获取阅读时间历史数据
        
        参数:
            year: 年份，默认当前年
            
        返回:
            日期到阅读分钟数的字典，格式 {"2024-01-01": 30}
        """
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
            
        logger.info(f'获取 {year} 年的阅读时间历史...')
        
        try:
            # 使用正确的请求头访问阅读数据接口
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://weread.qq.com/web/shelf',
            }
            
            # 先访问主页获取有效的 session
            self.session.get(WEREAD_URL, headers=headers)
            
            # 调用阅读数据接口（使用 web 端 URL）
            r = self.session.get(WEREAD_READ_TIME_URL, headers=headers)
            
            if r.ok:
                data = r.json()
                read_times = {}
                
                # 解析阅读时间数据
                if "readTimes" in data:
                    for timestamp, seconds in data["readTimes"].items():
                        dt = datetime.fromtimestamp(int(timestamp))
                        if dt.year == year:
                            date_str = dt.strftime("%Y-%m-%d")
                            minutes = round(int(seconds) / 60.0, 2)
                            read_times[date_str] = minutes
                            
                logger.info(f'获取到 {len(read_times)} 天的阅读时间数据')
                return read_times
            else:
                errcode = r.json().get("errcode", 0)
                self.handle_errcode(errcode)
                logger.error(f'获取阅读时间历史失败: {r.text}')
                return {}
        except Exception as e:
            logger.error(f'获取阅读时间历史异常: {e}')
            return {}

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_bookmark_list(self, bookId):
        """获取书籍标注列表"""
        self.session.get(WEREAD_URL)
        r = self.session.get(WEREAD_BOOKMARKLIST_URL, params={"bookId": bookId})
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get bookmark list {r.text}")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_chapter_info(self, bookIds):
        """获取章节信息"""
        self.session.get(WEREAD_URL)
        data = {"bookIds": bookIds}
        r = self.session.post(WEREAD_CHAPTER_INFO, json=data)
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get chapter info {r.text}")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_read_info(self, bookId):
        """获取阅读信息"""
        self.session.get(WEREAD_URL)
        params = {"bookId": bookId}
        r = self.session.get(WEREAD_READ_INFO_URL, params=params)
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get read info {r.text}")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_review_list(self, bookId):
        """获取笔记列表"""
        self.session.get(WEREAD_URL)
        params = {"bookId": bookId, "listType": 11, "mine": 1, "synckey": 0}
        r = self.session.get(WEREAD_REVIEW_LIST_URL, params=params)
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get review list {r.text}")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_bookinfo(self, bookId):
        """获取书籍信息"""
        self.session.get(WEREAD_URL)
        params = {"bookId": bookId}
        r = self.session.get(WEREAD_BOOK_INFO, params=params)
        if r.ok:
            return r.json()
        else:
            errcode = r.json().get("errcode", 0)
            self.handle_errcode(errcode)
            raise Exception(f"Could not get book info {r.text}")

    def get_url(self, bookId):
        """获取书籍详情页 URL"""
        return f"https://weread.qq.com/web/reader/{bookId}"

    def get_data(self, book):
        """获取书籍完整数据（标注、笔记、章节等）"""
        book_id = book["bookId"]
        book_info = self.get_bookinfo(book_id)
        bookmark_list = self.get_bookmark_list(book_id)
        summary = bookmark_list.get("updated", [])
        reviews = self.get_review_list(book_id).get("reviews", [])
        
        # 处理章节信息
        if summary:
            chapter_info = self.get_chapter_info([book_id])
            chapter_info = chapter_info.get("data", [])
            chapter_info = chapter_info[0].get("updated", []) if chapter_info else []
        else:
            chapter_info = []
            
        return {
            "book": book,
            "book_info": book_info,
            "bookmark_list": bookmark_list,
            "summary": summary,
            "reviews": reviews,
            "chapter_info": chapter_info
        }
