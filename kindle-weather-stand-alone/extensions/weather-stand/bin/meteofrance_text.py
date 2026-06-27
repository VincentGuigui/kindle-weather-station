# -*- coding: utf-8 -*-
"""Shared WMO weather-code -> human text for the Meteo-France generators (portrait + landscape).

Externalised so both generators use a single wording source, in English and French. The active
language is chosen by the `language` key in weather.conf (en | fr). Works on the Kindle's
Python 2.7 and on Python 3 (the test harness); the strings are unicode so French accents render
correctly in the UTF-8 SVG.

To add a language, add another sub-dict below keyed by its code (e.g. 'de'), using the same WMO
code keys; unknown codes fall back to English, then to 'N/A'.
"""
from __future__ import unicode_literals

WEATHER_TEXT = {
    'en': {
        0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
        45: 'Fog', 48: 'Depositing rime fog',
        51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
        56: 'Light freezing drizzle', 57: 'Dense freezing drizzle',
        61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
        66: 'Light freezing rain', 67: 'Heavy freezing rain',
        71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow', 77: 'Snow grains',
        80: 'Slight rain showers', 81: 'Moderate rain showers', 82: 'Violent rain showers',
        85: 'Slight snow showers', 86: 'Heavy snow showers',
        95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with heavy hail',
    },
    'fr': {
        0: 'Ciel dégagé', 1: 'Plutôt dégagé', 2: 'Partiellement nuageux', 3: 'Couvert',
        45: 'Brouillard', 48: 'Brouillard givrant',
        51: 'Bruine légère', 53: 'Bruine modérée', 55: 'Bruine dense',
        56: 'Bruine verglaçante légère', 57: 'Bruine verglaçante dense',
        61: 'Pluie faible', 63: 'Pluie modérée', 65: 'Pluie forte',
        66: 'Pluie verglaçante faible', 67: 'Pluie verglaçante forte',
        71: 'Neige faible', 73: 'Neige modérée', 75: 'Neige forte', 77: 'Grains de neige',
        80: 'Averses faibles', 81: 'Averses modérées', 82: 'Averses violentes',
        85: 'Averses de neige faibles', 86: 'Averses de neige fortes',
        95: 'Orage', 96: 'Orage avec grêle', 99: 'Orage avec forte grêle',
    },
}

# Weekday names, indexed by datetime.weekday() (Monday = 0 ... Sunday = 6). strftime('%A')
# is always English on the Kindle (no French locale data installed), so translate ourselves.
WEEKDAY_TEXT = {
    'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'fr': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
}

DEFAULT_LANGUAGE = 'en'


def weather_text(code, lang=DEFAULT_LANGUAGE):
    """Human-readable text for a WMO code in `lang`, falling back to English then 'N/A'."""
    table = WEATHER_TEXT.get(lang, WEATHER_TEXT[DEFAULT_LANGUAGE])
    if code in table:
        return table[code]
    return WEATHER_TEXT[DEFAULT_LANGUAGE].get(code, 'N/A')


def weekday_name(weekday, lang=DEFAULT_LANGUAGE):
    """Day name for a datetime.weekday() index (Mon=0..Sun=6) in `lang`, English fallback."""
    names = WEEKDAY_TEXT.get(lang, WEEKDAY_TEXT[DEFAULT_LANGUAGE])
    return names[weekday]
