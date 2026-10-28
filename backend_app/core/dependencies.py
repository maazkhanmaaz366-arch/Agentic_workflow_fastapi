from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import decode_access_token
from bson import ObjectId
from bson.errors import InvalidId
from core.database import user_collection



security = HTTPBearer()

async def get_current_user(credentials:HTTPAuthorizationCredentials =Depends(security)):

    token  = credentials.credentials
     
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "could not validate credentials",
        headers= {"WWW-Authenticate":"Bearer"},

    )

    payload = decode_access_token(token)

    if not payload:
        raise credentials_exception
    
    user_id:str = payload.get('sub')
    if not user_id:
        raise credentials_exception
    
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise credentials_exception
    
    user = await user_collection.find_one({"_id":oid})
    if not user:
        raise credentials_exception
    user.pop("hashed_password",None)
    user["_id"] = str(user["_id"])
    return user
    

async def current_admin(current_user:dict=Depends(get_current_user))->dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "you are not admin"
        )
    return current_user
    

