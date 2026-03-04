from retriever_AGENT import Sabrina , system_message
from langchain_core.messages import HumanMessage, SystemMessage


config = {"configurable": {"thread_id": "10"}}
#First interaction
question =  "Hi, I am Ben's mother, ID Student 8. He is going to be late today"
#question ="Hi, I am Bob's mother, ID Student 2. Can you tell me when he has class?"
#question ="Hi, I am Charlie's mother, ID Student 3. Is there any pending payment for him?"
#question ="Hi, I am Alice's mother, ID Student 1. I want to let you know that I paid today this month."
#question = "Hi, I am Daiana's mother, ID Student 4. She couldn't do the homework becasuse she was sick last week"
#question = "Hi, I want my child practice vocabulary for his English class. Her name is Fiona. The vocabulary may be cooking related. Could you help me with that?"
#question= "When she has class?"
response = Sabrina.invoke({
    "messages": [system_message, HumanMessage(content= question)]}, 
    config, stream_mode="values")

print("🧑 Parent:")
print(question)
print("🤖 Sabrina's Response:")
print(response['messages'][-1].content)

"""
#Second interaction (referencing the first)
question = "And has he paid for this month?"
response = Sabrina.invoke({
    "messages": [system_message, HumanMessage(content= question)]}, 
    config, stream_mode="values")

print("🧑 Parent:")
print(question)
print("🤖 Sabrina's Response:")
print(response['messages'][-1].content)
"""