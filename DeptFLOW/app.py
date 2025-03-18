import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from habit_manager import HabitManager
from visualizations import (
    create_completion_heatmap,
    create_completion_rate_chart,
    create_habit_summary,
    create_weekly_pattern
)

# Initialize session state
if 'habit_manager' not in st.session_state:
    st.session_state.habit_manager = HabitManager()

def main():
    st.title("Habit Tracker")
    
    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Daily Check-in", "Manage Habits", "Analytics", "Export Data"])
    
    if page == "Daily Check-in":
        show_daily_checkin()
    elif page == "Manage Habits":
        show_habit_management()
    elif page == "Analytics":
        show_analytics()
    else:
        show_export()

def show_daily_checkin():
    st.header("Daily Check-in")
    
    # Date selection
    selected_date = st.date_input(
        "Select Date",
        datetime.now().date()
    )
    
    habits = st.session_state.habit_manager.get_all_habits()
    if habits.empty:
        st.warning("No habits created yet. Please add habits in the Manage Habits section.")
        return
    
    st.subheader("Mark your habits")
    for _, habit in habits.iterrows():
        completed = st.checkbox(
            habit['name'],
            key=f"habit_{habit['id']}_{selected_date}"
        )
        st.session_state.habit_manager.log_habit_completion(
            habit['id'],
            selected_date,
            completed
        )

def show_habit_management():
    st.header("Manage Habits")
    
    # Add new habit
    new_habit = st.text_input("Add new habit")
    if st.button("Add Habit") and new_habit:
        st.session_state.habit_manager.create_habit(new_habit)
        st.success(f"Added new habit: {new_habit}")
        st.rerun()
    
    # List existing habits
    habits = st.session_state.habit_manager.get_all_habits()
    if not habits.empty:
        st.subheader("Existing Habits")
        for _, habit in habits.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(habit['name'])
            with col2:
                if st.button("Delete", key=f"delete_{habit['id']}"):
                    st.session_state.habit_manager.delete_habit(habit['id'])
                    st.success(f"Deleted habit: {habit['name']}")
                    st.rerun()

def show_analytics():
    st.header("Analytics Dashboard")
    
    habits = st.session_state.habit_manager.get_all_habits()
    if habits.empty:
        st.warning("No habits to analyze yet.")
        return
    
    # Habit selection for detailed analysis
    selected_habit = st.selectbox(
        "Select Habit for Detailed Analysis",
        habits['name']
    )
    selected_habit_id = habits[habits['name'] == selected_habit]['id'].iloc[0]
    
    # Time range selection
    time_range = st.slider(
        "Select Time Range (days)",
        min_value=7,
        max_value=90,
        value=30
    )
    
    # Get habit data
    habit_data = st.session_state.habit_manager.get_habit_data(
        selected_habit_id,
        time_range
    )
    
    # Display streak information
    current_streak, max_streak = st.session_state.habit_manager.get_streaks(selected_habit_id)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Streak", current_streak)
    with col2:
        st.metric("Longest Streak", max_streak)
    
    # Display visualizations
    st.subheader("Completion Heatmap")
    heatmap = create_completion_heatmap(habit_data, selected_habit)
    if heatmap:
        st.plotly_chart(heatmap)
    
    st.subheader("Completion Rate Trend")
    completion_chart = create_completion_rate_chart(habit_data)
    if completion_chart:
        st.plotly_chart(completion_chart)
    
    st.subheader("Weekly Pattern")
    weekly_pattern = create_weekly_pattern(habit_data)
    if weekly_pattern:
        st.plotly_chart(weekly_pattern)
    
    # Display summary statistics
    st.subheader("Summary Statistics")
    summary = create_habit_summary(habit_data)
    if not summary.empty:
        st.dataframe(summary)

def show_export():
    st.header("Export Data")
    
    if st.button("Download Habit Data"):
        data = st.session_state.habit_manager.export_data()
        if not data.empty:
            csv = data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="habit_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data to export.")

if __name__ == "__main__":
    main()
