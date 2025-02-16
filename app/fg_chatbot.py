import time
import ollama
import json
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
import streamlit as st
from langchain.memory import ChatMessageHistory
from app.agents.fg_agents import Agent
from app.agents.main_agent import MainAgent
ollama_models = ['llama3.1', 'mistral','deepseek-r1¸','deepseek-r1:14b', ]
openai_models = ['gpt-4o-mini', 'gpt-3.5-turbo-0125']

# Global dictionary to persist responses
global_responses = {}

#demo_ephemeral_chat_history_for_chain = ChatMessageHistory()

def which_agent_to_call(user_input,model,history,demo_ephemeral_chat_history_for_chain):
    #print(model)
    agent = MainAgent(user_input,model,history,demo_ephemeral_chat_history_for_chain)
    response = agent.process_query()
    #agent = Agent(user_input, model, openai_flag=False)
    #response = agent.fgagent1()

    # Persist response in global dictionary

    return response

#response = run_agents(query)
st.set_page_config(layout="wide")  # Increase overall size for window

model_select = st.sidebar.selectbox("Select Model", ollama_models + openai_models)
model = model_select
# Streamlit UI
st.title("GUI - FG / SPP Help channel Bot")
st.button("Refresh and Clear", on_click=lambda: [st.session_state["messages"].clear(), st.session_state["history"].clear()])

# Initialize chat history if not already present
if "messages" not in st.session_state:
    print("New Session started")
    st.session_state["messages"] = []
    st.session_state["history"] = ChatMessageHistory()
    demo_ephemeral_chat_history_for_chain = st.session_state["history"]

# Display chat history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        #demo_ephemeral_chat_history_for_chain = st.session_state["history"]

# User input
user_input = st.chat_input("Ask me anything...")
if user_input:
    # Display user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    demo_ephemeral_chat_history_for_chain = st.session_state["history"]
    history = st.session_state
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get chatbot response
    # Show waiting message
    with st.spinner("Thinking..."):
        print("*"*100)
        response = which_agent_to_call(user_input, str(model),history,demo_ephemeral_chat_history_for_chain)
        #print("$"*100)
        #print(demo_ephemeral_chat_history_for_chain)
    st.session_state["history"] = demo_ephemeral_chat_history_for_chain
    st.session_state["messages"].append({"role": "assistant", "content": response})
    #print("$"*100)
    #print(demo_ephemeral_chat_history_for_chain)
    with st.chat_message("assistant"):
        st.markdown(response)
        print("#"*100)
        #print(global_responses)
        #print("*"*100)
        #print( st.session_state)