import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import uuid
from streamlit_calendar import calendar
from datetime import datetime, timedelta


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

# Database connection paths
LEAVE_DB_PATH = '/Users/danielwanganga/Documents/Airtel_AI/leave_management.db'
SIM_DB_PATH = '/Users/danielwanganga/Documents/Airtel_AI/sim_distribution.db'
AGENT_DB_PATH = '/Users/danielwanganga/Documents/Airtel_AI/agent_management.db'


def init_dbs():
    """Initializes all necessary database tables."""
    # SIM Distribution DB
    conn_sim = sqlite3.connect(SIM_DB_PATH)
    c_sim = conn_sim.cursor()
    c_sim.execute("""
        CREATE TABLE IF NOT EXISTS sim_distributions (
            id TEXT PRIMARY KEY,
            se_name TEXT NOT NULL,
            distribution_date TEXT NOT NULL,
            recipient_type TEXT NOT NULL,
            recipient_name TEXT NOT NULL,
            sim_cards_distributed INTEGER NOT NULL,
            notes TEXT
        )
    """)
    conn_sim.commit()
    conn_sim.close()

    # Agent Management DB
    conn_agent = sqlite3.connect(AGENT_DB_PATH)
    c_agent = conn_agent.cursor()
    c_agent.execute("""
        CREATE TABLE IF NOT EXISTS agent_problems_visits (
            id TEXT PRIMARY KEY,
            se_name TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            scheduled_visit_date TEXT,
            status TEXT NOT NULL,
            recorded_date TEXT NOT NULL
        )
    """)
    conn_agent.commit()
    conn_agent.close()

