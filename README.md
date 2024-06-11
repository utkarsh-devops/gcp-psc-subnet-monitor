# Background
Automated process to monitor the PSC Publisher subnet utilisation in order to avoid the subnet running out of IPs. 
Details: Automation to retrieve all PSC Publishers across various folders and projects, along with their associated subnets and ranges. Calculate the total IPs in each subnet, subtract the used NAT IPs to determine the available IPs, and compute the percentage of available IPs.

# High Level Steps:
1. List all PSC Publisher Service across all the folders/projects in the organisation 
2. List its the attached subnets and their IP Range. 
3. Calculate the total number of IPs in the PSC Subnet 
4. List all the connected Forwarding Rules to the PSC Publisher 
5. Subtract the NAT IPs from the Total Number of IPs in Subnet along with the 4 reserved IPs per subnet to get the final number of available IPs. 
6. Generate the percentage of the available IPs to send alerts 
7. Send the Output JSON as Logs to GCP Log Explorer
8. Trigger an alert when for usage is 80%, 90%, 100% for the subnet utilisation.
9. Execution Phases:

# The aforementioned steps are divided into three steps 
- Step1: Pull the Publisher Information, Create a CSV and JSON Report and Upload to GCS 
- Step2: Send the JSON output file as custom logs on GCP Log explorer
- Step3: Setup Alert Policy on GCP Alerting to send alerts on 80%, 90%, 100% for the subnet utilisation. (This is one time activity) 
--------------------------------------------------------------------------------------------------------------------------------------------------------


# Step1: GCP Service Attachment Audit
This script provides a comprehensive overview of service attachments, their associated NAT subnets, and forwarding rule usage within your Google Cloud Platform (GCP) projects. It's designed to help you manage your service attachment resources, optimize utilization, and troubleshoot potential issues.

## Features
- `Recursive Project Discovery`: Automatically identifies all projects within specified parent folders or your entire GCP organization.
- `Service Attachment Details`: Retrieves detailed information about each service attachment, including its name, region, and associated NAT subnets.
- `NAT Subnet Analysis`: Calculates IP address counts, available IPs, and utilization percentages for each NAT subnet used by a service attachment.
- `Forwarding Rule Count`: Determines the number of forwarding rules connected to each service attachment.
- `CSV Output`: Generates a well-organized CSV file (service_attachments.csv) summarizing all the findings for easy analysis.
- `Error Handling`: Includes robust error handling to gracefully manage exceptions during API calls and data retrieval.

## Prerequisites
  1. `Python Environment`: Ensure you have Python 3.7 or higher installed.
  2. `Google Cloud SDK`: Install the Google Cloud SDK (gcloud)
  3. `Google Cloud Project Setup`:
       - Create a GCP project and enable the following APIs:
       - Cloud Resource Manager API
       - Cloud Asset API
       - Compute Engine API
  4. `Service Account`: Create a service account with the following roles:
       - Browser (roles/browser)
       - Cloud Asset Viewer (roles/cloudasset.viewer)
       - Compute Network Viewer (roles/compute.networkViewer)
  - `Environment Variable`: Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of your service account's JSON key file.
  5. Python Libraries: Install the required libraries using pip3:

      ```pip3 install google-cloud-resourcemanager google-cloud-asset google-cloud-compute```

  6. `IP Address Library`: Install the ipaddress library. (This is likely already included with your Python installation)
  
## Usage
  1. Edit Script: Open `psc_service_attachments_subnet_monitor.py` and modify `parent_folder_ids` with the actual ID(s) of your parent folders or organization node.
  2. Run the Script 
```
python3 psc_service_attachments_subnet_monitor.py
```
  The script will: 
  1. Discover all projects.
  2. Retrieve service attachments, NAT subnet data, and forwarding rule counts.
  3. Generate and save results in `service_attachments.csv`.
  4. Output progress messages to your terminal.
  
  
## Output (CSV File)
The service_attachments.csv file will contain the following columns:
- `Folder`: The folder or organization node containing the project.
- `Project`: The project ID.
- `ServiceAttachment`: The full resource name of the service attachment.
- `NATSubnets`: A comma-separated list of NAT subnet names.
- `NATSubnetRanges`: The IP address ranges of the NAT subnets.
- `NATSubnetIPCount`: The total number of IP addresses in each NAT subnet.
- `ForwardingRuleCount`: The number of forwarding rules using the service attachment.
- `AvailableIPs`: The number of IP addresses available for use in each NAT subnet.
- `AvgUtilization(%)`: The average utilization percentage of IP addresses across all NAT subnets

## Script Explanation
The script follows these steps:
1. `Initialization`: Sets up the clients for Google Cloud APIs (Resource Manager, Asset, Compute).
2. `Project Discovery`: Recursively searches for projects within the specified parent folders or organization.
3. `Service Attachment Retrieval`: Queries the Cloud Asset API for service attachments in each project.
4. `Data Extraction`: Retrieves details for each service attachment from the Compute Engine API, including its connected NAT subnets.
5. `NAT Subnet Analysis`: Fetches NAT subnet details from the Compute Engine API, calculates IP counts, available IPs, and utilization.
6. `Output Generation`: Stores the results in output_data and writes the data to the CSV file.

--------------------------------------------------------------------------------------------------------------------------------------------------------
# Step2: PSC Subnet Monitoring Log Ingestion
This script monitors and ingests log data about Private Service Connect (PSC) subnet utilization into Google Cloud Logging. It is designed to handle log entries in both list and dictionary formats, provided they adhere to a specific structure.

