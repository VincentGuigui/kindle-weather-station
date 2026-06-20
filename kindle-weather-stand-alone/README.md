# Kindle Weather Stand Project

## TL;DR

![Screenshot](https://raw.githubusercontent.com/x-magic/kindle-weather-stand-alone/master/demo.jpg)

## More about this project
This is largely inspired by [Kindle Weather Stand Project](https://github.com/x-magic/kindle-weather-stand-alone), which in turn is inspired by [Kindle Weather Stand Project](https://github.com/x-magic/kindle-weather-display). The difference is that this version runs on Kindle alone without need of a server. From version 3.0 this project is fully based on KUAL. You need to jailbreak your Kindle and install KUAL and Kindle Python to start weather stand. 

On a Kindle 4, the new method can continue to update weather up to 4 weeks on a single charge, when weather data is updated every hour. Unfortunately even after I reduce the wakeup rate to 4 times a day, it still lasts around 4 weeks. Not sure if there's a better way to prolong the battery life. For more information, please refer to inline comments. If you want to stress-test your Kindle's battery and find out how long it's probably gonna last, check out [this](https://github.com/x-magic/kindle-test-loop) repository. 

__Please notice that__ this project has been tested only on __Kindle 4 Silver Non-touch__ and __Kindle 5 Black Non-touch__ without issues, but probably won't work on other models (due to difference in system software - this project is heavily dependent on disabling OS services to gain battery life). You are more than welcome to fork and adapt to other models. 

## Key principles

## What do you need?

 - Some knowledge with Kindle jailbreak and Linux (Since Kindle is based on Linux)
 - A Kindle, of course (Kindle 4, silver or black should works the same, not tested on other model)
   - Kindle need to be [jailbroken](https://wiki.mobileread.com/wiki/Kindle4NTHacking) with [KUAL](https://www.mobileread.com/forums/showthread.php?t=203326) installed
   - Download [DevCerts 2025](https://www.mobileread.com/forums/showpost.php?p=4506164&postcount=1295)
   - You need to install [Kindle Python](https://www.mobileread.com/forums/showthread.php?t=88004) via [MR Package Installer](https://www.mobileread.com/forums/showthread.php?t=251143) or System Update
     - The Kindle Python package for Kindle 4 is `kindle-python-0.14.N-k4.zip` 
   - You need an extra Python library ([pytz](https://pypi.org/project/pytz/)) but it can be installed with a script within this project
 - A weather API key (free tier is more than enough for single device usage)
   - [OpenWeatherMap API](https://openweathermap.org/api) (a bit limited in daily forecast)
 - If you want a notification when Kindle is out of charge, get a pair of user and app keys from [Pushover](https://pushover.net/)
 - Almost forget... You're gonna need an Internet connection 

## Phase 1 : Turn your Kindle into a dev platform

 - Clone the project
 - Have a look at various scripts and replace API keys in several files
 - Put files on Kindle

## Phase 2 : Configure and Install Kindle Weather Stand
- Make sure KAUL and Kindle Python are installed and fully functional

1. Copy *extensions* folder into usbms (plug into a computer, or ``cd /mnt/us`` if you prefer SSH and SCP)
2. Open KAUL, you should see a new program called *Kindle Weather Stand Dependicies Checker*. Run it to check your Python installation. It will also install pytz library if not present (Internet connection required)
3. Update configurations and credentials
	1. (Optional) Open ``/extensions/weather-stand/bin/weather-manager.sh`` and replace Pushover credentials as instructed
	2. (Optional) Open ``/extensions/weather-stand/bin/weather-generator.sh`` and choose which weather API you want to use as instructed
	3. Configure your settings
		* for OpenWeatherMap, put your settings in a weather.conf file (use weather.example.conf as a template)
4. __Important!__ Delete ``/extensions/weather-stand/bin/disable`` file
   - This file is a kill switch. The script won't carry on if it presents
5. (Optional) Run ``/extensions/weather-stand/bin/weather-manager.sh`` from a terminal (SSH?) to retrieve weather information. Make sure there's no error occurs
   - You are more than welcome to report any issues or bugs [here](https://github.com/x-magic/kindle-weather-stand-alone/issues/new)
6. Finally, open KAUL and run *Kindle Weather Stand* program.

## Files explained

 - All executables and required parts are in *extensions* folder
   - *weather-stand* contains the weather stand program
     - *start.sh* contains the main loop, if you want to change refresh frequency, it's inside this file
     - *weather-manager.sh* is the main control file, update Pushover notification credentials here
     - *weather-generator.sh* is the loader of python script, you can choose which API to use here
     - *weather-generator-darksky.py* uses [Dark Sky API](https://darksky.net/dev) to load weather data
     - *weather-generator-openweathermap.py* uses [OpenWeatherMap API](https://openweathermap.org/api) to load weather data
   - *weather-stand-prerequisite* contains a program that checks python and required library installation
     - It will install the missing library ([pytz](https://pypi.org/project/pytz/)) if not present
 - *weather-icons.svg* contains all available weather icons for your reference (useful if you want to implement your own API)

## For those who helped
This project includes following components (in binary form) from [this link](http://www.mobileread.com/forums/showthread.php?t=200621) with some necessary modifications: 

 * pngcrush from fedora project repository [here](http://arm.koji.fedoraproject.org/koji/buildinfo?buildID=11465)
 * librsvg from [here](http://www.mobileread.com/forums/showpost.php?p=2743269&postcount=34)
 * SVG weather template and icons adapted from [here](https://mpetroff.net/2012/09/kindle-weather-display/)

These resources are mostly compiled binaries from open-source projects and included just for convenient distributions. If this cause any copyright infringement please contact me for removal. 

Code is released under MIT license and graphical components are released under CC0. Enjoy! 
