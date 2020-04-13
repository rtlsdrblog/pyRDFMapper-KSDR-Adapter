import os
import requests
import polling
import time
import calendar
import math
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

R = 6372.795477598

load_dotenv(verbose=True)

doa_server_addr = os.getenv('DOA_SERVER_ADDR')
rdf_server_addr = os.getenv('RDF_SERVER_ADDR')
station_id = os.getenv('STATION_ID')
station_latitude = float(os.getenv('STATION_LATITUDE'))
station_longitude = float(os.getenv('STATION_LONGITUDE'))
polling_interval = int(os.getenv('POLLING_INTERVAL'))
line_length = float(os.getenv('LINE_LENGTH'))
ksdr_bearing = float(os.getenv('KSDR_BEARING'))


def do_process():
    try:
        response = requests.get(doa_server_addr)
        response.raise_for_status()

        print('Received data...', response.text)

        doa_value = 0.0
        conf_value = 0.0
        pwr_value = 0.0

        for child in ET.fromstring(response.text):
            if child.tag.lower() == 'doa':
                doa_value = float(child.text)
            if child.tag.lower() == 'conf':
                conf_value = int(child.text)
            if child.tag.lower() == 'pwr':
                pwr_value = float(child.text)

        # TODO: dummy calculation
        e_lat, e_lng = calculate(station_latitude, station_longitude, doa_value, ksdr_bearing)
        post_data = {
            'id':   station_id,
            'time': calendar.timegm(time.gmtime()),
            'doa':  doa_value,
            'conf': conf_value,
            'pwr':  pwr_value,
            'slat': station_latitude,
            'slng': station_longitude,
            'elat': e_lat,
            'elng': e_lng
        }
        response = requests.post(rdf_server_addr, data=post_data)
        response.raise_for_status()

        print('Sent data... ', post_data)

    except requests.exceptions.Timeout as err:
        print(err)
    except requests.exceptions.TooManyRedirects as err:
        print(err)
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.RequestException as err:
        print(err)
    except ET.ParseError as err:
        print(err)


def calculate(s_lat: float, s_lng: float, doa: float, my_bearing: float) -> (float, float):
    theta = math.radians(my_bearing + (360 - doa))
    s_lat_in_rad = math.radians(s_lat)
    s_lng_in_rad = math.radians(s_lng)
    e_lat = math.asin(math.sin(s_lat_in_rad) * math.cos(line_length / R) + math.cos(s_lat_in_rad) * math.sin(line_length / R) * math.cos(theta))
    e_lng = s_lng_in_rad + math.atan2(math.sin(theta) * math.sin(line_length / R) * math.cos(s_lat_in_rad), math.cos(line_length / R) - math.sin(s_lat_in_rad) * math.sin(e_lat))
    return round(math.degrees(e_lat), 6), round(math.degrees(e_lng), 6)


def main():
    polling.poll(lambda: do_process(), step=int(polling_interval), poll_forever=True)


if __name__ == '__main__':
    main()
