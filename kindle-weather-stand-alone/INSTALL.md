# Installation and configuration of Kindle Weather Stand Project

- If not already done, make sure KAUL and Kindle Python are installed and fully functional, see Prerequisites in [../INSTALL.md](../INSTALL.md)

## 1. Get a free OpenWeatherMap API key

1. Sign up at <https://openweathermap.org/api> (free tier is enough but a bit limited in daily forecast)
2. Validate your email address. If not the API Key will not be enabled
3. Copy your **API key** (`APPID`).
4. Note your location — easiest is city ID or lat/lon. The script uses the still-free
   `/data/2.5/weather` and `/data/2.5/forecast` endpoints.

## 2. Out of charge Notifications (optional)
 If you want a notification when Kindle is out of charge, get a pair of user and app keys from [Pushover](https://pushover.net/)

## 3. Configuration

1. Edit `…\weather-stand\weather.conf` (plain key=value file at the extension root — no need
   to touch the Python):
   ```   
   api_key     = YOUR_OWM_API_KEY
   location    = lat=48.7853&lon=2.4136     # or q=City,CC or id=XXXXXXX
   units       = metric                     # or imperial
   time_format = 24                         # or 12
   timezone    = Europe/Paris               # your tz
   ```
2. *(Optional)* Pushover low-battery alert: put your keys in
   `…\bin\weather-manager.sh` (`PO_TOKEN`, `PO_USER`).
3. *(Optional)* Refresh interval: edit `…\bin\start.sh` — the `echo "+3600"` line is the
   sleep in seconds (3600 = hourly).
   
## 4. Install on Kindle
1. Copy kindle-weather-stand-alone/*extensions* folder in the kindle 
2. Open KAUL, you should see a new program called *Kindle Weather Stand Dependicies Checker*. Run it to check your Python installation. It will also install pytz library if not present (Internet connection required)
3. __Important!__ Delete ``/extensions/weather-stand/bin/disable`` file
   - This file is a kill switch. The script won't carry on if it presents
4. (Optional) Run ``/extensions/weather-stand/bin/weather-manager.sh`` from a terminal (SSH?) to retrieve weather information. Make sure there's no error occurs

## 5. Run
Finally, open KAUL and run *Kindle Weather Stand* program.


## Reverting to a normal Kindle
- Add an empty file named `disable` back into `weather-stand/bin/` and reboot → stops the
  weather loop.
  