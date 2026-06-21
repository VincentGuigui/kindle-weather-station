# Installation and configuration of Kindle Weather Stand Project

- If not already done, make sure KAUL and Kindle Python are installed and fully functional, see Prerequisites in [../INSTALL.md](../INSTALL.md)

## 1. Choose your weather source

Set the `provider` key in `weather.conf` (step 3) to one of:

- **`openweathermap`** (default) — worldwide coverage, ~5-day forecast. Requires a free API key.
- **`meteofrance`** — Météo-France's AROME/ARPEGE models via [Open-Meteo](https://open-meteo.com/en/docs/meteofrance-api).
  No API key, no `pytz`; best accuracy for France and neighbouring countries; forecast limited to 4 days.

### If you picked `openweathermap`: get a free API key

1. Sign up at <https://openweathermap.org/api> (free tier is enough but a bit limited in daily forecast)
2. Validate your email address. If not the API Key will not be enabled
3. Copy your **API key** (`APPID`) into `api_key`.
4. Note your location — easiest is city ID or lat/lon. The script uses the still-free
   `/data/2.5/weather` and `/data/2.5/forecast` endpoints.

### If you picked `meteofrance`

Nothing to sign up for — it needs no API key and no `pytz`. Just set your **latitude/longitude**
in `location` (the `q=` city-name and `id=` forms are OpenWeatherMap-only). Optionally set
`layout = landscape` for an 800×600 hourly temperature chart instead of the default portrait layout.

## 2. Out of charge Notifications (optional)
 If you want a notification when Kindle is out of charge, get a pair of user and app keys from [Pushover](https://pushover.net/)

## 3. Configuration

1. Edit `…\weather-stand\weather.conf` (plain key=value file at the extension root — no need
   to touch the Python):
   ```
   provider    = openweathermap             # or meteofrance
   layout      = portrait                   # meteofrance only: portrait or landscape
   api_key     = YOUR_OWM_API_KEY           # only used by openweathermap
   location    = lat=48.7853&lon=2.4136     # lat/lon required for meteofrance; or q=City,CC / id=XXXXXXX for openweathermap
   units       = metric                     # or imperial
   time_format = 24                         # or 12
   timezone    = Europe/Paris               # your tz
   ```
2. *(Optional)* Pushover low-battery alert: put your keys in
   `…\bin\weather-manager.sh` (`PO_TOKEN`, `PO_USER`).
3. *(Optional)* Refresh interval: edit `…\bin\start.sh` — the `REFRESH=3600` line is the
   sleep in seconds (3600 = hourly).
   
## 4. Install on Kindle
1. Copy kindle-weather-stand-alone/*extensions* folder in the kindle 
2. Open KAUL, you should see a new program called *Kindle Weather Stand Dependicies Checker*. Run it to check your Python installation. It will also install pytz library if not present (Internet connection required). *(pytz is only needed for the `openweathermap` source; `meteofrance` works without it.)*
3. __Important!__ Delete ``/extensions/weather-stand/bin/disable`` file
   - This file is a kill switch. The script won't carry on if it presents
4. (Optional) Run ``/extensions/weather-stand/bin/weather-manager.sh`` from a terminal (SSH?) to retrieve weather information. Make sure there's no error occurs

## 5. Run
Open KAUL → *Kindle Weather Stand Project* and pick a mode:
- **Normal (reboot to exit)** — production: stops the UI framework and deep-sleeps between
  updates for maximum battery life. The device is locked while it runs; reboot (hold power
  ~20 s) to get out.
- **Debug (press back to exit)** — leaves the UI running and does a single update so you can
  check the result and `/mnt/us/weather-debug.log` with the device still usable. Press Back
  to leave.


## Reverting to a normal Kindle
- Add an empty file named `disable` back into `weather-stand/bin/` and reboot → stops the
  weather loop.
  