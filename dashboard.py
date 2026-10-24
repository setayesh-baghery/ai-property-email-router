# dashboard.py

import streamlit as st
import pandas as pd
import gspread
import os
from dotenv import load_dotenv

# --- 1. CONFIGURATION AND DATA LOADING ---

# Load environment variables from .env file (for the gspread key)
load_dotenv() 

# Define constants
SPREADSHEET_NAME = 'PM Automation Tickets'
st.set_page_config(layout="wide", page_title="AI Maintenance Router Dashboard")

# >>>>> FIX: CSS TO DISABLE SELECTBOX SEARCH/TYPING & ADJUST HEADER POSITION <<<<<
st.markdown("""
<style>
/* Target the primary search input inside the selectbox widget */
div[data-baseweb="select"] input {
    pointer-events: none; /* Prevents cursor from being active */
    user-select: none;    /* Prevents selecting text */
    cursor: default;      /* Shows a default cursor instead of text entry cursor */
}
/* Ensure selectbox text is slightly smaller for better visual integration with the header */
div[data-baseweb="select"] {
    font-size: 14px; 
}

/* FIX: Move the main section header (All Incoming Requests) up slightly */
section.main h1 {
    margin-top: 100px !important; /* Adjust this value to control how far up it moves */
}

/* Remove margin below the manual refresh button for a cleaner look */
.stButton>button {
    margin-bottom: 0px; 
}
</style>
""", unsafe_allow_html=True)
# >>>>> END OF FIX <<<<<


@st.cache_data(ttl=60) # Caches data for 60 seconds to avoid hitting the API constantly
def load_data():
    """Loads and formats the data from the Google Sheet."""
    try:
        # Initialize Google Sheets client using service_account.json
        gc = gspread.service_account(filename='service_account.json')
        
        # Open the sheet and get all values from the first worksheet
        worksheet = gc.open(SPREADSHEET_NAME).sheet1
        data = worksheet.get_all_records()
        
        # Convert to Pandas DataFrame for easy formatting
        df = pd.DataFrame(data)
        
        # >>>>>> FIX: Ensure 'unit_or_address' is string to prevent sorting TypeError <<<<<<
        df['unit_or_address'] = df['unit_or_address'].astype(str)
        # >>>>>> END OF FIX <<<<<<

        # Sort by urgency and timestamp (newest first)
        urgency_order = ['HIGH', 'MEDIUM', 'LOW', 'N/A']
        df['urgency_level'] = pd.Categorical(df['urgency_level'], categories=urgency_order, ordered=True)
        
        # Ensure timestamp is treated as a date/time object for sorting
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce') 
        # Static sort removed for user-controlled sorting
        
        return df

    except Exception as e:
        st.error(f"Error loading data from Google Sheet: {e}. Check service account permissions or sheet name.")
        return pd.DataFrame() # Return an empty DataFrame on error

# --- 3b. Styling Function (Final Grouped Color Logic) ---
def highlight_row(row):
    # FIX: Use the RENAMED column names
    category = row['Category']
    
    # 1. Define color mapping based on category group
    color_map = {
        # --- Single, CRITICAL match (Vibrant Red) ---
        'Maintenance - Emergency': '#ff4d4d', 
        
        # --- Grouped colors (Standard pastels) ---
        'Maintenance': '#ffe0b2',       # Light Orange for routine work
        'Administrative': '#d0e0e0',    # Light Gray for process
        'Rental Inquiry': '#b3e0ff',    # Light Blue for leads
        'Tenant Complaint': '#ffdfb3',  # Deeper Yellow/Orange for disputes
        'General Question': '#d1e7dd',  # Light Green for general info
    }
    
    # 2. Determine the color by matching the start of the category string
    color = ''
    
    if category.startswith('Maintenance - Emergency'):
        color = color_map['Maintenance - Emergency']
    elif category.startswith('Maintenance'):
        color = color_map['Maintenance']
    elif category.startswith('Administrative'):
        color = color_map['Administrative']
    elif category.startswith('Rental Inquiry'):
        color = color_map['Rental Inquiry']
    elif category.startswith('Tenant Complaint'):
        color = color_map['Tenant Complaint']
    elif category == 'General Question':
        color = color_map['General Question']
        
    # 3. Apply Styling (White and Bold Text)
    
    # Only Junk/Spam/Unclassified should be plain white background
    if not color: # If color is empty, it means no category matched (Spam/Junk/N/A)
        # Apply white/bold text on the default light background (may be invisible!)
        final_style = 'color: white; font-weight: bold' 
    else:
        # Apply the background color with white, bold text
        final_style = f'background-color: {color}; color: white; font-weight: bold'

    # Return a list of styles for all columns in the row
    return [final_style] * len(row)

# --- 2. STREAMLIT APP LAYOUT ---

st.title("🏡 AI Maintenance Request Router")
st.markdown("A **live view** of all incoming tenant and prospect requests, automatically prioritized.")

# Add a manual refresh button
if st.button("Manual Refresh Data"):
    st.cache_data.clear() # Clears the cache to force a new load
    st.rerun()

# Load the data
df_tickets = load_data()


# --- 3. DATA VISUALIZATION AND FILTERING ---

