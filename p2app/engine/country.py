from p2app.events import *
import sqlite3

class CountriesEvents:
    """The processing of country-related events by the engine"""
    def __init__(self, connection):
        """Initializes the processor"""
        self.connect = connection

    def process_countries_events(self, event):
        """Handles the events that will be sent in the country view
        when receiving particular event call
        """
        if isinstance(event, StartCountrySearchEvent):
            countries_get = self.search_countries(event.country_code(), event.name())
            if isinstance(countries_get, list):
                for country_data in countries_get:
                    country_obj = Country(*country_data)
                    yield CountrySearchResultEvent(country_obj)
            else:
                yield ErrorEvent(countries_get)
        elif isinstance(event, LoadCountryEvent):
            country_load = self.load_countries(event.country_id())
            if isinstance(country_load, tuple):
                country_load_obj = Country(*country_load)
                yield CountryLoadedEvent(country_load_obj)
            else:
                yield ErrorEvent(country_load)
        elif isinstance(event, SaveNewCountryEvent):
            country_add = self.save_new_country(event.country().country_code, event.country().name,
                                                event.country().continent_id, event.country().wikipedia_link,
                                                event.country().keywords)
            if isinstance(country_add, tuple):
                country_add_obj = Country(*country_add)
                yield CountrySavedEvent(country_add_obj)
            else:
                yield SaveCountryFailedEvent(country_add)
        elif isinstance(event, SaveCountryEvent):
            loaded_country = self.load_countries(event.country().country_id)
            loaded_country_obj = Country(*loaded_country)
            country_edit = self.edit_country(loaded_country_obj.country_code, event.country().country_code,
                                             event.country().name, event.country().continent_id,
                                             event.country().wikipedia_link, event.country().keywords)
            if isinstance(country_edit, tuple):
                country_edit_obj = Country(*country_edit)
                yield CountrySavedEvent(country_edit_obj)
            else:
                yield SaveCountryFailedEvent(country_edit)

    def search_countries(self, country_code: str, name: str) ->list|str:
        """Queries the SQLite database for countries based on code and name"""
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            result = []
            if country_code and name:
                query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            WHERE country_code = ? AND name = ?
            """
                cursor.execute(query, (country_code, name))
                result = cursor.fetchall()
            elif country_code:
                query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            WHERE country_code = ?
            """
                cursor.execute(query, (country_code,))
                result = cursor.fetchall()
            elif name:
                query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            WHERE name = ?
                """
                cursor.execute(query, (name,))
                result = cursor.fetchall()
            if not result:
                return 'No result matches'
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def load_countries(self, country_id: int) ->tuple|str:
        """Queries the SQLite database for continents based on the id"""
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            WHERE country_id = ?
            """
            cursor.execute(query, (country_id, ))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def save_new_country(self, country_code: str, name: str, continent_id: int, wikipedia_link: str,
                         keywords: str) ->tuple|str:
        """
        Add new  country into the database,
        if it already exists or does not follow convention return False
        """
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if not country_code.isupper() or len(country_code) != 2:
                return ('Failed to save the new country information: Invalid country code'
                        '(should be two capital letters)')
            if wikipedia_link:
                if 'https://en.wikipedia.org/wiki/' not in wikipedia_link:
                    return 'Failed to save the new country information: Invalid web link'
            query = """
            INSERT INTO country (country_code, name, continent_id, wikipedia_link, keywords)
            VALUES(?, ?, ?, ?, ?)
            """
            cursor.execute(query, (country_code, name, continent_id, wikipedia_link, keywords))
            self.connect.commit()
            new_id = cursor.lastrowid
            select_query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            WHERE country_id = ?
            """
            cursor.execute(select_query, (new_id,))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def edit_country(self, country_code: str, new_country_code: str, new_name: str,
                     new_continent_id: int, new_wikipedia_link: str, new_keywords: str) ->tuple|str:
        """
        Update the current information of continent,
        return False if not follow convention
        """
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if new_country_code:
                if not new_country_code.isupper() or len(new_country_code) != 2:
                    return ('Failed to update country information: Invalid country code'
                        '(should be two capital letters)')
            if new_wikipedia_link:
                if 'https://en.wikipedia.org/wiki/' not in new_wikipedia_link:
                    return 'Failed to save the new country information: Invalid web link'
            data_changed = []
            columns = []
            changed_pair = {
                'country_code': new_country_code,
                'name': new_name,
                'continent_id': new_continent_id,
                'wikipedia_link': new_wikipedia_link,
                'keywords': new_keywords
            }
            for column, data in changed_pair.items():
                if data is not None:
                    columns.append(f'{column} = ?')
                    data_changed.append(data)
            data_changed.append(country_code)
            query = """
            UPDATE country 
            SET {}
            WHERE country_code = ?  
            """.format(",".join(columns))
            cursor.execute(query, tuple(data_changed))
            self.connect.commit()
            select_new_query = """
            SELECT country_id, country_code, name, continent_id, wikipedia_link, keywords FROM country
            where country_code = ?
            """
            cursor.execute(select_new_query, (new_country_code or country_code, ))
            change = cursor.fetchone()
            return change
        except sqlite3.Error as e:
            return f'Database error: {e}'
