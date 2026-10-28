from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from api.agent.tools import backend_tools
from core.config import settings
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()


llm = ChatGroq(model="openai/gpt-oss-120b",api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT= (
    
    "You are an expert AI E-Commerce Assistant for our store.\n"
    "You have direct access to database tools to check real inventory, export CSVs, update stock, and delete products.\n"
    "When a user asks to delete a product, always call delete_product_tool immediately. Do not ask for confirmation yourself in text, as the system automatically pauses for admin approval."


)

agent_graph = create_react_agent(
    model=llm,
    tools= backend_tools,
    prompt = SYSTEM_PROMPT,
    checkpointer = checkpointer
)