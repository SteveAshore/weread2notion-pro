"""
WeRead Cookie 管理模块
支持 CookieCloud 获取、AES 解密、自动验证和刷新
"""

import hashlib
import json
import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import quote, unquote
from datetime import datetime

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from requests.utils import cookiejar_from_dict

logger = logging.getLogger(__name__)


@dataclass
class Cookie:
    """Cookie 对象"""
    name: str
    value: str


class CookieUtil:
    """Cookie 解析��具"""

    @staticmethod
    def parse_cookie_string(cookie_string: str) -> Dict[str, str]:
        """
        解析 Cookie 字符串为字典

        示例:
            "wr_name=user; wr_vid=123" -> {"wr_name": "user", "wr_vid": "123"}
        """
        if not cookie_string:
            return {}

        cookies_dict = {}
        pairs = cookie_string.split(';')

        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = unquote(key.strip())
                value = unquote(value.strip())
                cookies_dict[key] = value

        return cookies_dict

    @staticmethod
    def parse_cookies_to_list(cookie_string: str) -> List[Cookie]:
        """
        解析 Cookie 字符串为 Cookie 对象列表
        """
        cookies_dict = CookieUtil.parse_cookie_string(cookie_string)
        return [Cookie(name=k, value=v) for k, v in cookies_dict.items()]

    @staticmethod
    def cookies_to_string(cookies: Dict[str, str]) -> str:
        """
        将 Cookie 字典转换为字符串
        """
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])


class CookieCloudDecryptor:
    """
    CookieCloud 解密器
    支持 AES-128-CBC 解密（MD5 密钥模式）
    """

    @staticmethod
    def decrypt_cookies(uuid: str, encrypted: str, password: str) -> Optional[Dict]:
        """
        解密 CookieCloud 返回的加密数据

        加密方式:
        - 密钥 = MD5(uuid + "-" + password) 的前16个字符
        - 算法 = AES-128-CBC
        - 编码 = base64

        返回: 解密后的 Cookie 字典或 None
        """
        try:
            # 生成解密密钥
            key_source = f"{uuid}-{password}"
            md5_hash = hashlib.md5(key_source.encode()).hexdigest()
            key = md5_hash[:16].encode()  # 取前16个字符

            # Base64 解码
            encrypted_data = base64.b64decode(encrypted)

            # 提取 IV 和密文
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]

            # AES 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

            # 解析 JSON
            cookie_dict = json.loads(decrypted_data.decode('utf-8'))

            logger.debug('CookieCloud 解密成功')
            return cookie_dict

        except Exception as e:
            logger.error(f'CookieCloud 解密失败: {e}')
            return None


class CookieCloudFetcher:
    """
    从 CookieCloud 服务器获取 Cookie
    """

    def __init__(self, server_url: str, uuid: str, password: str, timeout: int = 10):
        """
        初始化 CookieCloud 获取器

        参数:
            server_url: CookieCloud 服务器地址
            uuid: 用户 UUID
            password: 端对端加密密码
            timeout: 请求超时时间（秒）
        """
        self.server_url = server_url.rstrip('/')
        self.uuid = uuid
        self.password = password
        self.timeout = timeout

    def fetch_cookie_from_cloud(self) -> Optional[str]:
        """
        从 CookieCloud 获取 WeRead Cookie

        流程:
        1. 验证参数完整性
        2. 请求加密 Cookie 数据
        3. 解密数据
        4. 提取 WeRead Cookie

        返回: Cookie 字符串或 None
        """
        # 验证参数
        if not self.server_url or not self.uuid or not self.password:
            logger.error('CookieCloud 配置不完整')
            return None

        try:
            # 请求加密数据（支持两种请求方式）
            url = f"{self.server_url}/get/{self.uuid}"

            # 方式1: POST 请求（带密码在数据中）
            response = requests.post(
                url,
                data={'password': self.password},
                timeout=self.timeout
            )

            if response.status_code != 200:
                # 方式2: GET 请求（如果 POST 失败）
                response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                logger.error(f'CookieCloud 请求失败: {response.status_code}')
                return None

            data = response.json()

            # 检查返回数据格式（新格式：encrypted + 解密）
            if 'encrypted' in data:
                cookie_data = CookieCloudDecryptor.decrypt_cookies(
                    self.uuid,
                    data['encrypted'],
                    self.password
                )
            # 检查旧格式（直接 cookie_data）
            elif 'cookie_data' in data:
                cookie_data = data['cookie_data']
            else:
                logger.error('CookieCloud 响应格式不正确')
                return None

            if not cookie_data:
                return None

            # 提取 WeRead Cookie
            for domain, cookies in cookie_data.items():
                if 'weread' in domain.lower():
                    cookie_str = "; ".join([
                        f"{c['name']}={c['value']}"
                        for c in cookies
                    ])
                    logger.info('从 CookieCloud 成功获取 Cookie')
                    return cookie_str

            logger.error('CookieCloud 中未找到 WeRead Cookie')
            return None

        except requests.RequestException as e:
            logger.error(f'CookieCloud 请求异常: {e}')
            return None
        except Exception as e:
            logger.error(f'获取 CookieCloud Cookie 异常: {e}')
            return None


