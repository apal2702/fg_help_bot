import os
import sys
import streamlit as st
# Import page functions at the top
from app.fg_bot_app import fg_bot_app
from app.llm_test import llm_test
# Create a title for the app
st.title("DSG Auto Assist")

# Create a sidebar with navigation links
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page",["Home","FG HELP Bot","LLM Testing"] )

# Call the appropriate page function based on selection

if page == "FG HELP Bot":
    fg_bot_app()
if page == "LLM Testing":
    llm_test()
