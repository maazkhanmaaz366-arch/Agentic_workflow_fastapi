from api.product.schema import UpdateProduct
from langchain_core.tools import tool
from api.product.service import get_all_products_filter,category_states,update_product,delete_product
from api.product.schema import FilterProducts
import csv 
import uuid
from pathlib import Path
from langgraph.types import interrupt

@tool
async def search_products_tool(
    search:str  | None = None,
    category : str | None = None,
    min_price: float | None = None,
    max_price : float | None = None

) -> str:
# the comment or doctorian importent for the tool must add it in function for the agent understand what is the function do
    """Search and filter products in the database by name, category, or price range."""

    filters = FilterProducts(
        search=search,
        category = category,
        min_price = min_price,
        max_price = max_price,
        limit=5
      )
    result = await get_all_products_filter(filters)
    products = result.get("products",[])

    if not products:
        return f"No products found matching those criteria"

    summary = []
    for p in products:
        summary.append(f"-{p.get("name")} | category: {p.get("category")} | price: ${p.get("price")} |stock {p.get("stock")}")

    return "\n".join(summary)
     

@tool
async def get_category_analytics_tool() -> str:
# the comment or doctorian importent for the tool must add it in function for the agent understand what is the function do
    """Get category analytics, including total item counts, average prices, and price ranges."""
    stats = await category_states()
    if not stats:
        return "no statistics available"

    lines = []
    for s in stats:
        lines.append(f"Category: {s.get("_id")} -> Toal {s.get("total_products")} item,Avg price:${s.get("avg_price",0):.2f}, min:${s.get("min_price")}, max: ${s.get('max_price')}")  
    return "\n".join(lines)


@tool
async def export_inventory_csv_tool(
    search:str | None = None,
    category:str | None = None,
    min_price:float | None = None,
    max_price:float | None = None
)->str:
   """can make report according the filter can be all for one product more according to filters"""

   filter = FilterProducts(
    search = search,
    category = category,
    min_price = min_price,
    max_price = max_price,
    limit = 500
   )


   result = await get_all_products_filter(filter)
   products = result.get("products",[])

   if not products:
        return "no product found matching the criteria"

   report_dir = Path("static/reports")
   report_dir.mkdir(parents = True ,exist_ok=True)

   file_name = f"inventory_{uuid.uuid4().hex[:8]}.csv"
   file_path = report_dir/file_name

   with open(file_path,mode="w",newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "name" , "category","price","stock"])
        for p in products:
            writer.writerow([
                p.get("_id",""),
                p.get("name",""),
                p.get("category",""),
                p.get("price",0.0),
                p.get("stock",0)

            ])

   download_url = f"static/reports/{file_name}"
   return f"Inventory report has been generated. You can download it here: {download_url}"

@tool
async def update_product_stock_tool(product_id:str, new_stock:int)->str:
    """Update the stock quantity for a specific product by its ID. Returns the updated stock value."""
    
    if new_stock <0:
        return "the stock lesser than 0 the stock should be 0 or greater"
    
    update_data = UpdateProduct(stock=new_stock)
    update = await update_product(product_id,update_data)
    if not update:
        return f"the stock not update successfully for {product_id}"
    
    return f"stock successfully updated for {update.get("name")} (Id: {update.get("_id")}). new stock {update.get("stock")} unite"
    

@tool
async def delete_product_tool(product_id:str)->str:
    """Delete a product permanently from the database by its ID. 
Always invoke this tool immediately when a user asks to delete a product. 
The backend system will handle the approval breakpoint automatically."""

    is_approved = interrupt({
        "action":"delete_product",
        "product_id":product_id,
        "warning": "this action is permanent and cannot be undone"

    })
    if not is_approved:
        return f"Operation cancelled: Deletion of product {product_id} was rejected by admin"
    
    delete = await delete_product(product_id)
    if not delete:
        return f"error:product with ID {product_id} was not found or cannot be deleted"
    
    return f"product with ID {product_id} has been permanently deleted from the database"

backend_tools = [search_products_tool, get_category_analytics_tool, export_inventory_csv_tool,update_product_stock_tool,
delete_product_tool
]