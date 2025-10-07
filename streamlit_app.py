import streamlit as st
from retriever_AGENT import Sabrina, initial_state
from langchain_core.messages import HumanMessage

# Mantener estado del chat
if "state" not in st.session_state:
    st.session_state.state = initial_state

st.title("Sabrina - Teaching Assistant 🤖")

user_input = st.text_input("You:", "")

if st.button("Send") and user_input:
    st.session_state.state["messages"].append(HumanMessage(content=user_input))
    response_state = Sabrina.invoke(st.session_state.state)
    st.session_state.state = response_state
    ai_msg = response_state["messages"][-1].content
    st.text_area("Sabrina:", value=ai_msg, height=150)