
from bson import ObjectId
from bson.errors import InvalidId
from core.database import user_collection
from core.security import password_hash, verify_hash_password
from api.user.schema import UserFilter
from fastapi import UploadFile, File 
from pathlib import Path
import shutil
import uuid

ALLOWED_EXETENSION = {".jpg",".jpeg",".png",".webp"}

from api.user.schema import UserCreate, UserUpdate


def save_user_image(file:UploadFile | None) ->str|None:
    if not file:
        return None
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXETENSION:
        return None
    
    uid = uuid.uuid4()
    unique_file = f"{uid}{file_ext}"
    file_path = Path("static/users/")/unique_file
    file_path.parent.mkdir(parents=True, exist_ok = True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
    return f"/static/users/{unique_file}"

def format_user(user:dict) ->dict:
    user["_id"] = str(user["_id"])
    user.pop("hashed_password",None)
    return user

def remove_user_image(image_url:str |None )->None:
    if not image_url:
        return
    
    file_path = Path(image_url.lstrip("/"))
    file_path.unlink(missing_ok=True)

def format_id(id:str) ->ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        return None

async def clear_user_images(user_id:str) -> dict|None:
    oid = format_id(user_id)
    if oid is None:
        return None
    
    await user_collection.update_one({"_id":oid},{"$unset":{"image_url":""}})
    user = await user_collection.find_one({"_id":oid})
    return format_user(user) if user else None

async def create_user(user:UserCreate) ->dict:
    data = user.model_dump()
    raw_password = data.pop("password")
    data["hashed_password"] = password_hash(raw_password)
    result = await user_collection.insert_one(data)
    data['_id'] = str(result.inserted_id)
    return data

async def authenticate_user(email:str,password:str) ->dict|None:
    user = await user_collection.find_one({"email":email})
    if not user:
        return None
    if not verify_hash_password(password, user["hashed_password"]):
        return None
    return format_user(user)






async def get_user_by_id(user_id:str) ->dict:
    oid = format_id(user_id)
    if oid is None:
        return None
    
    user = await user_collection.find_one({"_id":oid})
    if user:
        return format_user(user)

    return None


async def get_all_users(filt:UserFilter)->list[dict]:
    query = {}
    if filt.search:
        query["name"]= {"$regex":filt.search , "$options":"i"}
    if filt.min_age is not None or filt.max_age is not None:
        query["age"]= {}
        if filt.min_age is not None:
            query["age"]["$gte"] = filt.min_age
        if filt.max_age is not None:
            query["age"]["$lte"] = filt.max_age
    
    if filt.role is not None:
        query["role"] = filt.role

    sort_direction =  1 if filt.order == "asc" else -1
    total = await user_collection.count_documents(query)
    cursor = (user_collection.find(query).sort(filt.sort_by, sort_direction)).skip(filt.skip).limit(filt.limit)
    user = await cursor.to_list(length=filt.limit)

    return {
        "total":total,
        "skip":filt.skip,
        "limit":filt.limit,
        "users": [format_user(u) for u in user]
    }

    


async def update_user(id:str, user:UserUpdate) ->dict:
    oid = format_id(id)
    if oid is None:
        return None
    
    data = user.model_dump(exclude_none=True, exclude_unset = True)
    if not data:
        return None
    
    user_data =  await user_collection.update_one({"_id":oid},{"$set":data})
    if user_data.matched_count == 0:
        return None
    
    update_user = await user_collection.find_one({"_id":oid})
    return format_user(update_user)


async def delete_user(id:str) ->bool:
    oid = format_id(id)

    if oid is None:
        return False
    
    result = await user_collection.delete_one({"_id":oid})
    return result.deleted_count >0


def self_or_admin(user_id:str, current_user:dict) ->bool:
    is_self = user_id == current_user["_id"]
    is_admin = current_user.get("role") == 'admin'
    return is_self or is_admin

import time

def welcome_email(name:str, email:str):
    time.sleep(2)
    print(f"Welcome to our services {name} <{email}>")

from datetime import datetime
def send_alert(email:str, name:str):
    time.sleep(2)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[gmail to {email}]Hi {name} a new login to your account was detected at {now}")
