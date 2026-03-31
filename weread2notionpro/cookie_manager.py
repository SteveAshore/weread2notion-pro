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
    """Cookie 解析工具"""

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
    支持 CryptoJS/OpenSSL 兼容的 AES 解密（EVP_BytesToKey 密钥派生）
    
    参考实现:
    - CookieCloud 官方: https://github.com/easychen/CookieCloud
    - obsidian-weread-plugin: https://github.com/zhaohongxuan/obsidian-weread-plugin
    """

    @staticmethod
    def _evp_bytes_to_key(password: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16, 
                          iterations: int = 1, hash_func=hashlib.md5) -> tuple:
        """
        实现 OpenSSL EVP_BytesToKey 密钥派生算法
        
        这是 CryptoJS AES 加密使用的标准密钥派生方式
        
        参数:
            password: 密码字节
            salt: 盐值字节（8字节）
            key_len: 派生密钥长度（默认32字节用于AES-256）
            iv_len: 派生IV长度（默认16字节）
            iterations: 迭代次数（CryptoJS默认1）
            hash_func: 哈希函数（默认MD5）
            
        返回:
            (key, iv) 元组
        """
        derived = b''
        block = b''
        
        while len(derived) < key_len + iv_len:
            # 每次迭代：hash(前一次结果 + 密码 + 盐)
            hasher = hash_func()
            hasher.update(block + password + salt)
            block = hasher.digest()
            
            # 多轮迭代（CryptoJS默认1轮，但OpenSSL兼容模式支持更多）
            for _ in range(1, iterations):
                block = hash_func(block).digest()
                
            derived += block
            
        return derived[:key_len], derived[key_len:key_len + iv_len]

    @staticmethod
    def _decrypt_cryptojs_aes(password: str, ciphertext_b64: str) -> Optional[bytes]:
        """
        解密 CryptoJS.AES.encrypt() 加密的数据
        
        密文格式: base64("Salted__" + 8字节salt + ciphertext)
        
        参数:
            password: 解密密钥（MD5(uuid+"-"+password)[:16]）
            ciphertext_b64: base64编码的密文
            
        返回:
            解密后的原始字节数据，失败返回 None
        """
        try:
            # Base64 解码
            encrypted_data = base64.b64decode(ciphertext_b64)
            
            # 检查 Salted__ 前缀
            if len(encrypted_data) < 16 or encrypted_data[:8] != b'Salted__':
                logger.error(f'无效的密文格式，缺少 Salted__ 前缀')
                return None
                
            # 提取 salt 和实际密文
            salt = encrypted_data[8:16]
            ciphertext = encrypted_data[16:]
            
            logger.debug(f'提取到 salt: {salt.hex()}, 密文长度: {len(ciphertext)}')
            
            # 使用 EVP_BytesToKey 派生 key 和 iv
            key, iv = CookieCloudDecryptor._evp_bytes_to_key(
                password.encode('utf-8'), 
                salt,
                key_len=32,  # AES-256
                iv_len=16
            )
            
            logger.debug(f'派生密钥长度: {len(key)}, IV长度: {len(iv)}')
            
            # AES-256-CBC 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            decrypted_data = unpad(decrypted_padded, AES.block_size)
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f'AES 解密失败: {e}')
            return None

    @staticmethod
    def decrypt_cookies(uuid: str, encrypted: str, password: str) -> Optional[Dict]:
        """
        解密 CookieCloud 返回的加密数据

        加密方式（与 obsidian-weread-plugin 保持一致）:
        - 密钥 = MD5(uuid + "-" + password) 的前16个字符
        - 算法 = CryptoJS.AES (OpenSSL EVP_BytesToKey + AES-256-CBC)
        - 编码 = base64

        返回: 解密后的 Cookie 字典或 None
        """
        try:
            # 生成解密密钥（与 obsidian 插件保持一致）
            key_source = f"{uuid}-{password}"
            the_key = hashlib.md5(key_source.encode()).hexdigest()[:16]
            logger.debug(f'解密密钥: MD5({key_source})[:16] = {the_key}')

            # 使用 EVP_BytesToKey 派生方式解密（CryptoJS 兼容）
            decrypted_data = CookieCloudDecryptor._decrypt_cryptojs_aes(the_key, encrypted)
            
            if not decrypted_data:
                logger.error('CookieCloud 解密失败')
                return None
                
            logger.debug(f'AES 解密成功，数据长度: {len(decrypted_data)}')

            # 解析 JSON
            try:
                cookie_dict = json.loads(decrypted_data.decode('utf-8'))
                logger.debug(f'JSON 解析成功，域名数量: {len(cookie_dict)}')
                return cookie_dict
            except Exception as e:
                logger.error(f'JSON 解析失败: {e}')
                return None

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
        2. GET 请求加密 Cookie 数据
        3. 本地解密数据
        4. 提取 WeRead Cookie

        返回: Cookie 字符串或 None
        """
        # 验证参数
        if not self.server_url or not self.uuid or not self.password:
            logger.error('CookieCloud 配置不完整，请检查 CC_URL, CC_ID, CC_PASSWORD 环境变量')
            return None

        try:
            # 请求加密数据（使用 GET 请求，与 obsidian 插件保持一致）
            url = f"{self.server_url}/get/{self.uuid}"
            logger.debug(f'请求 CookieCloud: {url}')

            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                logger.error(f'CookieCloud 请求失败: HTTP {response.status_code}')
                return None

            data = response.json()
            logger.debug(f'CookieCloud 响应: {data.keys()}')

            # 检查返回数据格式（新格式：encrypted + 解密）
            if 'encrypted' in data:
                logger.debug('检测到加密数据，开始解密...')
                cookie_data = CookieCloudDecryptor.decrypt_cookies(
                    self.uuid,
                    data['encrypted'],
                    self.password
                )
            # 检查旧格式（直接 cookie_data）
            elif 'cookie_data' in data:
                logger.debug('检测到明文 cookie_data')
                cookie_data = data['cookie_data']
            else:
                logger.error(f'CookieCloud 响应格式不正确，可用字段: {data.keys()}')
                return None

            if not cookie_data:
                logger.error('CookieCloud 解密失败或数据为空')
                return None

            # CookieCloud 解密后的数据结构: {cookie_data: {...}, local_storage_data: {...}}
            # 实际的 cookie 数据在 cookie_data 字段中
            actual_cookie_data = cookie_data.get('cookie_data', cookie_data)
            logger.debug(f'可用域名: {list(actual_cookie_data.keys())}')

            # 提取 WeRead Cookie（匹配 weread.qq.com 结尾的域名，与 obsidian 插件保持一致）
            for domain, cookies in actual_cookie_data.items():
                if domain.endswith('weread.qq.com'):
                    cookie_str = "; ".join([
                        f"{c['name']}={c['value']}"
                        for c in cookies
                    ])
                    logger.info(f'从 CookieCloud 成功获取 {domain} 的 Cookie')
                    logger.debug(f'Cookie 数量: {len(cookies)}')
                    return cookie_str

            logger.error('CookieCloud 中未找到 weread.qq.com 的 Cookie')
            logger.debug(f'实际获取到的域名: {list(actual_cookie_data.keys())}')
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

    WEREAD_BASE_URL = "https://weread.qq.com"
    WEREAD_API_URL = "https://weread.qq.com"  # 使用与 obsidian-weread-plugin 一致的域名

    def __init__(self, cookies: Dict[str, str], timeout: int = 10):
        """
        初始化验证器

        参数:
            cookies: Cookie 字典
            timeout: 请求超时时间
        """
        self.cookies = cookies
        self.timeout = timeout

    def _parse_set_cookie(self, set_cookie_header: str) -> Dict[str, str]:
        """
        解析 Set-Cookie 响应头，提取 cookie name=value
        
        支持多个 cookie（以逗号分隔的情况）
        """
        new_cookies = {}
        if not set_cookie_header:
            return new_cookies
            
        # 处理可能包含多个 cookie 的情况
        # 注意：简单的 split(',') 可能会出问题，因为 expires 属性也包含逗号
        # 这里使用简化的解析，只提取 name=value 部分
        import re
        
        # 匹配 cookie name=value 对（在第一个分号之前）
        cookie_pattern = r'([^=;]+)=([^;]+)'
        matches = re.findall(cookie_pattern, set_cookie_header)
        
        for name, value in matches:
            name = name.strip()
            value = value.strip()
            # 只保留微信读书相关的 cookie
            if name.startswith('wr_'):
                new_cookies[name] = value
                
        return new_cookies

    def _refresh_cookie(self, session: requests.Session) -> bool:
        """
        主动刷新 Cookie（使用 wr_rt 获取新的 wr_skey）
        
        参考 obsidian-weread-plugin 的 refreshCookie 实现
        """
        try:
            logger.info('正在主动刷新 Cookie...')
            
            # 使用 HEAD 请求访问主页，检查 Set-Cookie
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
                'Cookie': CookieUtil.cookies_to_string(self.cookies)
            }
            
            resp = session.head(
                self.WEREAD_BASE_URL,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 检查 Set-Cookie
            set_cookie = resp.headers.get('set-cookie') or resp.headers.get('Set-Cookie')
            if set_cookie:
                logger.debug(f'刷新 Cookie 收到 Set-Cookie: {set_cookie[:200]}...')
                new_cookies = self._parse_set_cookie(set_cookie)
                if new_cookies:
                    self.cookies.update(new_cookies)
                    logger.info(f'Cookie 刷新成功，更新字段: {list(new_cookies.keys())}')
                    # 使用新 Cookie 重新验证
                    return self.verify_cookie_validity()
            
            # 如果 HEAD 没有返回 Set-Cookie，尝试 GET 请求
            resp = session.get(
                self.WEREAD_BASE_URL,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            set_cookie = resp.headers.get('set-cookie') or resp.headers.get('Set-Cookie')
            if set_cookie:
                logger.debug(f'GET 刷新 Cookie 收到 Set-Cookie: {set_cookie[:200]}...')
                new_cookies = self._parse_set_cookie(set_cookie)
                if new_cookies:
                    self.cookies.update(new_cookies)
                    logger.info(f'Cookie 刷新成功，更新字段: {list(new_cookies.keys())}')
                    return self.verify_cookie_validity()
            
            logger.warning('主动刷新 Cookie 未收到 Set-Cookie 响应')
            return False
            
        except Exception as e:
            logger.error(f'主动刷新 Cookie 失败: {e}')
            return False

    def verify_cookie_validity(self) -> bool:
        """
        验证 Cookie 是否有效

        通过调用 WeRead API 来验证 Cookie
        返回: True 表示有效，False 表示失效
        """
        if not self.cookies:
            logger.warning('Cookie 为空')
            return False

        # 检查关键 cookie 是否存在
        if 'wr_vid' not in self.cookies:
            logger.warning('Cookie 中缺少 wr_vid（用户ID），可能未登录')

        try:
            # 首先访问主页建立会话（某些 Cookie 需要先访问主页才能生效）
            session = requests.Session()
            cookie_str = CookieUtil.cookies_to_string(self.cookies)
            
            # 使用与浏览器一致的请求头（关键：Referer 必须正确）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://weread.qq.com/web/shelf',  # 关键：Referer 必须来自书架页面
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cookie': cookie_str
            }
            
            # 预热请求：先访问主页
            logger.debug(f'预热请求: {self.WEREAD_BASE_URL}')
            warmup_resp = session.get(
                self.WEREAD_BASE_URL,
                headers={'User-Agent': headers['User-Agent'], 'Cookie': cookie_str},
                timeout=self.timeout,
                allow_redirects=True
            )
            logger.debug(f'预热响应: HTTP {warmup_resp.status_code}')

            # 使用与 obsidian-weread-plugin 一致的验证端点
            verify_url = f"{self.WEREAD_API_URL}/api/user/notebook"
            logger.debug(f'验证 URL: {verify_url}')
            logger.debug(f'请求 Cookie 字段: {list(self.cookies.keys())}')
            
            # 打印 Cookie 字符串（脱敏）用于调试
            cookie_str = CookieUtil.cookies_to_string(self.cookies)
            logger.debug(f'Cookie 字符串长度: {len(cookie_str)}')
            
            response = session.get(
                verify_url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            logger.debug(f'验证响应状态: HTTP {response.status_code}')
            logger.debug(f'响应头: {dict(response.headers)}')
            if response.text:
                logger.debug(f'响应内容: {response.text[:500]}...')
            
            # 检查响应头中的 Set-Cookie（服务器可能返回刷新后的 Cookie）
            set_cookie_header = response.headers.get('set-cookie') or response.headers.get('Set-Cookie')
            if set_cookie_header:
                logger.debug(f'收到 Set-Cookie: {set_cookie_header[:200]}...')
                # 解析并更新 Cookie
                new_cookies = self._parse_set_cookie(set_cookie_header)
                if new_cookies:
                    self.cookies.update(new_cookies)
                    logger.info(f'从响应中刷新 Cookie，更新字段: {list(new_cookies.keys())}')
                    # 使用新 Cookie 重新验证
                    return self.verify_cookie_validity()

            if response.status_code == 200:
                data = response.json()
                # 检查是否包含有效的笔记本信息
                if data.get('books') is not None:
                    logger.info(f'Cookie 验证成功，找到 {len(data.get("books", []))} 本笔记本')
                    return True
                else:
                    errcode = data.get('errcode', 0)
                    errmsg = data.get('errmsg', '未知错误')
                    if errcode in [-2012, -2010]:
                        logger.warning(f'Cookie 已过期（错误码: {errcode}, 信息: {errmsg}）')
                    else:
                        logger.warning(f'Cookie 验证失败（错误码: {errcode}, 信息: {errmsg}）')
                    return False
            
            # 处理 401 状态码
            if response.status_code == 401:
                try:
                    data = response.json()
                    errcode = data.get('errcode', 0)
                    errmsg = data.get('errmsg', '')
                    
                    # -2013 鉴权失败：尝试主动刷新 Cookie
                    if errcode == -2013:
                        logger.warning(f'收到 -2013 鉴权失败，尝试主动刷新 Cookie...')
                        return self._refresh_cookie(session)
                    elif errcode == -2012:
                        logger.warning(f'Cookie 已过期（-2012）')
                    else:
                        logger.warning(f'Cookie 验证失败（错误码: {errcode}, 信息: {errmsg}）')
                except:
                    pass
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
        4. 回退到环境变量 WEREAD_COOKIE

        参数:
            force_refresh: 是否强制刷新

        返回: Cookie 字典或 None
        """
        # 如果已缓存且有效，直接返回
        if not force_refresh and self.cookies_dict and self.is_valid:
            logger.debug('返回已缓存的有效 Cookie')
            return self.cookies_dict

        logger.info('开始获取 Cookie...')

        # 尝试从 CookieCloud 获取
        cookie_str = self._try_get_from_cookiecloud()

        if cookie_str:
            logger.info('从 CookieCloud 获取到 Cookie')
        else:
            logger.info('CookieCloud 获取失败，尝试从环境变量获取...')
            # 如果 CookieCloud 失败，回退到环境变量
            cookie_str = os.getenv('WEREAD_COOKIE')
            if cookie_str:
                logger.info('从环境变量 WEREAD_COOKIE 获取到 Cookie')

        if not cookie_str:
            logger.error('未能获取到有效的 Cookie，请检查：\n'
                        '1. CookieCloud 配置 (CC_URL, CC_ID, CC_PASSWORD)\n'
                        '2. 环境变量 WEREAD_COOKIE')
            return None

        # 解析 Cookie
        self.cookies_dict = CookieUtil.parse_cookie_string(cookie_str)
        self.last_update_time = datetime.now()
        logger.debug(f'Cookie 解析成功，共 {len(self.cookies_dict)} 个字段')

        # 验证 Cookie 有效性
        logger.info('正在验证 Cookie 有效性...')
        validator = CookieValidator(self.cookies_dict)
        self.is_valid = validator.verify_cookie_validity()

        if self.is_valid:
            logger.info('Cookie 验证通过')
        else:
            logger.warning('Cookie 验证失败，可能已过期')

        return self.cookies_dict

    def _try_get_from_cookiecloud(self) -> Optional[str]:
        """
        尝试从 CookieCloud 获取 Cookie

        返回: Cookie 字符串或 None
        """
        # 从环境变量读取配置
        server_url = os.getenv('CC_URL', 'https://cookiecloud.malinkang.com')
        uuid = os.getenv('CC_ID')
        password = os.getenv('CC_PASSWORD')

        logger.debug(f'CookieCloud 配置: URL={server_url}, UUID={uuid[:8] if uuid else None}...')

        if not all([server_url, uuid, password]):
            missing = []
            if not server_url:
                missing.append('CC_URL')
            if not uuid:
                missing.append('CC_ID')
            if not password:
                missing.append('CC_PASSWORD')
            logger.warning(f'CookieCloud 配置不完整，缺少: {", ".join(missing)}')
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