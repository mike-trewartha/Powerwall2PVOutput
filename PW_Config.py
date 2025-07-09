#!/usr/bin/env python
import os

# Non-sensitive configuration values 
pvo_host = "pvoutput.org"
extData = True
log_file = "pvo.log" 

# Sensitive credentials loaded from environment variables
# Provide default empty strings or raise errors if not set, depending on desired behavior
pvo_key = os.getenv("PVO_API_KEY", "")
pvo_systemid = os.getenv("PVO_SYSTEM_ID", "")
PowerwallIP = os.getenv("POWERWALL_IP", "")
PowerwallEmail = os.getenv("POWERWALL_EMAIL", "")
PowerwallPassword = os.getenv("POWERWALL_PASSWORD", "")

# Optional: Add checks to ensure critical variables are set
if not pvo_key:
    raise ValueError("PVO_API_KEY environment variable not set.")
if not pvo_systemid:
    raise ValueError("PVO_SYSTEM_ID environment variable not set.")
if not PowerwallIP:
    raise ValueError("POWERWALL_IP environment variable not set.")
if not PowerwallEmail:
    raise ValueError("POWERWALL_EMAIL environment variable not set.")
if not PowerwallPassword:
    raise ValueError("POWERWALL_PASSWORD environment variable not set.")
