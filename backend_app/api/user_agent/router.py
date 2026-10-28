import json
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, ToolMessage
from api.user_agent.graph import agent_graph
from api.user_agent.schema import ChatRequest, ChatResponse

router = APIRouter(prefix="/user_agent", tags=["User Agent"])


@router.post("/stream")
async def chat_with_user_agent(req:ChatRequest):
    async def event_generator():
        inputs = {"messages":[HumanMessage(content=req.message)]}
        config = {"configurable":{"thread_id":req.thread_id}}

        async for event in agent_graph.astream_events(inputs, config=config, version="v2"):
            kind = event.get("event")

            if kind == "on_tool_start":
                tool_name = event.get("name","tool")
                yield f"data: {json.dumps({"type":"tool_start", "name":tool_name})}\n\n"
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                if content:
                    if isinstance(content,str):
                        text = content
                    elif isinstance(content,list):
                        text = "".join([p.get("text","") for p in content if isinstance(p,dict)])
                    else:
                        text = ""
                    
                    if text:
                        yield f"data: {json.dumps({"type":"token", "content":text })}\n\n"
        yield f"data: {json.dumps({"type":"done"})}\n\n"
    return StreamingResponse(event_generator(), media_type= "text/event-stream")