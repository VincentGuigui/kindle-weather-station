import codecs
import json
import os
import urllib2
from datetime import datetime

import pytz


# Settings live in weather.conf at the extension root (one level above this bin/ folder),
# so you can edit your API key / location without touching this script. The values assigned
# after _load_config() are fallbacks used only when a key is absent from weather.conf.
def _load_config():
    cfg = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'weather.conf')
    try:
        handle = open(path, 'r')
    except IOError:
        return cfg
    for line in handle:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        cfg[key.strip()] = value.strip()
    handle.close()
    return cfg


_cfg = _load_config()

# Parameters (defaults; overridden by weather.conf when present)
weather_key = _cfg.get('api_key', '')  # OpenWeatherMap API key
location_string = _cfg.get('location', '')  # 'lat=..&lon=..' or 'q=City,CC' or 'id=CityID' or 'zip=..,cc'
# You can search for location with following ways:
# - By city name: city name and country code divided by comma, use ISO 3166 country codes. e.g. 'q=London,uk'
# - By city id: simply lookup your desired city in https://openweathermap.org/ and the city id will show up in URL field. e.g. 'id=2172797'
# - By geographic coordinates: by latitude and longitude. e.g. 'lat=35&lon=139'
# - By ZIP code: by zip/post code (if country is not specified, will search the USA). e.g. 'zip=94040,us'
unit_suite = _cfg.get('units', 'metric')  # Unit of measurements, can be 'metric' or 'imperial'
time_unit = int(_cfg.get('time_format', '24'))  # 24 for 23:59, or 12 for 11:59PM
timezone_string = _cfg.get('timezone', 'Europe/Paris')  # tz, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
script_version = '3.0'


# Timezone processor
def utc_to_timezone(epoch):
    utc = datetime.fromtimestamp(epoch, pytz.utc)
    return utc.astimezone(pytz.timezone(timezone_string))


# Time formatter
def format_time(dt, output_format):
    if output_format is 'day':
        return dt.strftime('%A')
    elif output_format is 'hour':
        if time_unit is 12:
            return dt.strftime('%-I%p')
        else:
            return dt.strftime('%-H:%M')
    elif output_format is 'minute':
        if time_unit is 12:
            return dt.strftime('%I:%M%p')
        else:
            return dt.strftime('%-H:%M')
    return None


def hourly_to_daily(forecasts, now):
    daily = {}
    for day in forecasts:
        current_date = utc_to_timezone(day['dt'])
        # Offset in whole calendar days from "now" (month-boundary safe; 0 = today, 1 = tomorrow, ...)
        delta = (current_date.date() - now.date()).days

        try:
            daily[delta]
        except KeyError:
            daily[delta] = {
                'day': None,
                'temp_high': -99,
                'temp_low': 99,
                'weathers': {},
                'weather_id': 900,
                'weather': '',
                'weather_descriptions': [],
                'icon': None,
                'wind_bearing': 0,
                'wind_bearing_count': 0,
                'wind_max': 0,
                'wind_min': 255
            }

        daily[delta]['day'] = format_time(current_date, 'day')

        if day['main']['temp_max'] > daily[delta]['temp_high']:
            daily[delta]['temp_high'] = day['main']['temp_max']

        if day['main']['temp_min'] < daily[delta]['temp_low']:
            daily[delta]['temp_low'] = day['main']['temp_min']

        for weather in day['weather']:
            daily[delta]['weathers'][weather['id']] = weather

        daily[delta]['wind_bearing'] = daily[delta]['wind_bearing'] + day['wind']['deg']
        daily[delta]['wind_bearing_count'] = daily[delta]['wind_bearing_count'] + 1

        if day['wind']['speed'] > daily[delta]['wind_max']:
            daily[delta]['wind_max'] = day['wind']['speed']

        if day['wind']['speed'] < daily[delta]['wind_min']:
            daily[delta]['wind_min'] = day['wind']['speed']

    # Calculate Wind bearing and daily weather/icon
    for delta, day in daily.items():
        daily[delta]['wind_bearing'] = day['wind_bearing'] / day['wind_bearing_count']
        for weather_id, weather_info in day['weathers'].items():
            daily[delta]['weather_descriptions'].append(weather_info['description'])
            if daily[delta]['weather_id'] > weather_info['id']:
                daily[delta]['weather_id'] = weather_info['id']
                daily[delta]['icon'] = weather_info['icon']
        daily[delta]['weather'] = ', '.join(day['weather_descriptions']).capitalize()

    return daily


