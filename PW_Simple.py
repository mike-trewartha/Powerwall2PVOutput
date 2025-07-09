#!/usr/bin/env python
import time
import datetime
import PW_Helper as hlp
import PW_Config as cfg
import requests # Import requests here for specific exception handling

# Setup logging as defined in PW_Helper
hlp.setup_logging(cfg.log_file)
logger = hlp.logging.getLogger(__name__)
logger.info('Start PVOutput simple')

# Initialize session to None. It will be created on the first loop iteration
# or re-created if it becomes invalid.
ssn = None

while True:
    try:
        # Step 1: Ensure we have an active Powerwall session
        # If 'ssn' is None (first run or invalidated by an error), try to get a new one.
        if not ssn:
            logger.info("Attempting to get new Powerwall session...")
            ssn = hlp.getSession(cfg.PowerwallIP, cfg.PowerwallEmail, cfg.PowerwallPassword)
            logger.info("Successfully obtained Powerwall session.")

        # Step 2: Initialize lists to collect data over the 5-minute period
        lpvPower=[]
        lpvVoltage=[]
        lpvBatteryFlow=[]
        lpvLoadPower=[]
        lpvSitePower=[]
        lpvLoadVoltage=[]
        lpvSOC=[]
        i=0 # Counter for the 60 data points (60 * 5 seconds = 300 seconds = 5 minutes)

        # Step 3: Collect Powerwall data every 5 seconds for a minute (60 iterations)
        while i < 60:
            pw = hlp.getPowerwallData(cfg.PowerwallIP, ssn)
            soc = hlp.getPowerwallSOCData(cfg.PowerwallIP, ssn)

            # Check if data retrieval was successful (not False, which hlp functions return on error)
            if pw is not False and soc is not False:
                lpvPower.append(float(pw['solar']['instant_power']))
                lpvVoltage.append(float(pw['solar']['instant_average_voltage']))
                lpvBatteryFlow.append(float(pw['battery']['instant_power']))
                lpvLoadPower.append(float(pw['load']['instant_power']))
                lpvSitePower.append(float(pw['site']['instant_power']))
                lpvLoadVoltage.append(float(pw['load']['instant_average_voltage']))
                lpvSOC.append(float(soc['percentage']))
            else:
                # If data retrieval failed for any reason (e.g., 403 error caught in hlp.getPowerwallData),
                # log a warning, invalidate the session, and break this inner loop.
                # The outer loop's 'try-except' will then handle the broader error,
                # or if no broad error, the next outer loop iteration will attempt a new session.
                logger.warning('Failed to get Powerwall data for current iteration. Forcing session refresh and retrying loop.')
                ssn = None # Invalidate session to force re-authentication on the next outer loop iteration
                break # Break the inner loop to re-attempt session creation and then data collection

            i = i + 1
            time.sleep(5) # Wait for 5 seconds before the next data point collection

        # Step 4: Process and send data to PVOutput, but only if a full minute of data was collected
        if len(lpvPower) == 60: # Ensure we have collected 60 valid data points
            pvPower = hlp.avg(lpvPower)
            pvVoltage = hlp.avg(lpvVoltage)
            pvBatteryFlow = hlp.avg(lpvBatteryFlow)
            pvLoadPower = hlp.avg(lpvLoadPower)
            pvSitePower = hlp.avg(lpvSitePower)
            pvLoadVoltage = hlp.avg(lpvLoadVoltage)
            pvSOC = hlp.avg(lpvSOC)

            # Apply specific logic for pvPower
            if pvPower <= 30:
                pvPower = 0

            pvTemp = 0 # Placeholder if temperature isn't available
            pvConsumption = pvLoadPower # Assuming consumption is load power for PVOutput 'v4' (import)

            # Get current date and time for PVOutput upload
            pwdate = datetime.datetime.now()
            pvDate = pwdate.strftime("%Y%m%d")
            pvTime = pwdate.strftime("%H:%M")

            # Initialize PVOutput Connection
            pvoutz = hlp.Connection(cfg.pvo_key, cfg.pvo_systemid, cfg.pvo_host)

            # Send data to PVOutput based on extData configuration
            if cfg.extData == True:
                # Using extended data fields
                pvoutz.add_status(pvDate, pvTime, power_exp=pvPower, power_imp=pvConsumption,
                                  temp=pvTemp, vdc=pvVoltage, battery_flow=pvBatteryFlow,
                                  load_power=pvLoadPower, soc=pvSOC, site_power=pvSitePower,
                                  load_voltage=lpvLoadVoltage, ext_power_exp=pvPower)
                std_out = (f"Date: {pvDate} Time: {pvTime} Watts: {pvPower:.2f} "
                           f"Load Power: {pvLoadPower:.2f} SOC: {pvSOC:.2f} Site Power: {pvSitePower:.2f} "
                           f"Load Voltage: {pvLoadVoltage:.2f} Battery Flow: {pvBatteryFlow:.2f} "
                           f"Temp: {pvTemp} Solar Voltage: {pvVoltage:.2f}")
                logger.info(std_out)
            else:
                # Using basic data fields
                pvoutz.add_status(pvDate, pvTime, power_exp=pvPower, power_imp=pvConsumption,
                                  temp=pvTemp, vdc=pvVoltage)
                std_out = (f"Date: {pvDate} Time: {pvTime} Watts: {pvPower:.2f} "
                           f"Solar Voltage: {pvVoltage:.2f}")
                logger.info(std_out)
        else:
            logger.info('Skipping data send to PVOutput due to incomplete data collection (less than 60 points).')

    # Step 5: Comprehensive Error Handling for the main loop
    # Specific error for requests library (network issues, HTTP errors like 403)
    except requests.exceptions.RequestException as req_err:
        logger.error(f'Network/Request Error with Powerwall or PVOutput API: {req_err}. Forcing session refresh and sleeping 1 minute before retrying.')
        ssn = None # Invalidate session to force re-authentication
        time.sleep(60) # Short sleep to allow network/Powerwall to recover
    # Specific error for value errors, primarily intended to catch Powerwall login failures from getSession
    except ValueError as val_err:
        if 'failed to log in to the Powerwall' in str(val_err):
            logger.error(f'Powerwall Login Error: {val_err}. Check credentials. Retrying login in 5 minutes.')
            ssn = None # Ensure session is cleared
            time.sleep(60 * 5) # Longer sleep for credential issues
        else:
            logger.error(f'Unexpected ValueError: {val_err}. Sleeping 5 minutes.')
            ssn = None # Invalidate session just in case
            time.sleep(60 * 5)
    # Catch any other unexpected exceptions that might occur
    except Exception as e:
        logger.error(f'Unhandled Exception in Main loop: {e}. Sleeping 5 minutes.')
        ssn = None # Invalidate session as something went wrong
        time.sleep(60 * 5) # Long sleep for unhandled errors
