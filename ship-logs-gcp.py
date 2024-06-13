import json
import logging
from google.auth import default, exceptions
from google.cloud.logging import Client
from google.cloud.logging_v2.resource import Resource

# --- Project Configuration ---
target_project_id = 'prj-t-600001687-hcf-reports'  

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG)

# --- Credential Management ---
try:
    credentials, _ = default()
except exceptions.DefaultCredentialsError:
    logging.warning("Default credentials not found. Logging may not work as expected.")
    credentials = None
client = Client(project=target_project_id, credentials=credentials)
logger = client.logger('psc-subnet-monitoring')

# --- Data Definitions ---
keys = [
    "folder_path", "project_id", "self_link", "subnet_name",
    "ip_range", "min_num_ips", "allocated_ips", "reserved_ips",
    "utilized_percent"
]

resource = Resource(
    type="gce_service_attachment",
    labels={
        "logtag": "psc-subnet-monitor",
    },
)

# --- Log File Processing ---
try:
    with open('service_attachments.json', 'r') as file:
        log_entries = json.load(file)
        logging.debug(f"Loaded {len(log_entries)} log entries from file")
except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
    logging.error(f"Error reading log file: {e}")
    exit(1) 

else:
    for entry in log_entries:
        try:
            # Initialize payload_dict before the conditional blocks
            payload_dict = None

            if isinstance(entry, list) and len(entry) == len(keys):
                payload_dict = dict(zip(keys, entry))
            elif isinstance(entry, dict) and all(key in entry for key in keys):
                payload_dict = entry

            if payload_dict:  # Check if payload_dict was assigned
                # Log the entry (with fallback for auth issues)
                try:
                    logger.log_struct({'jsonPayload': payload_dict}, resource=resource)
                except exceptions.DefaultCredentialsError:
                    logging.error("Authentication error. Logging to a basic logger.")
                    logging.basicConfig(level=logging.ERROR) 
                    logging.error(payload_dict)
                else:
                    source_project_id = payload_dict.get('project_id', 'Unknown Source Project')
                    logging.info(f"Successfully shipped log from project {source_project_id} to project: {target_project_id}")
            else:
                logging.warning(
                    f"Invalid log entry format or length/key mismatch with keys: {entry}. Skipping this entry."
                )

        except (KeyError, TypeError) as e:
            logging.error(f"Error processing log entry: {e}")

print(f"Finished processing logs. Check project '{target_project_id}' in Cloud Logging.")
