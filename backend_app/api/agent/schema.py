from pydantic import BaseModel


class ChatRequest(BaseModel):
    message:str
    thread_id:str="default_session"


class ChatResponse(BaseModel):
    response:str
    tool_used:list[str] = []
    thread_id:str="default_session"

class ApprovalRequest(BaseModel):
    thread_id:str = "default_session"