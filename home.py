import streamlit as st   
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from millify import prettify





# Backend Code
data = pd.read_csv("partner_streamlit.csv")

# Create SheerLogic and Fine Media Dataframes
terminated_sheerlogic = data[data['Partner'] == 'Sheer Logic']
headcount_sheerlogic = len(terminated_sheerlogic)
terminated_fine_media = data[data['Partner'] == 'Fine Media'] 
headcount_fine_media = len(terminated_fine_media)

# Count the number of terminated employees (non-null values in 'DateofTermination')
terminated_sheerlogic_COUNT = terminated_sheerlogic['DateofTermination'].notnull().sum()
terminated_fine_media_COUNT = terminated_fine_media['DateofTermination'].notnull().sum()

# Count the total number of employees
total_employees = len(data)

# Calculate the turnover rate
turnover_rate_sheerlogic = round((terminated_sheerlogic_COUNT / total_employees) * 100,1)
turnover_rate_fine_media = round((terminated_fine_media_COUNT / total_employees) * 100,1) 
leave_area_chart = data[['Partner','Amnt_Denied_Leave_Request']]

# Pie Chart

fig = px.pie(
    data_frame=data,
    names='Partner',
    values='Cumulative_Leave_Days',
    title= "Cumulatived Leave Days"
)    
# Gauge Chart
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = 270,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Speed"}))


leave_liability_sheerlogic = data[data['Partner'] == 'Sheer Logic']
leave_liability_sheerlogic = round(leave_liability_sheerlogic['Leave_Liability'].sum())


leave_liability_fine_media = data[data['Partner'] == 'Fine Media']

leave_liability_fine_media = round(leave_liability_fine_media['Leave_Liability'].sum())

leave_liability_sheerlogic = prettify(leave_liability_sheerlogic)

leave_liability_fine_media = prettify(leave_liability_fine_media)


# UI     
st.title("🏠 Off Roll Management System")


st.divider()

with st.container(border=False):
    col1,col2 = st.columns(2,gap='medium',vertical_alignment='top')
    with col1:
        st.image('file (1).svg',width=360)
        col3,col4 = st.columns(2)
        with col3:
            st.metric('Current Leave Liability in KES',leave_liability_sheerlogic,'+2.5%')
        with col4:    
            st.metric('Current Headcount',headcount_sheerlogic,'+2.5%')


            
    with col2:
        st.image("file.svg",width=450) 
        col5,col6 = st.columns(2)
        with col5:
            st.metric('Current Leave Liability in KES',leave_liability_fine_media,'+2.5%')
        with col6:    
            st.metric('Current Headcount',headcount_fine_media,'-2.5%')

st.divider()            
# Space for the Gauge
st.plotly_chart(fig)

st.divider()
try:
    data = pd.read_csv("partner_streamlit.csv")
    st.subheader("Partner Performance")

    # Dropdown for filtering by partner
    selected_partner = st.selectbox(
        "Select Partner:",
        data['Partner'].unique()
    )

    # Filter data based on selected partner
    filtered_df = data[data['Partner'] == selected_partner]

    performance = filtered_df['PerformanceScore'].value_counts()

    #st.dataframe(data=data)


    performance = pd.DataFrame(performance)
    performance = performance.reset_index()
    perform_graph = px.bar(data_frame=performance,x='PerformanceScore',y='count')
    st.divider()
    st.subheader("Agent Appraisal Review Results")
    st.plotly_chart(perform_graph)

except FileNotFoundError:
    st.error("Error: 'partner_streamlit.csv' not found. Please ensure the file path is correct.")
    st.info("Expected path: `partner_streamlit.csv`")
except Exception as e:
    st.error(f"An error occurred while loading partner data: {e}")


st.divider()
st.subheader("Leave Management Overview")

# Get all leave data
leaves_data = leave_data

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