@st.cache_data
def get_all_leaves():
    """Fetches all leave records from the leave management database."""
    conn = sqlite3.connect(LEAVE_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description, status FROM leaves")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@st.cache_data
def get_sim_distributions(se_name):
    """Fetches SIM card distribution records for a specific Sales Executive."""
    conn = sqlite3.connect(SIM_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM sim_distributions WHERE se_name = ? ORDER BY distribution_date DESC", (se_name,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_sim_distribution(se_name, distribution_date, recipient_type, recipient_name, sim_cards_distributed, notes):
    """Adds a new SIM card distribution record to the database."""
    conn = sqlite3.connect(SIM_DB_PATH)
    c = conn.cursor()
    distribution_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO sim_distributions (id, se_name, distribution_date, recipient_type, recipient_name, sim_cards_distributed, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (distribution_id, se_name, distribution_date, recipient_type, recipient_name, sim_cards_distributed, notes))
    conn.commit()
    conn.close()
    get_sim_distributions.clear() # Clear cache to refresh data

@st.cache_data
def get_agent_problems_visits(se_name):
    """Fetches agent problems and scheduled visits for a specific Sales Executive."""
    conn = sqlite3.connect(AGENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM agent_problems_visits WHERE se_name = ? ORDER BY recorded_date DESC", (se_name,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_agent_problem_visit(se_name, agent_name, problem_description, scheduled_visit_date, status, recorded_date):
    """Adds a new agent problem/visit record to the database."""
    conn = sqlite3.connect(AGENT_DB_PATH)
    c = conn.cursor()
    record_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO agent_problems_visits (id, se_name, agent_name, problem_description, scheduled_visit_date, status, recorded_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (record_id, se_name, agent_name, problem_description, scheduled_visit_date, status, recorded_date))
    conn.commit()
    conn.close()
    get_agent_problems_visits.clear() # Clear cache to refresh data

def update_agent_problem_status(record_id, new_status):
    """Updates the status of an agent problem/visit record."""
    conn = sqlite3.connect(AGENT_DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE agent_problems_visits SET status = ? WHERE id = ?", (new_status, record_id))
    conn.commit()
    conn.close()
    get_agent_problems_visits.clear() # Clear cache to refresh data

def sim_card_management(current_user_name):
    """Displays the SIM card distribution tracking interface."""
    st.subheader("📦 SIM Card Distribution Tracking")

    # Form for adding new distribution
    st.markdown("#### Record New SIM Distribution")
    with st.form("sim_distribution_form"):
        distribution_date = st.date_input("Date of Distribution", datetime.today())
        recipient_type = st.selectbox("Recipient Type", ["Agent", "Partner", "Outlet", "Other"])
        recipient_name = st.text_input("Recipient Name (e.g., Agent's Name, Partner Company)")
        sim_cards_distributed = st.number_input("Number of SIM Cards Distributed", min_value=1, value=100)
        notes = st.text_area("Notes (Optional)", "")

        submitted = st.form_submit_button("Record Distribution")

        if submitted:
            if recipient_name:
                try:
                    add_sim_distribution(
                        current_user_name,
                        distribution_date.strftime("%Y-%m-%d"),
                        recipient_type,
                        recipient_name,
                        sim_cards_distributed,
                        notes
                    )
                    st.success("✅ SIM card distribution recorded successfully!")
                except Exception as e:
                    st.error(f"Error recording distribution: {e}")
            else:
                st.warning("Please enter a Recipient Name.")
    st.markdown("---")

    # Display historical distribution
    st.markdown("#### My SIM Distribution History")
    distributions = get_sim_distributions(current_user_name)

    if distributions:
        total_distributed = sum(d['sim_cards_distributed'] for d in distributions)
        st.info(f"**Total SIM Cards Distributed by You: {total_distributed}**")

        st.dataframe(distributions, use_container_width=True)
    else:
        st.info("No SIM card distribution records found for you yet.")

    st.markdown("---")
    st.markdown("#### Planning Your Next SIM Card Load")
    st.write("""
        Consider the following factors when deciding how many SIM cards to carry for your next visit:
        * **Agent Performance:** Review the monthly performance of your agents (if accessible in another part of the app) to gauge their activation capabilities.
        * **Agent Requests:** Check with your agents (e.g., via WhatsApp group) if they have explicitly requested additional SIM cards.
        * **Daily Route & Number of Agents:** Account for the specific route you are covering and the number of active agents in that area.
        * **Average GA Registrations:** Consider the historical average number of Gross Activations (GAs) registered by your agents.
        * **SSO Activation Capacities:** Coordinate with your Sales & Service Officers (SSOs) to understand their activation capacities.
        * **Marketing Promotions/Campaigns:** Align with the marketing team to anticipate increased demand due to ongoing or upcoming promotions.
        * **Customer Flow in Outlets:** Observe or inquire about the expected customer flow in the outlets you plan to visit.
        """)

def agent_problem_management(current_user_name):
    """Allows recording agent problems and scheduling visits."""
    st.subheader("⚠️ Agent Problem & Visit Management")

    st.markdown("#### Record a New Agent Problem or Schedule a Visit")
    with st.form("agent_problem_form"):
        agent_name = st.text_input("Agent's Name", help="Name of the agent experiencing the problem.")
        problem_description = st.text_area("Problem Description", help="Describe the issue the agent is facing.")
        schedule_visit = st.checkbox("Schedule a follow-up visit?")
        scheduled_visit_date = None
        if schedule_visit:
            scheduled_visit_date = st.date_input("Scheduled Visit Date", min_value=datetime.today())

        submitted = st.form_submit_button("Record Problem / Schedule Visit")

        if submitted:
            if agent_name and problem_description:
                status = "Scheduled" if scheduled_visit_date else "Open"
                try:
                    add_agent_problem_visit(
                        current_user_name,
                        agent_name,
                        problem_description,
                        scheduled_visit_date.strftime("%Y-%m-%d") if scheduled_visit_date else None,
                        status,
                        datetime.today().strftime("%Y-%m-%d")
                    )
                    st.success("✅ Agent problem recorded and/or visit scheduled successfully!")
                except Exception as e:
                    st.error(f"Error recording: {e}")
            else:
                st.warning("Please enter Agent's Name and Problem Description.")
    st.markdown("---")

    st.markdown("#### My Agent Problems & Scheduled Visits")
    problems_visits = get_agent_problems_visits(current_user_name)

    if problems_visits:
        # Create columns for filtering
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "Open", "Scheduled", "Resolved"])
        with col2:
            search_agent = st.text_input("Search by Agent Name")

        filtered_problems = problems_visits
        if filter_status != "All":
            filtered_problems = [p for p in filtered_problems if p['status'] == filter_status]
        if search_agent:
            filtered_problems = [p for p in filtered_problems if search_agent.lower() in p['agent_name'].lower()]

        if filtered_problems:
            for i, record in enumerate(filtered_problems):
                st.markdown(f"**Agent: {record['agent_name']}** (Recorded: {record['recorded_date']})")
                st.write(f"Problem: {record['problem_description']}")
                if record['scheduled_visit_date']:
                    st.write(f"Scheduled Visit: {record['scheduled_visit_date']}")
                st.write(f"Status: **{record['status']}**")

                # Add buttons to change status
                col_btn1, col_btn2, _ = st.columns([0.2, 0.2, 0.6])
                if record['status'] != "Resolved":
                    with col_btn1:
                        if st.button(f"Mark Resolved", key=f"resolve_{record['id']}"):
                            update_agent_problem_status(record['id'], "Resolved")
                            st.experimental_rerun()
                if record['status'] == "Open" and not record['scheduled_visit_date']:
                     with col_btn2:
                        if st.button(f"Schedule Visit", key=f"schedule_{record['id']}"):
                            st.info("Please use the 'Record New Agent Problem' form to schedule a visit with a specific date.")
                st.markdown("---")
        else:
            st.info("No matching agent problems or visits found.")
    else:
        st.info("No agent problems or scheduled visits recorded for you yet.")


def generate_partner_visit_events(start_date, location="Mathare", total_visits=50):
    """Generates dummy partner visit events for the calendar."""
    visits_per_day = 10
    events = []
    for i in range(5):  # Mon–Fri
        visit_date = start_date + timedelta(days=i)
        events.append({
            "title": f"Visit {visits_per_day} Partners - {location}",
            "start": visit_date.strftime("%Y-%m-%dT09:00:00"),
            "end": visit_date.strftime("%Y-%m-%dT17:00:00"),
            "color": "#1e90ff"
        })
    return events


def leave_roster_calendar(current_user_name):
    """Displays the personal leave calendar for the current user."""
    st.subheader("📆 My Calendar")

    all_leaves = get_all_leaves()
    user_leaves = [leave for leave in all_leaves if leave['employee_name'] == current_user_name]
    events = []

    for leave in user_leaves:
        try:
            if leave["start_date"] and leave["end_date"]:
                events.append({
                    "id": str(uuid.uuid4()),
                    "title": f"{leave['leave_type']} Leave",
                    "start": leave["start_date"],
                    "end": leave["end_date"],
                    "color": "#ffd700" if leave["status"] == "Pending" else "#00cc00",
                })
        except Exception as e:
            st.warning(f"Skipping leave entry due to error: {e}")

    # Add scheduled agent visits to the calendar
    agent_visits = get_agent_problems_visits(current_user_name)
    for visit in agent_visits:
        if visit['scheduled_visit_date'] and visit['status'] != 'Resolved':
            events.append({
                "id": visit['id'], # Use the problem ID
                "title": f"Visit {visit['agent_name']} (Problem)",
                "start": visit['scheduled_visit_date'],
                "end": visit['scheduled_visit_date'], # Assuming full day visit or just a marker
                "color": "#FF5733", # Orange/Red for agent visits
                "allDay": True
            })


    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    events.extend(generate_partner_visit_events(start_of_week))


    calendar_options = {
        "editable": False,
        "selectable": True,
        "height": 600,
        "nowIndicator": True,
        "navLinks": True,
        "eventTimeFormat": {"hour": '2-digit', "minute": '2-digit', "hour12": False},
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek"
        }
    }

    custom_css = """
    .fc-toolbar-title {
        color: #FF4B4B;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .fc-event-title {
        font-weight: 600;
    }
    """

    st.markdown("### ➕ Add General Event or Reminder")
    with st.form("general_event_form"): # Renamed form key
        title = st.text_input("Event Title")
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
        color = st.color_picker("Color", "#007BFF")
        submitted = st.form_submit_button("Add Event")

        if submitted:
            events.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "color": color
            })
            st.success("✅ Event added. Please reload the calendar.")

    st.markdown("---")

    st.markdown("### 📌 Calendar View")

    cal_state = calendar(
        events=events,
        options=calendar_options,
        custom_css=custom_css,
        callbacks=["dateClick", "eventClick", "select"],
        license_key="CC-Attribution-NonCommercial-NoD",
        key="airtel_calendar"
    )

    if cal_state:
        if "eventClick" in cal_state:
            clicked = cal_state["eventClick"]["event"]
            st.info(f"📋 Event clicked: **{clicked['title']}** on **{clicked['start']}**")
        elif "dateClick" in cal_state:
            clicked_date = cal_state["dateClick"]["date"]
            st.success(f"📅 You clicked on: **{clicked_date}**")

