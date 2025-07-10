import streamlit as st
from datetime import date, timedelta
#from helpers.database import * # Import our new database module

#DATABASE LOGIC
import sqlite3
from datetime import date



def init_db():
    """Initializes the SQLite database and creates the leaves table if it doesn't exist."""
    conn = sqlite3.connect('/Users/danielwanganga/Documents/Airtel_AI/leave_management.db')
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

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard."""
    conn = sqlite3.connect('/Users/danielwanganga/Documents/Airtel_AI/leave_management.db')
    c = conn.cursor()
    
    query = "SELECT employee_name, leave_type, start_date, end_date, status, description, decline_reason FROM leaves WHERE 1=1"
    params = []

    if status_filter:
        query += f" AND status IN ({','.join('?' for _ in status_filter)})"
        params.extend(status_filter)
        
    if leave_type_filter:
        query += f" AND leave_type IN ({','.join('?' for _ in leave_type_filter)})"
        params.extend(leave_type_filter)

    if employee_filter and employee_filter != "All Team Members":
        query += " AND employee_name = ?"
        params.append(employee_filter)

    c.execute(query, params)
    leaves = c.fetchall()
    conn.close()
    return leaves

def get_all_employees():
    """Gets a unique list of all employees who have applied for leave."""
    conn = sqlite3.connect('/Users/danielwanganga/Documents/Airtel_AI/leave_management.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT employee_name FROM leaves")
    employees = [row[0] for row in c.fetchall()]
    conn.close()
    return employees

def get_leave_history(employee_name):
    """Fetches the leave history for a specific employee."""
    conn = sqlite3.connect('/Users/danielwanganga/Documents/Airtel_AI/leave_management.db')
    c = conn.cursor()
    c.execute("SELECT leave_type, start_date, end_date, description, status FROM leaves WHERE employee_name = ?", (employee_name,))
    history = c.fetchall()
    conn.close()
    return history

init_db()


# Ultra-modern CSS with glassmorphism and advanced animations
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

st.header("Team Leave Calendar")
            # You can enhance this to draw events on a calendar from the DB
            # This part requires a calendar component like streamlit-calendar
            # For now, we'll just list the approved leaves.
st.info("Calendar view shows all approved leaves.")
approved_leaves = get_team_leaves(status_filter=["Approved"])
            
events = []
for leave in approved_leaves:
    events.append({
                    "title": f"{leave[0]} - {leave[1]}",
                    "start": leave[2],
                    "end": leave[3],
        })
            
            # If you have streamlit_calendar installed
try:
    from streamlit_calendar import calendar
    calendar(events=events)
except ImportError:
    st.write(events)

# Placeholder for LEAVE_POLICIES if not defined elsewhere
LEAVE_POLICIES = {
    "Annual": {}, "Sick": {}, "Maternity": {}, 
    "Paternity": {}, "Study": {}, "Compassionate": {}, "Unpaid": {}
}    