if not df_tickets.empty:  # The single, correct check
    
    # --- 3a. Metrics Cards (KPIs) ---
    col1, col2, col3, col4 = st.columns(4) 
    
    urgent_count = df_tickets[df_tickets['urgency_level'] == 'HIGH'].shape[0]
    non_urgent_count = df_tickets[df_tickets['urgency_level'] == 'MEDIUM'].shape[0]
    inquiry_count = df_tickets[df_tickets['classification'] == 'Rental Inquiry'].shape[0]
    total_count = df_tickets.shape[0]

    col1.metric("🚨 Urgent Tickets (HIGH)", urgent_count)
    col2.metric("🛠️ Non-Urgent Maintenance", non_urgent_count)
    col3.metric("🤝 Rental Inquiries", inquiry_count)
    col4.metric("📈 Total Processed", total_count)
    
    st.write("---")
    
    # 3. FILTER THE DATAFRAME FIRST, THEN APPLY STYLE

    # 1. Select and rename columns for a professional view
    display_df = df_tickets.rename(columns={
        'timestamp': 'Date Received',
        'e-mail': 'Tenant Email', 
        'classification': 'Category',
        'urgency_level': 'Urgency',
        'issue_summary': 'Summary of Issue', 
        'unit_or_address': 'Unit / Address', 
        'required_trade': 'Required Trade',  
    })
    
    # 2. Define the FINAL order of columns to display
    columns_to_show = [
        'Date Received', 
        'Category', 
        'Urgency', 
        'Summary of Issue', 
        'Unit / Address',      
        'Required Trade',      
        'Tenant Email', 
    ]
    
    try:
        final_df_subset = display_df[columns_to_show] 
    except KeyError as e:
        st.error(f"Configuration Error: One of the sheet headers changed. Check your rename dictionary! Missing column(s): {e}")
        st.stop()

    # --- HEADER (LEFT) AND COMPACT INLINE SORT CONTROLS (RIGHT) ---
    
    # Vertical spacing adjustment: Removed the previous solution and relying only on negative margin CSS.

    # Create five columns for alignment: [Header] [Spacer] [Sort By Label] [Column Chooser] [Direction Chooser]
    # Header is on the left (0.2), Spacer pushes everything to the right (0.45), controls are tightly grouped.
    header_col, spacer_col, text_col, sort_col_widget, dir_col_widget = st.columns([0.2, 0.45, 0.06, 0.17, 0.12])
    
    # Place the single-line header in the first column
    with header_col:
        st.header("All Incoming Requests")
    
    # Add the text label in the third column (right after the spacer)
    text_col.markdown("_Sort By:_")
    
    # 1. Sort Column Selector
    with sort_col_widget:
        sort_column_raw = st.selectbox(
            "Sort Column:",
            options=['Date Received', 'Urgency', 'Unit / Address'],
            index=1, # Default to Urgency
            label_visibility="collapsed", # Hide the label
            key='sort_col_selector' 
        )
    
    # 2. Dynamic Direction Options and Mapping
    
    # Define directional options based on the chosen column type
    if sort_column_raw in ['Date Received']:
        dir_options = ['Newest First', 'Oldest First']
        default_index = 0 # Newest First
    elif sort_column_raw in ['Urgency']:
        dir_options = ['Highest Priority First', 'Lowest Priority First']
        default_index = 0 # Highest First
    else: # Unit / Address
        dir_options = ['A-Z (Ascending)', 'Z-A (Descending)']
        default_index = 0 # A-Z
        
    # 3. Direction Selector
    with dir_col_widget:
        sort_direction_raw = st.selectbox(
            "Sort Direction:",
            options=dir_options,
            index=default_index,
            label_visibility="collapsed", # Hide the label
            key='sort_dir_selector' 
        )
    
    # 4. Map the selection to DataFrame parameters
    sort_column_map = {
        'Date Received': 'Date Received',
        'Urgency': 'Urgency',
        'Unit / Address': 'Unit / Address'
    }
    
    # Determine the 'ascending' boolean
    if 'Newest First' in sort_direction_raw or 'Z-A' in sort_direction_raw:
        # Date (Newest First = False) | Unit (Z-A = False)
        ascending = False
    elif 'Oldest First' in sort_direction_raw or 'A-Z' in sort_direction_raw:
        # Date (Oldest First = True) | Unit (A-Z = True)
        ascending = True
    elif 'Highest Priority First' in sort_direction_raw:
        # FIX: Urgency sorting (Highest = HIGH, which is index 0 in Category list, so ascending=True)
        ascending = True 
    else: # Lowest Priority First
        # Urgency sorting (Lowest = N/A, which is index 3 in Category list, so ascending=False)
        ascending = False

    # Get the actual column name
    sort_col = sort_column_map[sort_column_raw]

    
    # --- APPLY DYNAMIC SORTING ---
    final_df_sorted = final_df_subset.sort_values(
        by=sort_col,
        ascending=ascending,
        kind='stable' # Use 'stable' to preserve original order on tie-breaks
    )

    # Apply the style to the FINAL sorted DataFrame
    styled_df_final = final_df_sorted.style.apply(highlight_row, axis=1)
    
    # Pass the styled object directly to st.dataframe
    st.dataframe(styled_df_final, use_container_width=True)
    
else: # Must align with the top IF
    st.info("The dashboard is ready, but the Google Sheet is empty or could not be loaded.")

# cd desktop/ai-autoreal
# streamlit run dashboard.py