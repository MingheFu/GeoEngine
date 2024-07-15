from p2app.events import *
import sqlite3

class ContinentsEvents:
    """The processing of continent-related events by the engine"""
    def __init__(self, connection):
        """Initializes the processor"""
        self.connect = connection

    def process_continents_events(self, event):
        """
        Handles the events that will be sent in the continent view
        when receiving particular event call
        """
        if isinstance(event, StartContinentSearchEvent):
            continents_get = self.search_continents(event.continent_code(), event.name())
            if isinstance(continents_get, list):
                for continent_data in continents_get:
                    continent_obj = Continent(*continent_data)
                    yield ContinentSearchResultEvent(continent_obj)
            else:
                yield ErrorEvent(continents_get)
        elif isinstance(event, LoadContinentEvent):
            continent_load = self.load_continents(event.continent_id())
            if isinstance(continent_load, tuple):
                continent_load_obj = Continent(*continent_load)
                yield ContinentLoadedEvent(continent_load_obj)
            else:
                yield ErrorEvent(continent_load)
        elif isinstance(event, SaveNewContinentEvent):
            continent_add = self.save_new_continent(event.continent().continent_code, event.continent().name)
            if isinstance(continent_add, tuple):
                 continent_add_obj = Continent(*continent_add)
                 yield ContinentSavedEvent(continent_add_obj)
            else:
                yield SaveContinentFailedEvent(continent_add)
        elif isinstance(event, SaveContinentEvent):
            loaded_continent = self.load_continents(event.continent().continent_id)
            loaded_continent_obj = Continent(*loaded_continent)
            continent_edit = self.edit_continent(loaded_continent_obj.continent_code,
                                                    loaded_continent_obj.name,
                                                    event.continent().continent_code,
                                                    event.continent().name)
            if  isinstance(continent_edit, tuple):
                continent_edit_obj = Continent(*continent_edit)
                yield ContinentSavedEvent(continent_edit_obj)
            else:
                yield SaveContinentFailedEvent(continent_edit)

    def search_continents(self, continent_code: str, name: str) -> list|str:
        """Queries the SQLite database for continents based on code and name"""
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            result = []
            if continent_code and name:
                query = """
            SELECT continent_id, continent_code, name FROM continent
            WHERE continent_code = ? AND name = ?
            """
                cursor.execute(query, (continent_code, name))
                result = cursor.fetchall()
            elif continent_code:
                query = """
            SELECT continent_id, continent_code, name FROM continent
            WHERE continent_code = ?
            """
                cursor.execute(query, (continent_code,))
                result = cursor.fetchall()
            elif name:
                query = """
                    SELECT continent_id, continent_code, name FROM continent
                    WHERE name = ?
                    """
                cursor.execute(query, (name,))
                result = cursor.fetchall()
            if not result:
                return 'No result matches'
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def load_continents(self, continent_id: int) ->tuple|str:
        """Queries the SQLite database for continents based on the id"""
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            query = """
            SELECT continent_id, continent_code, name FROM continent
            WHERE continent_id = ?
            """
            cursor.execute(query, (continent_id, ))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def save_new_continent(self, continent_code: str, name: str) ->tuple|str:
        """
        Add new continent into the database,
        return False if it does not follow convention or already exist
        """
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if not continent_code.isupper() or len(continent_code) != 2:
                return ('Failed to save the new continent information: Invalid continent code(should be two'
                        ' capital letters)')
            query = """
            INSERT INTO continent (continent_code, name)
            VALUES(?, ?)
            """
            cursor.execute(query, (continent_code, name))
            self.connect.commit()
            new_id = cursor.lastrowid
            select_query = """
            SELECT continent_id, continent_code, name FROM continent
            WHERE continent_id = ?
            """
            cursor.execute(select_query, (new_id,))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def edit_continent(self, continent_code: str, name: str, new_continent_code: str, new_name: str) ->tuple|str:
        """
        Update the current information of continent,
        return False if not follow convention
        """
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if new_continent_code and new_name:
                if not new_continent_code.isupper() or len(new_continent_code) != 2:
                    return ('Failed to save the new continent information: Invalid continent code(should be two'
                            ' capital letters)')
                query = """
                        UPDATE continent
                        SET continent_code = ?, name = ?
                        WHERE continent_code = ? AND name = ? 
                        """
                cursor.execute(query, (new_continent_code, new_name, continent_code, name))
            if new_continent_code:
                if not new_continent_code.isupper() or len(new_continent_code) != 2:
                    return ('Failed to save the new continent information: Invalid continent code(should be two'
                            ' capital letters)')
                query = """
                UPDATE continent
                SET continent_code = ?
                WHERE continent_code = ? AND name = ?
                """
                cursor.execute(query, (new_continent_code, continent_code, name))
            if new_name:
                query = """
                UPDATE continent
                SET name = ?
                WHERE continent_code = ? AND name = ?
                """
                cursor.execute(query, (new_name, continent_code, name))
            self.connect.commit()
            get_update = """
            SELECT continent_id, continent_code, name FROM continent
            WHERE continent_code = ? AND name = ?
            """
            cursor.execute(get_update, (new_continent_code or continent_code, new_name or name))
            change = cursor.fetchone()
            return change
        except sqlite3.Error as e:
            return f'Database error: {e}'
