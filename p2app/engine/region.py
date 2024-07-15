from p2app.events import *
import sqlite3

class RegionsEvents:
    """The processing of region-related events by the engine"""
    def __init__(self, connection):
        """Initializes the processor"""
        self.connect = connection

    def process_regions_event(self, event):
        """Handles the events that will be sent in the region view
        when receiving particular event call"""
        if isinstance(event, StartRegionSearchEvent):
            regions_get = self.search_regions(event.region_code(), event.local_code(), event.name())
            if isinstance(regions_get, list):
                for region in regions_get:
                    region_obj = Region(*region)
                    yield RegionSearchResultEvent(region_obj)
            else:
                yield ErrorEvent(regions_get)
        elif isinstance(event, LoadRegionEvent):
            region_loaded = self.load_region(event.region_id())
            if isinstance(region_loaded, tuple):
                region_load_obj = Region(*region_loaded)
                yield RegionLoadedEvent(region_load_obj)
            else:
                yield ErrorEvent(region_loaded)
        elif isinstance(event, SaveNewRegionEvent):
            region_added = self.save_new_region(event.region().region_code, event.region().local_code,
                                                event.region().name, event.region().continent_id,
                                                event.region().country_id, event.region().wikipedia_link,
                                                event.region().keywords)
            if isinstance(region_added, tuple):
                region_added_obj = Region(*region_added)
                yield RegionSavedEvent(region_added_obj)
            else:
                yield SaveRegionFailedEvent(region_added)
        elif isinstance(event, SaveRegionEvent):
            loaded_region = self.load_region(event.region().region_id)
            loaded_region_obj = Region(*loaded_region)
            region_edit = self.edit_region(loaded_region_obj.region_code, event.region().region_code,
                                           event.region().local_code,event.region().name,
                                           event.region().continent_id,event.region().country_id,
                                           event.region().wikipedia_link,event.region().keywords)
            if isinstance(region_edit, tuple):
                region_edit_obj = Region(*region_edit)
                yield RegionSavedEvent(region_edit_obj)
            else:
                yield SaveRegionFailedEvent(region_edit)

    def search_regions(self, region_code: str, local_code: str, name: str) ->list|str:
        """Queries the SQLite database for regions based on code, local code, and name"""
        cursor = self.connect.cursor()
        # cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            data_searched = []
            columns = []
            data_combination = {
                'region_code': region_code,
                'local_code': local_code,
                'name': name
            }
            for column, data in data_combination.items():
                if data is not None:
                    data_searched.append(data)
                    columns.append(f'{column} = ?')
            query = """
            SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, 
            keywords 
            FROM region 
            WHERE {}
            """.format(" AND ".join(columns))
            cursor.execute(query, tuple(data_searched))
            result = cursor.fetchall()
            if not result:
                return 'No result matches'
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def load_region(self, region_id: int) ->tuple|str:
        try:
            cursor = self.connect.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            query = """
            SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, 
            keywords
            FROM region
            WHERE region_id = ?
            """
            cursor.execute(query, (region_id, ))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def save_new_region(self, region_code: str, local_code: str, name: str, continent_id: int,
                        country_id: int, wikipedia_link: str, keywords: str) ->tuple|str:
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if not (region_code[:2].isupper() and region_code[2] == "-"):
                return 'Failed to save the new region information: Invalid region code'
            if  region_code[3:] != local_code:
                return ('Failed to save the new region information: Invalid local code(should match'
                        ' the second part of the region code')
            query  = """
            INSERT INTO region (region_code, local_code, name, continent_id, 
            country_id, wikipedia_link, keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (region_code, local_code, name, continent_id, country_id,
                                   wikipedia_link, keywords))
            self.connect.commit()
            new_id = cursor.lastrowid
            select_new = """
            SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, 
            keywords
            FROM region
            WHERE region_id = ?
            """
            cursor.execute(select_new, (new_id, ))
            result = cursor.fetchone()
            return result
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def edit_region(self, region_code, new_region_code, new_local_code, new_name, new_continent_id,
                   new_country_id, new_wikipedia_link, new_keywords) ->tuple|str:
        cursor = self.connect.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            if new_region_code:
                if not (new_region_code[:2].isupper() and new_region_code[2] == "-"):
                    return 'Failed to update the region information: Invalid region code'
            if new_local_code:
                if new_local_code != new_region_code[3:]:
                    return ('Failed to update the local code: Invalid local code(should match the second'
                            'part of the region code')
            data_changed = []
            columns = []
            changed_pair = {
                'region_code': new_region_code,
                'local_code': new_local_code,
                'name': new_name,
                'continent_id': new_continent_id,
                'country_id': new_country_id,
                'wikipedia_link': new_wikipedia_link,
                'keywords': new_keywords
            }
            for column, data in changed_pair.items():
                if data is not None:
                    columns.append(f'{column} = ?')
                    data_changed.append(data)
            data_changed.append(region_code)
            query = """
            UPDATE region
            SET {}
            WHERE region_code = ?  
            """.format(",".join(columns))
            cursor.execute(query, tuple(data_changed))
            self.connect.commit()
            select_new_query = """
            SELECT region_id, region_code, local_code, name, continent_id, country_id, wikipedia_link, 
            keywords 
            FROM region
            where region_code = ?
            """
            cursor.execute(select_new_query, (new_region_code or region_code,))
            change = cursor.fetchone()
            return change
        except  sqlite3.Error as e:
            return f'Database error: {e}'
