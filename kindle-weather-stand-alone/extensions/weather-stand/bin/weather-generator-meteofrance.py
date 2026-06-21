import codecs
import json
import os
import ssl
import urllib
import urllib2
from datetime import datetime


# Settings live in weather.conf at the extension root (one level above this bin/ folder),
# so you can edit your location without touching this script. The values assigned after
# _load_config() are fallbacks used only when a key is absent from weather.conf.
#
# Unlike the OpenWeatherMap generator this script needs no API key: Open-Meteo's
# Meteo-France model endpoint is free and key-less. It also returns timestamps already
# converted to the requested timezone, so the pytz dependency is no longer required.
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


# Location: prefer explicit latitude/longitude keys, but also accept the OpenWeatherMap
# style "location = lat=NN&lon=NN" so an existing weather.conf keeps working unchanged.
def _resolve_lat_lon(cfg):
    if cfg.get('latitude') and cfg.get('longitude'):
        return cfg['latitude'], cfg['longitude']
    parts = {}
    for token in cfg.get('location', '').replace('&', ' ').split():
        if '=' in token:
            k, _, v = token.partition('=')
            parts[k.strip()] = v.strip()
    return parts.get('lat', '48.85'), parts.get('lon', '2.35')


# Parameters (defaults; overridden by weather.conf when present)
latitude, longitude = _resolve_lat_lon(_cfg)
unit_suite = _cfg.get('units', 'metric')          # 'metric' or 'imperial'
time_unit = int(_cfg.get('time_format', '24'))    # 24 for 23:59, or 12 for 11:59PM
timezone_string = _cfg.get('timezone', 'Europe/Paris')  # any tz database name
script_version = '1.0-mf'


# ISO local-time parser ("2026-06-20T14:00" -> datetime). Open-Meteo returns local time
# (no offset suffix) when a timezone is requested, so a naive datetime is all we need.
def parse_iso(value):
    return datetime.strptime(value[:16], '%Y-%m-%dT%H:%M')


def parse_date(value):
    return datetime.strptime(value[:10], '%Y-%m-%d')


# Time formatter
def format_time(dt, output_format):
    if output_format == 'day':
        return dt.strftime('%A')
    elif output_format == 'hour':
        if time_unit == 12:
            return dt.strftime('%-I%p')
        else:
            return dt.strftime('%-H:%M')
    elif output_format == 'minute':
        if time_unit == 12:
            return dt.strftime('%I:%M%p')
        else:
            return dt.strftime('%-H:%M')
    return None


# WMO weather interpretation code -> icon id defined in weather-template.svg
icon_def = {
    0: 'fair', 1: 'fair', 2: 'partlycloudy', 3: 'overcast',
    45: 'fog', 48: 'fog',
    51: 'scartteredshowers', 53: 'shower', 55: 'shower',
    56: 'freezingrain', 57: 'freezingrain',
    61: 'rain', 63: 'rain', 65: 'heavyrain',
    66: 'freezingrain', 67: 'freezingrain',
    71: 'snow', 73: 'snow', 75: 'snow', 77: 'snow',
    80: 'scartteredshowers', 81: 'shower', 82: 'heavyrain',
    85: 'snow', 86: 'snow',
    95: 'thunderstorms', 96: 'thunderstorms', 99: 'thunderstorms',
}

# WMO weather interpretation code -> human readable condition
weather_def = {
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
}


def icon_for(code):
    # 'overcast' is the fallback for any code outside the table (Open-Meteo only emits the
    # mapped WMO codes, so this is defensive); the template has no "na" symbol. Out-of-window
    # days still show a blank icon via day_icon()'s own 'na' return.
    return icon_def.get(code, 'overcast')


def weather_for(code):
    return weather_def.get(code, 'N/A')


# Unit translation table. Open-Meteo lets us request the units directly so the values
# returned already match the label shown on the template.
unit_def = {
    'metric': {'temp': 'C', 'speed': 'm/s', 'api_temp': 'celsius', 'api_wind': 'ms'},
    'imperial': {'temp': 'F', 'speed': 'mph', 'api_temp': 'fahrenheit', 'api_wind': 'mph'},
}
weather_units = unit_def.get(unit_suite, unit_def['metric'])

# Get battery percentage
battery_capacity = open('/sys/devices/system/yoshi_battery/yoshi_battery0/battery_capacity', 'r')

