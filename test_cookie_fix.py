#!/usr/bin/env python3
"""
测试 CookieCloud 解密修复
验证 EVP_BytesToKey 密钥派生算法是否正确
"""

import hashlib
import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def evp_bytes_to_key(password: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16, 
                     iterations: int = 1, hash_func=hashlib.md5) -> tuple:
    """
    实现 OpenSSL EVP_BytesToKey 密钥派生算法
    """
    derived = b''
    block = b''
    
    while len(derived) < key_len + iv_len:
        hasher = hash_func()
        hasher.update(block + password + salt)
        block = hasher.digest()
        
        for _ in range(1, iterations):
            block = hash_func(block).digest()
            
        derived += block
        
    return derived[:key_len], derived[key_len:key_len + iv_len]


def decrypt_cryptojs_aes(password: str, ciphertext_b64: str) -> bytes:
    """
    解密 CryptoJS.AES.encrypt() 加密的数据
    """
    encrypted_data = base64.b64decode(ciphertext_b64)
    
    if len(encrypted_data) < 16 or encrypted_data[:8] != b'Salted__':
        raise ValueError('无效的密文格式，缺少 Salted__ 前缀')
        
    salt = encrypted_data[8:16]
    ciphertext = encrypted_data[16:]
    
    # 使用 EVP_BytesToKey 派生 key 和 iv
    key, iv = evp_bytes_to_key(
        password.encode('utf-8'), 
        salt,
        key_len=32,
        iv_len=16
    )
    
    # AES-256-CBC 解密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    decrypted_data = unpad(decrypted_padded, AES.block_size)
    
    return decrypted_data


def test_decrypt():
    """测试解密流程"""
    # 模拟测试数据
    # 使用已知的 uuid 和 password
    uuid = "test-uuid"
    password = "test-password"
    
    # 生成密钥（与实际代码一致）
    key_source = f"{uuid}-{password}"
    the_key = hashlib.md5(key_source.encode()).hexdigest()[:16]
    
    print(f"测试参数:")
    print(f"  UUID: {uuid}")
    print(f"  Password: {password}")
    print(f"  派生密钥: {the_key}")
    
    # 这里需要实际的加密数据进行测试
    # 可以通过浏览器插件或手动构造测试数据
    print("\n注意: 需要实际的 CookieCloud 加密数据进行完整测试")
    print("请从浏览器插件获取真实的 encrypted 数据进行验证")
    
    # 测试 EVP_BytesToKey 算法
    test_password = b"test"
    test_salt = b"12345678"
    key, iv = evp_bytes_to_key(test_password, test_salt, 32, 16)
    print(f"\nEVP_BytesToKey 测试:")
    print(f"  输入密码: {test_password}")
    print(f"  输入盐值: {test_salt}")
    print(f"  派生 Key: {key.hex()}")
    print(f"  派生 IV: {iv.hex()}")


if __name__ == "__main__":
    test_decrypt()
