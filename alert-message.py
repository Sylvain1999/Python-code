import json
from datetime import datetime, timedelta

# Constants for thresholds and time window
BATT_LOW_THRESHOLD = 8.0  # Red low limit for battery voltage
TSTAT_HIGH_THRESHOLD = 101.0  # Red high limit for thermostat
TIME_WINDOW = timedelta(minutes=5)

# Function to determine severity based on the value
def determine_severity(value, component):
    if component == "TSTAT":
        if float(value) > TSTAT_HIGH_THRESHOLD:
            return "RED HIGH"
        else:
            return "NORMAL"
    elif component == "BATT":
        if float(value) < BATT_LOW_THRESHOLD:
            return "RED LOW"
        else:
            return "NORMAL"
    return "UNKNOWN"

# Function to parse a single log entry and convert it to the desired format
def parse_log_entry(entry):
    fields = entry.split('|')
    timestamp = datetime.strptime(fields[0], '%Y%m%d %H:%M:%S.%f')
    satellite_id = int(fields[1])
    value = float(fields[6])
    component = fields[7]
    
    severity = determine_severity(value, component)

    return {
        "satelliteId": satellite_id,
        "severity": severity,
        "component": component,
        "value": value,
        "timestamp": timestamp
    }

# Function to check violation conditions for each satellite and create alert messages
def check_violations(parsed_entries):
    alerts = []
    battery_readings = {}
    thermostat_readings = {}

    for entry in parsed_entries:
        satellite_id = entry['satelliteId']
        timestamp = entry['timestamp']
        severity = entry['severity']
        component = entry['component']
        
        if component == "BATT" and severity == "RED LOW":
            # Store battery voltage readings under RED LOW severity
            if satellite_id not in battery_readings:
                battery_readings[satellite_id] = []
            battery_readings[satellite_id].append(timestamp)

            # Remove readings outside the 5-minute window
            battery_readings[satellite_id] = [t for t in battery_readings[satellite_id] if t >= timestamp - TIME_WINDOW]

            # Check if there are 3 readings in the 5-minute window
            if len(battery_readings[satellite_id]) >= 3:
                alert = {
                    "satelliteId": satellite_id,
                    "severity": "RED LOW",
                    "component": "BATT",
                    "timestamp": timestamp.isoformat() + "Z"
                }
                alerts.append(alert)

        elif component == "TSTAT" and severity == "RED HIGH":
            # Store thermostat readings above RED HIGH severity
            if satellite_id not in thermostat_readings:
                thermostat_readings[satellite_id] = []
            thermostat_readings[satellite_id].append(timestamp)

            # Remove readings outside the 5-minute window
            thermostat_readings[satellite_id] = [t for t in thermostat_readings[satellite_id] if t >= timestamp - TIME_WINDOW]

            # Check if there are 3 readings in the 5-minute window
            if len(thermostat_readings[satellite_id]) >= 3:
                alert = {
                    "satelliteId": satellite_id,
                    "severity": "RED HIGH",
                    "component": "TSTAT",
                    "timestamp": timestamp.isoformat() + "Z"
                }
                alerts.append(alert)
    
    return alerts

# Function to read the input from an ASCII file
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

# Input file path
file_path = '/Users/sylvain/devops-lab/interview-projet/projet-interview-for-python/data.txt'  # Change this to your actual ASCII file path

# Read data from the file
data = read_file(file_path)

# Parse each entry and store it
parsed_entries = [parse_log_entry(entry.strip()) for entry in data]

# Check for violations and generate alert messages
alert_messages = check_violations(parsed_entries)

# Output alert messages as valid JSON
print(json.dumps(alert_messages, indent=4))
