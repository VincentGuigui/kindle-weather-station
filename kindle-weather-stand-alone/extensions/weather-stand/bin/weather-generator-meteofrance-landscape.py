import codecs
import json
import os
import urllib
import urllib2
from datetime import datetime

try:
    string_types = (str, unicode)  # Python 2: keep unicode values (e.g. the icon <defs>) unicode
except NameError:
    string_types = (str,)          # Python 3


# Landscape (800x600) generator for the Open-Meteo Meteo-France model. It shares the data
# fetching/parsing of weather-generator-meteofrance.py but draws an hourly temperature chart
# instead of the portrait strip: a curve over the next 12 hours, with the matching weather
# icon aligned above each time slot and the window's min/max marked.
#
# Like the portrait generator it needs no API key and no pytz (Open-Meteo returns local time).
# The weather icons are not duplicated here: their <defs> are read from weather-template.svg
# at run time and injected, so both layouts share a single icon source.
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
unit_suite = _cfg.get('units', 'metric')
time_unit = int(_cfg.get('time_format', '24'))
timezone_string = _cfg.get('timezone', 'Europe/Paris')
script_version = '1.0-mf-landscape'

ICON_SOURCE = 'weather-template.svg'              # icons (<defs>) are read from here
LAYOUT_TEMPLATE = 'weather-template-landscape.svg'

# Hourly chart geometry (must match the placeholders/axes in the landscape template)
HOURS = 12
X0, X1 = 70.0, 770.0           # left / right edge of the plotted points
PLOT_TOP, PLOT_BOTTOM = 172.0, 415.0   # shorter plot -> more room for the daily strip below
ICON_Y = 104.0                 # top of the icon row, above the plot
ICON_SCALE = 0.40              # icon native art is ~100px wide -> ~40px
TIME_Y = 435.0                 # baseline of the time labels under the chart


def parse_iso(value):
    return datetime.strptime(value[:16], '%Y-%m-%dT%H:%M')


def parse_date(value):
    return datetime.strptime(value[:10], '%Y-%m-%d')


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
    # mapped WMO codes, so this is defensive) -- the template has no "na" symbol.
    return icon_def.get(code, 'overcast')


def weather_for(code):
    return weather_def.get(code, 'N/A')


unit_def = {
    'metric': {'temp': 'C', 'api_temp': 'celsius'},
    'imperial': {'temp': 'F', 'api_temp': 'fahrenheit'},
}
weather_units = unit_def.get(unit_suite, unit_def['metric'])

# Get battery percentage
battery_capacity = open('/sys/devices/system/yoshi_battery/yoshi_battery0/battery_capacity', 'r')

# Get weather data from Open-Meteo (no key required). models=meteofrance_seamless selects
# the Meteo-France AROME/ARPEGE blend (rather than Open-Meteo's default best-match), which
# is capped at 4 forecast days.
api_url = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=' + latitude +
    '&longitude=' + longitude +
    '&timezone=' + urllib.quote(timezone_string) +
    '&models=meteofrance_seamless' +
    '&forecast_days=4' +
    '&temperature_unit=' + weather_units['api_temp'] +
    '&current=temperature_2m,weather_code' +
    '&hourly=temperature_2m,weather_code' +
    '&daily=weather_code,temperature_2m_max,temperature_2m_min'
)
weather_response = urllib2.urlopen(api_url)
weather_query = json.loads(weather_response.read())
weather_response.close()

current = weather_query['current']
hourly = weather_query['hourly']
daily = weather_query['daily']

current_datetime = parse_iso(current['time'])
hourly_times = [parse_iso(t) for t in hourly['time']]
daily_dates = [parse_date(d) for d in daily['time']]
n_daily = len(daily_dates)

current_hour = current_datetime.replace(minute=0, second=0, microsecond=0)
hourly_start = 0
for i, t in enumerate(hourly_times):
    if t >= current_hour:
        hourly_start = i
        break


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


def location_label():
    tz = weather_query.get('timezone', timezone_string)
    return tz.rsplit('/', 1)[-1].replace('_', ' ') if '/' in tz else latitude + ', ' + longitude


# ---- build the hourly chart overlay (all data-dependent SVG lives here) ----
chart_idx = [hourly_start + k for k in range(HOURS) if hourly_start + k < len(hourly_times)]
n = len(chart_idx)
spacing = (X1 - X0) / (n - 1) if n > 1 else 0.0
xs = [X0 + spacing * k for k in range(n)]
temps = [hourly['temperature_2m'][i] for i in chart_idx]
codes = [hourly['weather_code'][i] for i in chart_idx]
times = [format_time(hourly_times[i], 'hour') for i in chart_idx]

