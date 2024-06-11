import json
import logging
from google.cloud.logging import Client
from google.cloud.logging_v2.resource import Resource

# Configure logging client
client = Client()
logger = client.logger('psc-subnet-monitoring')

# Define descriptive keys for the list elements in your jsonPayload (if applicable)
keys = [
    "folder_path",
    "project_id",
    "self_link",
    "subnet_name",
    "ip_range",
    "min_num_ips",
    "allocated_ips",
    "reserved_ips",
    "utilized_percent",
]

# Custom Resource Labels - Modify to fit your environment
resource = Resource(
    type="gce_service_attachment",  
    labels={
        "logtag": "psc-subnet-monitor",
    },
)

# Read JSON log file
try:
    with open('service_attachments.json', 'r') as file:
        log_entries = json.load(file)
except FileNotFoundError:
    logger.log_text("Log file 'service_attachments.json' not found", severity="ERROR")
except json.JSONDecodeError as e:
    logger.log_text(f"Invalid JSON in file: {e}", severity="ERROR")
except Exception as e:  # Catch any unexpected error
    logger.log_text(f"Error reading log file: {e}", severity="ERROR")
else:
    # Ingest log entries
    for entry in log_entries:
        try:
            if isinstance(entry, list) and len(entry) == len(keys):
                # Convert the list directly to a dictionary
                payload_dict = dict(zip(keys, entry))
                logger.log_struct({'jsonPayload': payload_dict}, resource=resource)

            elif isinstance(entry, dict) and all(key in entry for key in keys):
                # If it's already a dictionary with the correct keys, log directly
                logger.log_struct({'jsonPayload': entry}, resource=resource)
                
            else:
                logger.log_text(
                    f"Unexpected log entry format or length/key mismatch with keys: {entry}", 
                    severity='WARNING'
                )

        except (KeyError, TypeError) as e:
            logger.log_text(f"Error processing log entry: {e}", severity='ERROR')