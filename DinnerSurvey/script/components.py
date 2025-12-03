import streamlit as st
import calendar
from datetime import date, timedelta

# Configuration
TARGET_YEAR = 2026
TARGET_MONTH = 1
HOLIDAYS = [
    date(2026, 1, 1),  # New Year's Day
    date(2026, 1, 2),  # Extended Holiday
]

def is_workday(d):
    """
    Returns True if the date is a workday (Mon-Fri) and not a holiday.
    """
    # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    if d.weekday() >= 5:
        return False
    if d in HOLIDAYS:
        return False
    return True

def toggle_date(target_date):
    """
    Toggles a date in the session state.
    Enforces a maximum of 3 selected dates.
    """
    if 'selected_dates' not in st.session_state:
        st.session_state.selected_dates = []
    
    # Convert to date object if it's not already
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
        
    # Create a copy to ensure state mutation is detected
    current_selection = list(st.session_state.selected_dates)
    
    if target_date in current_selection:
        current_selection.remove(target_date)
    else:
        if len(current_selection) >= 3:
            st.warning("最多只能選擇 3 個日期喔！ (You can only select up to 3 days)", icon="⚠️")
        else:
            current_selection.append(target_date)
            
    st.session_state.selected_dates = current_selection

def render_calendar(year=TARGET_YEAR, month=TARGET_MONTH):
    """
    Renders a custom calendar grid for Jan 2026.
    Locked to this specific month.
    """
    # Header for the calendar
    month_name = calendar.month_name[month]
    st.markdown(f"### 🗓️ {month_name} {year}")
    
    # Days of week header
    cols = st.columns(7)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day in enumerate(days):
        cols[i].markdown(f"**{day}**", unsafe_allow_html=True)
        
    # Calendar grid
    cal = calendar.monthcalendar(year, month)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("") # Empty slot
            else:
                current_date = date(year, month, day)
                is_selected = current_date in st.session_state.get('selected_dates', [])
                
                # Check if date is selectable
                selectable = is_workday(current_date)
                
                # Button styling logic
                if not selectable:
                    # Disabled look
                    label = f"{day}"
                    cols[i].button(label, key=f"cal_btn_dis_{day}", disabled=True)
                else:
                    # Determine button type (primary = selected)
                    btn_type = "primary" if is_selected else "secondary"
                    key = f"cal_btn_{year}_{month}_{day}"
                    
                    if cols[i].button(f"{day}", key=key, type=btn_type, use_container_width=True):
                        toggle_date(current_date)
                        st.rerun()

def render_date_list():
    """
    Renders a list view of available dates in Jan 2026.
    Uses full-width buttons for better clickability.
    """
    st.markdown("### 📋 Available Dates (Jan 2026)")
    
    # Generate all days in Jan 2026
    num_days = calendar.monthrange(TARGET_YEAR, TARGET_MONTH)[1]
    all_days = [date(TARGET_YEAR, TARGET_MONTH, day) for day in range(1, num_days + 1)]
    
    # Filter for workdays only
    available_days = [d for d in all_days if is_workday(d)]
    
    # Create a container for the list
    with st.container():
        for d in available_days:
            is_selected = d in st.session_state.get('selected_dates', [])
            
            # Use columns to separate Checkbox and Text
            # col1: Checkbox (Small width)
            # col2: Button (Rest of width, styled as text row)
            col1, col2 = st.columns([0.1, 0.9])
            
            # --- Column 1: Checkbox ---
            def on_chk_change(d=d):
                toggle_date(d)
                
            col1.checkbox(
                "Select", 
                value=is_selected, 
                key=f"list_chk_{d}", 
                label_visibility="collapsed",
                on_change=on_chk_change
            )
            
            # --- Column 2: Clickable Text Button ---
            # Button styling logic
            btn_type = "primary" if is_selected else "secondary"
            key = f"list_btn_{d}"
            
            # Display date details
            day_name = d.strftime("%A")
            date_str = d.strftime("%Y-%m-%d")
            
            # Wrap in custom class for left alignment
            col2.markdown('<div class="row-btn">', unsafe_allow_html=True)
            
            # Simplified Format: "06 | Monday" (Removed 2026-01)
            # Larger Font: wrapped in span with font-size
            day_num = d.strftime("%d")
            day_name = d.strftime("%A")
            label_html = f'<span style="font-size: 1.2rem; font-weight: 600;">{day_num}</span> <span style="color: #64748b; margin-left: 10px;">| {day_name}</span>'
            
            # Since st.button doesn't support HTML, we have to use the label as plain text
            # OR we can use the previous trick of putting the button inside a container 
            # but the button text itself is limited.
            
            # Wait, the user wants larger font. st.button text size is hard to change without global CSS.
            # But we can change the label text to be simpler: "06  |  Monday"
            # And use CSS to target the button text size.
            
            label_text = f"{day_num}  |  {day_name}"
                
            if col2.button(label_text, key=key, type=btn_type, use_container_width=True):
                toggle_date(d)
                st.rerun()
                
            col2.markdown('</div>', unsafe_allow_html=True)
