# Tesla Powerwall 2 to PVOutput.org Uploader

## Project Overview

This project provides a Python application, designed to run within a Docker container, for automatically extracting energy data from a Tesla Powerwall 2 and uploading it to PVOutput.org.

---

## Features

* **Automated Data Collection:** Continuously polls the Tesla Powerwall 2 for real-time energy metrics, including solar generation, home consumption, grid import/export, and battery State of Charge.
* **5-Minute Averaging:** Aggregates collected data into 5-minute averages, suitable for PVOutput.org's status update interval.
* **PVOutput.org Integration:** Uploads processed energy data to a specified PVOutput.org system ID via its API.
* **Dockerized Deployment:** Packaged for easy deployment and management using Docker and Docker Compose, suitable for devices like a Raspberry Pi.
* **Credential Management:** Utilizes environment variables via a `.env` file for secure handling of sensitive API keys and login credentials.
* **Error Handling & Resilience:** Includes logic for handling Powerwall API communication failures, including session re-authentication, to maintain continuous operation.
* **Logging:** Implements detailed logging to a file and standard output for monitoring and debugging.

---

## Requirements

* Tesla Powerwall 2 (with local network access)
* PVOutput.org account (with a registered System ID and API Key)
* Host system with Docker and Docker Compose installed (e.g., Raspberry Pi OS)
* Python 3.9+ (as specified in `Dockerfile`)

---

## Setup and Installation

### 1. Project Files

Obtain the project files by cloning this repository:

```bash
git clone https://github.com/mike-trewartha/Powerwall2PVOutput.git
cd Powerwall2PVOutput
```

### 2. Environment Configuration (.env file)
To secure sensitive credentials, this project utilizes environment variables loaded from a .env file. Create a .env file in the root of your project directory:

```bash
touch .env
```
Populate .env with your specific credentials and Powerwall details:
```markdown
PVO_API_KEY=YOUR_PVOUTPUT_API_KEY
PVO_SYSTEM_ID=YOUR_PVOUTPUT_SYSTEM_ID
POWERWALL_IP=YOUR_POWERWALL_LOCAL_IP_ADDRESS
POWERWALL_EMAIL=YOUR_TESLA_ACCOUNT_EMAIL
POWERWALL_PASSWORD=YOUR_TESLA_ACCOUNT_PASSWORD
```
Warning: The `.env` file must not be committed to version control. It is explicitly ignored by `.gitignore`.

### 3. Configuration File (PW_Config.py)
Review and adjust non-sensitive configuration parameters in PW_Config.py as needed:
```python
pvo_host: # PVOutput API hostname (default: pvoutput.org)
extData:  # Boolean to enable/disable extended PVOutput data fields (v7-v12)
log_file: # Path for the application's log file within the container. If using a Docker volume for logs, ensure this path aligns with the volume mount (e.g., /app/logs/pvo.log).
```

### 4. Build and Run the Container
From your project's root directory, execute the following command to build the Docker image and start the service:

```bash
docker compose up --build --force-recreate -d
```
`--build`: Forces a rebuild of the Docker image, incorporating any changes to the Dockerfile or source code.

`--force-recreate`: Ensures existing containers are stopped and new ones are created from the latest image.

`-d`: Runs the container in detached (background) mode.

---
## Monitoring and Logging
To view the application's logs in real-time:
```bash
docker logs -f powerwall2pvoutput
```

---

## Project Structure
* docker-compose.yaml: Defines the Docker services.
* Dockerfile: Instructions for building the Docker image.
* requirements.txt: Lists Python dependencies (e.g., requests).
* PW_Simple.py: Main application script responsible for data collection and PVOutput integration.
* PW_Helper.py: Contains helper functions for Powerwall API interaction, PVOutput API interaction, and logging setup.
* PW_Config.py: Configuration file for non-sensitive settings; sensitive data loaded from environment variables.
* .env: (Local file, not committed to Git) Stores sensitive credentials.
* .gitignore: Specifies files and directories to be ignored by Git.

---

## LICENSE: Project's open-source license.
This project is licensed under the [MIT License](LICENSE).
