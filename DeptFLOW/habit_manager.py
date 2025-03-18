from database import HabitDatabase
from datetime import datetime, timedelta
import pandas as pd

class HabitManager:
    def __init__(self):
        self.db = HabitDatabase()

    def create_habit(self, name):
        return self.db.add_habit(name)

    def get_all_habits(self):
        return self.db.get_habits()

    def delete_habit(self, habit_id):
        self.db.delete_habit(habit_id)

    def log_habit_completion(self, habit_id, date, completed):
        self.db.log_habit(habit_id, date, completed)

    def get_habit_data(self, habit_id=None, days=30):
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return self.db.get_habit_logs(habit_id, start_date, end_date)

    def get_streaks(self, habit_id):
        return self.db.get_streak_data(habit_id)

    def export_data(self):
        return self.db.get_habit_logs()
