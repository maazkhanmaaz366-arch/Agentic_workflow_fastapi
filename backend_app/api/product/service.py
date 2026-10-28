from anyio import from_thread
from bson import ObjectId
from bson.errors import InvalidId
from api.product.schema import CreateProduct, UpdateProduct, FilterProducts
from core.database import product_collection
from pathlib import Path
import uuid
import shutil
from fastapi import UploadFile,File
ALLOWED_EXT = {".jpg",".jpeg",".png",".webp"}
def insert_product_image_to_disk(file:UploadFile | None) ->str |None:
    if not file:
        return None
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXT:
        return None
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = Path("static/")/unique_filename
    
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    return  f"/static/{unique_filename}"

def remove_image_from_disk(image_url:str |None) ->None:
    if not image_url:
        return
    
    file_path = Path(image_url.lstrip("/"))
    
    file_path.unlink(missing_ok=True)


def format_product(product:dict )->dict:
    product["_id"] = str(product["_id"])
    return  product

def format_id(id:str) ->ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        return None


async def get_all_products_filter(filter:FilterProducts)->dict:
    query = {}
    if filter.search:
        query["name"] = {"$regex":filter.search,"$options":"i"}
    if filter.category:
        query["category"] = filter.category
    if filter.min_price is not None or filter.max_price is not None:
        query["price"] = {}
        if filter.min_price is not None:
            query["price"]["$gte"] = filter.min_price
        if filter.max_price is not None:
            query["price"]["$lte"] =filter.max_price
    
    total  = await product_collection.count_documents(query)

    sort_direction = 1 if filter.order.lower() == "asc" else -1

    cursor = (
        product_collection.find(query).sort(filter.sort_by,sort_direction).skip(filter.skip).limit(filter.limit)
    )

    products = await cursor.to_list(length=filter.limit)
    return {
        "total": total,
        "skip":filter.skip,
        "limit":filter.limit,
        "products": [format_product(p) for p in products]
    }
    


async def create_product(product:CreateProduct, user_id:str) -> dict:
      data = product.model_dump()
      data["created_by"] = user_id
      result = await product_collection.insert_one(data)
      data['_id'] = str(result.inserted_id)
      return data


async def get_product_by_id(id:str) ->dict:
    oid = format_id(id)
    if oid is None:
        return None
    product = await product_collection.find_one({"_id":oid})
    if not product:
        return None
    return format_product(product)

async def get_all_products(limit:int=10) ->list[dict]:
    products = await product_collection.find().to_list(length= limit)
    return [format_product(p) for p in products]


async def update_product(id:str, product:UpdateProduct) -> dict:
    data = product.model_dump(exclude_unset = True, exclude_none= True)
    if not data:
        return None
    oid = format_id(id)
    if oid is None:
        return None
    update = await product_collection.update_one({"_id":oid},{"$set":data})
    if not update.matched_count > 0:
        return None

    result= await product_collection.find_one({'_id':oid})
    if not result:
        return None
    return format_product(result)


async def delete_product(id:str)->bool:
    oid = format_id(id)
    if oid is None:
        return False
    
    result = await product_collection.delete_one({"_id":oid})
    if result.deleted_count > 0:
        return True
    
    return False



async def get_user_products(id:str, limit:int = 10)->dict:
    oid = format_id(id)
    if oid is None:
        return None
    
    products = await product_collection.find({'created_by':id}).to_list(length=limit)
    return [format_product(p) for p in products]
    

async def get_product_with_creator(id:str) ->dict:

    oid = format_id(id)
    if oid is None:
        return None

    
    pipline = [
       {"$match":{"_id":oid}},
       {"$addFields":{"creator_oid":{"$toObjectId":"$created_by"}}},
       {"$lookup":{
        "from":"users",
        "localField":"creator_oid",
        "foreignField":"_id",
        "as":"creator"
       }},
       {"$unwind":{
        "path":"$creator",
        "preserveNullAndEmptyArrays":True

       }},
       {"$project":{
        "creator.hashed_password":0,
        "creator_oid":0

       }}

       
    ]
    cursor = product_collection.aggregate(pipline)
    result = await cursor.to_list(length=1)
    if not result:
        return None
    product = result[0]
    product["_id"] =str(product["_id"])
    if "creator" in product and product["creator"]:
        product["creator"]["_id"] = str(product["creator"]["_id"])

    return product


async def category_states():
    pipline=[
        {"$group":{
            "_id":"$category",
            "total_products":{"$sum":1},
            "avg_price":{"$avg":"$price"},
            "min_price":{"$min":"$price"},
            "max_price":{"$max":"$price"},
            "total_stock":{"$sum":"$stock"},
             
        }
        
        }
    ]

    cursor = product_collection.aggregate(pipline)
    result = await cursor.to_list(length=None)
    return result


import time

def product_created(name:str):
    time.sleep(2)
    print(f"product Successfully created {name}>")
    
    


async def clear_product_image(id:str)->dict|None:
    oid = format_id(id)
    if not oid:
        return None
    
    await product_collection.update_one({"_id":oid},{"$unset":{"image_url":""}})

    product = await product_collection.find_one({"_id":oid})
    if not product:
        return None
    
    return format_product(product) if product else None