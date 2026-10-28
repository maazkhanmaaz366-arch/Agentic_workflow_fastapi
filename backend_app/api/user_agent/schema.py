from pydantic import BaseModel

class ChatRequest(BaseModel):

    message:str
    thread_id:str="default_sessions"


class ChatResponse(BaseModel):
    response:str
    thread_id:str="default_sessions"
    tool_used:list[str] = []