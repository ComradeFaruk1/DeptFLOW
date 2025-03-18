import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import calendar
from datetime import datetime, timedelta

def create_completion_heatmap(habit_logs, habit_name):
    if habit_logs.empty:
        return None
        
    # Prepare data for heatmap
    habit_logs['week'] = pd.to_datetime(habit_logs['date']).dt.isocalendar().week
    habit_logs['weekday'] = pd.to_datetime(habit_logs['date']).dt.weekday
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        x=habit_logs['weekday'],
        y=habit_logs['week'],
        z=habit_logs['completed'].astype(int),
        colorscale=[[0, 'lightgrey'], [1, 'green']],
        showscale=False
    ))
    
    fig.update_layout(
        title=f'Habit Completion Heatmap - {habit_name}',
        xaxis=dict(
            ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            tickvals=[0, 1, 2, 3, 4, 5, 6]
        ),
        yaxis=dict(
            title='Week of Year'
        )
    )
    return fig

def create_completion_rate_chart(habit_logs):
    if habit_logs.empty:
        return None
        
    # Calculate completion rate by date
    completion_rate = habit_logs.groupby('date')['completed'].mean().reset_index()
    
    fig = px.line(
        completion_rate,
        x='date',
        y='completed',
        title='Daily Completion Rate',
        labels={'completed': 'Completion Rate', 'date': 'Date'}
    )
    return fig

def create_habit_summary(habit_logs):
    if habit_logs.empty:
        return pd.DataFrame()
        
    summary = habit_logs.groupby('name').agg({
        'completed': ['count', 'sum']
    }).reset_index()
    
    summary.columns = ['Habit', 'Total Days', 'Days Completed']
    summary['Completion Rate'] = (summary['Days Completed'] / summary['Total Days'] * 100).round(2)
    
    return summary

def create_weekly_pattern(habit_logs):
    if habit_logs.empty:
        return None
        
    habit_logs['weekday'] = pd.to_datetime(habit_logs['date']).dt.day_name()
    weekly_pattern = habit_logs.groupby('weekday')['completed'].mean().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )
    
    fig = px.bar(
        x=weekly_pattern.index,
        y=weekly_pattern.values,
        title='Weekly Completion Pattern',
        labels={'x': 'Day of Week', 'y': 'Completion Rate'}
    )
    return fig
