import streamlit as st
import json
import os
import requests
import pandas as pd
import base64
from PIL import Image
import io
import cv2
import numpy as np
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from twilio.rest import Client
from datetime import datetime
import pytesseract
import re
import sqlite3
import json
import db_utils            # <-- new
# Save the provided code as 'roamgenie_db.py' and then use these imports:

# Basic imports for core functionality
from db_utils import (
    # Database initialization
    init_db,
    initialize_admin_system,
    
    # Flight search logging and retrieval
    log_flight_search,
    log_enhanced_flight_search,
    fetch_recent_searches,
    fetch_all_searches,
    
    # Contact management
    log_enhanced_contact,
    fetch_contacts,
    
    # Analytics functions
    get_total_searches_count,
    get_recent_searches_count,
    get_monthly_searches,
    get_average_trip_duration,
    get_weekly_growth_rate,
    
    # Top destinations and origins
    get_top_destinations,
    get_top_departures,
    
    # Distribution analytics
    get_budget_distribution,
    get_class_distribution,
    
    # Time-based analytics
    get_searches_over_time,
    get_flight_analytics,
    
    # Admin functions
    get_admin_summary_stats,
    generate_analytics_summary,
    
    # Event logging
    log_event,
    
    # Utility functions
    backup_database,
    get_database_info,
    get_flight_analytic
)

import hashlib
import plotly.express as px
import plotly.graph_objects as go
import uuid

# Initialize session_id if not already present
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())  # Generates a unique session ID




# Admin credentials - you can move this to secrets
try:
    ADMIN_CREDENTIALS = {
        st.secrets["admin"]["admin_username"]: st.secrets["admin"]["admin_password"],
        st.secrets["admin"]["manager_username"]: st.secrets["admin"]["manager_password"]
    }
except:
    # Fallback credentials
    ADMIN_CREDENTIALS = {
        "Webisdom": "admin@123"
    }

def check_admin_credentials(username, password):
    """Check if admin credentials are correct"""
    return username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password

def admin_login():
    """Admin login interface"""
    st.markdown("### 🔐 Admin Authentication")
    
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            username_col, password_col = st.columns(2)
            with username_col:
                username = st.text_input("Username")
            with password_col:
                password = st.text_input("Password", type="password")
            
            login_btn = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if login_btn:
                if check_admin_credentials(username, password):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")
        
        # Show demo credentials for testing
        st.info("**Demo Credentials:**\n- Username: `Webisdom` Password: `admin@123`")
        return False
    else:
        header_col, logout_col = st.columns([6, 1])
        with header_col:
            st.success(f"✅ Logged in as: **{st.session_state.admin_username}**")
        with logout_col:
            if st.button("🚪 Logout", key="admin_logout_btn"):
                st.session_state.admin_logged_in = False
                st.rerun()
        return True

def display_overview_metrics():
    """Display comprehensive overview metrics"""
    st.markdown("## 📊 Key Performance Indicators")
    
    # Get comprehensive stats
    try:
        stats = get_admin_summary_stats()
        total_searches = get_total_searches_count()
        contacts_df = fetch_contacts()
        total_contacts = len(contacts_df) if contacts_df is not None and not contacts_df.empty else 0
        recent_searches = get_recent_searches_count(7)
        avg_duration = get_average_trip_duration()
    except Exception as e:
        st.error(f"Error fetching metrics: {e}")
        stats = {}
        total_searches = 0
        total_contacts = 0
        recent_searches = 0
        avg_duration = 0
    
    # Main KPIs Row 1
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    with kpi1:
        st.metric("Total Searches", stats.get('total_searches', total_searches))
    with kpi2:
        st.metric("Total Contacts", stats.get('total_contacts', total_contacts))
    with kpi3:
        st.metric("Last 7 Days", stats.get('searches_7d', recent_searches))
    with kpi4:
        st.metric("Last 24h Searches", stats.get('searches_24h', 0))
    with kpi5:
        st.metric("Avg Trip Duration", f"{stats.get('avg_trip_duration', avg_duration):.1f} days")
    
    st.markdown("---")
    
    # Additional Stats Row 2
    stat1, stat2, stat3, stat4 = st.columns(4)
    
    with stat1:
        try:
            budget_stats = get_budget_distribution()
            most_popular_budget = budget_stats[0][0] if budget_stats and len(budget_stats) > 0 else "N/A"
        except:
            most_popular_budget = "N/A"
        st.metric("Popular Budget", most_popular_budget)
    
    with stat2:
        try:
            class_stats = get_class_distribution()
            most_popular_class = class_stats[0][0] if class_stats and len(class_stats) > 0 else "N/A"
        except:
            most_popular_class = "N/A"
        st.metric("Popular Class", most_popular_class)
    
    with stat3:
        try:
            monthly_searches = get_monthly_searches()
        except:
            monthly_searches = 0
        st.metric("This Month", monthly_searches)
    
    with stat4:
        try:
            weekly_growth = get_weekly_growth_rate()
        except:
            weekly_growth = 0
        st.metric("Weekly Growth", f"{weekly_growth:+.1f}%")

def display_charts_section():
    """Display comprehensive charts and analytics"""
    st.markdown("## 📈 Analytics & Trends")
    
    flight_data = get_flight_analytics()
    
    if flight_data.empty:
        st.info("No flight data available for charts.")
        return
    
    # Top section - Destination and Departure charts
    st.markdown("### 🌍 Geographic Analytics")
    dest_col, dep_col = st.columns(2)
    
    with dest_col:
        st.markdown("#### Top Destinations")
        try:
            df_top_destinations = get_top_destinations(10)
            if df_top_destinations is not None and not df_top_destinations.empty:
                fig_dest = px.bar(
                    df_top_destinations, 
                    x='count', 
                    y='destination',
                    orientation='h',
                    title='Most Popular Destinations',
                    color='count',
                    color_continuous_scale='viridis'
                )
                fig_dest.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_dest, use_container_width=True)
                
                # Show data table
                with st.expander("📊 View Destination Data"):
                    st.dataframe(df_top_destinations, use_container_width=True)
            else:
                st.info("No destination data available yet.")
        except Exception as e:
            st.error(f"Error loading destination data: {e}")
    
    with dep_col:
        st.markdown("#### Top Departure Cities")
        try:
            df_departures = get_top_departures(10)
            if df_departures is not None and not df_departures.empty:
                fig_dep = px.bar(
                    df_departures, 
                    x='count', 
                    y='origin',
                    orientation='h',
                    title='Most Popular Departure Cities',
                    color='count',
                    color_continuous_scale='plasma'
                )
                fig_dep.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_dep, use_container_width=True)
                
                # Show data table
                with st.expander("📊 View Departure Data"):
                    st.dataframe(df_departures, use_container_width=True)
            else:
                st.info("No departure data available yet.")
        except Exception as e:
            st.error(f"Error loading departure data: {e}")
    
    st.markdown("---")
    
    # Time-based analytics
    st.markdown("### ⏰ Temporal Analytics")
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        # Search trends over time
        st.markdown("#### Search Trends Over Time")
        try:
            df_time = get_searches_over_time()
            if df_time is not None and not df_time.empty:
                df_time['date'] = pd.to_datetime(df_time['date'])
                fig_time = px.line(
                    df_time, 
                    x='date', 
                    y='count',
                    title='Daily Search Volume',
                    markers=True
                )
                fig_time.update_layout(height=400)
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("No search trend data available yet.")
        except Exception as e:
            st.error(f"Error loading search trends: {e}")
    
    with time_col2:
        # Budget distribution
        st.markdown("#### Budget Distribution")
        if 'budget_preference' in flight_data.columns:
            budget_dist = flight_data['budget_preference'].value_counts()
            fig_budget = px.pie(values=budget_dist.values, names=budget_dist.index, 
                       title='Budget Preference Distribution')
            fig_budget.update_layout(height=400)
            st.plotly_chart(fig_budget, use_container_width=True)
    
    st.markdown("---")
    
    # Advanced analytics row
    st.markdown("### 🔍 Advanced Analytics")
    advanced_col1, advanced_col2, advanced_col3 = st.columns(3)
    
    with advanced_col1:
        # Hourly search pattern
        if 'hour_of_day' in flight_data.columns:
            hourly_data = flight_data['hour_of_day'].value_counts().sort_index()
            fig_hourly = px.bar(x=hourly_data.index, y=hourly_data.values,
                       title='Search Activity by Hour of Day',
                       labels={'x': 'Hour', 'y': 'Number of Searches'})
            fig_hourly.update_layout(height=350)
            st.plotly_chart(fig_hourly, use_container_width=True)
    
    with advanced_col2:
        # Flight class distribution
        if 'flight_class' in flight_data.columns:
            class_dist = flight_data['flight_class'].value_counts()
            fig_class = px.pie(values=class_dist.values, names=class_dist.index,
                       title='Flight Class Distribution')
            fig_class.update_layout(height=350)
            st.plotly_chart(fig_class, use_container_width=True)
    
    with advanced_col3:
        # Trip duration distribution
        if 'duration_days' in flight_data.columns:
            fig_duration = px.histogram(flight_data, x='duration_days',
                             title='Trip Duration Distribution',
                             labels={'duration_days': 'Days', 'count': 'Frequency'})
            fig_duration.update_layout(height=350)
            st.plotly_chart(fig_duration, use_container_width=True)

