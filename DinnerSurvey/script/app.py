import streamlit as st
from datetime import date
import calendar
from pathlib import Path
import csv
import os

# Import custom components
from components import render_calendar

# ==========================================
# Configuration & Setup
# ==========================================
st.set_page_config(
    page_title="Dinner Survey",
    page_icon="🍽️",
    layout="centered"
)

# Load Custom CSS
def load_css():
    css_path = Path(__file__).parent / "styles.css"
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ==========================================
# State Management
# ==========================================
if 'selected_dates' not in st.session_state:
    st.session_state.selected_dates = []

if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if 'view_only' not in st.session_state:
    st.session_state.view_only = False

# ==========================================
# Helper Functions
# ==========================================
import pandas as pd

DATA_FILE = Path("data/submissions.csv")

def load_user_data(name):
    """Loads previous submission for the user if it exists."""
    if not DATA_FILE.exists():
        return
    
    try:
        df = pd.read_csv(DATA_FILE)
        # Filter by name (case-insensitive? let's do exact match for now to be safe, or strip)
        user_row = df[df["Name"] == name]
        
        if not user_row.empty:
            # Get the last entry if multiple (though we try to overwrite)
            last_entry = user_row.iloc[-1]
            
            loaded_dates = []
            for col in ["Date 1", "Date 2", "Date 3"]:
                if pd.notna(last_entry[col]) and last_entry[col] != "":
                    try:
                        loaded_dates.append(date.fromisoformat(last_entry[col]))
                    except ValueError:
                        pass
            
            st.session_state.selected_dates = loaded_dates
            # If we loaded data, maybe we should show the result page directly? 
            # Or let them edit? User said "read previous selection and let them modify".
            # So we stay on the survey page but pre-fill the data.
            st.toast(f"Welcome back, {name}! Loaded your previous selection.", icon="👋")
            
    except Exception as e:
        print(f"Error loading data: {e}")

def save_submission(name, dates):
    """Saves the submission to a CSV file. Overwrites previous entry for the same name."""
    # Ensure data directory exists
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare new row data
    date_strs = [d.strftime("%Y-%m-%d") for d in dates]
    while len(date_strs) < 3:
        date_strs.append("")
        
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {"Name": name, "Date 1": date_strs[0], "Date 2": date_strs[1], "Date 3": date_strs[2], "Timestamp": timestamp}
    
    # Check if file exists
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE)
            # Remove existing entries for this user
            df = df[df["Name"] != name]
            # Append new row
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        except Exception:
            # If read fails, just overwrite/create new
            df = pd.DataFrame([new_row])
    else:
        df = pd.DataFrame([new_row])
        
    df.to_csv(DATA_FILE, index=False)

def render_statistics():
    """Renders the public statistics section."""
    st.subheader("📊 Current Voting Results")
    
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE)
            date_cols = [col for col in df.columns if "Date" in col]
            
            if date_cols:
                # Melt to get Date -> Name mapping
                # We need to keep the Name column when melting
                all_votes = df.melt(id_vars=["Name"], value_vars=date_cols, value_name="Selected Date").dropna()
                all_votes = all_votes[all_votes["Selected Date"] != ""]
                
                if not all_votes.empty:
                    # Count votes
                    vote_counts = all_votes["Selected Date"].value_counts().reset_index()
                    vote_counts.columns = ["Date", "Votes"]
                    
                    # Aggregate voters per date
                    voters_per_date = all_votes.groupby("Selected Date")["Name"].apply(lambda x: ", ".join(x)).reset_index()
                    voters_per_date.columns = ["Date", "Voters"]
                    
                    # --- Top 3 Display ---
                    st.markdown("##### 🏆 Top 3 Popular Dates")
                    top_3 = vote_counts.sort_values(by="Votes", ascending=False).head(3)
                    
                    cols = st.columns(3)
                    for i, (index, row) in enumerate(top_3.iterrows()):
                        if i < 3:
                            with cols[i]:
                                st.metric(label=f"Rank #{i+1}", value=row['Date'], delta=f"{row['Votes']} votes")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # --- Full List Display ---
                    with st.expander("📅 View All Dates & Votes", expanded=True):
                        # Generate all valid workdays for Jan 2026
                        import calendar
                        TARGET_YEAR = 2026
                        TARGET_MONTH = 1
                        HOLIDAYS = [date(2026, 1, 1), date(2026, 1, 2)]
                        
                        def is_workday_local(d):
                            if d.weekday() >= 5: return False
                            if d in HOLIDAYS: return False
                            return True
                            
                        num_days = calendar.monthrange(TARGET_YEAR, TARGET_MONTH)[1]
                        all_days = [date(TARGET_YEAR, TARGET_MONTH, day) for day in range(1, num_days + 1)]
                        valid_days = [d.strftime("%Y-%m-%d") for d in all_days if is_workday_local(d)]
                        
                        # Create a dataframe for all valid days
                        full_stats = pd.DataFrame({"Date": valid_days})
                        
                        # Merge with vote counts
                        full_stats = full_stats.merge(vote_counts, on="Date", how="left")
                        full_stats["Votes"] = full_stats["Votes"].fillna(0).astype(int)
                        
                        # Merge with voters list
                        full_stats = full_stats.merge(voters_per_date, on="Date", how="left")
                        full_stats["Voters"] = full_stats["Voters"].fillna("")
                        
                        # Calculate height to show all rows (approx 35px per row + header)
                        # Adding a little buffer
                        table_height = (len(full_stats) + 1) * 35 + 3
                        
                        st.dataframe(
                            full_stats,
                            column_config={
                                "Date": "Date",
                                "Votes": st.column_config.ProgressColumn(
                                    "Votes",
                                    help="Number of votes",
                                    format="%d",
                                    min_value=0,
                                    max_value=int(full_stats["Votes"].max()) if not full_stats.empty else 10,
                                ),
                                "Voters": st.column_config.TextColumn(
                                    "Voters",
                                    help="Who voted for this date",
                                    width="large"
                                )
                            },
                            hide_index=True,
                            use_container_width=True,
                            height=table_height
                        )
        except Exception as e:
            st.error(f"Error loading statistics: {e}")

