# p2app/engine/main.py
#
# ICS 33 Fall 2023
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.
#
# This is the outermost layer of the part of the program that you'll need to build,
# which means that YOU WILL DEFINITELY NEED TO MAKE CHANGES TO THIS FILE.

from .application import ApplicationEvents
from .continent import ContinentsEventsrt
from .country import CountriesEvents
from .region import RegionsEvents

class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self.app_engine = ApplicationEvents()
        self.app_events = ['QuitInitiatedEvent', 'OpenDatabaseEvent', 'CloseDatabaseEvent']
        self.continent_event = ['StartContinentSearchEvent', 'LoadContinentEvent', 'SaveNewContinentEvent',
                                'SaveContinentEvent']
        self.country_event = ['StartCountrySearchEvent', 'LoadCountryEvent', 'SaveNewCountryEvent',
                              'SaveCountryEvent']
        self.region_event = ['StartRegionSearchEvent', 'LoadRegionEvent', 'SaveNewRegionEvent',
                             'SaveRegionEvent']

    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""

        # This is a way to write a generator function that always yields zero values.
        # You'll want to remove this and replace it with your own code, once you start
        # writing your engine, but this at least allows the program to run.
        if event.__class__.__name__ in self.app_events:
            yield from self.app_engine.process_application(event)
        elif event.__class__.__name__ in self.continent_event:
            continent_engine = ContinentsEvents(self.app_engine.connect)
            yield from continent_engine.process_continents_events(event)
        elif event.__class__.__name__ in self.country_event:
            country_engine = CountriesEvents(self.app_engine.connect)
            yield from country_engine.process_countries_events(event)
        elif event.__class__.__name__ in self.region_event:
            region_engine = RegionsEvents(self.app_engine.connect)
            yield from region_engine.process_regions_event(event)
