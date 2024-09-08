World Clock Comparison
==========================

A graphical application to compare the current time in different cities around the world.

Features
--------

*   Add and remove cities from the list
*   Automatically detect the timezone of each city
*   Display the current time in each city, including the timezone offset from UTC
*   Show the time difference between each city
*   Toggle between 12-hour and 24-hour time formats
*   Drag-and-drop to reorder the city list

Requirements
------------

*   Python 3.x
*   PyQt6
*   pytz
*   geopy
*   timezonefinder
*   suntime

Installation
------------

1.  Clone the repository: `git clone https://github.com/your-username/world-clock-comparison.git`
2.  Install the required packages: `pip install -r requirements.txt`
3.  Run the application: `python main.py`

Usage
-----

1.  Enter a city name in the input field and click "Add Location" to add it to the list.
2.  Use the "Remove Selected Location" button to remove a city from the list.
3.  Drag-and-drop to reorder the city list.
4.  Click the "12/24 Hr" button to toggle between 12-hour and 24-hour time formats.

Notes
-----

*   The application uses the Nominatim geocoding service to determine the latitude and longitude of each city.
*   The TimezoneFinder library is used to determine the timezone of each city based on its latitude and longitude.
*   The suntime library is used to calculate the sunrise and sunset times for each city.