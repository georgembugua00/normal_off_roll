# --- leave_management.py ---
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Define the path to your SQLite database
DB_PATH = 'leave_management.db'

def init_db():
    """
    Initializes the SQLite database and creates the 'leaves' table if it doesn't exist.
    This function should be called once at the start of your main application.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                description TEXT,
                attachment BOOLEAN,
                status TEXT NOT NULL,
                decline_reason TEXT,
                recall_reason TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Database initialized at {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")

def apply_for_leave(employee_name, leave_type, start_date, end_date, description, attachment):
    """
    Adds a new leave application to the database with 'Pending' status.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leaves (employee_name, leave_type, start_date, end_date, description, attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (employee_name, leave_type, str(start_date), str(end_date), description, attachment))
        conn.commit()
        conn.close()
        print(f"Leave application submitted for {employee_name}")
    except sqlite3.Error as e:
        print(f"Error applying for leave: {e}")

def get_leave_history(employee_name):
    """
    Fetches the leave history for a specific employee.
    Returns a list of tuples: (leave_type, start_date, end_date, description, status)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT leave_type, start_date, end_date, description, status FROM leaves WHERE employee_name = ?", (employee_name,))
        history = c.fetchall()
        conn.close()
        return history
    except sqlite3.Error as e:
        print(f"Error fetching leave history: {e}")
        return []

def get_all_pending_leaves():
    """
    Fetches all leave requests with a 'Pending' status for the manager's review.
    Returns a list of tuples: (id, employee_name, leave_type, start_date, end_date, description)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description FROM leaves WHERE status = 'Pending'")
        pending_leaves = c.fetchall()
        conn.close()
        return pending_leaves
    except sqlite3.Error as e:
        print(f"Error fetching pending leaves: {e}")
        return []

def update_leave_status(leave_id, new_status, reason=None):
    """
    Updates the status of a leave request (Approved, Declined, Recalled, Withdrawn).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if new_status == "Declined":
            c.execute("UPDATE leaves SET status = ?, decline_reason = ? WHERE id = ?", (new_status, reason, leave_id))
        elif new_status == "Recalled":
            c.execute("UPDATE leaves SET status = ?, recall_reason = ? WHERE id = ?", (new_status, reason, leave_id))
        elif new_status == "Withdrawn":
            c.execute("UPDATE leaves SET status = ?, recall_reason = ? WHERE id = ?", (new_status, reason, leave_id))
        else: # Approved
            c.execute("UPDATE leaves SET status = ? WHERE id = ?", (new_status, leave_id))
        conn.commit()
        conn.close()
        print(f"Leave ID {leave_id} status updated to {new_status}")
    except sqlite3.Error as e:
        print(f"Error updating leave status: {e}")

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """
    Fetches all team leaves with optional filters for the manager's dashboard.
    Returns a list of tuples: (employee_name, leave_type, start_date, end_date, status, description, decline_reason)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        query = "SELECT employee_name, leave_type, start_date, end_date, status, description, decline_reason FROM leaves WHERE 1=1"
        params = []

        if status_filter:
            # Ensure status_filter is a list/tuple for IN clause
            placeholders = ','.join('?' for _ in status_filter)
            query += f" AND status IN ({placeholders})"
            params.extend(status_filter)
            
        if leave_type_filter:
            # Ensure leave_type_filter is a list/tuple for IN clause
            placeholders = ','.join('?' for _ in leave_type_filter)
            query += f" AND leave_type IN ({placeholders})"
            params.extend(leave_type_filter)

        if employee_filter and employee_filter != "All Team Members":
            query += " AND employee_name = ?"
            params.append(employee_filter)

        c.execute(query, params)
        leaves = c.fetchall()
        conn.close()
        return leaves
    except sqlite3.Error as e:
        print(f"Error fetching team leaves: {e}")
        return []

