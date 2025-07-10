import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta, datetime
import os
import hashlib
import json
import logging
#from dotenv import load_dotenv

# Load environment variables
#load_dotenv()

# --- Configuration ---
# DATABASE PATH - IMPORTANT: This path should be accessible by your Docker container
# For Docker, it's often best to use a path relative to the container's WORKDIR
# or a path within a mounted volume.
DATABASE_PATH = 'leave_management.db' # Will be created in the container's working directory

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Dummy USERS data (in a real app, this would come from a secure database) ---
# This dictionary defines user roles and basic information.
USERS = {
    "23188032": {
        "role": "Sales Executive",
        "name": "Stacy",
        "surname": "Mbugua",
        "email": "stacy@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/face-portrait-manager-happy-black-260nw-2278812777.jpg",
        "position": "Sales Executive",
        "managing_partner": "Fine Media",
        "cumulative_leave": 21,
        "used_leave": 6
    },
    "1388231": {
        "role": "Manager",
        "name": "Bryan",
        "surname": "Osoro",
        "email": "bryan@airtel.com",
        "profile_pic": "https://www.shutterstock.com/image-photo/smiling-cheerful-young-adult-african-260nw-1850821510.jpg",
        "position": "Zonal Sales Manager",
        "franchise_type": "On Roll"
    },
    "daniel": {
        "role": "HR", # Added HR role
        "name": "Daniel",
        "surname": "Wanganga",
        "position": "HR Manager",
        "managing_partner": "Airtel HR",
        "cumulative_leave": 21,
        "used_leave": 4,
        "profile_pic": None,
    },
    "testuser": { # Added a generic test user for "Sales Executive" role
        "role": "Sales Executive",
        "name": "Test",
        "surname": "User",
        "email": "test@airtel.com",
        "profile_pic": "https://placehold.co/100x100/aabbcc/ffffff?text=TU",
        "position": "Sales Executive",
        "managing_partner": "Test Partner",
        "cumulative_leave": 21,
        "used_leave": 0
    },
}

# Generate simple logins and passwords for demonstration
USER_CREDENTIALS = {}
for user_id, user_data in USERS.items():
    if "name" in user_data:
        username = user_data["name"].lower()
        USER_CREDENTIALS[username] = {
            "password": "password123", # Simple password for demonstration
            "user_id": user_id,
            "full_name": f"{user_data.get('name', '')} {user_data.get('surname', '')}".strip(),
            "role": user_data.get("role", "Employee") # Store role in credentials
        }