t_min = min(temps)
t_max = max(temps)
pad = max(1.0, (t_max - t_min) * 0.2)
lo = t_min - pad
hi = t_max + pad


def y_of(temp):
    return PLOT_BOTTOM - (temp - lo) / (hi - lo) * (PLOT_BOTTOM - PLOT_TOP)


ys = [y_of(t) for t in temps]
parts = []

# light area under the curve, for legibility on e-ink
if n > 1:
    area = ['%.1f,%.1f' % (xs[0], PLOT_BOTTOM)]
    area += ['%.1f,%.1f' % (xs[k], ys[k]) for k in range(n)]
    area += ['%.1f,%.1f' % (xs[-1], PLOT_BOTTOM)]
    parts.append('<polygon points="%s" fill="#e6e6e6" stroke="none"/>' % ' '.join(area))

# the temperature curve
if n > 1:
    line = ' '.join('%.1f,%.1f' % (xs[k], ys[k]) for k in range(n))
    parts.append('<polyline points="%s" fill="none" stroke="#000000" stroke-width="3"/>' % line)

# per-slot: dot, temperature value, time label, weather icon aligned above the slot
for k in range(n):
    parts.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#000000"/>' % (xs[k], ys[k]))
    parts.append('<text style="text-anchor:middle;" font-size="30px" x="%.1f" y="%.1f">'
                 '%d&#176;</text>' % (xs[k], ys[k] - 12.0, int(round(temps[k]))))
    parts.append('<text style="text-anchor:middle;" font-size="15px" x="%.1f" y="%.1f">%s</text>'
                 % (xs[k], TIME_Y, times[k]))
    icon_x = xs[k] - 50.0 * ICON_SCALE
    parts.append('<g transform="translate(%.1f,%.1f) scale(%.2f)"><use xlink:href="#%s"/></g>'
                 % (icon_x, ICON_Y, ICON_SCALE, icon_for(codes[k])))

chart_overlay = '\n\t'.join(parts)

# icons live in weather-template.svg; lift its <defs> block verbatim
icon_src = codecs.open(ICON_SOURCE, 'r', encoding='utf-8').read()
_start = icon_src.find('<defs>')
_end = icon_src.find('</defs>')
icon_defs = icon_src[_start:_end + len('</defs>')] if _start != -1 and _end != -1 else ''

today_high = day_high(0) if n_daily else int(round(current['temperature_2m']))
today_low = day_low(0) if n_daily else today_high

weather_data = {
    'VAR_ICON_DEFS': icon_defs,
    'VAR_CHART_OVERLAY': chart_overlay,
    'VAR_TEMP_UNIT': weather_units['temp'],
    'VAR_LOCATION': location_label(),
    'VAR_UPDATE_TIME': format_time(current_datetime, 'minute'),
    'VAR_NOW_ICON': icon_for(current['weather_code']),
    'VAR_NOW_TEMP': int(round(current['temperature_2m'])),
    'VAR_TODAY_HIGH': today_high,
    'VAR_TODAY_LOW': today_low,
    'VAR_DAILY_TOM_ICON': day_icon(1),
    'VAR_DAILY_TOM_DAY': day_label(1),
    'VAR_DAILY_TOM_HIGH': day_high(1),
    'VAR_DAILY_TOM_LOW': day_low(1),
    'VAR_DAILY_1_ICON': day_icon(2),
    'VAR_DAILY_1_DAY': day_label(2),
    'VAR_DAILY_1_HIGH': day_high(2),
    'VAR_DAILY_1_LOW': day_low(2),
    'VAR_DAILY_2_ICON': day_icon(3),
    'VAR_DAILY_2_DAY': day_label(3),
    'VAR_DAILY_2_HIGH': day_high(3),
    'VAR_DAILY_2_LOW': day_low(3),
    'VAR_PROVIDER_STRING': 'Powered by Meteo-France via Open-Meteo',
    'VAR_BATTERY_CAPACITY': battery_capacity.read(),
    'VAR_VERSION': script_version,
}

# Generate the SVG. Replace the longest keys first so a key that is a prefix of another
# (e.g. VAR_NOW_TEMP vs VAR_TEMP_UNIT) cannot corrupt it.
output = codecs.open(LAYOUT_TEMPLATE, 'r', encoding='utf-8').read()
for key in sorted(weather_data.keys(), key=len, reverse=True):
    value = weather_data[key]
    # leave string values (notably the unicode icon <defs>) untouched; only coerce numbers,
    # so the template stays unicode end-to-end under Python 2.
    output = output.replace(key, value if isinstance(value, string_types) else str(value))

codecs.open('/tmp/weather-latest.svg', 'w', encoding='utf-8').write(output)