## Prerequisites
* Google Cloud Project: You need an active Google Cloud Project with Cloud Logging enabled.
* Service Account: A service account with the "Cloud Logging Log Writer" role to write logs to Cloud Logging.
* Authentication: Set up the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account's JSON key file.
* Log File: The script expects a JSON log file named `service_attachments.json` in the same directory.

## Log File Structure
The `service_attachments.json` file should contain log entries in one of the following formats:
 1. List Format
 2. Each entry should be a list of values corresponding to the following keys, in this order:
```["folder_path", "project_id", "self_link", "subnet_name", "ip_range", "min_num_ips", "allocated_ips", "reserved_ips", "utilized_percent"]```

Example:
```
[
  "/folders/1234567890", 
  "my-project-123", 
  "https://www.googleapis.com/compute/v1/projects/my-project-123/regions/us-central1/subnetworks/my-subnet",
  "my-subnet",
  "10.1.0.0/24",
  10,
  8,
  2,
  80.0
]
```

## Customization
* Logger Name: Change the `logger = client.logger('psc-subnet-monitoring')` line to modify the name of your logger in Cloud Logging.
* Resource Labels: Update the `resource` object with appropriate labels for your environment.

## How to Run
1. Install Dependencies:
```
pip3 install google-cloud-logging
```
2. Prepare Log File: Create the `service_attachments.json` file with properly formatted entries.
Run the Script:
```python3 ship-logs-gcp.py```

## Troubleshooting
- Log File Not Found: Ensure the service_attachments.json file is in the same directory as the script.
- Invalid JSON: Check your log file for syntax errors.
- Unexpected Log Entry Formats: The script will log warnings for entries that do not match the expected structure.


--------------------------------------------------------------------------------------------------------------------------------------------------------
# Step3: Google Cloud Monitoring Alert Policy Creation from JSON
This script automates the creation of alert policies in Google Cloud Monitoring using JSON configuration files. It streamlines the process of defining complex alerting conditions and notifications, reducing the risk of manual errors.

## Prerequisites
1. Google Cloud Project: Ensure you have an active Google Cloud Project with Cloud Monitoring enabled.
2. Service Account: A service account with the roles/monitoring.admin role to manage alert policies in Cloud Monitoring.
3. Authentication: Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to your service account's JSON key file.
4. Python and Libraries: Install the Google Cloud Monitoring library:
```pip install google-cloud-monitoring```
5. JSON Configuration: Create a JSON file (e.g., alert_policy_data.json) adhering to the required structure (see below).

## How to Run
1. Configure: Update the project_id variable in the script with your actual project ID.
2. Prepare JSON: Create your alert_policy_data.json file with the correct structure and values.
3. Execute: Run the script from your terminal:
```python3 setup-alert.py```
 
You should see a confirmation message indicating that the alert policy has been created.

## Customization
- Filter Expression: Carefully tailor the filter expression in the `conditionMatchedLog` section to match the specific log entries you want to monitor. Use the correct log name and field names from your log entries.
- Notification Channels: Replace the placeholder in `notificationChannels` with the actual names of your notification channels (e.g., email, Slack, etc.).

## Important Notes
- JSON Structure: Ensure your JSON data strictly adheres to the required format, as even minor errors can cause the script to fail.
- Log-Based Alerts: This script focuses on creating log-based alert policies. Refer to the Google Cloud Monitoring documentation for creating other types of alerts (e.g., metric-based).

## Sample alert_policy_data.json
```
{
  "name": "projects/<project-abc>/alertPolicies/123456",
  "displayName": "PSC Publisher Subnet utilisation is above 80%",
  "documentation": {
    "content": "psc-subnet-monitor-alert \n\nThe PSC Subnet utilisation above 80% please take a look.",
    "mimeType": "text/markdown"
  },
  "userLabels": {},
  "conditions": [
    {
      "name": "projects/<project-abc>/alertPolicies/123456/conditions/1234567",
      "displayName": "Log match condition",
      "conditionMatchedLog": {
        "filter": "logName=\"projects/<project-abc>/logs/psc-subnet-monitoring\" AND jsonPayload.jsonPayload.utilized_percent > 80",
        "labelExtractors": {
          "utilizedpercent": "EXTRACT(jsonPayload.jsonPayload.utilized_percent)",
          "iprange": "EXTRACT(jsonPayload.jsonPayload.ip_range)",
          "psc": "EXTRACT(jsonPayload.jsonPayload.self_link)",
          "folder": "EXTRACT(jsonPayload.jsonPayload.folder_path)",
          "subnet": "EXTRACT(jsonPayload.jsonPayload.subnet_name)",
          "project": "EXTRACT(jsonPayload.jsonPayload.project_id)"
        }
      }
    }
  ],
  "alertStrategy": {
    "notificationRateLimit": {
      "period": "300s"
    },
    "autoClose": "259200s"
  },
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "projects/<project-abc>/notificationChannels/987654321"
  ],
  "creationRecord": {
    "mutateTime": "2024-05-24T09:52:10.878910368Z",
    "mutatedBy": "xyz@google.com"
  },
  "mutationRecord": {
    "mutateTime": "2024-05-25T07:17:38.763603696Z",
    "mutatedBy": "xyz@google.com"
  },
  "severity": "WARNING"
}
```