# --- Database Utilities ---
def init_db():
    """Initializes the SQLite database and creates necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Create employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            surname TEXT,
            partner TEXT,
            department TEXT,
            position TEXT,
            salary INTEGER,
            profile_pic TEXT
        )
    ''')

    # Create leave_entitlements table
    c.execute('''
        CREATE TABLE IF NOT EXISTS leave_entitlements (
            employee_id TEXT PRIMARY KEY,
            annual_leave INTEGER NOT NULL DEFAULT 0,
            sick_leave INTEGER NOT NULL DEFAULT 0,
            compensation_leave INTEGER NOT NULL DEFAULT 0,
            maternity_leave_days INTEGER NOT NULL DEFAULT 0,
            paternity_leave_days INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    ''')

    # Create leaves table
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

    # Populate employees and entitlements if empty (for demo purposes)
    for user_id, user_data in USERS.items():
        try:
            c.execute("INSERT OR IGNORE INTO employees (id, name, surname, partner, department, position, salary, profile_pic) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (user_id, user_data.get("name"), user_data.get("surname"), user_data.get("managing_partner"),
                       user_data.get("department"), user_data.get("position"), user_data.get("salary", 0), user_data.get("profile_pic")))
            conn.commit()
            
            # Insert entitlements if employee is new and not already in entitlements
            c.execute("INSERT OR IGNORE INTO leave_entitlements (employee_id, annual_leave, sick_leave, compensation_leave, maternity_leave_days, paternity_leave_days) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, user_data.get("cumulative_leave", 21), 10, 5, 90, 7))
            conn.commit()
        except sqlite3.IntegrityError as e:
            logger.warning(f"Skipping employee/entitlement insert for {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error populating employee/entitlement for {user_id}: {e}")


    conn.close()
    logger.info("Database initialized and populated.")

# Initialize DB (ensure this runs only once per session)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

def get_employee_by_id(employee_id):
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
    logger.info(f"Leave application submitted for employee_id: {employee_id}, type: {leave_type}")

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leaves WHERE employee_id = ? ORDER BY id DESC", (employee_id,))
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
    logger.info(f"Leave ID {leave_id} status updated to {new_status} by {st.session_state.get('full_name', 'Unknown')}")

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

def get_all_leaves_for_display():
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
    logger.info(f"Leave ID {leave_id} withdrawn by {st.session_state.get('full_name', 'Unknown')}")

def get_latest_leave_entry_for_employee(employee_id):
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

def get_approved_days_for_partner(partner_name):
    """Calculates total approved leave days for a specific partner."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT SUM(JULIANDAY(l.end_date) - JULIANDAY(l.start_date) + 1)
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Approved' AND e.partner = ?
    """, (partner_name,))
    approved_days = c.fetchone()[0]
    conn.close()
    return approved_days if approved_days is not None else 0

def get_denied_requests_for_partner(partner_name):
    """Counts total denied leave requests for a specific partner."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(l.id)
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Declined' AND e.partner = ?
    """, (partner_name,))
    denied_requests = c.fetchone()[0]
    conn.close()
    return denied_requests if denied_requests is not None else 0

def get_cumulated_leave_days_for_partner(partner_name):
    """Calculates total cumulated leave days for a specific partner."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT SUM(JULIANDAY(l.end_date) - JULIANDAY(l.start_date) + 1)
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status IN ('Approved', 'Pending') AND e.partner = ?
    """, (partner_name,))
    cumulated_days = c.fetchone()[0]
    conn.close()
    return cumulated_days if cumulated_days is not None else 0

def get_upcoming_leaves():
    """Fetches leave requests that are approved and start in the future."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')
    c.execute("""
        SELECT e.name, l.leave_type, l.start_date, l.end_date
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Approved' AND l.start_date > ?
        ORDER BY l.start_date ASC
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

def get_current_leaves():
    """Fetches leave requests that are currently active (start_date <= today <= end_date)."""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')
    c.execute("""
        SELECT e.name, l.leave_type, l.start_date, l.end_date
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'Approved' AND l.start_date <= ? AND l.end_date >= ?
        ORDER BY l.start_date ASC
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

# --- CSS Injection ---
def inject_premium_css():
    st.html("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #1f1f1f 0%, #000000 50%, #1a1a1a 100%);
            font-family: 'Inter', sans-serif;
            color: white;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        /* Premium glassmorphism cards with red accents */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(220, 38, 38, 0.3);
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 60px rgba(220, 38, 38, 0.2);
            border-color: rgba(220, 38, 38, 0.5);
        }
        
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #dc2626, #ef4444, #f87171, #dc2626);
            background-size: 200% 100%;
            animation: redShimmer 3s ease-in-out infinite;
        }
        
        @keyframes redShimmer {
            0%, 100% { background-position: 200% 0; }
            50% { background-position: -200% 0; }
        }
        
        /* Premium sidebar with black theme */
        .css-1d391kg {
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border-right: 2px solid rgba(220, 38, 38, 0.3);
        }
        
        /* Notification bell with red pulse animation */
        .notification-container {
            position: relative;
            display: inline-block;
        }
        
        .notification-bell {
            font-size: 2rem;
            color: #dc2626;
            animation: redPulse 2s infinite;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .notification-bell:hover {
            transform: scale(1.2);
            color: #ef4444;
            filter: drop-shadow(0 0 10px #dc2626);
        }
        
        @keyframes redPulse {
            0% { transform: scale(1); color: #dc2626; }
            50% { transform: scale(1.1); color: #ef4444; }
            100% { transform: scale(1); color: #dc2626; }
        }
        
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: linear-gradient(45deg, #dc2626, #ef4444);
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 700;
            animation: redBounce 1s infinite;
            box-shadow: 0 0 10px rgba(220, 38, 38, 0.5);
        }
        
        @keyframes redBounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-5px); }
            60% { transform: translateY(-3px); }
        }
        
        /* Status badges with red theme */
        .status-badge {
            display: inline-block;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .status-pending {
            background: linear-gradient(45deg, #dc2626, #ef4444);
            color: white;
            box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
        }
        
        .status-approved {
            background: linear-gradient(45deg, #1f1f1f, #374151);
            color: white;
            border: 1px solid #dc2626;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }
        
        .status-declined {
            background: linear-gradient(45deg, #991b1b, #7f1d1d);
            color: white;
            box-shadow: 0 4px 20px rgba(153, 27, 27, 0.4);
        }
        
        .status-recalled {
            background: linear-gradient(45deg, #b91c1c, #991b1b);
            color: white;
            box-shadow: 0 4px 20px rgba(185, 28, 28, 0.4);
        }
        
        /* Premium buttons with red theme */
        .premium-btn {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            border: none;
            border-radius: 25px;
            color: white;
            padding: 0.75rem 2rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .premium-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(220, 38, 38, 0.5);
            background: linear-gradient(45deg, #ef4444, #dc2626);
        }
        
        .premium-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .premium-btn:hover::before {
            left: 100%;
        }
        
        .danger-btn {
            background: linear-gradient(45deg, #7f1d1d, #450a0a);
            box-shadow: 0 8px 25px rgba(127, 29, 29, 0.3);
        }
        
        .danger-btn:hover {
            box-shadow: 0 12px 35px rgba(127, 29, 29, 0.5);
        }
        
        /* Employee cards with black/red theme */
        .employee-card {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(220, 38, 38, 0.2);
            transition: all 0.3s ease;
            position: relative;
        }
        
        .employee-card:hover {
            background: rgba(0, 0, 0, 0.6);
            transform: translateX(10px);
            border-color: rgba(220, 38, 38, 0.5);
            box-shadow: 0 10px 30px rgba(220, 38, 38, 0.2);
        }
        
        .employee-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(45deg, #dc2626, #991b1b);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            font-weight: 700;
            margin-bottom: 1rem;
            border: 2px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        /* Leave type icons */
        .leave-type-icon {
            font-size: 2rem;
            margin-right: 0.5rem;
            vertical-align: middle;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }
        
        /* Stats cards with red/black gradients */
        .stats-card {
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(31, 31, 31, 0.4));
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(220, 38, 38, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stats-card:hover {
            transform: scale(1.05);
            border-color: rgba(220, 38, 38, 0.6);
            box-shadow: 0 15px 40px rgba(220, 38, 38, 0.2);
        }
        
        .stats-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(220, 38, 38, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .stats-card:hover::before {
            opacity: 1;
        }
        
        .stats-number {
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, #dc2626, #ef4444, #f87171);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 20px rgba(220, 38, 38, 0.3);
        }
        
        .stats-label {
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Premium typography */
        h1, h2, h3 {
            color: white;
            font-weight: 800;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        
        .welcome-text {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.6;
            text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
            font-weight: 400;
        }
        
        /* Tab styling with red accents */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 15px;
            padding: 0.5rem;
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        .stTabs [data-baseweb="tab-list"] button {
            background: transparent;
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 600;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            color: white;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
            border-color: rgba(220, 38, 38, 0.5);
        }
        
        .stTabs [data-baseweb="tab-list"] button:hover {
            border-color: rgba(220, 38, 38, 0.3);
            background: rgba(220, 38, 38, 0.1);
        }
        
        /* Calendar styling */
        .fc {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 1rem;
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        .fc-toolbar-title {
            color: white !important;
            font-weight: 700 !important;
        }
        
        .fc-button-primary {
            background: linear-gradient(45deg, #dc2626, #991b1b) !important;
            border-color: #dc2626 !important;
        }
        
        .fc-button-primary:hover {
            background: linear-gradient(45deg, #ef4444, #dc2626) !important;
        }
        
        /* Sidebar content */
        .sidebar-content {
            color: white;
        }
        
        .sidebar-content h3 {
            color: #dc2626;
            font-weight: 700;
        }
        
        /* Input styling with red accents */
        .stSelectbox > div > div {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 10px;
            color: white;
        }
        
        .stTextInput > div > div > input {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 10px;
            color: white;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #dc2626;
            box-shadow: 0 0 10px rgba(220, 38, 38, 0.3);
        }
        
        /* Loading animations */
        .loading-spinner {
            border: 3px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            border-top: 3px solid #dc2626;
            width: 30px;
            height: 30px;
            animation: redSpin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes redSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Button overrides for Streamlit */
        .stButton > button {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
        }
        
        .stButton > button:hover {
            background: linear-gradient(45deg, #ef4444, #dc2626);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
        }
        
        /* Success, error, and info message styling */
        .stSuccess {
            background: rgba(0, 0, 0, 0.6);
            border-left: 4px solid #dc2626;
            color: white;
        }
        
        .stError {
            background: rgba(127, 29, 29, 0.3);
            border-left: 4px solid #7f1d1d;
            color: white;
        }
        
        .stInfo {
            background: rgba(0, 0, 0, 0.6);
            border-left: 4px solid #dc2626;
            color: white;
        }
        
        .stWarning {
            background: rgba(185, 28, 28, 0.3);
            border-left: 4px solid #b91c1c;
            color: white;
        }
        
        /* Expandar styling */
        .streamlit-expanderHeader {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(220, 38, 38, 0.3);
            color: white;
        }
        
        .streamlit-expanderContent {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .glass-card {
                padding: 1rem;
                margin: 0.5rem 0;
            }
            
            .stats-number {
                font-size: 2rem;
            }
            
            .employee-avatar {
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
            }
        }
        
        /* Special red glow effects */
        .red-glow {
            box-shadow: 0 0 20px rgba(220, 38, 38, 0.5);
        }
        
        .red-glow:hover {
            box-shadow: 0 0 30px rgba(220, 38, 38, 0.7);
        }
    </style>
    """)

# --- UI Components / Page Views ---

# 1. Employee Leave Portal (from leave.py)
LEAVE_TYPE_MAPPING = {
    "Annual": "annual_leave",
    "Sick": "sick_leave",
    "Maternity": "maternity_leave_days",
    "Paternity": "paternity_leave_days",
    "Study": "compensation_leave",
    "Compassionate": "compensation_leave",
    "Unpaid": None
}

def employee_leave_portal_page():
    logger.info(f"User {st.session_state.get('full_name', 'Unknown')} ({st.session_state.get('user_id', 'N/A')}) - Role: {st.session_state.get('user_role', 'N/A')} accessed Employee Leave Portal.")

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

    logged_in_user_id = st.session_state.get('user_id')
    logged_in_full_name = st.session_state.get('full_name')

    if logged_in_user_id and logged_in_full_name:
        st.session_state['current_employee_id'] = logged_in_user_id
        st.session_state['current_employee_name'] = logged_in_full_name

        # Sidebar Alert for Leave Status Updates
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
        return # Use return instead of st.stop() to allow other parts of the app to render if needed

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
                    elif status_hist == "Withdrawn" and recall_reason_hist:
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

# 2. Manager Leave Request Manager (from home_page.py)
def manager_leave_request_manager_page():
    logger.info(f"User {st.session_state.get('full_name', 'Unknown')} ({st.session_state.get('user_id', 'N/A')}) - Role: {st.session_state.get('user_role', 'N/A')} accessed Manager Leave Request Manager.")

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
        .stButton>button[key*="decline"] {
            background-color: #e74c3c;
        }
        .stButton>button[key*="decline"]:hover {
            background-color: #c0392b;
        }
        .stButton>button[key*="recall"] { /* New style for recall button */
            background-color: #f39c12; /* Orange */
        }
        .stButton>button[key*="recall"]:hover {
            background-color: #e67e22; /* Darker orange */
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
        <h1>📅 Leave Request Manager</h1>
        <p style="margin: 0; opacity: 0.9;">Review and manage employee leave requests</p>
    </div>
    """)

    def pending_leaves_view():
        st.header("Pending Leave Requests for Review")
        pending_leaves = get_all_pending_leaves()

        if not pending_leaves:
            st.success("✨ All caught up! There are no pending leave requests.")
            return

        for leave in pending_leaves:
            leave_id = leave["id"]
            employee = leave["employee_name"]
            leave_type = leave["leave_type"]
            start_date = leave["start_date"]
            end_date = leave["end_date"]
            description = leave["description"]

            with st.expander(f"Request from {employee} ({leave_type}) - {start_date} to {end_date}", expanded=True):
                st.write(f"**Employee:** {employee}")
                st.write(f"**Leave Type:** {leave_type}")
                st.write(f"**Dates:** {start_date} to {end_date}")
                st.write(f"**Reason:** {description}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Approve", key=f"approve_{leave_id}"):
                        update_leave_status(leave_id, "Approved")
                        st.success(f"Leave for {employee} approved.")
                        st.rerun()
                with col2:
                    if st.button("❌ Decline", key=f"decline_{leave_id}"):
                        if f"show_reason_{leave_id}" not in st.session_state:
                            st.session_state[f"show_reason_{leave_id}"] = False
                        st.session_state[f"show_reason_{leave_id}"] = not st.session_state[f"show_reason_{leave_id}"]

                        if st.session_state[f"show_reason_{leave_id}"]:
                            decline_reason = st.text_input("Reason for declining:", key=f"reason_{leave_id}")
                            if st.button("Confirm Decline", key=f"confirm_decline_{leave_id}"):
                                if decline_reason:
                                    update_leave_status(leave_id, "Declined", reason=decline_reason)
                                    st.error(f"Leave for {employee} declined.")
                                    st.rerun()
                                else:
                                    st.warning("A reason is required to decline a request.")

    def approved_leaves_for_recall_view():
        st.header("Approved Leaves (for Recall)")
        approved_leaves = get_approved_leaves()

        if not approved_leaves:
            st.info("No approved leaves currently.")
            return

        for leave in approved_leaves:
            leave_id = leave["id"]
            employee = leave["employee_name"]
            leave_type = leave["leave_type"]
            start_date_str = leave["start_date"]
            end_date_str = leave["end_date"]
            description = leave["description"]

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                st.error(f"⚠️ Invalid date format in leave ID {leave_id} for {employee}: {start_date_str} to {end_date_str}")
                continue

            today = date.today()

            if today > end_date:
                days_left = 0
            elif today < start_date:
                days_left = (end_date - start_date).days + 1
            else:
                days_left = (end_date - today).days + 1

            with st.expander(f"Approved Leave for {employee} ({leave_type}) - {start_date_str} to {end_date_str}", expanded=True):
                st.write(f"**Employee:** {employee}")
                st.write(f"**Leave Type:** {leave_type}")
                st.write(f"**Dates:** {start_date_str} to {end_date_str}")
                st.write(f"**Reason:** {description}")
                st.write(f"**Days Remaining:** {days_left}")

                if st.button("↩️ Recall Leave", key=f"recall_{leave_id}"):
                    if days_left > 3:
                        recall_reason = "OPERATIONS"
                        update_leave_status(leave_id, "Recalled", reason=recall_reason)
                        st.warning(f"Leave for {employee} has been recalled due to {recall_reason}.")
                        st.rerun()
                    else:
                        st.error(f"Cannot recall leave for {employee}. Less than 3 days ({days_left} days) remaining or leave has ended.")

    def team_leaves_dashboard_view():
        st.header("Team Leave Dashboard")

        all_employees = ["All Team Members"] + get_all_employees_from_db()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_employee = st.selectbox("Filter by Employee", all_employees)
        with col2:
            selected_status = st.multiselect("Filter by Status", ["Pending", "Approved", "Declined", "Withdrawn", "Recalled"], default=["Pending", "Approved"])
        with col3:
            all_leave_types = ["Annual", "Sick", "Maternity", "Paternity", "Study", "Compassionate", "Unpaid"]
            selected_leave_type = st.multiselect("Filter by Leave Type", all_leave_types)

        filtered_leaves = get_team_leaves(
            status_filter=selected_status if selected_status else None,
            leave_type_filter=selected_leave_type if selected_leave_type else None,
            employee_filter=selected_employee if selected_employee != "All Team Members" else None
        )

        if not filtered_leaves:
            st.info("No team leaves found matching the selected filters.")
            return

        st.subheader("Filtered Team Leaves")
        leave_data = []
        for leave in filtered_leaves:
            leave_data.append({
                "Employee": leave["employee_name"],
                "Leave Type": leave["leave_type"],
                "Start Date": leave["start_date"],
                "End Date": leave["end_date"],
                "Status": leave["status"],
                "Description": leave["description"],
                "Decline Reason": leave["decline_reason"] if leave["decline_reason"] else "N/A"
            })

        st.dataframe(pd.DataFrame(leave_data), use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Pending Requests", "Approved Leaves (Recall)", "Team Leave Dashboard"])

    with tab1:
        pending_leaves_view()

    with tab2:
        approved_leaves_for_recall_view()

    with tab3:
        team_leaves_dashboard_view()

    st.markdown("---")
    st.html("""
    <div style="text-align: center; color: #6b7280; padding: 1rem;">
        <p>Leave Request Management System | Manager View | Built with Streamlit</p>
    </div>
    """)

# 3. HR Leave Management Dashboard (from leave_page.py)
def hr_leave_management_dashboard_page():
    logger.info(f"User {st.session_state.get('full_name', 'Unknown')} ({st.session_state.get('user_id', 'N/A')}) - Role: {st.session_state.get('user_role', 'N/A')} accessed HR Leave Management Dashboard.")

    st.title("📅 Leave Management Dashboard (HR View)")

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
        st.subheader("Fine Media Metrics")
        col1, col2, col3 = st.tabs(['Approved','Denied','Cumulated'])
        with col1:
            st.metric("Days Approved", approved_days_finemedia, '-10%')
        with col2:
            st.metric("Declined Leave Requests", deny_days_finemedia, "+10%")
        with col3:
            st.metric("Total Cumulated Leave Days", cumulated_leave_finemedia, '+21.3%')        

    with sheerlogic2:
        st.subheader("Sheer Logic Metrics")
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

# 4. Team Leave Calendar (from team_leaves.py)
def team_leave_calendar_page():
    logger.info(f"User {st.session_state.get('full_name', 'Unknown')} ({st.session_state.get('user_id', 'N/A')}) - Role: {st.session_state.get('user_role', 'N/A')} accessed Team Leave Calendar.")

    st.header("Team Leave Calendar")
    st.info("Calendar view shows all approved leaves.")
    approved_leaves = get_team_leaves(status_filter=["Approved"])
                
    events = []
    for leave in approved_leaves:
        # Assuming leave is a sqlite3.Row object or tuple (employee_name, leave_type, start_date, end_date, ...)
        # Adjust indexing if the order of columns from get_team_leaves changes
        events.append({
                        "title": f"{leave['employee_name']} - {leave['leave_type']}",
                        "start": leave['start_date'],
                        "end": leave['end_date'],
            })
                
    try:
        from streamlit_calendar import calendar
        calendar(events=events)
    except ImportError:
        st.warning("`streamlit_calendar` not installed. Displaying events as a list.")
        st.write(events)

# --- Main Application Logic ---
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
                    st.session_state.user_role = USER_CREDENTIALS[username]["role"] # Store user role
                    logger.info(f"User {username} ({st.session_state.user_id}) logged in as {st.session_state.user_role}.")
                    st.success(f"Welcome, {st.session_state.full_name}!")
                    st.rerun() # Rerun to display the main application
                else:
                    logger.warning(f"Failed login attempt for username: {username}.")
                    st.error("Invalid Username or Password")
    else:
        main_app()

def main_app():
    # Define pages based on user role
    user_role = st.session_state.get('user_role', 'Guest')
    logger.info(f"Rendering main app for user: {st.session_state.get('full_name', 'N/A')}, Role: {user_role}")

    pages = {}

    # Common pages for all logged-in users (e.g., Home, Logout)
    home_page = st.Page(
        page="Home",
        icon=":material/home:",
        default=True,
        title=lambda: st.write(f"## Welcome, {st.session_state.full_name} ({st.session_state.user_role})!") # Simple home for now
    )
    pages["Home"] = [home_page]

    if user_role == "Sales Executive":
        l_hub = st.Page(
            title="My Leave Hub",
            icon=":material/flight_takeoff:",
            page='normal_employee/main.py'
        )
        pages["Leave Management"] = [l_hub]
    elif user_role == "Manager":
        manager_hub = st.Page(
            title="Manage Team Leaves",
            icon=":material/group_add:",
            page='Manager/home_page.py'
        )
        team_calendar = st.Page(
            title="Team Leave Calendar",
            icon=":material/calendar_month:",
            page='Manager/team_overview'
        )
        pages["Leave Management"] = [manager_hub, team_calendar]
    elif user_role == "HR":
        hr_dashboard = st.Page(
            title="HR Leave Dashboard",
            icon=":material/dashboard:",
            func=hr_leave_management_dashboard_page
        )
        manager_hub = st.Page( # HR can also manage team leaves
            title="Manage Team Leaves",
            icon=":material/group_add:",
            func=manager_leave_request_manager_page
        )
        team_calendar = st.Page(
            title="Team Leave Calendar",
            icon=":material/calendar_month:",
            func=team_leave_calendar_page
        )
        pages["HR & Leave"] = [hr_dashboard, manager_hub, team_calendar]
    else:
        st.warning("Your role does not have access to specific leave functionalities.")

    # Add a logout button
    def logout():
        st.session_state.logged_in = False
        if 'username' in st.session_state: del st.session_state.username
        if 'user_id' in st.session_state: del st.session_state.user_id
        if 'full_name' in st.session_state: del st.session_state.full_name
        if 'user_role' in st.session_state: del st.session_state.user_role
        logger.info(f"User logged out.")
        st.rerun()

    st.sidebar.button("Logout", on_click=logout)

    # Run the navigation
    page_navigator = st.navigation(pages)
    page_navigator.run()

# --- Main Execution ---
if __name__ == "__main__":
    st.set_page_config(
        page_title="Airtel Leave Portal",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "This is a Streamlit-based Leave Management Application."
        }
    )
    inject_premium_css()
    login_page()