# Weather icon translation table
icon_def = {
    '01d': 'fair',
    '01n': 'fair',
    '02d': 'partlycloudy',
    '02n': 'partlycloudy',
    '03d': 'mostlycloudy',
    '03n': 'mostlycloudy',
    '04d': 'overcast',
    '04n': 'overcast',
    '09d': 'rain',
    '09n': 'rain',
    '10d': 'scartteredshowers',
    '10n': 'scartteredshowers',
    '11d': 'thunderstorms',
    '11n': 'thunderstorms',
    '13d': 'snow',
    '13n': 'snow',
    '50d': 'mist',
    '50n': 'mist',
}

# Unit translation table
unit_def = {
    'metric': {'temp': 'C', 'speed': 'm/s'},
    'imperial': {'temp': 'F', 'speed': 'mph'}
}

# Get battery percentage
battery_capacity = open('/sys/devices/system/yoshi_battery/yoshi_battery0/battery_capacity', 'r')

# Get weather data from API
weather_url = 'http://api.openweathermap.org/data/2.5/weather?APPID=' + weather_key + '&units=' + unit_suite + '&' + location_string
weather_response = urllib2.urlopen(weather_url)
weather_query = json.loads(weather_response.read())
weather_response.close()

forecast_url = 'http://api.openweathermap.org/data/2.5/forecast?APPID=' + weather_key + '&units=' + unit_suite + '&' + location_string
forecast_response = urllib2.urlopen(forecast_url)
forecast_query = json.loads(forecast_response.read())
forecast_response.close()

current_datetime = utc_to_timezone(weather_query['dt'])
forecast_daily = hourly_to_daily(forecast_query['list'], current_datetime)
forecast_hourly = forecast_query['list']

weather_units = unit_def[unit_suite]

# The 3-hour forecast may not include any slots left for "today" (e.g. in the
# evening), so today's high/low come from the current-weather endpoint instead.
# Upcoming days are taken in order from tomorrow onward, with N/A fallbacks so a
# short forecast window can never crash the generator.
today_main = weather_query['main']
today_high = int(round(today_main.get('temp_max', today_main['temp'])))
today_low = int(round(today_main.get('temp_min', today_main['temp'])))

future_deltas = sorted(d for d in forecast_daily if d >= 1)


def future_day(idx):
    # idx 0 = tomorrow, 1 = day after, ... ; returns the day dict or None
    if 0 <= idx < len(future_deltas):
        return forecast_daily[future_deltas[idx]]
    return None


def day_icon(day):
    return icon_def.get(day['icon'], 'na') if day else 'na'


def day_label(day):
    return day['day'] if day else 'N/A'


def day_high(day):
    return int(round(day['temp_high'])) if day else 0


def day_low(day):
    return int(round(day['temp_low'])) if day else 0


def hourly_icon(slot):
    return icon_def.get(slot['weather'][-1]['icon'], 'na')


tom = future_day(0)
fd1 = future_day(1)
fd2 = future_day(2)
fd3 = future_day(3)

if tom:
    tom_cond = tom['weather']
    tom_wind_bearing = tom['wind_bearing']
    tom_wind = ' at ' + str(int(round(tom['wind_min']))) + weather_units['speed'] + ", up to " + str(int(round(tom['wind_max']))) + weather_units['speed']
else:
    tom_cond = 'N/A'
    tom_wind_bearing = 0
    tom_wind = ''

