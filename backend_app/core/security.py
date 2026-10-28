from datetime import datetime, timezone, timedelta
import jwt
from pwdlib import PasswordHash
from core.config import settings


hash_password = PasswordHash.recommended()

def password_hash(password:str) ->str:
    return hash_password.hash(password)

def verify_hash_password(password:str, hashed_password:str) ->bool:
    return hash_password.verify(password, hashed_password)

def create_access_token(data:dict, expire_delta:timedelta |None = None)->str:
   payload  = data.copy()
   if expire_delta:
        expire_at = datetime.now(timezone.utc) + expire_delta
   else:
        expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_TIME)
   
   
   payload['exp'] = expire_at

   to_encode = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
   return to_encode

def decode_access_token(token:str)-> dict|None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        return payload
    except jwt.ExpiredSignatureError:
        return None
    
    except jwt.InvalidTokenError:
        return None

