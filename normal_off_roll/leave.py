# user_view.py
import streamlit as st
from datetime import date, timedelta, datetime

# database_utils.py
import sqlite3
from datetime import datetime, date, timedelta

# DATABASE PATH - IMPORTANT: Update this to your actual database file path
DATABASE_PATH = '/Users/danielwanganga/Documents/Airtel_AI/leave_management.db'

def init_db():
    """Initializes the SQLite database and creates necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Create employees table if it doesn't exist (assuming 'id' is employee_id)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            surname TEXT,
            partner TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            salary INTEGER NOT NULL,
            profile_pic TEXT
        )
    ''')

    # Create leave_entitlements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_entitlements (
            employee_id TEXT PRIMARY KEY,
            annual_leave INTEGER NOT NULL,
            sick_leave INTEGER NOT NULL,
            compensation_leave INTEGER NOT NULL,
            maternity_leave_days INTEGER NOT NULL,
            paternity_leave_days INTEGER NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            description TEXT,
            attachment BOOLEAN,
            status TEXT NOT NULL,
            decline_reason TEXT,
            recall_reason TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_employee_by_id(employee_id): # New function to get employee by ID
    """Fetches employee details by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, surname, partner, department, position, salary, profile_pic FROM employees WHERE id = ?", (employee_id,))
    employee = c.fetchone()
    conn.close()
    return employee

def get_employee_by_name(employee_name):
    """Fetches employee details by name."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name FROM employees WHERE name = ? COLLATE NOCASE", (employee_name,))
    employee = c.fetchone()
    conn.close()
    return employee

def apply_for_leave(employee_id, leave_type, start_date, end_date, description, attachment):
    """Adds a new leave application to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO leaves (employee_id, leave_type, start_date, end_date, description, attachment, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (employee_id, leave_type, start_date.isoformat(), end_date.isoformat(), description, bool(attachment)))
    conn.commit()
    conn.close()

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leaves WHERE employee_id = ? ORDER BY id DESC", (employee_id,)) # Ordered by ID for latest first
    history = c.fetchall()
    conn.close()
    return history

def get_all_pending_leaves():
    """Fetches all leave requests with a 'Pending' status for the manager."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Pending'
    """)
    pending_leaves = c.fetchall()
    conn.close()
    return pending_leaves

def get_approved_leaves():
    """Fetches all leave requests with an 'Approved' status, including dates for recall logic."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Approved'
    """)
    approved_leaves = c.fetchall()
    conn.close()
    return approved_leaves

def update_leave_status(leave_id, new_status, reason=None):
    """Updates the status of a leave request (Approve, Decline, Recall)."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    if new_status == "Declined":
        c.execute("UPDATE leaves SET status = ?, decline_reason = ? WHERE id = ?", (new_status, reason, leave_id))
    elif new_status == "Recalled":
        c.execute("UPDATE leaves SET status = ?, recall_reason = ? WHERE id = ?", (new_status, reason, leave_id))
    else: # Approved
        c.execute("UPDATE leaves SET status = ? WHERE id = ?", (new_status, leave_id))
    conn.commit()
    conn.close()

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    query = """
        SELECT e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.status, l.description, l.decline_reason
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE 1=1
    """
    params = []
    if status_filter:
        placeholders = ','.join('?' * len(status_filter))
        query += f" AND l.status IN ({placeholders})"
        params.extend(status_filter)
    if leave_type_filter:
        placeholders = ','.join('?' * len(leave_type_filter))
        query += f" AND l.leave_type IN ({placeholders})"
        params.extend(leave_type_filter)
    if employee_filter and employee_filter != "All Team Members":
        query += " AND e.name = ?"
        params.append(employee_filter)
    c.execute(query, params)
    leaves = c.fetchall()
    conn.close()
    return leaves

def get_all_employees_from_db():
    """Gets a unique list of all employees from the employees table."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM employees ORDER BY name")
    employees = [row[0] for row in c.fetchall()]
    conn.close()
    return employees

def get_all_leaves_for_display(): # Renamed to avoid conflict, returns full info
    """Fetches all leave records, joining with employee names, for display in general views."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description, l.status
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
    """)
    rows = c.fetchall()
    conn.close()
    leaves = []
    for row in rows:
        leaves.append({
            "id": row["id"],
            "name": row["employee_name"],
            "type": row["leave_type"],
            "start": row["start_date"],
            "end": row["end_date"],
            "description": row["description"],
            "status": row["status"]
        })
    return leaves

