
from api.product.schema import UpdateProduct
from langchain_core.tools import tool
from api.user.service import get_all_users, update_user
from api.user.schema import UserFilter, UserUpdate


@tool
async def search_user_tool(
    search:str | None = None,
    min_age:int | None = None,
    max_age:int | None = None,
    role:str |None = None,
    sort_by:str = "role",
    order:str | None = None
) ->str:
    """used this search user tool if the user ask for the user data in the database
     use to get the user the data from database"""
    filter = UserFilter(
        search = search,
        min_age = min_age,
        max_age = max_age,
        role = role,
        sort_by = sort_by,
        order = order
    )

    result = await get_all_users(filter)
    users = result.get("users",[])
    summary = []
    for user in users:
        summary.append(f"id: {user.get("_id")}, | name: {user.get("name")},|age:{user.get("age")} | role: {user.get("role")} | email:{user.get("email")}| image_url:{user.get("image_url")}")
    
    return "\n".join(summary)



@tool
async def update_user_tool(
    id:str,
    name:str | None = None,
    age:int | None = None,
    email:str | None = None,
    role:str | None = None,
    image_url:str | None = None
) -> str:
    """used to update user in the database if the user ask to update the user data in data base"""
    update = UserUpdate(
        id = id,
        name = name,
        age = age,
        email =email,
        role = role,
        image_url= image_url
    )

    result = await update_user(id,update)

    return f"update user {result}"





backend_tools = [search_user_tool, update_user_tool]