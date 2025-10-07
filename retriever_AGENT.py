from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_openai import ChatOpenAI
import os
from datetime import datetime
import re
from dotenv import load_dotenv
from Tools_AGENT import student_info_tool, check_payment_status_tool, record_payment_tool, topic_search_tool, alert_tool
from IPython.display import display, Image

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-4o-mini",  
    temperature=0
)

chat = llm
tools = [student_info_tool, check_payment_status_tool, record_payment_tool, topic_search_tool, alert_tool]
chat_with_tools = chat.bind_tools(tools)

from langchain_core.messages import SystemMessage

system_message = SystemMessage(content="""
You are Sabrina, a teaching assistant.
You have access to the following tools:

- student_info_tool: get student schedule and information, always review comments from the teacher.
- check_payment_status_tool: check payment status of a student
- record_payment_tool: update payment status
- alert_tool: create an alert for the teacher in a specific file

Rules:
- If a parent says a student won't go to class, couldn't do the homework, wants to reschudle or want to talk with the teacher, call alert_tool.
- If a parent asks about payment, call check_payment_status_tool.
- If a parent wants to update a payment, call record_payment_tool.
- Always use the most appropriate tool before answering.
- Only respond after calling the correct tool if needed.
                               
If any tool return that could not find student ID in the message or no matching student found, let the parent know and ask for the student ID again.
""")



class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    recursion_count: int

initial_state = AgentState(messages=[system_message])

def assistant(state: AgentState):
    state["recursion_count"] = state.get("recursion_count", 0) + 1
    #print(f"\n=== ASSISTANT TURN {state['recursion_count']} ===")
    #print("Messages so far:", [m.content for m in state["messages"]])
      #Evitar loop si ya se creó la alerta
    if state.get("alert_created"):
        return {"messages": state["messages"] + [AIMessage(content="Alert already created")]}
    
    response = chat_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}



# ------------------------------ The graph

from langgraph.checkpoint.memory import InMemorySaver
memory = InMemorySaver()

builder = StateGraph(AgentState)
# Assistant node 
builder.add_node("assistant", assistant)
# Tools node
builder.add_node("tools", ToolNode(tools))
# START → assistant
builder.add_edge(START, "assistant")
# Assistant decides whether to call tools or respond directly
builder.add_conditional_edges("assistant", tools_condition)
# Once the assistant responds, it can go back to itself for further processing
builder.add_edge("tools", "assistant")

# Graph compilation
Sabrina = builder.compile(checkpointer=memory)



"""
# Save the graph image as a PNG file
img_data = Sabrina.get_graph(xray=True).draw_mermaid_png()
with open("sabrina_graph.png", "wb") as img_file:
    img_file.write(img_data)

#Save the graph in dot format
graph = Sabrina.get_graph()
with open("sabrina_graph.dot", "w") as f:
    f.write(graph.draw_mermaid())
print(graph.draw_mermaid())
"""