
from fastapi import APIRouter, HTTPException, status,Depends,BackgroundTasks,UploadFile,File
from api.product.schema import CreateProduct, UpdateProduct, FilterProducts
from api.product.service import (create_product,get_all_products,
 get_product_by_id,update_product,delete_product, 
 get_user_products,get_all_products_filter,get_product_with_creator,
 category_states, product_created, remove_image_from_disk,insert_product_image_to_disk,
 clear_product_image)
from core.dependencies import get_current_user
import shutil
import uuid
from pathlib import Path

ALLOWED_EXETENSION = {".jpg",".jpeg",".png",".webp"}
router = APIRouter(prefix = "/products", tags = ["Products"])

@router.post("/{id}/image")
async def upload_product_image(id:str,file:UploadFile=File(...),current_user:dict=Depends(get_current_user)):
    existing = await get_product_by_id(id)

    if not existing:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND)

    is_owner = existing.get("created_by") == current_user["_id"]
    is_admin = current_user.get("role") == "admin"

    if not(is_owner or is_admin):
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    old_image = existing.get("image_url")
    new_image = insert_product_image_to_disk(file)
    if not new_image:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    if old_image:
        remove_image_from_disk(old_image)
    
    
    data = await update_product(id,UpdateProduct(image_url=new_image))
    if not data:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    
    return {
        "message":"image uploaded successfully",
        "data":data
    }


@router.delete("/{id}/image")
async def delete_product_image(id:str, current_user:dict=Depends(get_current_user)):
    product = await get_product_by_id(id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    
    is_owner = product.get("created_by") == current_user["_id"]
    is_admin = current_user.get("role") == "admin"
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    if not product.get("image_url"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    remove_image_from_disk(product["image_url"])
    data = await update_product(id,UpdateProduct(image_url=None))
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return {
        "message":"image deleted successfully",
        "data":data
    }
    





@router.get("/status")
async def get_stats():  
    data = await category_states()
    return data
@router.get('/my/products')
async def my_products(current_user:dict=Depends(get_current_user),limit:int=10):
    user_id = current_user["_id"]
    products = await get_user_products(user_id, limit)
    if not products:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    
    return products

@router.get("/")
async def get_product_filter(filter:FilterProducts = Depends()):
    products = await get_all_products_filter(filter)
    return products


@router.post("/",status_code = status.HTTP_201_CREATED)
async def create(product:CreateProduct,background_tasks:BackgroundTasks,current_user:dict=Depends(get_current_user)):
    result = await create_product(product, user_id=current_user["_id"])
    if not result:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT)
    
    background_tasks.add_task(product_created, product.name)
    return {
        'message':"product successfully created",
        "product":result
    }


@router.get('/{id}')
async def get_one_product(id:str):
    product = await get_product_with_creator(id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return product

@router.put('/{id}')
async def update_one_product(id:str, product:UpdateProduct,current_user:dict=Depends(get_current_user)):
     
    existing = await get_product_by_id(id)
    if not existing:
       raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    
    is_owner = existing.get("created_by") == current_user['_id']
    is_admin = current_user.get("role") == 'admin'
    if not(is_owner or is_admin):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You are not authorized to update this product"
        )
    


    data = await update_product(id, product)
    if not data:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    return {
        'message' :"product successfully updated",
        "product": data
    }

@router.delete('/{id}')
async def delete_one_product(id:str,current_user:dict=Depends(get_current_user)):

    existing = await get_product_by_id(id)
    if not existing:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    
    is_owner = existing.get("created_by") == current_user['_id']
    is_admin = current_user.get("role") == 'admin'
    if not(is_owner or is_admin):
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "You are not authorized to delete this product"
        )
    
    image_url = existing.get("image_url")
    if image_url:
        remove_image_from_disk(image_url)
    
    result = await delete_product(id)
    if not result:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)
    return {
        "message": "product successfully deleted",
        "product": id
    }