def withdraw_leave(leave_id, recall_reason=None):
    """Marks a leave request as Withdrawn with an optional reason."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE leaves SET status = 'Withdrawn', recall_reason = ? WHERE id = ?", (recall_reason, leave_id))
    conn.commit()
    conn.close()

def get_latest_leave_entry_for_employee(employee_id): # New specific function
    """Fetches the details of the most recently added leave entry for a specific employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description, l.status, l.decline_reason, l.recall_reason
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.employee_id = ?
        ORDER BY l.id DESC LIMIT 1
    """, (employee_id,))
    latest_entry = c.fetchone()
    conn.close()
    return latest_entry

def get_employee_leave_entitlements(employee_id):
    """Fetches leave entitlements for a given employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM leave_entitlements WHERE employee_id = ?", (employee_id,))
    entitlements = c.fetchone()
    conn.close()
    return entitlements

def get_employee_used_leave(employee_id, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    query = "SELECT SUM(JULIANDAY(end_date) - JULIANDAY(start_date) + 1) FROM leaves WHERE employee_id = ? AND status = 'Approved'"
    params = [employee_id]
    if leave_type:
        query += " AND leave_type = ?"
        params.append(leave_type)
    c.execute(query, params)
    used_days = c.fetchone()[0]
    conn.close()
    return int(used_days) if used_days else 0

# Initialize DB (ensure this runs only once per session)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

# Leave Policies - Now dynamically fetched or derived
LEAVE_TYPE_MAPPING = {
    "Annual": "annual_leave",
    "Sick": "sick_leave",
    "Maternity": "maternity_leave_days",
    "Paternity": "paternity_leave_days",
    "Study": "compensation_leave",
    "Compassionate": "compensation_leave",
    "Unpaid": None
}

st.set_page_config(layout="wide") # Use wide layout for better display

st.html("""
<style>
    .header-style {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .header-style h1 {
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .header-style p {
        color: #7f8c8d;
        font-size: 1.1em;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stButton>button[key*="withdraw"] {
        background-color: #e74c3c;
    }
    .stButton>button[key*="withdraw"]:hover {
        background-color: #c0392b;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
<div class="header-style">
    <h1>📝 Employee Leave Portal</h1>
    <p style="margin: 0; opacity: 0.9;">Apply, withdraw, and track your leave requests</p>
</div>
""")


# Check if a user is logged in from main.py
logged_in_user_id = st.session_state.get('user_id')
logged_in_full_name = st.session_state.get('full_name')

if logged_in_user_id and logged_in_full_name:
    st.session_state['current_employee_id'] = logged_in_user_id
    st.session_state['current_employee_name'] = logged_in_full_name



    # Sidebar Alert for Leave Status Updates - Now directly for the logged-in user
    st.sidebar.header("Your Latest Leave Status")
    user_latest_leave = get_latest_leave_entry_for_employee(logged_in_user_id)

    if user_latest_leave:
        leave_type = user_latest_leave["leave_type"]
        start_date = user_latest_leave["start_date"]
        end_date = user_latest_leave["end_date"]
        status = user_latest_leave["status"]
        decline_reason = user_latest_leave["decline_reason"]
        recall_reason = user_latest_leave["recall_reason"]

        st.sidebar.markdown(f"**Latest Leave Request**")
        if status == "Declined":
            st.sidebar.error(f"Declined: {leave_type} Leave from {start_date} to {end_date}. Reason: {decline_reason}")
        elif status == "Recalled":
            st.sidebar.warning(f"Recalled: {leave_type} Leave from {start_date} to {end_date}. Reason: {recall_reason}")
        elif status == "Approved":
            st.sidebar.success(f"Approved: {leave_type} Leave from {start_date} to {end_date}")
        elif status == "Pending":
            st.sidebar.info(f"Pending: {leave_type} Leave from {start_date} to {end_date}.")
        elif status == "Withdrawn":
            st.sidebar.info(f"Withdrawn: {leave_type} Leave from {start_date} to {end_date}. Reason: {recall_reason}")
    else:
        st.sidebar.info("No leave entries found for your profile yet.")
else:
    st.sidebar.info("Please log in via the Home Page to access leave features.")
    st.warning("You are not logged in. Please go to the 'Home Page' to log in.")
    st.stop() # Stop execution if not logged in

tabs = st.tabs(["Apply Leave", "Withdraw Leave", "Leave History", "Leave Planner"])

# Apply Leave
with tabs[0]:
    st.header("Apply for Leave")

    employee_id_for_application = st.session_state.get('current_employee_id')

    if employee_id_for_application:
        leave_type = st.selectbox("Select Leave Type", list(LEAVE_TYPE_MAPPING.keys()), key="apply_leave_type")
        start = st.date_input("Start Date", min_value=date.today(), key="apply_start_date")
        end = st.date_input("End Date", min_value=start, key="apply_end_date")
        description = st.text_area("Reason for Leave", key="apply_description")

        attachment_required = leave_type in ["Sick", "Maternity", "Paternity", "Compassionate"]
        attachment = st.file_uploader("Upload Attachment (if required)", type=['pdf', 'jpg', 'png'], key="apply_attachment") if attachment_required else None

        leave_days_taken = (end - start).days + 1

        entitlements = get_employee_leave_entitlements(employee_id_for_application)
        if entitlements:
            leave_column = LEAVE_TYPE_MAPPING.get(leave_type)
            if leave_column and leave_column in entitlements:
                max_days = entitlements[leave_column]
                used_days_for_type = get_employee_used_leave(employee_id_for_application, leave_type)
                remaining_days = max_days - used_days_for_type - leave_days_taken

                st.info(f"**Total Entitled Days ({leave_type})**: {max_days}")
                st.warning(f"**Days Used (this type)**: {used_days_for_type}")
                st.info(f"**Days Applying For**: {leave_days_taken}")
                st.success(f"**Remaining ({leave_type})**: {remaining_days}")

                if st.button("Apply Leave", key="submit_apply_leave"):
                    if remaining_days >= 0:
                        apply_for_leave(employee_id_for_application, leave_type, start, end, description, bool(attachment))
                        st.success("Leave request submitted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Cannot apply for {leave_days_taken} days. You only have {max(0, max_days - used_days_for_type)} days remaining for {leave_type} leave.")
            elif leave_type == "Unpaid":
                st.info("Unpaid leave generally does not have a set maximum, but is subject to approval.")
                if st.button("Apply Leave", key="submit_apply_unpaid"):
                    apply_for_leave(employee_id_for_application, leave_type, start, end, description, bool(attachment))
                    st.success("Unpaid leave request submitted successfully!")
                    st.rerun()
            else:
                st.warning(f"No specific entitlement found for {leave_type}. Please check leave policies or contact HR.")
                if st.button("Apply Leave (No Entitlement Check)", key="submit_apply_no_check"):
                    apply_for_leave(employee_id_for_application, leave_type, start, end, description, bool(attachment))
                    st.success("Leave request submitted successfully (no specific entitlement policy applied).")
                    st.rerun()

        else:
            st.warning("Leave entitlements not found for your profile. Please contact HR to set up entitlements.")
            if st.button("Apply Leave (No Entitlement Check)", key="submit_apply_no_entitlement"):
                apply_for_leave(employee_id_for_application, leave_type, start, end, description, bool(attachment))
                st.success("Leave request submitted successfully (no entitlement check performed).")
                st.rerun()
    else:
        st.info("Please log in via the Home Page to apply for leave.")

# Withdraw Leave
with tabs[1]:
    st.header("Withdraw Leave Request")
    employee_id_for_withdrawal = st.session_state.get('current_employee_id')

    if employee_id_for_withdrawal:
        # Fetch only leaves belonging to the current employee for withdrawal
        all_leaves_for_user = get_leave_history(employee_id_for_withdrawal)
        # Assuming get_leave_history returns tuples, convert to dict-like for easy access if needed
        leaves_to_withdraw = []
        for leave_data in all_leaves_for_user:
            # Need the leave ID to withdraw. get_leave_history doesn't return it currently.
            # We need to modify get_leave_history or introduce a new function that returns IDs.
            # For now, let's assume we fetch all leaves and filter by employee_id and status.
            # This requires get_all_leaves_for_display to return IDs and then filter.
            # Let's adjust get_all_leaves_for_display to be more useful here.
            # get_all_leaves_for_display currently returns dicts, which is good.

            # Re-fetching using a more appropriate function that returns IDs
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT l.id, e.name AS employee_name, l.leave_type, l.start_date, l.end_date, l.description, l.status
                FROM leaves l
                JOIN employees e ON l.employee_id = e.id
                WHERE l.employee_id = ? AND l.status = 'Pending'
            """, (employee_id_for_withdrawal,))
            leaves_to_withdraw_from_db = c.fetchall()
            conn.close()

            leaves_to_withdraw = [
                {"id": row["id"], "type": row["leave_type"], "start": row["start_date"], "end": row["end_date"], "description": row["description"]}
                for row in leaves_to_withdraw_from_db
            ]

        if not leaves_to_withdraw:
            st.info("No pending leave requests to withdraw for your profile.")
        else:
            for i, leave in enumerate(leaves_to_withdraw):
                with st.expander(f"{leave['type']} Leave: {leave['start']} to {leave['end']}"):
                    st.markdown(f"**Reason**: {leave['description']}")
                    withdraw_reason = st.selectbox("Reason for Withdrawal", ["Change of Plan", "Emergency", "Other"], key=f"w{leave['id']}")
                    if withdraw_reason == "Other":
                        withdraw_reason = st.text_area("Please Specify", key=f"wcustom{leave['id']}")
                    if st.button("Withdraw", key=f"withdraw{leave['id']}"):
                        withdraw_leave(leave['id'], withdraw_reason)
                        st.success("Leave withdrawn.")
                        st.rerun()
    else:
        st.info("Please log in via the Home Page to withdraw leave requests.")


# Leave History
with tabs[2]:
    st.header("Your Leave History")
    employee_id_for_history = st.session_state.get('current_employee_id')

    if employee_id_for_history:
        employee_leave_history = get_leave_history(employee_id_for_history)
        if employee_leave_history:
            for hist_entry in employee_leave_history:
                leave_type_hist, start_date_hist, end_date_hist, description_hist, status_hist, decline_reason_hist, recall_reason_hist = hist_entry
                status_display = f"({status_hist})"
                if status_hist == "Declined" and decline_reason_hist:
                    status_display += f" - Reason: {decline_reason_hist}"
                elif status_hist == "Recalled" and recall_reason_hist:
                    status_display += f" - Reason: {recall_reason_hist}"
                elif status_hist == "Withdrawn" and recall_reason_hist: # Display withdraw reason
                     status_display += f" - Reason: {recall_reason_hist}"

                st.markdown(f"""
                <div style='border:1px solid #ddd; padding:10px; margin:10px; border-radius:5px;'>
                    <strong>{leave_type_hist} Leave</strong> {status_display}<br>
                    {start_date_hist} to {end_date_hist}<br>
                    <em>{description_hist}</em>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No leave history found for your profile.")
    else:
        st.info("Please log in via the Home Page to view your leave history.")

# Leave Planner
with tabs[3]:
    st.header("AI-Powered Leave Planner 🧠")
    st.info("This feature helps you plan your leave and delegate tasks.")
    if logged_in_user_id:
        total_days = st.number_input("How many leave days do you want to use?", min_value=1, max_value=365, key="planner_total_days")
        spread_days = st.number_input("Over how many days should they be spread?", min_value=1, max_value=365, key="planner_spread_days")
        deadlines = st.text_area("List any important deadlines during that period", key="planner_deadlines")
        emergency_contact = st.text_input("Emergency Contact Person and Number", key="planner_emergency_contact")
        task_info = st.text_area("List any ongoing tasks or projects", key="planner_task_info")
        delegated_to = st.text_input("Who will pick up your tasks?", key="planner_delegated_to")
        notes = st.text_area("Any notes for task handover", key="planner_notes")
        events = st.text_input("Any events you're planning to attend?", key="planner_events")
        if st.button("Generate Plan", key="generate_plan_btn"):
            leave_plan = {
                "start_date": str(date.today() + timedelta(days=2)),
                "end_date": str(date.today() + timedelta(days=1 + total_days + 1)),
                "days": total_days
            }
            delegation_plan = {
                "task": task_info,
                "delegate": delegated_to,
                "notes": notes
            }
            st.success("✅ Plan Generated")
            st.write("### 🗓️ Leave Schedule")
            st.json(leave_plan)
            st.write("### 🧾 Task Delegation")
            st.json(delegation_plan)
    else:
        st.info("Please log in via the Home Page to use the Leave Planner.")


st.markdown("---")
st.html("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Employee Leave Portal | Built with Streamlit</p>
</div>
""")