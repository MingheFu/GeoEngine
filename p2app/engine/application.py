from p2app.events import *
import sqlite3
from pathlib import Path

class ApplicationEvents:
    """The processing of application-level events from the engine"""
    def __init__(self):
        """Initializes the application events processing"""
        self.connect = None

    def process_application(self, event: object):
        """Handles the events that will be sent when receiving particular event call"""
        if isinstance(event, QuitInitiatedEvent):
            yield EndApplicationEvent()
        if isinstance(event, OpenDatabaseEvent):
            event_path = event.path()
            opened = self.connect_database(event_path)
            if isinstance(opened, bool):
                yield DatabaseOpenedEvent(event_path)
            else:
                yield DatabaseOpenFailedEvent(opened)
        if isinstance(event, CloseDatabaseEvent):
            if self.connect:
                self.connect.close()
                self.connect = None
            yield DatabaseClosedEvent()

    def connect_database(self, event_path: Path) ->bool|str:
        """Connects to SQL data"""
        try:
            self.connect = sqlite3.connect(event_path)
            cursor = self.connect.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            tables = ['continent', 'country', 'region']
            for table in tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                               (table,))
                if not cursor.fetchone():
                    self.connect.close()
                    self.connect = None
                    return 'Failed to open the database: Invalid database'
            return True
        except sqlite3.Error as e:
            return f'Database error: {e}'
