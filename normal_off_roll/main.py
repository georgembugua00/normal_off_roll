import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import hashlib
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Airtel Partner Portal",
    layout="wide",
    initial_sidebar_state="collapsed", # Keep this for initial state
)

# Dummy USERS data (in a real app, this would come from a secure database)
# This is extracted from home_page.py for demonstration.
USERS = {
    "23188032": {
        "role": "Sales Executive",
        "name": "Stacy",
        "surname": "Mbugua",
        "email": "george@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/face-portrait-manager-happy-black-260nw-2278812777.jpg",
        "position": "Sales Executive",
        "managing_partner": "Fine Media",
        "cumulative_leave": 21,
        "used_leave": 6
    },
    "1388231": {
        "role": "Manager",
        "name": "Bryan Osoro",
        "email": "john@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/smiling-cheerful-young-adult-african-260nw-1850821510.jpg" ,
        "position": "Zonal Sales Manager",
        "franchise_type": "On Roll"
    },
      "daniel": {
        "name": "Daniel",
        "surname": "Wanganga",
        "position": "Sales Exec",
        "managing_partner": "Sheer Logic",
        "franchise_type": "Franchise",
        "cumulative_leave": 21,
        "used_leave": 4,
        "profile_pic": None,
    },
}

# Generate simple logins and passwords
# Usernames will be lowercase version of the employee's first name
# Passwords will be 'password123' for all
USER_CREDENTIALS = {}
for user_id, user_data in USERS.items():
    if "name" in user_data:
        username = user_data["name"].lower()
        USER_CREDENTIALS[username] = {
            "password": "password123", # Simple password for demonstration
            "user_id": user_id,
            "full_name": f"{user_data.get('name', '')} {user_data.get('surname', '')}".strip()
        }

# --- Login Authentication ---
def login_page():
    # Only show the login title if not logged in
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Airtel Partner Portal Login") # Show title only on login page
        with st.form("login_form"):
            username = st.text_input("Username").lower()
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = USER_CREDENTIALS[username]["user_id"]
                    st.session_state.full_name = USER_CREDENTIALS[username]["full_name"]
                    st.success(f"Welcome, {st.session_state.full_name}!")
                    st.rerun() # Rerun to display the main application
                else:
                    st.error("Invalid Username or Password")
    else:
        # If logged in, proceed to the main application
        main_app()

def main_app():
    # Placeholder for actual page imports. In a real app, these would be in separate files.
    # For this response, we'll just show the navigation.
    # You would replace these with actual imports and function calls for your pages.
    # For now, we'll mimic the structure from main.py
    # ========== PAGE SETUP ==========

    home_page = st.Page(
        page="home_page.py", # This would be the path to your actual home page file
        title="Home Page",
        icon=":material/home:",
        default=True
    )


    knowledge_base = st.Page(
        page="knowledgebases.py", # Path to knowledgebases.py
        title="Knowledge Base",
        icon=":material/cognition:"
    )

    l_hub = st.Page(
        page="leave.py", # Path to leave.py
        title="Leave Management",
        icon=":material/flight_takeoff:"
    )




    # ========== NAVIGATION ==========
    page_navigator = st.navigation({
        "Home": [home_page],
        "Leave Hub": [l_hub]
    })

    page_navigator.run()

 

# Run the login page first
login_page()
