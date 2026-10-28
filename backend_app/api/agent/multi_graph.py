from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage,AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from core.config import settings
from api.agent.tools import search_products_tool,get_category_analytics_tool
from pydantic import BaseModel

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]
    next:str

llm = ChatGroq(model="openai/gpt-oss-120b",api_key=settings.GROQ_API_KEY)

inventory_agent = create_react_agent(
    model = llm,
    tools = [search_products_tool],
    prompt="You are an Inventory Specialist. You check available items, search products, prices, and stock in the database."
)

analytics_agent = create_react_agent(
    model=llm,
    tools=[get_category_analytics_tool],
    prompt="You are a Business Analytics Specialist. You provide category totals, average prices, and financial summaries."

)

options = ["Inventory_Specialist", "Analytics_Specialist"]

class Router(BaseModel):
    next:Literal ["Inventory_Specialist", "Analytics_Specialist"]

supervisor_prompt = (
    "You are the Supervisor of a store operations team. "
    "Analyze the user's message and delegate to the right specialist: "
    "- For specific items, stock, or products, choose 'Inventory_Specialist'. "
    "- For categories, averages, or store statistics, choose 'Analytics_Specialist'. "
    "Respond in valid JSON with the key 'next'."
)

async def supervisor_node(state:AgentState):
    messages = [SystemMessage(content=supervisor_prompt)] + list(state["messages"])
    structured_llm = llm.with_structured_output(Router,method="json_mode")
    decision = await structured_llm.ainvoke(messages)
    return {"next":decision.next}


async def run_inventory(state: AgentState):
    result = await inventory_agent.ainvoke(state)
    return {"messages": [AIMessage(content=result["messages"][-1].content, name="Inventory_Specialist")]}



async def run_analytics(state:AgentState):
    result = await analytics_agent.ainvoke(state)
    return {"messages":[AIMessage(content=result["messages"][-1].content,name="Analytics_Specialist")]}

workflow = StateGraph(AgentState)
workflow.add_node("Supervisor",supervisor_node)
workflow.add_node("Inventory_Specialist",run_inventory)
workflow.add_node("Analytics_Specialist",run_analytics)

workflow.add_edge(START,"Supervisor")

workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Inventory_Specialist": "Inventory_Specialist",
        "Analytics_Specialist": "Analytics_Specialist",
        
    }
)

workflow.add_edge("Inventory_Specialist",END)
workflow.add_edge("Analytics_Specialist",END)

final_graph = workflow.compile()
    