# Use a default or dummy user for demo purposes
default_user_key = list(USERS.keys())[0]
user = USERS[default_user_key]

if 'user' not in st.session_state:
    st.session_state.user = user

# Initialize all databases
init_dbs()

# --- Home Page ---
slideshow_html = """
<div class="slideshow-container">
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/Send-Money-for%20Free-Web%20Banners.jpg" alt="Airtel Offer 1">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/2GB-@-99-Bob-web-banners.jpg" alt="Airtel Offer 2">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/1GB-@15-Bob-web-banners.jpg" alt="Airtel Offer 3">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/AIRTEL-KENYA_HVC_CAMPAIGN_700_by_700_1.jpg" alt="Airtel Offer 4">
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/airtel-money/kenya/assets/images/google-play.png" alt="Airtel Offer 5">
</div>

<div style="text-align:center; padding: 15px 0;">
  <span class="dot"></span>
  <span class="dot"></span>
  <span class="dot"></span>
  <span class="dot"></span>
</div>

<script>
let slideIndex = 0;
function showSlides() {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";
  dots[slideIndex-1].className += " active";
  setTimeout(showSlides, 5000); // Change image every 5 seconds
}

document.addEventListener('DOMContentLoaded', showSlides);
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif; }

.slideshow-container {
    width: 100%;
    max-width: 900px;
    position: relative;
    margin: 20px auto;
    overflow: hidden;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    background-color: #1a1a1a;
}

.mySlides {
    display: none;
    width: 100%;
    height: auto;
    text-align: center;
}

.mySlides img {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 12px;
    object-fit: cover;
}

.dot {
    height: 12px;
    width: 12px;
    margin: 0 4px;
    background-color: #666;
    border-radius: 50%;
    display: inline-block;
    transition: background-color 0.4s ease, transform 0.2s ease;
    cursor: pointer;
}

.dot.active {
    background-color: #FF4B4B;
    transform: scale(1.2);
}

.dot:hover {
    background-color: #FF6F6F;
}

.fade {
  -webkit-animation-name: fade;
  -webkit-animation-duration: 1.5s;
  animation-name: fade;
  animation-duration: 1.5s;
}

@-webkit-keyframes fade {
  from {opacity: .7}
  to {opacity: 1}
}

@keyframes fade {
  from {opacity: .7}
  to {opacity: 1}
}

@media (max-width: 768px) {
    .slideshow-container {
        margin: 15px auto;
        border-radius: 8px;
    }
    .dot {
        height: 10px;
        width: 10px;
        margin: 0 3px;
    }
}
</style>
"""

