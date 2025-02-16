import os
import sys
import streamlit as st
# Import page functions at the top

from app.fg_chatbot import fg_help_bot


#role = 'accsec-ai-playground'
#config = load_config(role)
#presto_username, presto_password = 'svc.accsecaiuser' , 'HqEnUTRONCxSBJdr7yK445DE'#load_credentials(config["presto_creds"])
#conn = Connections()
#conn.presto_connector(presto_username, presto_password)
# Create a title for the app
st.title("DSG Auto Assist")

# Create a sidebar with navigation links
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Select a page",
        ["FG HELP Bot"] 
)

# Call the appropriate page function based on selection

if page == "FG HELP Bot":
    fg_help_bot()