weather_data = {
    'VAR_TEMP_UNIT': weather_units['temp'],
    'VAR_LOCATION': weather_query['name'] + ', ' + weather_query['sys']['country'],
    'VAR_UPDATE_TIME': format_time(current_datetime, 'minute'),
    'VAR_NOW_ICON': icon_def.get(weather_query['weather'][0]['icon'], 'na'),
    'VAR_NOW_TEMP': int(round(weather_query['main']['temp'])),
    'VAR_TODAY_HIGH': today_high,
    'VAR_TODAY_LOW': today_low,
    'VAR_HOURLY_1_ICON': hourly_icon(forecast_hourly[0]),
    'VAR_HOURLY_1_TIME': format_time(utc_to_timezone(forecast_hourly[0]['dt']), 'hour'),
    'VAR_HOURLY_1_TEMP': int(round(forecast_hourly[0]['main']['temp'])),
    'VAR_HOURLY_2_ICON': hourly_icon(forecast_hourly[1]),
    'VAR_HOURLY_2_TIME': format_time(utc_to_timezone(forecast_hourly[1]['dt']), 'hour'),
    'VAR_HOURLY_2_TEMP': int(round(forecast_hourly[1]['main']['temp'])),
    'VAR_HOURLY_3_ICON': hourly_icon(forecast_hourly[2]),
    'VAR_HOURLY_3_TIME': format_time(utc_to_timezone(forecast_hourly[2]['dt']), 'hour'),
    'VAR_HOURLY_3_TEMP': int(round(forecast_hourly[2]['main']['temp'])),
    'VAR_HOURLY_4_ICON': hourly_icon(forecast_hourly[3]),
    'VAR_HOURLY_4_TIME': format_time(utc_to_timezone(forecast_hourly[3]['dt']), 'hour'),
    'VAR_HOURLY_4_TEMP': int(round(forecast_hourly[3]['main']['temp'])),
    'VAR_HOURLY_5_ICON': hourly_icon(forecast_hourly[4]),
    'VAR_HOURLY_5_TIME': format_time(utc_to_timezone(forecast_hourly[4]['dt']), 'hour'),
    'VAR_HOURLY_5_TEMP': int(round(forecast_hourly[4]['main']['temp'])),
    'VAR_DAILY_TOM_ICON': day_icon(tom),
    'VAR_DAILY_TOM_DAY': day_label(tom),
    'VAR_DAILY_TOM_HIGH': day_high(tom),
    'VAR_DAILY_TOM_LOW': day_low(tom),
    'VAR_DAILY_TOM_COND': tom_cond,
    'VAR_DAILY_TOM_WIND_BEARING': tom_wind_bearing,
    'VAR_DAILY_TOM_WIND': tom_wind,
    'VAR_DAILY_1_ICON': day_icon(fd1),
    'VAR_DAILY_1_DAY': day_label(fd1),
    'VAR_DAILY_1_HIGH': day_high(fd1),
    'VAR_DAILY_1_LOW': day_low(fd1),
    'VAR_DAILY_2_ICON': day_icon(fd2),
    'VAR_DAILY_2_DAY': day_label(fd2),
    'VAR_DAILY_2_HIGH': day_high(fd2),
    'VAR_DAILY_2_LOW': day_low(fd2),
    'VAR_DAILY_3_ICON': day_icon(fd3),
    'VAR_DAILY_3_DAY': day_label(fd3),
    'VAR_DAILY_3_HIGH': day_high(fd3),
    'VAR_DAILY_3_LOW': day_low(fd3),
    'VAR_DAILY_4_ICON': 'na',
    'VAR_DAILY_4_DAY': 'N/A',
    'VAR_DAILY_4_HIGH': 0,
    'VAR_DAILY_4_LOW': 0,
    'VAR_DAILY_5_ICON': 'na',
    'VAR_DAILY_5_DAY': 'N/A',
    'VAR_DAILY_5_HIGH': 0,
    'VAR_DAILY_5_LOW': 0,
    'VAR_PROVIDER_STRING': 'Powered by OpenWeatherMap',
    'VAR_BATTERY_CAPACITY': battery_capacity.read(),
    'VAR_VERSION': script_version
}

# Generate SVG file from template
output = codecs.open('weather-template.svg', 'r', encoding='utf-8').read()
for (key, value) in weather_data.items():
    output = output.replace(key, str(value))

codecs.open('/tmp/weather-latest.svg', 'w', encoding='utf-8').write(output)
