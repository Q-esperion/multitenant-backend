from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def encrypt_password(password: str) -> str:
    """使用AES加密密码"""
    # 生成随机IV
    iv = os.urandom(16)
    
    # 创建AES加密器
    key = settings.SECRET_KEY.encode('utf-8')[:32]
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # 对密码进行填充
    padder = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
    padded_data = padder(password).encode('utf-8')
    
    # 加密
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    # 将IV和密文进行base64编码
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
    
    # 返回JSON格式的加密结果
    return json.dumps({
        "iv": iv_b64,
        "ciphertext": ciphertext_b64
    })

def decrypt_password(encrypted_data: str) -> str:
    """解密密码"""
    try:
        # 解析JSON数据
        data = json.loads(encrypted_data)
        iv = base64.b64decode(data["iv"])
        ciphertext = base64.b64decode(data["ciphertext"])
        
        # 创建AES解密器
        key = settings.SECRET_KEY.encode('utf-8')[:32]
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 去除填充
        unpadder = lambda s: s[:-ord(s[len(s)-1:])]
        return unpadder(decrypted.decode('utf-8'))
    except Exception as e:
        raise ValueError(f"密码解密失败: {str(e)}") 