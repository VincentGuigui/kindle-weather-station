# Kindle Weather Stand Project

End-to-end guide for turning a **stock Kindle 4 / 5 Non-Touch into a standalone weather display.

## TL;DR

![Screenshot](demo.jpg)

## More about this project
This is largely inspired by [Kindle Weather Stand Project](https://github.com/x-magic/kindle-weather-stand-alone), which in turn is inspired by [Kindle Weather Stand Project](https://github.com/x-magic/kindle-weather-display). The difference is that this version runs on Kindle alone without need of a server. From version 3.0 this project is fully based on KUAL. You need to jailbreak your Kindle and install KUAL and Kindle Python to start weather stand. 

On a Kindle 4, the new method can continue to update weather up to 4 weeks on a single charge, when weather data is updated every hour. Unfortunately even after I reduce the wakeup rate to 4 times a day, it still lasts around 4 weeks. Not sure if there's a better way to prolong the battery life. For more information, please refer to inline comments. If you want to stress-test your Kindle's battery and find out how long it's probably gonna last, check out [this](https://github.com/x-magic/kindle-test-loop) repository. 

__Please notice that__ this project has been tested only on __Kindle 4 Silver Non-touch__ and __Kindle 5 Black Non-touch__ without issues, but probably won't work on other models (due to difference in system software - this project is heavily dependent on disabling OS services to gain battery life). You are more than welcome to fork and adapt to other models. 


## Configure and Install Kindle Weather Stand

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