def display_customer_management():
    """Display comprehensive customer management"""
    st.markdown("## 👥 Customer Management")
    
    # Get customer data
    customers = fetch_contacts(1000)  # Get more for admin
    
    if customers is None or customers.empty:
        st.info("No customer data available.")
        return
    
    # Search and filter section
    st.markdown("### 🔍 Search & Filter")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        search_term = st.text_input("🔍 Search customers", 
                                   placeholder="Name, email, or phone")
    with filter_col2:
        show_count = st.selectbox("Show records", [25, 50, 100, 200, "All"])
    with filter_col3:
        sort_by = st.selectbox("Sort by", ["Registration Date", "Name", "Email"])
    
    # Filter customers
    filtered_customers = customers.copy()
    
    if search_term:
        mask = (
            customers['firstName'].str.contains(search_term, case=False, na=False) |
            customers['secondName'].str.contains(search_term, case=False, na=False) |
            customers['email'].str.contains(search_term, case=False, na=False) |
            customers['phone'].str.contains(search_term, case=False, na=False)
        )
        filtered_customers = customers[mask]
    
    # Sort customers
    if sort_by == "Registration Date" and 'created_at' in filtered_customers.columns:
        filtered_customers = filtered_customers.sort_values('created_at', ascending=False)
    elif sort_by == "Name":
        filtered_customers = filtered_customers.sort_values(['firstName', 'secondName'])
    elif sort_by == "Email":
        filtered_customers = filtered_customers.sort_values('email')
    
    # Limit results
    if show_count != "All":
        filtered_customers = filtered_customers.head(show_count)
    
    # Display results
    st.markdown(f"### 📊 Customer Records ({len(filtered_customers)} shown)")
    
    if not filtered_customers.empty:
        # Prepare display data
        display_data = filtered_customers.copy()
        
        # Format registration date
        if 'created_at' in display_data.columns:
            display_data['Registration Date'] = pd.to_datetime(
                display_data['created_at'], errors='coerce'
            ).dt.strftime('%Y-%m-%d %H:%M')
        
        # Select and rename columns
        display_columns = []
        column_mapping = {
            'firstName': 'First Name',
            'secondName': 'Last Name',
            'email': 'Email',
            'phone': 'Phone'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in display_data.columns:
                display_data[new_col] = display_data[old_col]
                display_columns.append(new_col)
        
        if 'Registration Date' in display_data.columns:
            display_columns.append('Registration Date')
        
        # Show dataframe
        st.dataframe(display_data[display_columns], use_container_width=True)
        
        # Recent activity sidebar
        with st.expander("📋 Recent Customer Activity", expanded=False):
            st.markdown("#### Recent CRM Contacts")
            try:
                crm_df = fetch_contacts(5)  # Limit to 5 recent contacts
                if crm_df is not None and not crm_df.empty:
                    for idx, row in crm_df.iterrows():
                        first_name = row.get('firstName', row.get('first_name', ''))
                        last_name = row.get('secondName', row.get('last_name', ''))
                        name = f"{first_name} {last_name}".strip()
                        email = row.get('email', 'N/A')
                        phone = row.get('phone', 'N/A')
                        created_at = row.get('created_at', '')
                        
                        if created_at:
                            try:
                                reg_date = pd.to_datetime(created_at).strftime('%Y-%m-%d')
                            except:
                                reg_date = 'N/A'
                        else:
                            reg_date = 'N/A'
                        
                        st.markdown(f"""
                        **{name if name.strip() else 'N/A'}**  
                        📧 {email} | 📞 {phone} | 📅 {reg_date}
                        """)
                        st.markdown("---")
                else:
                    st.info("No recent contacts available.")
            except Exception as e:
                st.error(f"Error loading contacts: {e}")

def display_flight_management():
    """Display comprehensive flight search management"""
    st.markdown("## ✈️ Flight Search Management")
    
    # Get flight data
    flight_data = get_flight_analytics()
    
    if flight_data.empty:
        st.info("No flight search data available.")
        return
    
    # Filters section
    st.markdown("### 🔧 Filters")
    filter1, filter2, filter3, filter4 = st.columns(4)
    
    with filter1:
        origins = ['All'] + sorted(flight_data['origin'].unique().tolist())
        selected_origin = st.selectbox("Origin", origins)
    
    with filter2:
        destinations = ['All'] + sorted(flight_data['destination'].unique().tolist())
        selected_destination = st.selectbox("Destination", destinations)
    
    with filter3:
        budgets = ['All'] + sorted(flight_data['budget_preference'].dropna().unique().tolist())
        selected_budget = st.selectbox("Budget", budgets)
    
    with filter4:
        classes = ['All'] + sorted(flight_data['flight_class'].dropna().unique().tolist())
        selected_class = st.selectbox("Class", classes)
    
    # Apply filters
    filtered_data = flight_data.copy()
    
    if selected_origin != 'All':
        filtered_data = filtered_data[filtered_data['origin'] == selected_origin]
    if selected_destination != 'All':
        filtered_data = filtered_data[filtered_data['destination'] == selected_destination]
    if selected_budget != 'All':
        filtered_data = filtered_data[filtered_data['budget_preference'] == selected_budget]
    if selected_class != 'All':
        filtered_data = filtered_data[filtered_data['flight_class'] == selected_class]
    
    # Display summary metrics for filtered data
    st.markdown("### 📊 Filtered Data Summary")
    summary1, summary2, summary3 = st.columns(3)
    
    with summary1:
        st.metric("Filtered Records", len(filtered_data))
    
    with summary2:
        avg_duration = filtered_data['duration_days'].mean()
        st.metric("Avg Duration", f"{avg_duration:.1f} days" if not pd.isna(avg_duration) else "N/A")
    
    with summary3:
        if 'estimated_price' in filtered_data.columns:
            avg_price = filtered_data['estimated_price'].mean()
            st.metric("Avg Price", f"₹{avg_price:,.0f}" if not pd.isna(avg_price) else "N/A")
    
    st.markdown("---")
    
    # Flight data table
    st.markdown(f"### 📋 Flight Searches ({len(filtered_data)} records)")
    
    if not filtered_data.empty:
        # Prepare display data
        display_columns = [
            'origin', 'destination', 'departure_date', 'return_date',
            'duration_days', 'budget_preference', 'flight_class', 'created_at'
        ]
        
        display_data = filtered_data[
            [col for col in display_columns if col in filtered_data.columns]
        ].copy()
        
        # Format dates
        if 'created_at' in display_data.columns:
            display_data['Search Time'] = pd.to_datetime(
                display_data['created_at']
            ).dt.strftime('%Y-%m-%d %H:%M')
        
        # Show dataframe
        st.dataframe(display_data, use_container_width=True)
        
        # Recent searches sidebar
        with st.expander("🔍 Recent Flight Searches", expanded=False):
            try:
                recent_searches_df = fetch_recent_searches(5)
                if recent_searches_df is not None and not recent_searches_df.empty:
                    for idx, row in recent_searches_df.iterrows():
                        search_date = pd.to_datetime(row.get('created_at', '')).strftime('%Y-%m-%d %H:%M') if 'created_at' in row and row.get('created_at') else 'N/A'
                        origin = row.get('origin', 'N/A')
                        destination = row.get('destination', 'N/A')
                        duration = row.get('duration_days', 'N/A')
                        
                        st.markdown(f"""
                        **{origin} → {destination}**  
                        📅 {search_date} | 🗓️ {duration} days
                        """)
                        st.markdown("---")
                else:
                    st.info("No recent searches available.")
            except Exception as e:
                st.error(f"Error loading recent searches: {e}")

def display_system_status():
    """Display system status and health"""
    st.markdown("## 🔧 System Status & Health")
    
    # Database status section
    st.markdown("### 💾 Database Status")
    db_col1, db_col2 = st.columns(2)
    
    with db_col1:
        try:
            # Get database info
            db_info = get_database_info()
            
            st.success("✅ Database: Connected")
            st.write(f"**File Size:** {db_info.get('file_size_mb', 'Unknown')} MB")
            
            # Table information
            st.markdown("**Table Counts:**")
            for table, count in db_info.get('table_counts', {}).items():
                st.write(f"• {table}: {count:,} records")
                
        except Exception as e:
            st.error(f"❌ Database Error: {e}")
    
    with db_col2:
        st.markdown("#### API & Service Status")
        
        # Check API keys
        api_status = {
            "SerpAPI": SERPAPI_KEY is not None and SERPAPI_KEY != "",
            "Google API": GOOGLE_API_KEY is not None and GOOGLE_API_KEY != "",
            "Twilio": Client is not None
        }
        
        for service, status in api_status.items():
            if status:
                st.success(f"✅ {service}: Connected")
            else:
                st.error(f"❌ {service}: Not configured")
        
        # System metrics
        st.markdown("**System Info:**")
        st.write(f"• Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"• Session State Keys: {len(st.session_state)}")
    
    # Backup and export section
    st.markdown("---")
    st.markdown("### 📥 Data Management")
    
    backup_col1, backup_col2 = st.columns(2)
    
    with backup_col1:
        st.markdown("#### Backup Options")
        if st.button("💾 Create Database Backup", key="backup_btn", use_container_width=True):
            backup_name = backup_database()
            if backup_name:
                st.success(f"Backup created: {backup_name}")
            else:
                st.error("Backup failed")
    
    with backup_col2:
        st.markdown("#### Export Options")
        
        export1, export2, export3 = st.columns(3)
        
        with export1:
            if st.button("📊 Search Data", key="export_search_btn"):
                try:
                    search_data = fetch_all_searches()
                    if search_data is not None and not search_data.empty:
                        csv = search_data.to_csv(index=False)
                        st.download_button(
                            "💾 Download",
                            csv,
                            f"flight_searches_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            key="download_search_btn"
                        )
                    else:
                        st.warning("No search data available.")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with export2:
            if st.button("👥 Contact Data", key="export_contact_btn"):
                try:
                    contact_data = fetch_contacts()
                    if contact_data is not None and not contact_data.empty:
                        csv = contact_data.to_csv(index=False)
                        st.download_button(
                            "💾 Download",
                            csv,
                            f"contacts_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            key="download_contact_btn"
                        )
                    else:
                        st.warning("No contact data available.")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with export3:
            if st.button("📈 Analytics", key="export_analytics_btn"):
                try:
                    analytics_summary = generate_analytics_summary()
                    st.download_button(
                        "💾 Download",
                        analytics_summary,
                        f"analytics_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        key="download_analytics_btn"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

def unified_admin_dashboard():
    """Main unified admin dashboard"""
    st.markdown("# 🔐 RoamGenie Admin Dashboard")
    
    # Authentication
    if not admin_login():
        return
    
    st.markdown("---")
    
    # Navigation - Use selectbox instead of tabs for better organization
    dashboard_section = st.selectbox(
        "📋 Select Dashboard Section:",
        [
            "📊 Overview & Metrics",
            "📈 Analytics & Charts", 
            "👥 Customer Management",
            "✈️ Flight Management",
            "🔧 System Management"
        ],
        key="dashboard_section_selector"
    )
    
    st.markdown("---")
    
    # Display selected section
    if dashboard_section == "📊 Overview & Metrics":
        display_overview_metrics()
    
    elif dashboard_section == "📈 Analytics & Charts":
        display_charts_section()
    
    elif dashboard_section == "👥 Customer Management":
        display_customer_management()
    
    elif dashboard_section == "✈️ Flight Management":
        display_flight_management()
    
    elif dashboard_section == "🔧 System Management":
        display_system_status()

def handle_admin_dashboard():
    """Handle admin dashboard in main app"""
    # Dashboard Header
    st.header("📊 RoamGenie Dashboard")
    
    admin_access = st.checkbox("🔐 Admin Access", key="admin_access_checkbox")
    
    if admin_access:
        # Show unified admin dashboard
        unified_admin_dashboard()
    else:
        st.info("🔒 Dashboard access is restricted. Please enable Admin Access and login to view dashboard.")



st.set_page_config(page_title="RoamGenie - AI Travel Planner", layout="wide",initial_sidebar_state="collapsed")

with st.sidebar:
    st.markdown("### 🔑 Admin Access")
    if st.checkbox("Enable Admin Dashboard"):
        st.session_state.current_page = "Dashboard"


st.markdown("""
    <style>
        .title-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .main-title {
            font-size: 48px;
            font-weight: bold;
            color: #4A4A6A;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 24px;
            color: #777;
            margin-top: 0;
        }
        .stSlider > div { background-color: #f9f9f9; padding: 10px; border-radius: 10px; }
        .passport-scan { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin: 20px 0; }
        .visa-free-card {
            background: #f8f9fa;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .country-name {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .visa-status {
            font-size: 12px;
            color: #28a745;
            font-weight: 500;
        }
        .top-navigation {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .top-navigation button {
            background-color: transparent;
            color: #667eea;
            border: none;
            padding: 10px 15px;
            font-size: 18px;
            cursor: pointer;
            transition: color 0.3s, border-bottom 0.3s;
        }
        .top-navigation button:hover {
            color: #764ba2;
            border-bottom: 2px solid #764ba2;
        }
        .top-navigation button.active {
            color: #764ba2;
            font-weight: bold;
            border-bottom: 2px solid #764ba2;
        }
        .flight-card {
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            background-color: #f9f9f9;
            margin-bottom: 20px;
        }
        .flight-card img {
            max-width: 100px;
            margin-bottom: 10px;
        }
        .flight-card h3 {
            margin: 10px 0;
        }
        .flight-card p {
            margin: 5px 0;
        }
        .flight-card .price {
            color: #008000;
            font-size: 24px;
            font-weight: bold;
            margin-top: 10px;
        }
        .flight-card .book-now-link {
            display: inline-block;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            background-color: #007bff;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = "Roamlogo.png"
logo_base64 = get_base64_image(logo_path)

if 'passport_country' not in st.session_state:
    st.session_state.passport_country = None
if 'visa_free_countries' not in st.session_state:
    st.session_state.visa_free_countries = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Travel Plan"

st.markdown(f"""
    <div class="title-container">
        <img src="data:image/png;base64,{logo_base64}" width="150" style="margin-bottom: 10px;">
        <div class="main-title">RoamGenie</div>
        <p class="subtitle">AI-Powered Travel Planner</p>
    </div>
""", unsafe_allow_html=True)

SERPAPI_KEY = "38ad79ce3da5c3b2281cb1bc8a07c89997f88b30480f9de6866161da700d5da7"
GOOGLE_API_KEY = "AIzaSyCraftTEqYDP9NBHlJTQaoH0JnGrWIycok"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

OCR_SPACE_API_KEY = "YOUR_OCR_SPACE_API_KEY"
MINDEE_API_KEY = "YOUR_MINDEE_API_KEY"

class PassportScanner:
    def __init__(self):
        self.visa_data = None
        self.country_flags = {}
        self.load_visa_dataset()
        self.load_country_flags()

    def load_visa_dataset(self):
        try:
            url1 = "https://raw.githubusercontent.com/ilyankou/passport-index-dataset/master/passport-index-tidy.csv"
            try:
                self.visa_data = pd.read_csv(url1)
                return
            except Exception as e1:
                st.warning(f"Failed to load primary dataset: {e1}. Attempting secondary...")

            url2 = "https://raw.githubusercontent.com/datasets/passport-index/main/data/passport-index-tidy.csv"
            try:
                self.visa_data = pd.read_csv(url2)
                return
            except Exception as e2:
                st.warning(f"Failed to load secondary dataset: {e2}. Creating comprehensive dataset as fallback...")

            self.create_comprehensive_visa_data()

        except Exception as e:
            st.error(f"Error loading visa dataset: {e}")
            self.create_comprehensive_visa_data()

    def create_comprehensive_visa_data(self):
        visa_data = {
            'India': {
                'visa_free': [
                    'Bhutan', 'Nepal', 'Maldives', 'Mauritius', 'Seychelles', 'Fiji',
                    'Vanuatu', 'Micronesia', 'Samoa', 'Cook Islands', 'Niue', 'Tuvalu',
                    'Indonesia', 'Thailand', 'Malaysia', 'Singapore', 'Philippines',
                    'Cambodia', 'Laos', 'Myanmar', 'Sri Lanka', 'Bangladesh',
                    'South Korea', 'Japan', 'Qatar', 'UAE', 'Oman', 'Kuwait',
                    'Bahrain', 'Jordan', 'Iran', 'Armenia', 'Georgia', 'Kazakhstan',
                    'Kyrgyzstan', 'Tajikistan', 'Uzbekistan', 'Mongolia', 'Turkey',
                    'Serbia', 'Albania', 'North Macedonia', 'Bosnia and Herzegovina',
                    'Montenegro', 'Moldova', 'Belarus', 'Madagascar', 'Comoros',
                    'Cape Verde', 'Guinea-Bissau', 'Mozambique', 'Zimbabwe', 'Zambia',
                    'Uganda', 'Rwanda', 'Burundi', 'Tanzania', 'Kenya', 'Ethiopia',
                    'Djibouti', 'Somalia', 'Sudan', 'Egypt', 'Morocco', 'Tunisia',
                    'Barbados', 'Dominica', 'Grenada', 'Haiti', 'Jamaica',
                    'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines',
                    'Trinidad and Tobago', 'El Salvador', 'Honduras', 'Nicaragua',
                    'Bolivia', 'Ecuador', 'Suriname'
                ]
            },
            'United States': {
                'visa_free': [
                    'Canada', 'Mexico', 'United Kingdom', 'Ireland', 'France', 'Germany',
                    'Italy', 'Spain', 'Netherlands', 'Belgium', 'Luxembourg', 'Austria',
                    'Switzerland', 'Portugal', 'Greece', 'Denmark', 'Sweden', 'Norway',
                    'Finland', 'Iceland', 'Estonia', 'Latvia', 'Lithuania', 'Poland',
                    'Czech Republic', 'Slovakia', 'Hungary', 'Slovenia', 'Croatia',
                    'Malta', 'Cyprus', 'Japan', 'South Korea', 'Singapore', 'Australia',
                    'New Zealand', 'Chile', 'Uruguay', 'Argentina', 'Brazil', 'Israel',
                    'Taiwan', 'Hong Kong', 'Macau', 'Brunei', 'Malaysia', 'Thailand'
                ]
            },
            'Germany': {
                'visa_free': [
                    'European Union Countries', 'United States', 'Canada', 'Australia',
                    'New Zealand', 'Japan', 'South Korea', 'Singapore', 'Malaysia',
                    'Thailand', 'Philippines', 'Indonesia', 'Vietnam', 'Cambodia',
                    'Israel', 'United Arab Emirates', 'Qatar', 'Kuwait', 'Bahrain',
                    'Chile', 'Argentina', 'Brazil', 'Uruguay', 'Paraguay', 'Mexico',
                    'Costa Rica', 'Nicaragua', 'Honduras', 'El Salvador', 'Guatemala',
                    'Panama', 'Colombia', 'Ecuador', 'Peru', 'Bolivia', 'Venezuela',
                    'Guyana', 'Suriname', 'South Africa', 'Botswana', 'Namibia',
                    'Mauritius', 'Seychelles', 'Morocco', 'Tunisia', 'Turkey',
                    'Serbia', 'Montenegro', 'Albania', 'North Macedonia', 'Bosnia and Herzegovina'
                ]
            },
            'Singapore': {
                'visa_free': [
                    'Malaysia', 'Thailand', 'Indonesia', 'Philippines', 'Vietnam',
                    'Cambodia', 'Laos', 'Myanmar', 'Brunei', 'Japan', 'South Korea',
                    'Hong Kong', 'Macau', 'Taiwan', 'United States', 'Canada',
                    'United Kingdom', 'Ireland', 'European Union Countries',
                    'Australia', 'New Zealand', 'Chile', 'Argentina', 'Brazil',
                    'Uruguay', 'Israel', 'Turkey', 'United Arab Emirates', 'Qatar',
                    'Kuwait', 'Bahrain', 'Oman', 'Saudi Arabia', 'Jordan'
                ]
            },
            'United Kingdom': {
                'visa_free': [
                    'European Union Countries', 'United States', 'Canada', 'Australia',
                    'New Zealand', 'Japan', 'South Korea', 'Singapore', 'Malaysia',
                    'Thailand', 'Philippines', 'Indonesia', 'Vietnam', 'Hong Kong',
                    'Macau', 'Taiwan', 'Israel', 'United Arab Emirates', 'Qatar',
                    'Kuwait', 'Bahrain', 'Oman', 'Chile', 'Argentina', 'Brazil',
                    'Uruguay', 'Mexico', 'Costa Rica', 'Panama', 'Colombia',
                    'Ecuador', 'Peru', 'Bolivia', 'Venezuela', 'Guyana', 'Suriname'
                ]
            }
        }

        passport_data = []
        destination_data = []
        requirement_data = []

        for passport_country, data in visa_data.items():
            for dest_country in data['visa_free']:
                passport_data.append(passport_country)
                destination_data.append(dest_country)
                requirement_data.append('visa free')

        self.visa_data = pd.DataFrame({
            'Passport': passport_data,
            'Destination': destination_data,
            'Requirement': requirement_data
        })

    def load_country_flags(self):
        self.country_flags = {
            'Thailand': '', 'Singapore': '', 'Malaysia': '', 'Indonesia': '',
            'Philippines': '', 'Cambodia': '', 'Laos': '', 'Myanmar': '',
            'Vietnam': '', 'Brunei': '', 'Nepal': '', 'Bhutan': '',
            'Maldives': '', 'Sri Lanka': '', 'Bangladesh': '', 'India': '',
            'Japan': '', 'South Korea': '', 'China': '', 'Taiwan': '',
            'Hong Kong': '', 'Macau': '', 'Mongolia': '', 'Kazakhstan': '',
            'Kyrgyzstan': '', 'Tajikistan': '', 'Uzbekistan': '',

            'UAE': '', 'Qatar': '', 'Oman': '', 'Kuwait': '',
            'Bahrain': '', 'Saudi Arabia': '', 'Jordan': '', 'Lebanon': '',
            'Syria': '', 'Iraq': '', 'Iran': '', 'Israel': '',
            'Turkey': '', 'Cyprus': '', 'Armenia': '', 'Georgia': '',

            'United Kingdom': '', 'Ireland': '', 'France': '', 'Germany': '',
            'Italy': '', 'Spain': '', 'Portugal': '', 'Netherlands': '',
            'Belgium': '', 'Luxembourg': '', 'Switzerland': '', 'Austria': '',
            'Denmark': '', 'Sweden': '', 'Norway': '', 'Finland': '',
            'Iceland': '', 'Greece': '', 'Malta': '', 'Poland': '',
            'Czech Republic': '', 'Slovakia': '', 'Hungary': '',
            'Slovenia': '', 'Croatia': '', 'Bosnia and Herzegovina': '',
            'Serbia': '', 'Montenegro': '', 'Albania': '',
            'North Macedonia': '', 'Bulgaria': '', 'Romania': '',
            'Moldova': '', 'Ukraine': '', 'Belarus': '', 'Russia': '',
            'Estonia': '', 'Latvia': '', 'Lithuania': '',

            'United States': '', 'Canada': '', 'Mexico': '', 'Guatemala': '',
            'Belize': '', 'El Salvador': '', 'Honduras': '', 'Nicaragua': '',
            'Costa Rica': '', 'Panama': '', 'Colombia': '', 'Venezuela': '',
            'Guyana': '', 'Suriname': '', 'Brazil': '', 'Ecuador': '',
            'Peru': '', 'Bolivia': '', 'Paraguay': '', 'Uruguay': '',
            'Argentina': '', 'Chile': '', 'Cuba': '', 'Jamaica': '',
            'Haiti': '', 'Dominican Republic': '', 'Puerto Rico': '',
            'Trinidad and Tobago': '', 'Barbados': '', 'Saint Lucia': '',
            'Grenada': '', 'Saint Vincent and the Grenadines': '',
            'Saint Kitts and Nevis': '', 'Dominica': '',

            'Morocco': '', 'Algeria': '', 'Tunisia': '', 'Libya': '',
            'Egypt': '', 'Sudan': '', 'Ethiopia': '', 'Kenya': '',
            'Uganda': '', 'Tanzania': '', 'Rwanda': '', 'Burundi': '',
            'Somalia': '', 'Djibouti': '', 'Madagascar': '', 'Mauritius': '',
            'Seychelles': '', 'Comoros': '', 'South Africa': '',
            'Namibia': '', 'Botswana': '', 'Zimbabwe': '', 'Zambia': '',
            'Mozambique': '', 'Malawi': '', 'Angola': '', 'Ghana': '',
            'Nigeria': '', 'Senegal': '', 'Mali': '', 'Burkina Faso': '',
            'Niger': '', 'Chad': '', 'Cameroon': '', 'Central African Republic': '',
            'Democratic Republic of the Congo': '', 'Republic of the Congo': '',
            'Gabon': '', 'Equatorial Guinea': '', 'Sao Tome and Principe': '',
            'Cape Verde': '', 'Guinea-Bissau': '', 'Guinea': '',
            'Sierra Leone': '', 'Liberia': '', 'Ivory Coast': '', 'Togo': '',
            'Benin': '',

            'Australia': '', 'New Zealand': '', 'Fiji': '', 'Papua New Guinea': '',
            'Solomon Islands': '', 'Vanuatu': '', 'New Caledonia': '',
            'French Polynesia': '', 'Samoa': '', 'Tonga': '', 'Tuvalu': '',
            'Kiribati': '', 'Nauru': '', 'Palau': '', 'Marshall Islands': '',
            'Micronesia': '', 'Cook Islands': '', 'Niue': ''
        }

    def extract_passport_info_tesseract(self, image_file):
        try:
            image = Image.open(image_file)
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh, config='--psm 6')
            return self.parse_passport_text(text)

        except Exception as e:
            st.error(f"Tesseract OCR Error: {e}")
            return None

    def parse_passport_text(self, text):
        text = text.upper()

        country_patterns = [
            r'REPUBLIC OF ([A-Z\s]+)',
            r'UNITED STATES OF AMERICA',
            r'UNITED KINGDOM',
            r'PASSPORT\s+([A-Z\s]+)',
            r'NATIONALITY\s+([A-Z\s]+)',
            r'COUNTRY CODE\s+([A-Z]{3})',
        ]

        country_mapping = {
            'INDIA': 'India',
            'UNITED STATES OF AMERICA': 'United States',
            'UNITED KINGDOM': 'United Kingdom',
            'GERMANY': 'Germany',
            'FRANCE': 'France',
            'SINGAPORE': 'Singapore',
            'JAPAN': 'Japan',
            'AUSTRALIA': 'Australia',
            'CANADA': 'Canada',
        }

        for pattern in country_patterns:
            match = re.search(pattern, text)
            if match:
                country = match.group(1) if match.groups() else match.group(0)
                country = country.strip()
                if country in country_mapping:
                    return {'country': country_mapping[country], 'confidence': 0.8}

        for country_key, country_name in country_mapping.items():
            if country_key in text:
                return {'country': country_name, 'confidence': 0.6}

        return None

    def get_visa_free_countries(self, passport_country):
        if self.visa_data is None:
            st.error("Visa dataset not loaded")
            return []

        try:
            passport_country_clean = passport_country.strip()

            visa_free_data = self.visa_data[
                (self.visa_data['Passport'].str.strip().str.lower() == passport_country_clean.lower()) &
                (self.visa_data['Requirement'].str.contains('visa free|visa-free|visa on arrival', case=False, na=False))
            ]

            if visa_free_data.empty:
                visa_free_data = self.visa_data[
                    (self.visa_data['Passport'].str.contains(passport_country_clean, case=False, na=False)) &
                    (self.visa_data['Requirement'].str.contains('visa free|visa-free|visa on arrival', case=False, na=False))
                ]

            countries = sorted(visa_free_data['Destination'].unique().tolist())

            countries = [country for country in countries if country and str(country).strip()]

            st.success(f"Found {len(countries)} visa-free destinations for {passport_country_clean}")

            return countries

        except Exception as e:
            st.error(f"Error fetching visa-free countries: {e}")
            return []

passport_scanner = PassportScanner()

# Navigation Bar
col_nav = st.columns(5)
if col_nav[0].button("Travel Plan", key="nav_travel_plan", help="Plan your next trip"):
    st.session_state.current_page = "Travel Plan"
if col_nav[1].button("Passport", key="nav_passport", help="Find visa-free destinations based on your passport"):
    st.session_state.current_page = "Passport"
if col_nav[2].button("IVR Call", key="nav_ivr_call", help="Initiate a travel IVR call"):
    st.session_state.current_page = "IVR Call"
if col_nav[3].button("Contact Us", key="nav_contact_us", help="Get in touch with us"):
    st.session_state.current_page = "Contact Us"
if col_nav[4].button("Emergency Support", key="nav_emergency_support", help="Emergency & offline help"):
    st.session_state.current_page = "Emergency & Offline Support"



st.markdown("---")

# Conditional Content Display
if st.session_state.current_page == "Travel Plan":
    st.subheader("Plan Your Adventure")

    col_plan1, col_plan2 = st.columns(2)
    with col_plan1:
        st.markdown("### Where are you headed?")
        destination_default = "DEL"
        if st.session_state.visa_free_countries:
            st.info(f"Tip: You can travel visa-free to {len(st.session_state.visa_free_countries)} countries!")

            popular_destinations = []
            if st.session_state.passport_country == 'India':
                popular_destinations = [country for country in ['Thailand', 'Singapore', 'Malaysia', 'UAE', 'Nepal']
                                          if country in st.session_state.visa_free_countries]
            elif st.session_state.passport_country == 'United States':
                popular_destinations = [country for country in ['United Kingdom', 'France', 'Germany', 'Japan', 'Canada']
                                          if country in st.session_state.visa_free_countries]

            if popular_destinations:
                st.write("Popular visa-free destinations for you:")
                dest_cols = st.columns(len(popular_destinations))
                for idx, dest in enumerate(popular_destinations):
                    with dest_cols[idx]:
                        flag = passport_scanner.country_flags.get(dest, '')
                        st.write(f"{flag} {dest}")

        source = st.text_input("Departure City (IATA Code):", "BOM")
        destination = st.text_input("Destination (IATA Code):", destination_default)

        num_days = st.slider("Trip Duration (days):", 1, 14, 5)
        travel_theme = st.selectbox("Select Your Travel Theme:", ["Couple Getaway", "Family Vacation", "Adventure Trip", "Solo Exploration"])

        activity_preferences = st.text_area("What activities do you enjoy?", "Relaxing on the beach, exploring historical sites")
        departure_date = st.date_input("Departure Date", min_value=datetime.today())
        return_date = st.date_input("Return Date", min_value=datetime.today())

    with col_plan2:
        st.subheader("Your Preferences")
        budget = st.radio("Budget Preference:", ["Economy", "Standard", "Luxury"])
        flight_class = st.radio("Flight Class:", ["Economy", "Business", "First Class"])
        hotel_rating = st.selectbox("Preferred Hotel Rating:", ["Any", "3", "4", "5"])

        st.subheader("Packing Checklist")
        packing_list = {
            "Clothes": True,
            "Comfortable Footwear": True,
            "Sunglasses & Sunscreen": False,
            "Travel Guidebook": False,
            "Medications & First-Aid": True
        }
        for item, checked in packing_list.items():
            st.checkbox(item, value=checked)

        st.subheader("Travel Essentials")
        visa_required_checkbox = st.checkbox("Check Visa Requirements")
        travel_insurance_checkbox = st.checkbox("Get Travel Insurance")
        currency_converter_checkbox = st.checkbox("Currency Exchange Rates")

    def format_datetime(iso_string):
        try:
            dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
            return dt.strftime("%b-%d, %Y | %I:%M %p")
        except:
            return "N/A"

    def fetch_flights(source_iata, destination_iata, departure_date_obj, return_date_obj):
        params = {
            "engine": "google_flights",
            "departure_id": source_iata,
            "arrival_id": destination_iata,
            "outbound_date": str(departure_date_obj),
            "return_date": str(return_date_obj),
            "currency": "INR",
            "hl": "en",
            "api_key": SERPAPI_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    
    def extract_cheapest_flights(flight_data):
        best_flights = flight_data.get("best_flights", [])
        return sorted(best_flights, key=lambda x: x.get("price", float("inf")))[:3]

    def get_destination_country(iata_code):
        iata_to_country = {
            'DEL': 'India', 'BOM': 'India', 'BLR': 'India', 'MAA': 'India',
            'BKK': 'Thailand', 'SIN': 'Singapore', 'KUL': 'Malaysia',
            'DXB': 'UAE', 'DOH': 'Qatar', 'KTM': 'Nepal', 'CMB': 'Sri Lanka',
            'NRT': 'Japan', 'ICN': 'South Korea', 'TPE': 'Taiwan',
            'LHR': 'United Kingdom', 'CDG': 'France', 'FRA': 'Germany',
            'FCO': 'Italy', 'MAD': 'Spain', 'AMS': 'Netherlands',
            'ZUR': 'Switzerland', 'VIE': 'Austria', 'ARN': 'Sweden',
            'CPH': 'Denmark', 'OSL': 'Norway', 'HEL': 'Finland',
            'JFK': 'United States', 'LAX': 'United States', 'YYZ': 'Canada',
            'SYD': 'Australia', 'MEL': 'Australia', 'AKL': 'New Zealand'
        }
        return iata_to_country.get(iata_code.upper(), 'Unknown')

    researcher = Agent(
        name="Researcher",
        instructions=[
            "Identify destination, research climate, safety, top attractions, and activities.",
            "Use reliable sources and summarize results clearly."
        ],
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[SerpApiTools(api_key=SERPAPI_KEY)],
        add_datetime_to_instructions=True,
    )

    planner = Agent(
        name="Planner",
        instructions=[
            "Create a detailed itinerary with travel preferences, time estimates, and budget alignment."
        ],
        model=Gemini(id="gemini-2.0-flash-exp"),
        add_datetime_to_instructions=True,
    )

    hotel_restaurant_finder = Agent(
        name="Hotel & Restaurant Finder",
        instructions=[
            "Find top-rated hotels and restaurants near main attractions. Include booking links if possible."
        ],
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[SerpApiTools(api_key=SERPAPI_KEY)],
        add_datetime_to_instructions=True,
    )

    if st.button("Generate Travel Plan"):
        visa_status = "Unknown"
        destination_country = get_destination_country(destination)

        if st.session_state.passport_country and st.session_state.visa_free_countries:
            if destination_country in st.session_state.visa_free_countries:
                visa_status = "Visa-Free"
            elif destination_country != 'Unknown':
                visa_status = "Visa Required"
            else:
                visa_status = "Check visa requirements"

        if visa_status == "Visa-Free":
            st.success(f"Great news! {visa_status} travel to {destination_country}")
        elif visa_status == "Visa Required":
            st.warning(f"{visa_status} for {destination_country} - Please check visa requirements")
        else:
            st.info(f"{visa_status} for {destination_country}")

        with st.spinner("Fetching best flight options..."):
            flight_data = fetch_flights(source, destination, departure_date, return_date)
            cheapest_flights = extract_cheapest_flights(flight_data)

        with st.spinner("Researching best attractions & activities..."):
            research_prompt = (
                f"Research top attractions in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
                f"Interests: {activity_preferences}. Budget: {budget}. Class: {flight_class}. Rating: {hotel_rating}."
            )
            research_results = researcher.run(research_prompt, stream=False)

        with st.spinner("Searching for hotels & restaurants..."):
            hotel_restaurant_prompt = (
                f"Recommend hotels and restaurants in {destination} for a {travel_theme.lower()} trip. "
                f"Preferences: {activity_preferences}. Budget: {budget}. Hotel Rating: {hotel_rating}."
            )
            hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

        with st.spinner("Creating itinerary..."):
            planning_prompt = (
                f"Create a {num_days}-day travel itinerary to {destination} for a {travel_theme.lower()} trip. "
                f"Preferences: {activity_preferences}. Budget: {budget}. Class: {flight_class}. Rating: {hotel_rating}. "
                f"Research: {research_results.content}. Flights: {json.dumps(cheapest_flights)}. "
                f"Hotels & Restaurants: {hotel_restaurant_results.content}."
            )
            itinerary = planner.run(planning_prompt, stream=False)

        st.subheader("Cheapest Flight Options")
        if cheapest_flights:
            cols = st.columns(len(cheapest_flights))
            for idx, flight in enumerate(cheapest_flights):
                with cols[idx]:
                    airline_logo = flight.get("airline_logo", "")
                    airline_name = flight.get("airline", "Unknown Airline")
                    price = flight.get("price", "Not Available")
                    total_duration_minutes = flight.get("total_duration", "N/A")

                    flights_details = flight.get("flights", [{}])
                    departure_airport_info = flights_details[0].get("departure_airport", {})
                    arrival_airport_info = flights_details[-1].get("arrival_airport", {})

                    departure_time = format_datetime(departure_airport_info.get("time", "N/A"))
                    arrival_time = format_datetime(arrival_airport_info.get("time", "N/A"))
                    
                    booking_link = flight.get("link", f"https://www.google.com/flights?q={source}+{destination}")

                    st.markdown(
                        f"""
                        <div class="flight-card">
                            <img src="{airline_logo}" alt="Airline Logo" />
                            <h3>{airline_name}</h3>
                            <p><strong>Departure:</strong> {departure_time}</p>
                            <p><strong>Arrival:</strong> {arrival_time}</p>
                            <p><strong>Duration:</strong> {total_duration_minutes} min</p>
                            <div class="price">₹ {price}</div>
                            <a href="{booking_link}" target="_blank" class="book-now-link">Book Now</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning("No flight data available.")

        st.subheader("Hotels & Restaurants")
        st.write(hotel_restaurant_results.content)

        st.subheader("Your Personalized Itinerary")
        st.write(itinerary.content)

        # inside Generate Travel Plan block, after you build 'itinerary' and cheapest_flights
        price_estimate = None
        try:
            price_estimate = float(cheapest_flights[0].get("price")) if cheapest_flights and cheapest_flights[0].get("price") else None
        except Exception:
            price_estimate = None

        # Log into DB
        try:
            log_flight_search(
                source, destination, str(departure_date), str(return_date),
                num_days, budget, flight_class, price_estimate
            )
        except Exception as e:
            st.warning(f"Could not log flight search: {e}")

        st.success("Travel plan generated successfully!")

elif st.session_state.current_page == "Passport":
    st.markdown("""
        <div class="passport-scan">
            <h2 style="color: white; text-align: center;">Passport Scanner</h2>
            <p style="color: white; text-align: center;">Upload your passport photo to discover visa-free travel destinations!</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Upload Passport Photo")
        uploaded_file = st.file_uploader(
            "Choose passport image...",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a clear photo of your passport's main page"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Passport", use_column_width=True)

            if st.button("Scan Passport"):
                with st.spinner("Scanning passport..."):
                    uploaded_file.seek(0)

                    passport_info = passport_scanner.extract_passport_info_tesseract(uploaded_file)

                    if passport_info:
                        st.session_state.passport_country = passport_info['country']
                        st.success(f"Passport detected: {passport_info['country']} (Confidence: {passport_info['confidence']:.1%})")

                        with st.spinner("Finding visa-free destinations..."):
                            visa_free = passport_scanner.get_visa_free_countries(passport_info['country'])
                            st.session_state.visa_free_countries = visa_free

                    else:
                        st.error("Could not extract passport information. Please try a clearer image.")

    with col2:
        st.subheader("Manual Country Selection")
        st.write("Or select your passport country manually:")

        available_countries = []
        if passport_scanner.visa_data is not None:
            available_countries = sorted(passport_scanner.visa_data['Passport'].unique().tolist())
        else:
            available_countries = [
                'India', 'United States', 'United Kingdom', 'Germany', 'France',
                'Singapore', 'Japan', 'Australia', 'Canada', 'Netherlands',
                'Switzerland', 'Sweden', 'Norway', 'Denmark', 'Finland'
            ]

        selected_country = st.selectbox("Select your passport country:", [''] + available_countries)

        if selected_country and st.button("Find Visa-Free Countries"):
            st.session_state.passport_country = selected_country
            with st.spinner("Finding visa-free destinations..."):
                visa_free = passport_scanner.get_visa_free_countries(selected_country)
                st.session_state.visa_free_countries = visa_free

    if st.session_state.passport_country and st.session_state.visa_free_countries:
        st.markdown("---")
        st.subheader(f"Visa-Free Destinations for {st.session_state.passport_country} Passport Holders")

        st.info(f"Great news! You can travel to {len(st.session_state.visa_free_countries)} countries visa-free!")

        search_country = st.text_input("Search countries:", placeholder="Type to filter countries...")

        filtered_countries = st.session_state.visa_free_countries
        if search_country:
            filtered_countries = [country for country in st.session_state.visa_free_countries
                                  if search_country.lower() in country.lower()]
            st.write(f"Found {len(filtered_countries)} countries matching '{search_country}'")

        if filtered_countries:
            cols = st.columns(4)
            for idx, country in enumerate(filtered_countries):
                col_idx = idx % 4
                with cols[col_idx]:
                    flag = passport_scanner.country_flags.get(country, '')

                    st.markdown(f"""
                        <div class="visa-free-card">
                            <div class="country-name">{flag} {country}</div>
                            <div class="visa-status">Visa-Free Entry</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("No countries found matching your search.")

        st.markdown("### Regional Breakdown")

        asia_countries = ['Thailand', 'Singapore', 'Malaysia', 'Indonesia', 'Philippines',
                          'Cambodia', 'Laos', 'Myanmar', 'Vietnam', 'Brunei', 'Nepal', 'Bhutan',
                          'South Korea', 'Japan', 'Mongolia', 'Kazakhstan', 'Kyrgyzstan',
                          'Tajikistan', 'Uzbekistan']

        europe_countries = ['Germany', 'France', 'Italy', 'Spain', 'United Kingdom', 'Ireland',
                            'Netherlands', 'Belgium', 'Switzerland', 'Austria', 'Portugal',
                            'Greece', 'Denmark', 'Sweden', 'Norway', 'Finland', 'Iceland',
                            'Poland', 'Czech Republic', 'Slovakia', 'Hungary', 'Slovenia',
                            'Croatia', 'Serbia', 'Montenegro', 'Albania', 'North Macedonia',
                            'Bosnia and Herzegovina', 'Bulgaria', 'Romania', 'Moldova', 'Belarus']

        middle_east_countries = ['UAE', 'Qatar', 'Oman', 'Kuwait', 'Bahrain', 'Saudi Arabia',
                                 'Jordan', 'Turkey', 'Armenia', 'Georgia', 'Iran', 'Israel']

        africa_countries = ['Mauritius', 'Seychelles', 'Madagascar', 'Comoros', 'Cape Verde',
                            'Guinea-Bissau', 'Mozambique', 'Zimbabwe', 'Zambia', 'Uganda',
                            'Rwanda', 'Burundi', 'Tanzania', 'Kenya', 'Ethiopia', 'Djibouti',
                            'Somalia', 'Sudan', 'Egypt', 'Morocco', 'Tunisia', 'South Africa',
                            'Namibia', 'Botswana']

        americas_countries = ['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina',
                              'Chile', 'Uruguay', 'Paraguay', 'Colombia', 'Ecuador', 'Peru',
                              'Bolivia', 'Venezuela', 'Guyana', 'Suriname', 'Jamaica', 'Haiti',
                              'Barbados', 'Trinidad and Tobago', 'Dominica', 'Grenada',
                              'Saint Lucia', 'Saint Vincent and the Grenadines',
                              'Saint Kitts and Nevis', 'El Salvador', 'Honduras', 'Nicaragua']

        oceania_countries = ['Australia', 'New Zealand', 'Fiji', 'Vanuatu', 'Samoa', 'Tonga',
                             'Cook Islands', 'Niue', 'Tuvalu', 'Micronesia', 'Papua New Guinea']

        asia_count = sum(1 for country in st.session_state.visa_free_countries if country in asia_countries)
        europe_count = sum(1 for country in st.session_state.visa_free_countries if country in europe_countries)
        middle_east_count = sum(1 for country in st.session_state.visa_free_countries if country in middle_east_countries)
        africa_count = sum(1 for country in st.session_state.visa_free_countries if country in africa_countries)
        americas_count = sum(1 for country in st.session_state.visa_free_countries if country in americas_countries)
        oceania_count = sum(1 for country in st.session_state.visa_free_countries if country in oceania_countries)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Asia", asia_count)
        with col2:
            st.metric("Europe", europe_count)
        with col3:
            st.metric("Middle East", middle_east_count)
        with col4:
            st.metric("Africa", africa_count)
        with col5:
            st.metric("Americas", americas_count)
        with col6:
            st.metric("Oceania", oceania_count)

elif st.session_state.current_page == "IVR Call":
    # Replace this with your actual n8n webhook URL
    N8N_WEBHOOK_URL = "https://lala-roamgenie.app.n8n.cloud/webhook/initiate-call"

    user_phone = st.text_input("Enter your phone number (with country code)", "+91XXXXXXXXX")

    if st.button("Start Call"):
        # Enhanced validation
        if user_phone.startswith("+91") and len(user_phone) == 13 and user_phone[3:].isdigit():
            with st.spinner("Calling..."):
                try:
                    payload = {
                        "to_number": user_phone
                    }
                    
                    # Add debugging information
                    st.write(f"Debug: Sending request to {N8N_WEBHOOK_URL}")
                    st.write(f"Debug: Payload: {payload}")

                    response = requests.post(
                        N8N_WEBHOOK_URL, 
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=30  # Add timeout
                    )
                    
                    # Enhanced response handling
                    st.write(f"Debug: Response status code: {response.status_code}")
                    st.write(f"Debug: Response headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            st.write(f"Debug: Response JSON: {result}")
                            
                            if result.get("success"):
                                st.success(f"Call initiated successfully! SID: {result.get('sid', 'N/A')}")
                            else:
                                st.warning(f"Call request processed but marked as unsuccessful: {result}")
                        except ValueError as json_error:
                            st.error(f"Response received but not valid JSON: {response.text}")
                    else:
                        st.error(f"Call initiation failed. Status: {response.status_code}")
                        st.error(f"Response content: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please check your internet connection and try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Connection error. Please check if the webhook URL is accessible.")
                except requests.exceptions.RequestException as req_error:
                    st.error(f"Request error: {req_error}")
                except Exception as e:
                    st.error(f"Unexpected error: {type(e).__name__}: {e}")
                    
        else:
            st.warning("Please enter a valid Indian phone number starting with +91 (13 digits total).")
            if not user_phone.startswith("+91"):
                st.info("Phone number should start with +91")
            elif len(user_phone) != 13:
                st.info(f"Phone number should be 13 characters long (currently {len(user_phone)})")
            elif not user_phone[3:].isdigit():
                st.info("Phone number should contain only digits after +91")

    # Add a test connectivity button
    if st.button("Test Webhook Connectivity"):
        try:
            test_response = requests.get(N8N_WEBHOOK_URL.replace('/webhook/', '/webhook-test/'), timeout=10)
            st.info(f"Webhook test response: {test_response.status_code}")
        except Exception as e:
            st.error(f"Webhook connectivity test failed: {e}")

    # Display current session state for debugging
    if st.checkbox("Show Debug Info"):
        st.write("Current session state:")
        for key, value in st.session_state.items():
            st.write(f"- {key}: {value}")

# Fixed Contact Us Section
elif st.session_state.current_page == "Contact Us":
    st.header("💾 Save Your Plan / Contact Us")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Contact Information")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        message = st.text_area("Message (Optional)", "I'm interested in travel planning services...")

        def save_contact_locally(first_name, last_name, email, phone, message=""):
            """Save contact to local database using the imported function"""
            try:
                # Fix: Use the correct function signature from your database code
                success = log_enhanced_contact(
                    firstName=first_name,
                    secondName=last_name,  # Note: database uses secondName, not last_name
                    email=email,
                    phone=phone,
                    source='web_form'
                )
                
                if success:
                    # Log the event with message
                    log_event('contact_submitted', {
                        'email': email,
                        'message': message,
                        'source': 'web_form'
                    }, getattr(st.session_state, 'session_id', 'unknown'))
                    return True, "Contact saved successfully!"
                else:
                    return True, "Contact updated successfully!"  # False means updated, not failed
                    
            except Exception as e:
                return False, f"Database error: {e}"

        def send_to_vendasta(first_name, last_name, email, phone, message=""):
            """Send contact info to Vendasta CRM"""
            payload = {
                "firstName": first_name,
                "secondName": last_name,
                "email": email,
                "phone": phone,
                "message": message
            }
            try:
                res = requests.post(
                    "https://automations.businessapp.io/start/UNMG/59276034-e50b-4344-b053-7022d7eac352",
                    json=payload,
                    timeout=10
                )
                if res.status_code == 200:
                    return True, "Info sent to our CRM successfully!"
                else:
                    return False, f"CRM submission failed. Status code: {res.status_code}"
            except Exception as e:
                return False, f"Error sending to CRM: {e}"

        if st.button("📤 Send My Info", key="send_contact_info"):
            if all([first_name, last_name, email, phone]):
                with st.spinner("Saving your information..."):
                    # Save locally first
                    local_success, local_message = save_contact_locally(first_name, last_name, email, phone, message)
                    
                    if local_success:
                        st.success(f"✅ {local_message}")
                        
                        # Then send to Vendasta
                        vendasta_success, vendasta_message = send_to_vendasta(first_name, last_name, email, phone, message)
                        
                        if vendasta_success:
                            st.success(f"✅ {vendasta_message}")
                        else:
                            st.warning(f"⚠️ {vendasta_message} (But saved locally)")
                        
                    else:
                        st.error(f"❌ {local_message}")
            else:
                st.warning("⚠️ Please complete all required fields (First Name, Last Name, Email, Phone).")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                if key not in ['session_id']:  # Keep session ID
                    del st.session_state[key]
            st.success("Session reset successfully!")
            st.rerun()


# Enhanced Admin Dashboard Functi
# Your existing Dashboard section with the admin call fix
elif st.session_state.current_page == "Dashboard":
    handle_admin_dashboard()
        
elif st.session_state.current_page == "Emergency & Offline Support":
    st.markdown("## 🛡️ Emergency & Offline Support")

    st.write("SEND (join edge-general) on +14155238886 to join our WhatsApp group fallback simulation.")
    user_whatsapp = st.text_input("📱 Enter your WhatsApp number (with +91)", "+91")

    # Twilio WhatsApp credentials
    try:
        TWILIO_SID = st.secrets["TWILIO_SID"]
        TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
        TWILIO_WHATSAPP = "whatsapp:+14155238886"  # Twilio sandbox number
        whatsapp_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    except KeyError:
        whatsapp_client = None
        st.warning("WhatsApp service not configured")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚨 Simulate Flight Cancellation Alert"):
            if user_whatsapp.startswith("+91") and len(user_whatsapp) == 13:
                try:
                    if whatsapp_client:
                        whatsapp_client.messages.create(
                            from_=TWILIO_WHATSAPP,
                            to=f"whatsapp:{user_whatsapp}",
                            body="🚨 [Emergency] Your flight AI302 has been CANCELLED. Please check your email for rebooking or call +91-9999999999 for help."
                        )
                        st.success("Emergency WhatsApp alert sent successfully!")
                    else:
                        st.error("WhatsApp service not available")
                except Exception as e:
                    st.error(f"Error sending WhatsApp message: {e}")
            else:
                st.warning("Please enter a valid WhatsApp number.")

    with col2:
        if st.button("📴 Simulate Offline Fallback"):
            st.info("It seems you're offline or unable to access live assistance.")
            try:
                if whatsapp_client:
                    whatsapp_client.messages.create(
                        from_=TWILIO_WHATSAPP,
                        to=f"whatsapp:{user_whatsapp}",
                        body="📴 [Fallback] Our systems are temporarily offline. For urgent help, call +91-9999999999 or visit your nearest airline office."
                    )
                    st.success("Offline fallback message sent to WhatsApp!")
                else:
                    st.error("WhatsApp service not available")
            except Exception as e:
                st.error(f"Could not send fallback message: {e}")