class CookieValidator:
    """
    Cookie 有效性验证器
    """

    WEREAD_BASE_URL = "<https://weread.qq.com>"
    WEREAD_API_URL = "<https://i.weread.qq.com>"

    def __init__(self, cookies: Dict[str, str], timeout: int = 10):
        """
        初始化验证器

        参数:
            cookies: Cookie 字典
            timeout: 请求超时时间
        """
        self.cookies = cookies
        self.timeout = timeout

    def verify_cookie_validity(self) -> bool:
        """
        验证 Cookie 是否有效

        通过调用 WeRead API 来验证 Cookie
        返回: True 表示有效，False 表示失效
        """
        if not self.cookies:
            logger.warning('Cookie 为空')
            return False

        try:
            # 验证端点：获取笔记本列表
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': self.WEREAD_BASE_URL,
                'Cookie': CookieUtil.cookies_to_string(self.cookies)
            }

            response = requests.get(
                f"{self.WEREAD_API_URL}/user/notebooks",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                # 检查是否包含有效的笔记本信息
                if data.get('books') is not None:
                    logger.info('Cookie 验证成功')
                    return True
                else:
                    errcode = data.get('errcode', 0)
                    if errcode in [-2012, -2010]:
                        logger.warning('Cookie 已过期（错误码: %s）', errcode)
                    return False

            logger.warning(f'Cookie 验证返回状态码: {response.status_code}')
            return False

        except requests.RequestException as e:
            logger.error(f'Cookie 验证请求异常: {e}')
            return False
        except Exception as e:
            logger.error(f'Cookie 验证异常: {e}')
            return False


class CookieManager:
    """
    Cookie 管理主类
    集成获取、解密、验证、存储等功能
    """

    def __init__(self):
        """初始化 Cookie 管理器"""
        self.cookies_dict: Optional[Dict[str, str]] = None
        self.last_update_time: Optional[datetime] = None
        self.is_valid: bool = False

    def get_cookies(self, force_refresh: bool = False) -> Optional[Dict[str, str]]:
        """
        获取 Cookie

        优先级:
        1. 如果 force_refresh=True，强制刷新
        2. 如果已缓存且有效，直接返回
        3. 尝试从 CookieCloud 获取
        4. 回退到环境变量

        参数:
            force_refresh: 是否强制刷新

        返回: Cookie 字典或 None
        """
        # 如果已缓存且有效，直接返回
        if not force_refresh and self.cookies_dict and self.is_valid:
            logger.debug('返回已缓存的有效 Cookie')
            return self.cookies_dict

        # 尝试从 CookieCloud 获取
        cookie_str = self._try_get_from_cookiecloud()

        # 如果 CookieCloud 失败，回退到环境变量
        if not cookie_str:
            cookie_str = os.getenv('WEREAD_COOKIE')

        if not cookie_str:
            logger.error('未能获取到有效的 Cookie')
            return None

        # 解析 Cookie
        self.cookies_dict = CookieUtil.parse_cookie_string(cookie_str)
        self.last_update_time = datetime.now()

        # 验证 Cookie 有效性
        validator = CookieValidator(self.cookies_dict)
        self.is_valid = validator.verify_cookie_validity()

        if not self.is_valid:
            logger.warning('获取的 Cookie 无效')

        return self.cookies_dict

    def _try_get_from_cookiecloud(self) -> Optional[str]:
        """
        尝试从 CookieCloud 获取 Cookie

        返回: Cookie 字符串或 None
        """
        server_url = os.getenv('CC_URL', '<https://cookiecloud.malinkang.com>')
        uuid = os.getenv('CC_ID')
        password = os.getenv('CC_PASSWORD')

        if not all([server_url, uuid, password]):
            logger.debug('CookieCloud 配置不完整，跳过')
            return None

        fetcher = CookieCloudFetcher(server_url, uuid, password)
        return fetcher.fetch_cookie_from_cloud()

    def is_cookie_valid(self) -> bool:
        """
        检查 Cookie 是否有效
        """
        if not self.cookies_dict:
            return False

        validator = CookieValidator(self.cookies_dict)
        self.is_valid = validator.verify_cookie_validity()
        return self.is_valid

    def get_cookies_string(self) -> str:
        """获取 Cookie 字符串"""
        if not self.cookies_dict:
            self.get_cookies()

        if not self.cookies_dict:
            return ""

        return CookieUtil.cookies_to_string(self.cookies_dict)

    def get_cookiejar(self):
        """
        获取 requests 库需要的 cookiejar 对象
        """
        if not self.cookies_dict:
            self.get_cookies()

        if not self.cookies_dict:
            return cookiejar_from_dict({})

        return cookiejar_from_dict(self.cookies_dict)