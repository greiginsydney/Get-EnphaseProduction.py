# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# This script is part of our solar monitoring project. See:
# https://github.com/greiginsydney/Get-EnphaseProduction.py
# https://greiginsydney.com/get-enphaseproduction-py
# https://greiginsydney.com/category/prtg/


# from *WINDOWS* call as python ./Get-EnphaseProduction.py '{\"host\":\"<IP>\"}'
# e.g. Get-EnphaseProduction\python> &"C:\Program Files (x86)\PRTG Network Monitor\python\python" ./Get-EnphaseProduction.py '{\"host\":\"http://<IP>\"}'


import json
import re           # for the regex replacement (sub)
import requests     # for the web call to Enphase
import sys


if __name__ == "__main__":
    try:
        url = ''
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
            # Check for 'host' and 'params' keys in the passed JSON, with params taking precedence:
            # (We strip any http or https prefix, but there's no other validation)
            for i in ("host", "params"):
                if args.get(i):
                    url = re.sub("https?:", "", args[i]).strip().strip('/')
            result = {'prtg': {'text' : "This sensor queries %s" % url}}
        if len(url) == 0:
            result = {'prtg': {'text' : 'Unsufficient or bad arguments', 'error' : {'args' : sys.argv}}}
            print(json.dumps(result))
            sys.exit(1)
        try:
            response = None
            query = "http://" + url + "/production.json"
            response = requests.get(query, timeout=20)
            response.raise_for_status() #Throws a HTTPError if we didn't receive a 2xx response
            jsonResponse = json.loads(response.text)

            if jsonResponse:
                result['prtg'].update({'result': []})
                for direction in ('production', 'consumption'):
                    value=1
                    for title in ('wNow', 'whToday', 'whLastSevenDays'):
                        if 'production' in direction:
                            eim_data = ([x for x in jsonResponse[direction] if (x['type'] == 'eim') and (x['measurementType'] == 'production') ])
                        elif 'consumption' in direction:
                            eim_data = ([x for x in jsonResponse[direction] if (x['type'] == 'eim') and (x['measurementType'] == 'total-consumption') ])
                        else:
                            continue

                        if 'wNow' in title:
                            name='Current ' + direction
                            CustomUnit='kW'
                            chart=1
                        elif 'whToday' in title:
                            name="Today's " + direction
                            CustomUnit='kWh'
                            chart=0
                        elif 'whLastSevenDays' in title:
                            name="Last week's " + direction
                            CustomUnit='kWh'
                            chart=0
                        
                        value = eim_data[0][title]
                        if value < 0:
                            value = 0
                        else:
                            value = float(format(value / 1000, '.3f'))
                        
                        result['prtg']['result'].append(
                            {'Channel' : name,
                            'Value' : value,
                            'CustomUnit' : CustomUnit,
                            'Float' : 1,
                            'DecimalMode' : 3,
                            'ShowChart' : chart,
                            'ShowTable' : 1
                            })
                            
        except requests.exceptions.Timeout as e:
            result = {'prtg': {'text' : 'Remote host timeout error', 'error' : "%s" % str(e)}}
        except requests.exceptions.ConnectionError as e:
            result = {'prtg': {'text' : 'Remote host connection error', 'error' : "%s" % str(e)}}
        except requests.exceptions.HTTPError as e:
            result = {'prtg': {'text' : 'Remote host HTTP error', 'error' : "%s" % str(e)}}
        except requests.exceptions.TooManyRedirects as e:
            result = {'prtg': {'text' : 'Remote host Too Many Redirects error', 'error' : "%s" % str(e)}}
        except Exception as e:
            result = {'prtg': {'text' : 'Unhandled error', 'error' : "%s" % str(e)}}
            
    except Exception as e:
        result = {'prtg': {'text' : 'Python Script execution error', 'error' : "%s" % str(e)}}

    print('')
    print(json.dumps(result))

# References:
# ValueCustomUnits: C:\Program Files (x86)\PRTG Network Monitor\python\Lib\site-packages\prtg\sensor\CustomUnits.py
# https://thecomputerperson.wordpress.com/2016/08/03/enphase-envoy-s-data-scraping/