def get_all_employees():
    """
    Gets a unique list of all employees who have applied for leave.
    Returns a list of employee names.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT DISTINCT employee_name FROM leaves")
        employees = [row[0] for row in c.fetchall()]
        conn.close()
        return employees
    except sqlite3.Error as e:
        print(f"Error fetching all employees: {e}")
        return []

def get_all_leaves():
    """
    Fetches all leave records from the database.
    Returns a list of dictionaries, each representing a leave record.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description, status FROM leaves")
        rows = c.fetchall()
        conn.close()
        
        leaves = []
        for row in rows:
            leaves.append({
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "start": row[3],
                "end": row[4],
                "description": row[5],
                "status": row[6]
            })
        return leaves
    except sqlite3.Error as e:
        print(f"Error fetching all leaves: {e}")
        return []

def withdraw_leave(leave_id, recall_reason=None):
    """
    Marks a leave request as 'Withdrawn' with an optional reason.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE leaves SET status = 'Withdrawn', recall_reason = ? WHERE id = ?", (recall_reason, leave_id))
        conn.commit()
        conn.close()
        print(f"Leave ID {leave_id} withdrawn.")
    except sqlite3.Error as e:
        print(f"Error withdrawing leave: {e}")

# --- New functions for HR Dashboard (leave_page.py) ---

def get_approved_days_for_partner(partner_name):
    """
    Calculates total approved leave days for a specific partner.
    For simplicity, assuming 'partner_name' can be mapped to 'employee_name' or a group of employees.
    You might need to adjust this based on how 'Partner' is defined in your DB.
    Here, we'll sum up approved leaves for employees associated with a 'partner'.
    This is a placeholder and might need a more sophisticated join/mapping if 'Partner' is not directly in 'leaves' table.
    For now, it assumes 'employee_name' can be used to group by 'partner'.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # This query is a simplification. If 'Partner' is a separate entity,
        # you'd need a more complex query involving a 'partners' table or a mapping.
        # For now, it counts days for all employees.
        c.execute("""
            SELECT SUM(JULIANDAY(end_date) - JULIANDAY(start_date) + 1)
            FROM leaves
            WHERE status = 'Approved'
            AND employee_name LIKE ?  -- Using LIKE for a simple "partner" mapping
        """, (f"%{partner_name}%",)) # Adjust this if 'partner_name' is a direct employee name
        approved_days = c.fetchone()[0]
        conn.close()
        return approved_days if approved_days is not None else 0
    except sqlite3.Error as e:
        print(f"Error getting approved days for partner {partner_name}: {e}")
        return 0

def get_denied_requests_for_partner(partner_name):
    """
    Counts total denied leave requests for a specific partner.
    Similar simplification as get_approved_days_for_partner.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(id)
            FROM leaves
            WHERE status = 'Declined'
            AND employee_name LIKE ?
        """, (f"%{partner_name}%",))
        denied_requests = c.fetchone()[0]
        conn.close()
        return denied_requests if denied_requests is not None else 0
    except sqlite3.Error as e:
        print(f"Error getting denied requests for partner {partner_name}: {e}")
        return 0

def get_cumulated_leave_days_for_partner(partner_name):
    """
    Calculates total cumulated leave days for a specific partner.
    This metric is usually calculated based on company policy (e.g., accrual rate).
    For demonstration, we'll sum up all leave days (approved, pending, etc.) for employees
    associated with the partner, assuming 'cumulated' means total allocated/used.
    A more accurate 'cumulated' would require a separate table for leave accruals.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # This is a simplified interpretation of "cumulated".
        # It sums up the duration of all non-denied/non-withdrawn leaves.
        c.execute("""
            SELECT SUM(JULIANDAY(end_date) - JULIANDAY(start_date) + 1)
            FROM leaves
            WHERE status IN ('Approved', 'Pending')
            AND employee_name LIKE ?
        """, (f"%{partner_name}%",))
        cumulated_days = c.fetchone()[0]
        conn.close()
        return cumulated_days if cumulated_days is not None else 0
    except sqlite3.Error as e:
        print(f"Error getting cumulated leave days for partner {partner_name}: {e}")
        return 0

def get_upcoming_leaves():
    """
    Fetches leave requests that are approved and start in the future.
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = date.today().strftime('%Y-%m-%d')
        c.execute("""
            SELECT employee_name, leave_type, start_date, end_date
            FROM leaves
            WHERE status = 'Approved' AND start_date > ?
            ORDER BY start_date ASC
        """, (today,))
        rows = c.fetchall()
        conn.close()
        
        upcoming_leaves = []
        for row in rows:
            upcoming_leaves.append({
                "Employee_Name": row[0],
                "Leave_Type": row[1],
                "Start_Date": row[2],
                "End_Date": row[3]
            })
        return upcoming_leaves
    except sqlite3.Error as e:
        print(f"Error fetching upcoming leaves: {e}")
        return []

