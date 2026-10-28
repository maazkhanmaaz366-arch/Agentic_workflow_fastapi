from fastapi import APIRouter,HTTPException, status
from fastapi.responses import StreamingResponse 
import json
from api.agent.schema import ChatRequest, ChatResponse,ApprovalRequest
from api.agent.graph import agent_graph
from langchain_core.messages import HumanMessage,ToolMessage
from api.agent.multi_graph import final_graph
from langgraph.types import Command


router = APIRouter(prefix="/agent", tags=["AI Agent"])
@router.post("/team", response_model = ChatResponse)
async def chat_with_multi_agent_team(req:ChatRequest):

    try:
        inputs = {"messages":[HumanMessage(content=req.message)]}
        result = await final_graph.ainvoke(inputs,config={"recursion_limit":6})
        messages = result.get("messages",[])
        final_answer = messages[-1].content if messages else "No response generated."
        # Track which team members participated in answering
        workers_involved = [m.name for m in messages if getattr(m, "name", None)]
        return ChatResponse(
            response=str(final_answer),
            tool_used=workers_involved,
            thread_id=req.thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/stream")
async def stream_agent_chat(req:ChatRequest):
    async def event_generator():
        inputs = {"messages": [HumanMessage(content=req.message)]}
        config = {"configurable":{"thread_id":req.thread_id}}

        async for event in agent_graph.astream_events(inputs,config=config, version='v2'):
        
           kind = event["event"]

           if kind == "on_tool_start":
               tool_name = event.get("name", "tool")
               yield f"data: {json.dumps({"type":"tool_start", "tool":tool_name})}\n\n"
        
           elif kind == "on_chat_model_stream":
               chunk = event["data"]["chunk"]
               content = chunk.content
               if content:
                  if isinstance(content,str):
                    text = content
                  elif isinstance(content, list):
                    text = "".join([p.get("text","") for p in content if isinstance(p,dict)])
                  else:
                    text=""
                  if text: 
                    yield f"data: {json.dumps({'type':"token","content":text})}\n\n"
        state = await agent_graph.aget_state(config)
        pending_interrupts = [t.interrupts[0].value for t in state.tasks if getattr(t,"interrupts",[])]
        if pending_interrupts:
            info = pending_interrupts[0]
            yield f"data : {json.dumps({"type":'approval_required', 'details':info, 'thread_id':req.thread_id})}\n\n"
        yield f"data: {json.dumps({'type':'done'})}\n\n"
    return StreamingResponse(event_generator(),media_type = "text/event-stream")


@router.post("/chat",response_model=ChatResponse)
async def chat_with_agent(req:ChatRequest):
    try:
        inputs = {"messages":[HumanMessage(content=req.message)]}
        config = {"configurable":{"thread_id":req.thread_id}}

        result = await agent_graph.ainvoke(inputs,config=config)
        messages = result.get("messages",[])

        tools_called = [
            msg.name for msg in messages if isinstance(msg,ToolMessage)]
        
        raw_content = messages[-1].content if messages else "no response generated"
        if isinstance (raw_content,list):
            final_answer = "".join([part.get("text"," ") for part in raw_content if isinstance(part, dict)])
        else:
            final_answer = str(raw_content)

        return ChatResponse(
            response=final_answer,
            tool_used= tools_called,
            thread_id = req.thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))


@router.post("/approve",response_model=ChatResponse)
async def approve_action(req:ApprovalRequest):

    try:
        config = {"configurable":{"thread_id":req.thread_id}}

        state = await agent_graph.aget_state(config)
        if not any(getattr(t,"interrupts", None) for t in state.tasks): raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,detail= f"no pending action waiting for the approval{req.thread_id}")

        result = await agent_graph.ainvoke(Command(resume=True),config=config)
        messages = result.get("messages",[])
        tools_called = [msg.name for msg in messages if isinstance(msg,ToolMessage)]
        final_answer = messages[-1].content if messages else "product deletion approved and complete"
        return ChatResponse(
            response=final_answer,
            tool_used=tools_called,
            thread_id=req.thread_id
        )
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))
    

@router.post("/reject",response_model=ChatResponse)
async def reject_action(req:ApprovalRequest):
    try:
        config = {"configurable":{"thread_id":req.thread_id}}
        state = await agent_graph.aget_state(config)
        if not any(getattr(t,"interrupts",[]) for t in state.tasks):
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"no pending action waiting there for approval in session{req.thread_id}")
        
        result = await agent_graph.ainvoke(Command(resume=False),config=config)
        messages = result.get("messages",[])
        tool_called = [msg.name for msg in messages if isinstance(msg,ToolMessage)]
        final_answer = messages[-1].content if messages else "Action cancelled"

        return ChatResponse(
            response=final_answer,
            tool_used = tool_called,
            thread_id=req.thread_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))

        


        
    