from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher # ⚠️ 오타 주의: bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from typing import Any, Union

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """
    비밀번호를 해시(암호화)하여 반환
    사용자가 입력한 평문 비밀번호를 Argon2 알고리즘을 사용하여
    복호화가 불가능한 해시 문자열로 변환

    Args:
        password(str): 평문 비밀번호
    
    Returns:
        str: 암호화된 비밀번호
    """
    password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 1. 해쉬 검증 도구 생성
    password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))
    # 2. 검증 수행 및 결과 반환 (true/false)
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    JWT를 생성해 반환합니다.

    Args:
        data (dict): JWT에 포함할 페이로드 정보.
        expires_delta (Union[timedelta, None], optional): 만료 시간. 지정 없으면 기본값을 사용합니다.

    Returns:
        str: 인코딩된 JWT 문자열.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

if __name__ == "__main__":
    password = "dhrdmstn"
    hashed_password = hash_password(password)
    print("Hashed Password:", hashed_password)
    
    # 검증 테스트
    print("Verification:", verify_password(password, hashed_password))
