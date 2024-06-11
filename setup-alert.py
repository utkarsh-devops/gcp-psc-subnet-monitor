import json
from google.cloud import monitoring_v3

def create_alert_policy(project_id, alert_policy_data):
    """Creates a Monitoring alert policy from the given JSON data."""

    client = monitoring_v3.AlertPolicyServiceClient()
    parent = f"projects/{project_id}"

    # Convert the JSON data to a Monitoring AlertPolicy object
    alert_policy = monitoring_v3.AlertPolicy()
    alert_policy.display_name = alert_policy_data["displayName"]
    alert_policy.documentation.content = alert_policy_data["documentation"]["content"]
    alert_policy.documentation.mime_type = alert_policy_data["documentation"]["mimeType"]
    alert_policy.user_labels = alert_policy_data["userLabels"]
    alert_policy.alert_strategy.notification_rate_limit.period = alert_policy_data["alertStrategy"]["notificationRateLimit"]["period"]
    alert_policy.alert_strategy.auto_close = alert_policy_data["alertStrategy"]["autoClose"]
    alert_policy.combiner = alert_policy_data["combiner"]
    alert_policy.enabled = alert_policy_data["enabled"]
    alert_policy.notification_channels = alert_policy_data["notificationChannels"]
    alert_policy.severity = alert_policy_data["severity"]

    # Build the log match condition
    condition = monitoring_v3.AlertPolicy.Condition()
    condition.display_name = alert_policy_data["conditions"][0]["displayName"]
    condition.condition_matched_log.filter = alert_policy_data["conditions"][0]["conditionMatchedLog"]["filter"]
    condition.condition_matched_log.label_extractors = alert_policy_data["conditions"][0]["conditionMatchedLog"]["labelExtractors"]
    alert_policy.conditions.append(condition)

    # Create the alert policy
    created_alert_policy = client.create_alert_policy(
        name=parent, alert_policy=alert_policy
    )

    print(f"Alert policy created: {created_alert_policy.name}")


# Replace with your actual project ID
project_id = "abc-project" #replace with your project ID

# Load the JSON data from your file
with open("alert_policy_data.json", "r") as file:
    alert_policy_data = json.load(file)

create_alert_policy(project_id, alert_policy_data)