# Get weather data from Open-Meteo (no key required). models=meteofrance_seamless selects the
# Meteo-France AROME/ARPEGE blend (not Open-Meteo's default best-match), which is capped at 4
# forecast days (today + 3).
api_url = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=' + latitude +
    '&longitude=' + longitude +
    '&timezone=' + urllib.quote(timezone_string) +
    '&models=meteofrance_seamless' +
    '&forecast_days=4' +
    '&temperature_unit=' + weather_units['api_temp'] +
    '&wind_speed_unit=' + weather_units['api_wind'] +
    '&current=temperature_2m,weather_code,wind_speed_10m,wind_direction_10m' +
    '&hourly=temperature_2m,weather_code,wind_speed_10m' +
    '&daily=weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_direction_10m_dominant'
)
# The Kindle's Python has no usable CA bundle (and its clock often drifts), so HTTPS
# certificate verification fails. The weather data is public and unauthenticated, so we
# disable verification rather than ship/maintain a CA store on the device.
_ssl_ctx = ssl._create_unverified_context()
weather_response = urllib2.urlopen(api_url, context=_ssl_ctx)
weather_query = json.loads(weather_response.read())
weather_response.close()

current = weather_query['current']
hourly = weather_query['hourly']
daily = weather_query['daily']

current_datetime = parse_iso(current['time'])
hourly_times = [parse_iso(t) for t in hourly['time']]
daily_dates = [parse_date(d) for d in daily['time']]
n_daily = len(daily_dates)

# Index of the first hourly slot at or after the current hour, so the strip starts "now".
current_hour = current_datetime.replace(minute=0, second=0, microsecond=0)
hourly_start = 0
for i, t in enumerate(hourly_times):
    if t >= current_hour:
        hourly_start = i
        break


def hourly_index(offset):
    idx = hourly_start + offset
    return idx if 0 <= idx < len(hourly_times) else None


def hourly_time(offset):
    idx = hourly_index(offset)
    return format_time(hourly_times[idx], 'hour') if idx is not None else 'N/A'


def hourly_temp(offset):
    idx = hourly_index(offset)
    return int(round(hourly['temperature_2m'][idx])) if idx is not None else 0


def hourly_icon(offset):
    idx = hourly_index(offset)
    return icon_for(hourly['weather_code'][idx]) if idx is not None else 'na'


# Daily accessors keyed by calendar offset (0 = today, 1 = tomorrow, ...). Anything beyond
# the model's 4-day window falls back to N/A, exactly like the OpenWeatherMap generator.
def daily_value(day_index, key):
    return daily[key][day_index] if 0 <= day_index < n_daily else None


def day_label(day_index):
    return format_time(daily_dates[day_index], 'day') if 0 <= day_index < n_daily else 'N/A'


def day_high(day_index):
    v = daily_value(day_index, 'temperature_2m_max')
    return int(round(v)) if v is not None else 0


def day_low(day_index):
    v = daily_value(day_index, 'temperature_2m_min')
    return int(round(v)) if v is not None else 0


def day_icon(day_index):
    v = daily_value(day_index, 'weather_code')
    return icon_for(v) if v is not None else 'na'


def day_cond(day_index):
    v = daily_value(day_index, 'weather_code')
    return weather_for(v) if v is not None else 'N/A'


def day_bearing(day_index):
    v = daily_value(day_index, 'wind_direction_10m_dominant')
    return int(round(v)) if v is not None else 0


# Tomorrow's wind range is derived from the hourly data for that calendar day (the daily
# endpoint only exposes the maximum, not the minimum).
def day_wind_range(day_index):
    if not (0 <= day_index < n_daily):
        return None, None
    target = daily_dates[day_index].date()
    speeds = [hourly['wind_speed_10m'][i] for i, t in enumerate(hourly_times) if t.date() == target]
    return (min(speeds), max(speeds)) if speeds else (None, None)


def location_label():
    tz = weather_query.get('timezone', timezone_string)
    return tz.rsplit('/', 1)[-1].replace('_', ' ') if '/' in tz else latitude + ', ' + longitude


# Today's high/low come from the daily endpoint; fall back to the current reading if the
# daily array is somehow empty so the generator can never crash on a short response.
today_high = day_high(0) if n_daily else int(round(current['temperature_2m']))
today_low = day_low(0) if n_daily else today_high

