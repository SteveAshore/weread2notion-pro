# CookieCloud 加密解密原理

## 概述

CookieCloud 使用 **CryptoJS** 库进行 AES 加密，Python 端需要正确实现解密才能获取 Cookie 数据。

## 加密流程

### 1. 密钥生成

```javascript
const the_key = CryptoJS.MD5(uuid + '-' + password).toString().substring(0, 16);
```

- 输入：UUID 和密码
- 处理：`MD5(uuid + "-" + password)`
- 输出：取前 16 个字符作为加密密钥

### 2. 数据加密

```javascript
const encrypted = CryptoJS.AES.encrypt(data, the_key).toString();
```

CryptoJS.AES.encrypt 内部流程：

1. **生成随机 Salt**
   - 8 字节随机数

2. **密钥派生 (EVP_BytesToKey)**
   - 使用 OpenSSL 兼容的 EVP_BytesToKey 算法
   - 输入：password（上面生成的 the_key）+ salt
   - 输出：32-byte AES key + 16-byte IV
   - 算法：
     ```
     D_i = MD5(D_{i-1} + password + salt)  // i = 1, 2, ...
     derived = D_1 + D_2 + ...             // 直到达到所需长度
     key = derived[0:32]
     iv = derived[32:48]
     ```

3. **AES 加密**
   - 算法：AES-256-CBC
   - 填充：PKCS7

4. **输出编码**
   - 格式：`Salted__` + salt + ciphertext
   - 编码：Base64

## 解密流程

Python 端需要逆向上述流程：

### 1. Base64 解码

```python
encrypted_data = base64.b64decode(encrypted_b64)
```

### 2. 解析密文结构

```python
if encrypted_data[:8] != b'Salted__':
    raise ValueError('Invalid format')
    
salt = encrypted_data[8:16]      # 8 字节 salt
ciphertext = encrypted_data[16:]  # 实际密文
```

### 3. 密钥派生 (EVP_BytesToKey)

```python
def evp_bytes_to_key(password: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16):
    derived = b''
    block = b''
    
    while len(derived) < key_len + iv_len:
        hasher = hashlib.md5()
        hasher.update(block + password + salt)
        block = hasher.digest()
        derived += block
        
    return derived[:key_len], derived[key_len:key_len + iv_len]

key, iv = evp_bytes_to_key(the_key.encode(), salt, 32, 16)
```

### 4. AES 解密

```python
cipher = AES.new(key, AES.MODE_CBC, iv)
decrypted_padded = cipher.decrypt(ciphertext)
decrypted_data = unpad(decrypted_padded, AES.block_size)
```

### 5. JSON 解析

```python
cookie_data = json.loads(decrypted_data.decode('utf-8'))
```

## 完整 Python 实现

```python
import hashlib
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def decrypt_cookiecloud(uuid: str, password: str, encrypted_b64: str) -> dict:
    # 1. 生成密钥
    the_key = hashlib.md5(f"{uuid}-{password}".encode()).hexdigest()[:16]
    
    # 2. Base64 解码
    encrypted_data = base64.b64decode(encrypted_b64)
    
    # 3. 解析结构
    if encrypted_data[:8] != b'Salted__':
        raise ValueError('Invalid format')
    salt = encrypted_data[8:16]
    ciphertext = encrypted_data[16:]
    
    # 4. EVP_BytesToKey 密钥派生
    def evp_bytes_to_key(password, salt, key_len=32, iv_len=16):
        derived = b''
        block = b''
        while len(derived) < key_len + iv_len:
            hasher = hashlib.md5()
            hasher.update(block + password + salt)
            block = hasher.digest()
            derived += block
        return derived[:key_len], derived[key_len:key_len + iv_len]
    
    key, iv = evp_bytes_to_key(the_key.encode(), salt)
    
    # 5. AES 解密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    # 6. JSON 解析
    return json.loads(decrypted.decode('utf-8'))
```

## 常见错误

### 1. PKCS#7 padding is incorrect

**原因**：直接使用 MD5 值作为 key，没有使用 EVP_BytesToKey 派生

**错误代码**：
```python
# 错误！
key = hashlib.md5(f"{uuid}-{password}".encode()).hexdigest()[:16].encode()
iv = encrypted_data[:16]  # 错误地假设前16字节是 IV
cipher = AES.new(key, AES.MODE_CBC, iv)
```

**正确代码**：
```python
# 正确！使用 EVP_BytesToKey 派生 key 和 iv
the_key = hashlib.md5(f"{uuid}-{password}".encode()).hexdigest()[:16]
salt = encrypted_data[8:16]  # 从 Salted__ 后提取 salt
key, iv = evp_bytes_to_key(the_key.encode(), salt)
```

### 2. 密文格式错误

**原因**：没有正确处理 `Salted__` 前缀

**正确做法**：
- 检查前 8 字节是否为 `Salted__`
- salt 是接下来的 8 字节
- ciphertext 从第 16 字节开始

## 参考链接

- [CookieCloud GitHub](https://github.com/easychen/CookieCloud)
- [CryptoJS AES 文档](https://cryptojs.gitbook.io/docs/#ciphers)
- [OpenSSL EVP_BytesToKey](https://www.openssl.org/docs/man1.1.1/man3/EVP_BytesToKey.html)
- [obsidian-weread-plugin](https://github.com/zhaohongxuan/obsidian-weread-plugin)
