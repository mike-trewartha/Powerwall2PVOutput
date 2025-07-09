#!/usr/bin/env python
import datetime
import time
import urllib.request, urllib.parse, urllib.error
import http.client
import requests
import os
import json
import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import handlers

logger = logging.getLogger(__name__)

# Powerwall uses a self signed cert
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def setup_logging(log_file):
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    format = logging.Formatter("%(asctime)s - %(message)s")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    fh = handlers.RotatingFileHandler(log_file, maxBytes=(1048576*5), backupCount=1)
    fh.setFormatter(format)
    log.addHandler(fh)

def avg(l):
    return sum(l,0.00)/len(l)

def getSession(PowerwallIP, PowerwallEmail, PowerwallPassword):
    auth_data = {
        "username":"customer",
        "password":PowerwallPassword,
        "email":PowerwallEmail,
        "force_sm_off":False
    }
    session = requests.Session()
    response = session.post('https://'+PowerwallIP+'/api/login/Basic', json=auth_data, verify=False)
    if response.status_code != 200:
        logger.error("getSession: " + str(response.status_code) + " - " + response.text)
        raise ValueError('getSession failed to log in to the Powerwall. check your email and password')
    return session

def getPowerwallData(PowerwallIP, session):
    try:
        response = session.get('https://'+PowerwallIP+'/api/meters/aggregates', verify=False)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e: # Catch requests-specific exceptions
        logger.error("Failed to retrieve Powerwall data: " + str(e))
        return False
    except Exception as e: # Catch any other unexpected exceptions
        logger.error("getPowerwallData: Unexpected error: " + str(e))
        return False

def getPowerwallSOCData(PowerwallIP, session):
    try:
        response = session.get('https://'+PowerwallIP+'/api/system_status/soe', verify=False)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e: # Catch requests-specific exceptions
        logger.error("Failed to retrieve Powerwall SOC data: " + str(e))
        return False
    except Exception as e: # Catch any other unexpected exceptions
        logger.error("getPowerwallSOCData: Unexpected error: " + str(e))
        return False

class Connection():
    def __init__(self, api_key, system_id, host):
        self.host = host
        self.api_key = api_key
        self.system_id = system_id

    def get_status(self, date=None, time=None):
        path = '/service/r2/getstatus.jsp'
        params = {}
        if date:
            params['d'] = date
        if time:
            params['t'] = time
        params = urllib.parse.urlencode(params)

        conn = http.client.HTTPConnection(self.host)
        headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'X-Pvoutput-Apikey': self.api_key,
                'X-Pvoutput-SystemId': self.system_id
                }
        conn.request("GET", path + "?" + params, None, headers)

        response = conn.getresponse()

        if response.status == 400:
            # Initialise a "No status found"
            return "%s,00:00,,,,,,," % datetime.datetime.now().strftime('%Y%m%d')
        if response.status != 200:
            raise Exception(f"Pvoutput get_status failed with status {response.status}: {response.read().decode()}")

        return response.read().decode()

    def add_status(self, date, time, energy_exp=None, power_exp=None, energy_imp=None, power_imp=None, temp=None, vdc=None, battery_flow=None, load_power=None, soc=None, site_power=None, load_voltage=None, ext_power_exp=None, cumulative=False):

        path = '/service/r2/addstatus.jsp'
        params = {
                'd': date,
                't': time
                }
        if energy_exp:
            params['v1'] = energy_exp
        if power_exp:
            params['v2'] = power_exp
        if energy_imp:
            params['v3'] = energy_imp
        if power_imp:
            params['v4'] = power_imp
        if temp:
            params['v5'] = temp
        if vdc:
            params['v6'] = vdc
        if battery_flow:
            params['v7'] = battery_flow
        if load_power:
            params['v8'] = load_power
        if soc:
            params['v9'] = soc
        if site_power:
            params['v10'] = site_power
        if load_voltage:
            params['v11'] = load_voltage
        if ext_power_exp:
            params['v12'] = ext_power_exp
        if cumulative:
            params['c1'] = 1
        encoded_params = urllib.parse.urlencode(params)
        logger.info("POSTING to PVOutput: " + str(encoded_params))

        conn = http.client.HTTPConnection(self.host)
        headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
                'X-Pvoutput-Apikey': self.api_key,
                'X-Pvoutput-SystemId': self.system_id
                }
        conn.request('POST', path, encoded_params, headers)

        response = conn.getresponse()

        if response.status == 400:
            error_message = response.read().decode()
            raise ValueError(f"Pvoutput add_status failed with status 400: {error_message}")
        if response.status != 200:
            error_message = response.read().decode()
            raise Exception(f"Pvoutput add_status failed with status {response.status}: {error_message}")
        else:
            logger.info(f"PVOutput update successful: {response.read().decode()}")