tom_min, tom_max = day_wind_range(1)
if tom_min is not None:
    tom_wind = ' at ' + str(int(round(tom_min))) + weather_units['speed'] + ', up to ' + str(int(round(tom_max))) + weather_units['speed']
else:
    dmax = daily_value(1, 'wind_speed_10m_max')
    tom_wind = (' up to ' + str(int(round(dmax))) + weather_units['speed']) if dmax is not None else ''

weather_data = {
    'VAR_TEMP_UNIT': weather_units['temp'],
    'VAR_LOCATION': location_label(),
    'VAR_UPDATE_TIME': format_time(current_datetime, 'minute'),
    'VAR_NOW_ICON': icon_for(current['weather_code']),
    'VAR_NOW_TEMP': int(round(current['temperature_2m'])),
    'VAR_TODAY_HIGH': today_high,
    'VAR_TODAY_LOW': today_low,
    'VAR_HOURLY_1_ICON': hourly_icon(0),
    'VAR_HOURLY_1_TIME': hourly_time(0),
    'VAR_HOURLY_1_TEMP': hourly_temp(0),
    'VAR_HOURLY_2_ICON': hourly_icon(1),
    'VAR_HOURLY_2_TIME': hourly_time(1),
    'VAR_HOURLY_2_TEMP': hourly_temp(1),
    'VAR_HOURLY_3_ICON': hourly_icon(2),
    'VAR_HOURLY_3_TIME': hourly_time(2),
    'VAR_HOURLY_3_TEMP': hourly_temp(2),
    'VAR_HOURLY_4_ICON': hourly_icon(3),
    'VAR_HOURLY_4_TIME': hourly_time(3),
    'VAR_HOURLY_4_TEMP': hourly_temp(3),
    'VAR_HOURLY_5_ICON': hourly_icon(4),
    'VAR_HOURLY_5_TIME': hourly_time(4),
    'VAR_HOURLY_5_TEMP': hourly_temp(4),
    'VAR_DAILY_TOM_ICON': day_icon(1),
    'VAR_DAILY_TOM_DAY': day_label(1),
    'VAR_DAILY_TOM_HIGH': day_high(1),
    'VAR_DAILY_TOM_LOW': day_low(1),
    'VAR_DAILY_TOM_COND': day_cond(1),
    'VAR_DAILY_TOM_WIND_BEARING': day_bearing(1),
    'VAR_DAILY_TOM_WIND': tom_wind,
    'VAR_DAILY_1_ICON': day_icon(2),
    'VAR_DAILY_1_DAY': day_label(2),
    'VAR_DAILY_1_HIGH': day_high(2),
    'VAR_DAILY_1_LOW': day_low(2),
    'VAR_DAILY_2_ICON': day_icon(3),
    'VAR_DAILY_2_DAY': day_label(3),
    'VAR_DAILY_2_HIGH': day_high(3),
    'VAR_DAILY_2_LOW': day_low(3),
    'VAR_DAILY_3_ICON': day_icon(4),
    'VAR_DAILY_3_DAY': day_label(4),
    'VAR_DAILY_3_HIGH': day_high(4),
    'VAR_DAILY_3_LOW': day_low(4),
    'VAR_DAILY_4_ICON': day_icon(5),
    'VAR_DAILY_4_DAY': day_label(5),
    'VAR_DAILY_4_HIGH': day_high(5),
    'VAR_DAILY_4_LOW': day_low(5),
    'VAR_DAILY_5_ICON': day_icon(6),
    'VAR_DAILY_5_DAY': day_label(6),
    'VAR_DAILY_5_HIGH': day_high(6),
    'VAR_DAILY_5_LOW': day_low(6),
    'VAR_PROVIDER_STRING': 'Powered by Meteo-France via Open-Meteo',
    'VAR_BATTERY_CAPACITY': battery_capacity.read(),
    'VAR_VERSION': script_version,
}

# Generate SVG file from template. Replace the longest keys first so that a key which is a
# prefix of another (e.g. VAR_DAILY_TOM_WIND vs VAR_DAILY_TOM_WIND_BEARING) cannot corrupt it.
output = codecs.open('weather-template.svg', 'r', encoding='utf-8').read()
for key in sorted(weather_data.keys(), key=len, reverse=True):
    output = output.replace(key, str(weather_data[key]))

codecs.open('/tmp/weather-latest.svg', 'w', encoding='utf-8').write(output)
