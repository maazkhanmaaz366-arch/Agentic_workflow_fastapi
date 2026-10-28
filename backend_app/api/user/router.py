
from fastapi import APIRouter, HTTPException , status,Depends,BackgroundTasks,UploadFile,File,Request
from api.user.schema import UserCreate,UserUpdate,UserLogin, TokenReponse,UserFilter
from api.user.service import (create_user, get_user_by_id , 
get_all_users, update_user , welcome_email,send_alert,
delete_user,authenticate_user,self_or_admin,save_user_image,remove_user_image,
clear_user_images)
from core.security import create_access_token 
from core.dependencies import get_current_user,current_admin
from core.limiter import limiter

router = APIRouter(prefix = '/users', tags=['Users'])


@router.get('/me')
async def get_my_profile(current_user:dict = Depends(get_current_user)):
    return {
        "message":"Authentication complete",
        "user":current_user
    } 

@router.post("/{id}/image")
async def upadate_image(id:str,file:UploadFile=File(...), current_user:dict=Depends(get_current_user)):
      if not self_or_admin(id,current_user):
          raise HTTPException(status.HTTP_403_FORBIDDEN)
      
      user = await get_user_by_id(id)
      
      if not user:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
      
      old_imge = user.get("image_url")
      new_image = save_user_image(file)
      if not new_image:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to save image")
      remove_user_image(old_imge)

      data = await update_user(id,UserUpdate(image_url=new_image))
      return {
        "message":"image updated successfully",
        "data":data
      }

@router.delete("/{id}/image")
async def delete_image_user(id:str, current_user:dict=Depends(get_current_user)):
    
    if not self_or_admin(id,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    user = await get_user_by_id(id)

    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND)
    
    remove_user_image(user.get("image_url"))
    data = await clear_user_images(id)
    return{
            "message": "image deleted successfully",
            "user":data
    }






@router.post('/login',response_model=TokenReponse)
@limiter.limit("5/minute")
async def login(request:Request,credentials: UserLogin,back_task:BackgroundTasks):
    user = await authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "wrong password or email", headers={"WWW-Authenticate":"Bearer"})
    token_payload = {
        "sub": str(user["_id"]),
        "email":user["email"],
        "role":user.get("role","user")
    }
    
    token = create_access_token(data = token_payload)
    back_task.add_task(send_alert,user["email"],user.get("name","user"))
    return {
        "access_token":token,
        "token_type":"bearer"
    }

@router.post('/',status_code=status.HTTP_201_CREATED)
async def create(user:UserCreate,background_tasks:BackgroundTasks):
    new_user = await create_user(user)
    background_tasks.add_task(welcome_email,user.name,user.email)
    return {
        'message':"user created successfully",
        "data": new_user
    }

@router.get('/')
async def list_user(filtered:UserFilter = Depends(),admin:dict= Depends(current_admin)):
    
    users = await get_all_users(filtered)
    return users

@router.get('/{id}')
async def get_one(id:str, current_user:dict=Depends(get_current_user)):
   
    if not self_or_admin(id,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to view this user")
    user = await get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail='user not found')
    return user


@router.put('/{id}')
async def update_one(id:str, user:UserUpdate,current_user:dict=Depends(get_current_user)):
    if not self_or_admin(id,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to update this user")
    data = await update_user(id,user)

    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return{
        'message': "user successfully update",
        'user': data
    }

@router.delete('/{id}')
async def delete_one(id:str, current_user: dict = Depends(get_current_user)):
    if not self_or_admin(id,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you are not authorized to delete this user")
    user = await get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if user.get("image_url"):
        remove_user_image(user["image_url"])
    success = await delete_user(id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return{
        'message': "user successfully deleted",
        'data' : id
    }