def profile_summary():
    """Displays the user's profile summary and leave statistics."""
    user = st.session_state.user
    remaining_leave = user['cumulative_leave'] - user['used_leave']

    st.html(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}

        .profile-card {{
            background: linear-gradient(135deg, #FF4B4B 0%, #CC0000 100%);
            padding: 30px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            flex-wrap: wrap;
            justify-content: center;
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease-in-out;
        }}
        .profile-card:hover {{
            transform: translateY(-5px);
        }}

        .profile-img {{
            border-radius: 50%;
            width: 180px;
            height: 180px;
            object-fit: cover;
            margin-right: 30px;
            border: 4px solid #F0F0F0;
            box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.2), 0 0 0 16px rgba(255, 255, 255, 0.1);
            flex-shrink: 0;
            max-width: 100%;
            transition: border-color 0.3s ease;
        }}
        .profile-img:hover {{
            border-color: #FFD700;
        }}

        .profile-info {{
            flex-grow: 1;
            color: #FFFFFF;
            min-width: 250px;
            padding-top: 5px;
            text-align: left;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}
        .profile-info h2 {{
            font-size: 2.2em;
            margin-bottom: 5px;
            font-weight: 700;
            line-height: 1.2;
            color: #FFFFFF;
        }}
        .profile-info p {{
            font-size: 1em;
            margin-bottom: 3px;
            opacity: 0.9;
            font-weight: 300;
        }}

        .leave-stats {{
            display: flex;
            gap: 20px;
            margin-top: 25px;
            flex-wrap: wrap;
            justify-content: center;
            width: 100%;
        }}

        .leave-card {{
            background-color: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(5px);
            padding: 15px 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #E0E0E0;
            flex: 1 1 150px;
            max-width: 180px;
            box-sizing: border-box;
            min-width: 120px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, background-color 0.3s ease;
        }}
        .leave-card:hover {{
            transform: translateY(-3px);
            background-color: rgba(0, 0, 0, 0.4);
        }}
        .leave-card > div:first-child {{
            font-size: 1.8em;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 5px;
        }}
        .leave-card > div:last-child {{
            font-size: 0.85em;
            opacity: 0.8;
        }}
        .leave-card.approved {{
            border-left: 5px solid #00E676;
            background-color: rgba(0, 50, 0, 0.4);
        }}
        .leave-card.approved > div:first-child {{
            color: #98FB98;
        }}

        @media (max-width: 768px) {{
            .profile-card {{
                flex-direction: column;
                align-items: center;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .profile-img {{
                width: 120px;
                height: 120px;
                margin-right: 0;
                margin-bottom: 20px;
                border: 3px solid #F0F0F0;
                box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.2);
            }}
            .profile-info {{
                text-align: center;
                width: 100%;
                min-width: unset;
                color: #FFFFFF;
            }}
            .profile-info h2 {{
                font-size: 1.8em;
                color: #FFFFFF;
            }}
            .profile-info p {{
                font-size: 0.9em;
            }}
            .leave-stats {{
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
                margin-top: 15px;
            }}
            .leave-card {{
                flex: 1 1 45%;
                max-width: 48%;
                padding: 12px 10px;
                font-size: 0.9em;
            }}
            .leave-card > div:first-child {{
                font-size: 1.4em;
            }}
            .leave-card > div:last-child {{
                font-size: 0.8em;
            }}
        }}

        @media (max-width: 480px) {{
            .leave-stats {{
                flex-direction: column;
                align-items: center;
            }}
            .leave-card {{
                width: 90%;
                max-width: 250px;
            }}
        }}
    </style>

    <div class="profile-card">
        <img src="{user.get('profile_pic', 'https://media.istockphoto.com/id/1828923094/photo/portrait-of-happy-woman-with-crossed-arms-on-white-background-lawyer-businesswoman-accountant.jpg')}" class="profile-img">
        <div class="profile-info">
            <h2>{user['name']} {user.get('surname', '')}</h2>
            <p>📌 {user.get('position', 'Agent')}</p>
            <p>🏢 {user.get('managing_partner', 'Airtel Kenya')}</p>
            <p>🏷️ {user.get('franchise_type', 'Eastleigh')}</p>

            <div class="leave-stats">
                <div class="leave-card">
                    <div>{user['cumulative_leave']}</div>
                    <div>Cumulative Days</div>
                </div>
                <div class="leave-card">
                    <div>{user['used_leave']}</div>
                    <div>Used Days</div>
                </div>
                <div class="leave-card approved">
                    <div>{remaining_leave}</div>
                    <div>Remaining Days</div>
                </div>
            </div>
        </div>
    </div>
    """)


st.html("""
    <style>
    .css-1d3f8gq {
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    h1,  h3, h4, h5, h6 {
        color: #FF4B4B;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""")


st.header("")
st.markdown("---")
profile_summary()
st.subheader("📢 Latest Offers")
components.html(slideshow_html, height=500)
leave_roster_calendar(st.session_state.user['name'])
