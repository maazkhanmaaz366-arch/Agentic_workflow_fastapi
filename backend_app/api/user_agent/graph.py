from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from core.config import settings
from api.user_agent.tools import backend_tools
from langgraph.checkpoint.memory import MemorySaver


checkpoint = MemorySaver()

llm = ChatGroq(model = "openai/gpt-oss-120b",api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = (
  "You are the user Management assisstent  who manage user data and manipulation\n"
  "you have direct access to database tools to check real time user data\n"
  "always use your to query database and before answering question about users and updata user\n"
  "naver make up fake user or data\n"
)

agent_graph = create_react_agent(
    model=llm,
    tools = backend_tools,
    prompt = SYSTEM_PROMPT,
    checkpointer = checkpoint
)

