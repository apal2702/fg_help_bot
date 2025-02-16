import streamlit as st
from app.agents.presto_query_agent import AccountInfo

def get_account_details(account_sid, country = None, mcc = None):
    acc_info_obj = AccountInfo(st, account_sid, country, mcc)
    acc_info_obj.get_account_info()

    #return account_info


def chatbot_response(user_input):
    # Simple example bot logic
    return f"Bot: You said '{user_input}'"

st.set_page_config(layout="wide")

# Streamlit app
st.title("FG/ SPP Account Analysis")

# Text input
user_input = st.text_input("Enter Account SID", max_chars = 40)
# Additional inputs
col1, col2, col3 = st.columns(3)
with col1:
    country_input = st.text_input("Enter Country (optional)", key="country")
with col2:
    mcc_input = st.text_input("Enter MCC (optional)", key="mcc") 
with col3:
    mnc_input = st.text_input("Enter MNC (optional)", key="mnc")


# Button
if st.button("Send"):
    if user_input:
        response = get_account_details(user_input)
        st.write(response)
    else:
        st.write("Please enter a message.")