def render_admin():
    """Renders the admin panel."""
    st.title("🔒 Survey Admin Panel")
    
    ADMIN_PASSWORD = "admin"

    # Simple Login
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        password = st.text_input("Enter Admin Password", type="password")
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            if st.button("Login"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        with col2:
            if st.button("🔙 Back to Survey"):
                st.session_state.page = "home"
                st.rerun()
    else:
        st.success("Logged in as Admin")
        
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            if st.button("Logout"):
                st.session_state.admin_logged_in = False
                st.rerun()
        with col2:
            if st.button("🔙 Back to Survey"):
                st.session_state.page = "home"
                st.rerun()
            
        st.markdown("---")
        
        if DATA_FILE.exists():
            try:
                df = pd.read_csv(DATA_FILE)
                st.subheader("📋 Survey Data Management")
                st.info("Admin Panel is for data management only. Public statistics are visible on the main result page.")
                
                st.dataframe(df, use_container_width=True)
                
                # Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "submissions.csv",
                    "text/csv",
                    key='download-csv'
                )
                
                st.markdown("---")
                
                # Delete Individual Records
                st.subheader("🗑️ Delete Specific Records")
                users_to_delete = st.multiselect(
                    "Select users to remove:",
                    options=df["Name"].unique(),
                    placeholder="Choose names..."
                )
                
                if users_to_delete:
                    if st.button(f"Delete {len(users_to_delete)} Selected Record(s)", type="primary"):
                        # Filter out selected users
                        new_df = df[~df["Name"].isin(users_to_delete)]
                        new_df.to_csv(DATA_FILE, index=False)
                        st.success(f"Deleted records for: {', '.join(users_to_delete)}")
                        st.rerun()
                
                st.markdown("---")
                
                # Reset Data Option
                with st.expander("⚠️ Danger Zone (Clear All)"):
                    if st.button("🔥 Clear ENTIRE Database"):
                        DATA_FILE.unlink()
                        st.warning("All data has been wiped!")
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error reading data: {e}")
        else:
            st.info("No submissions yet.")

def handle_login():
    if st.session_state.temp_name:
        st.session_state.user_name = st.session_state.temp_name
        load_user_data(st.session_state.user_name)
        st.rerun()

def handle_submit():
    if not st.session_state.user_name:
        st.error("Please login first!")
        return
        
    save_submission(st.session_state.user_name, st.session_state.selected_dates)
    st.session_state.submitted = True
    st.balloons()
    st.rerun()

def handle_edit():
    st.session_state.submitted = False
    st.rerun()

# ==========================================
# Main App Logic
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "admin":
    render_admin()

else:
    # --- View Only Mode ---
    if st.session_state.view_only:
        st.title("📊 Voting Results")
        render_statistics()
        
        st.markdown("---")
        if st.button("🔙 Back to Login"):
            st.session_state.view_only = False
            st.rerun()

    # --- Login Screen ---
    elif not st.session_state.user_name:
        st.title("🍽️ Dinner Survey")
        st.markdown("### Please enter your name to start")
        
        st.text_input("Name", key="temp_name", on_change=handle_login)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start / Login", type="primary", use_container_width=True):
                handle_login()
        with col2:
            if st.button("👀 Just View Results", use_container_width=True):
                st.session_state.view_only = True
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 Admin Panel", type="secondary"):
            st.session_state.page = "admin"
            st.rerun()

    # --- Main App (Logged In) ---
    else:
        # Header
        col1, col2 = st.columns([0.8, 0.2])
        col1.title(f"Hi, {st.session_state.user_name} 👋")
        if col2.button("Logout"):
            st.session_state.user_name = ""
            st.session_state.selected_dates = []
            st.session_state.submitted = False
            st.rerun()

        if not st.session_state.submitted:
            st.markdown("### Select up to 3 dates for dinner in **January 2026**")
            
            # Layout: Calendar on top, Selected Dates below
            render_calendar()
            
            # Spacer
            st.markdown("<br>", unsafe_allow_html=True)

            # Submit Button
            if st.button("🚀 Submit My Choices", type="primary", use_container_width=True):
                handle_submit()

        else:
            # --- Result Page ---
            st.success("🎉 Thanks! Your choices have been saved.")
            
            st.markdown("### You selected:")
            for d in sorted(st.session_state.selected_dates):
                st.markdown(f"- 🗓️ **{d.strftime('%Y-%m-%d')} ({d.strftime('%A')})**")
                
            st.markdown("---")
            
            # --- Public Statistics Section ---
            render_statistics()
                
            st.markdown("---")
            st.info("Need to change your mind? You can edit your selection below.")
            
            if st.button("✏️ Edit Selection"):
                handle_edit()
