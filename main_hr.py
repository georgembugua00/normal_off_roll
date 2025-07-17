# --- main.py ---
import streamlit as st
#from inhouse.leave_page import leave_management_page
#from inhouse.partner_stats import hr_portal_page

st.set_page_config(page_title="HR & Leave App", layout="wide")



home = st.Page(
    title="Home",
    page='/Users/danielwanganga/Documents/Airtel_AI/inhouse/home.py',   
    default=True
)
   

leave_management = st.Page(
    title="Partner Stats",
    page='/Users/danielwanganga/Documents/Airtel_AI/inhouse/leave_page.py',   
)

performance = st.Page(
    title='Agent Hub',
    page='/Users/danielwanganga/Documents/Airtel_AI/inhouse/partner_stats.py'
)
payroll = st.Page(
    title='Payroll',
    page='/Users/danielwanganga/Documents/Airtel_AI/inhouse/payroll.py'
)


navigation = st.navigation({
    "Home": [home],
    'Leave Hub' :[leave_management],
    "Payroll" : [payroll],
    "Performance":[performance]
})

navigation.run()


