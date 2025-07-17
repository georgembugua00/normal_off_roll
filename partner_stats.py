import streamlit as st
import pandas as pd
from PIL import Image
import plotly.express as px
import sqlite3
import uuid # Needed for potential record IDs if adding/modifying leaves
from datetime import datetime, timedelta # Needed for date handling

# --- Database connection path for leave management ---
LEAVE_DB_PATH = '/Users/danielwanganga/Documents/Airtel_AI/leave_management.db'

def init_leave_db():
    """Initializes the leave_management table if it doesn't exist."""
    conn = sqlite3.connect(LEAVE_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            id TEXT PRIMARY KEY,
            employee_name TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@st.cache_data
def get_all_leaves():
    """Fetches all leave records from the leave management database."""
    conn = sqlite3.connect(LEAVE_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description, status FROM leaves")
    rows = c.fetchall()
    conn.close()
    # Convert sqlite3.Row objects to dictionaries for serializability
    return [dict(row) for row in rows]

# Initialize the leave database when the app starts
init_leave_db()


# --- kenya_towns.py content (as provided) ---
kenya_towns = {
    "Nairobi": [
        "Westlands", "Kilimani", "Kenyatta", "Karen", "Eastleigh",
        "Lang’ata", "South B", "South C", "Ruaraka", "Dagoretti",
        "Kasarani", "Gikambura"
    ],
    "Mombasa": [
        "Mombasa Island", "Nyali", "Likoni", "Changamwe", "Kisauni",
        "Bamburi", "Port Reitz", "Tudor", "Shanzu"
    ],
    "Uasin Gishu (Eldoret)": [
        "Eldoret", "Turbo", "Ziwa", "Moi’s Bridge", "Kesses",
        "Burnt Forest", "Soy"
    ],
    "Kisumu": [
        "Kisumu", "Ahero", "Maseno", "Muhoroni", "Nyahera",
        "Kombewa", "Koru", "Katito", "Kajulu"
    ],
    "Kajiado": [
        "Kajiado", "Ngong", "Kitengela", "Isinya", "Namanga",
        "Ongata Rongai", "Loitokitok", "Ilbisil", "Magadi"
    ]
}


# --- Main HR Portal Content ---
st.title("HR Portal: Leave & Partner Management")

# Load partner data
try:
    data = pd.read_csv("/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/data/partner_streamlit.csv")
    st.subheader("Partner Performance")

    # Dropdown for filtering by partner
    selected_partner = st.selectbox(
        "Select Partner:",
        data['Partner'].unique()
    )

    # Filter data based on selected partner
    filtered_df = data[data['Partner'] == selected_partner]

    performance = filtered_df['PerformanceScore'].value_counts()

    st.dataframe(data=data)


    performance = pd.DataFrame(performance)
    performance = performance.reset_index()
    perform_graph = px.bar(data_frame=performance,x='PerformanceScore',y='count')
    st.divider()
    st.subheader("Agent Appraisal Review Results")
    st.plotly_chart(perform_graph)

except FileNotFoundError:
    st.error("Error: 'partner_streamlit.csv' not found. Please ensure the file path is correct.")
    st.info("Expected path: `/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/data/partner_streamlit.csv`")
except Exception as e:
    st.error(f"An error occurred while loading partner data: {e}")


st.divider()
st.subheader("Leave Management Overview")

# Get all leave data
leaves_data = get_all_leaves()

if leaves_data:
    leaves_df = pd.DataFrame(leaves_data)

    st.write("#### All Leave Requests")
    st.dataframe(leaves_df, use_container_width=True)

    # Basic Leave Statistics
    st.write("#### Leave Statistics")
    leave_status_counts = leaves_df['status'].value_counts().reset_index()
    leave_status_counts.columns = ['Status', 'Count']
    st.bar_chart(leave_status_counts.set_index('Status'))

    # You can add more detailed filtering or management tools here for HR
    st.markdown("---")
    st.write("For detailed leave management (approve/reject), you might want to add more UI elements here.")

else:
    st.info("No leave records found in the database.")