def get_current_leaves():
    """
    Fetches leave requests that are currently active (start_date <= today <= end_date).
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        today = date.today().strftime('%Y-%m-%d')
        c.execute("""
            SELECT employee_name, leave_type, start_date, end_date
            FROM leaves
            WHERE status = 'Approved' AND start_date <= ? AND end_date >= ?
            ORDER BY start_date ASC
        """, (today, today))
        rows = c.fetchall()
        conn.close()
        
        current_leaves = []
        for row in rows:
            current_leaves.append({
                "Employee_Name": row[0],
                "Leave_Type": row[1],
                "Start_Date": row[2],
                "End_Date": row[3]
            })
        return current_leaves
    except sqlite3.Error as e:
        print(f"Error fetching current leaves: {e}")
        return []



# Initialize DB (ensure this runs only once per session)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

def leave_management_page():
    st.title("📅 Leave Management Dashboard (HR View)")

    # --- Fetching data from SQLite DB for HR metrics ---
    # NOTE: The 'partner' concept (Fine Media, Sheer Logic) is not directly in the 'leaves' table.
    # For demonstration, I'm assuming 'employee_name' might contain partner-specific keywords
    # or you'd have a separate 'employees' table linked to 'partners'.
    # For a robust solution, you'd need a 'partners' table and link employees to them.
    # Here, I'm using a simplified `LIKE` query in the database functions.

    # Data for Fine Media (example)
    approved_days_finemedia = get_approved_days_for_partner("Fine Media")
    deny_days_finemedia = get_denied_requests_for_partner("Fine Media")
    cumulated_leave_finemedia = get_cumulated_leave_days_for_partner("Fine Media")

    # Data for Sheer Logic (example)
    approved_days_sheerlogic = get_approved_days_for_partner("Sheer Logic")
    deny_days_sheerlogic = get_denied_requests_for_partner("Sheer Logic")
    cumulated_leave_sheerlogic = get_cumulated_leave_days_for_partner("Sheer Logic")

    # Fetch Upcoming and Currently on Leave from DB
    upcoming_leaves_df = pd.DataFrame(get_upcoming_leaves())
    current_leaves_df = pd.DataFrame(get_current_leaves())

    fine_media1, sheerlogic2 = st.columns(2)
    
    with fine_media1:
        # st.image("/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/images/file.svg",width=120)
        st.subheader("Fine Media Metrics") # Changed to subheader for clarity
        col1, col2, col3 = st.tabs(['Approved','Denied','Cumulated'])
        with col1:
            st.metric("Days Approved", approved_days_finemedia, '-10%')  # Sample data for change
        with col2:
            st.metric("Declined Leave Requests", deny_days_finemedia, "+10%")
        with col3:
            st.metric("Total Cumulated Leave Days", cumulated_leave_finemedia, '+21.3%')        


    with sheerlogic2:
        # st.image('/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/images/file (1).svg',width=100)
        st.subheader("Sheer Logic Metrics") # Changed to subheader for clarity
        col1, col2, col3 = st.tabs(['Approved','Denied','Cumulated'])
        with col1:  
            st.metric("Days Approved", approved_days_sheerlogic, "+6.4%")
        with col2:
            st.metric("Declined Leave Requests", deny_days_sheerlogic, "+4.3%")
        with col3:
            st.metric("Total Cumulated Leave Days", cumulated_leave_sheerlogic, '+11.3%') 
                
    st.markdown("---")
    st.subheader("Upcoming Leaves")
    if not upcoming_leaves_df.empty:
        st.dataframe(data=upcoming_leaves_df)
    else:
        st.info("No upcoming leaves found.")

    st.subheader("Currently on Leave")
    if not current_leaves_df.empty:
        st.dataframe(data=current_leaves_df)
    else:
        st.info("No employees are currently on leave.")

leave_management_page()
