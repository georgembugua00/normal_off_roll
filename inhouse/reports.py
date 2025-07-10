import streamlit as st
import pandas as pd
import plotly.express as px

# Sample DataFrame (replace with your actual data)
data = pd.read_csv("/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/data/partner_streamlit.csv")
# Dropdown for filtering by partner
selected_partner = st.selectbox(
    "Select Partner:",
    data['Partner'].unique()
)

# Filter data based on selected partner
filtered_df = data[data['Partner'] == selected_partner]

# Salary Distribution
st.subheader("Salary Distribution")
salary_fig = px.histogram(filtered_df, x='Salary', title='Salary Distribution')
st.plotly_chart(salary_fig)