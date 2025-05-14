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
from app.agents.main_agent import MainAgent, get_agent_responses,convert_responses_to_json,format_response

def fg_bot_app():

    
    ollama_models = ['llama3.1', 'mistral','deepseek-r1','deepseek-r1:14b', ]
    openai_models = ['gpt-4o-mini', 'gpt-3.5-turbo-0125']
    
    # Global dictionary to persist responses
    global_responses = {}

    #demo_ephemeral_chat_history_for_chain = ChatMessageHistory()

    def call_fg_help_agent(user_input,model,history,openai_flag):
        print(model)
        agent = Agent(user_input, model, history, openai_flag=openai_flag)
        agent_responses = get_agent_responses(agent)
        json_responses = convert_responses_to_json(agent,agent_responses)
        final_response = agent.final_response_agent(agent_responses['agent3_response'])
        #response = format_response(json_responses)
        #response = agent_responses
        return agent_responses , json_responses , final_response

    def display_chat_history(st, messages):
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def display_agent_responses(st, response,agent_responses,final_response):
        st.markdown(":green[🤖 Summary Agent tried to summarize the response to include all relevant details.] ")
        st.markdown(response['summart_agent_response'])
        st.markdown(":green[🤖 Agent 1 tried to extract meaningful info like Acc sid, Country, MCC_MNC, Date, Error Code etc..] ")
        st.markdown(response['agent1_response'])
        st.markdown(":green[🤖 Agent 2 tried to detect Product] ")
        st.markdown(response['agent2_response'])
        st.markdown(":green[🤖 Agent 3 tried to understand Issues] ")
        st.markdown(response['agent3_response'])
        #st.markdown(":red[🤖 Agent 4 tried to understand Issues] ")
        #st.markdown(response['agent4_response'])
        st.subheader(":blue[Json Response]",divider=True)
        st.markdown(agent_responses['agent1_json_response'])
        st.markdown(agent_responses['agent2_json_response'])
        st.markdown(agent_responses['agent3_json_response'])
        st.subheader(":red[FINAL RESPONSE]",divider=True)
        st.markdown(f":red[{final_response}]")
        
        
    def run_agents_on_chat(st):
        # Increase overall size for window

        model_select = st.sidebar.selectbox("Select Model", ollama_models + openai_models)
        model = model_select
        # Streamlit UI
        st.button("Refresh and Clear", on_click=lambda: [st.session_state["messages"].clear(), st.session_state["history"].clear()])

        # Initialize chat history if not already present
        if "messages" not in st.session_state:
            print("New Session started")
            st.session_state["messages"] = []
            st.session_state["history"] = ChatMessageHistory()
            demo_ephemeral_chat_history_for_chain = st.session_state["history"]

        # Display chat history
        display_chat_history(st, st.session_state["messages"])
        if model in openai_models:
            openai_flag = True
        else:
            openai_flag = False

        # User input
        user_input = st.chat_input("Please share your Query regarding FG / SPP related issue.")
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
                response,agent_responses,final_response = call_fg_help_agent(user_input, str(model),demo_ephemeral_chat_history_for_chain,openai_flag)
                
            st.session_state["history"] = demo_ephemeral_chat_history_for_chain
            st.session_state["messages"].append({"role": "assistant", "content": response})

            display_agent_responses(st, response,agent_responses,final_response)

            print("#"*100)
        sentiment_mapping = [":material/thumb_down:", ":material/thumb_up:"]
        selected = st.feedback("thumbs")
        if selected is not None:
            st.markdown(f"You selected: {sentiment_mapping[selected]}")

    def run_agents_on_Q_A(st):
        # Increase overall size for window
        demo_ephemeral_chat_history_for_chain = ChatMessageHistory()
        model_select = st.sidebar.selectbox("Select Model", ollama_models + openai_models)
        model = model_select
        # Streamlit UI
        #st.button("Refresh and Clear", on_click=lambda: [st.session_state["messages"].clear(), st.session_state["history"].clear()])
        
        if model in ['gpt-4o-mini', 'gpt-3.5-turbo-0125']:
            openai_flag = True
        else:
            openai_flag = False

        # User input
        user_input = st.text_area("Please share your Query regarding FG / SPP related issue.", height= 200)
        button = st.button("Run Agents")
        if button:
            with st.spinner("Thinking........."):
                print("*"*100)
                response,agent_responses,final_response = call_fg_help_agent(user_input, str(model),demo_ephemeral_chat_history_for_chain,openai_flag)
            display_agent_responses(st, response,agent_responses,final_response)
            print("#"*100)
        # Get user feedback
        feedback_col1, feedback_col2 = st.columns([3,1])
        with feedback_col1:
            st.write("Was this response helpful?")
        sentiment_mapping = [":material/thumb_down:", ":material/thumb_up:"]
        selected = st.feedback("thumbs")
        if selected is not None:
            st.markdown(f"Thanks for sharing your feedback! {sentiment_mapping[selected]}")
            # Could store feedback in database here

    st.sidebar.title("Page Selection")
    page = st.sidebar.selectbox("Select a page", ["Q&A Interface", "Chat Interface"])

    if page == "Q&A Interface":
        st.title("GUI - FG / SPP Help channel Bot")
        st.header("Q&A Interface")
        run_agents_on_Q_A(st)
    elif page == "Chat Interface":
        st.title("GUI - FG / SPP Help channel Bot")
        st.header("Chat Interface")
        run_agents_on_chat(st)

if __name__ == "__main__":
    fg_bot_app()