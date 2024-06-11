import csv
import ipaddress
import json
from google.cloud import resourcemanager_v3
from google.cloud.asset_v1 import AssetServiceClient
from google.cloud import compute_v1
from google.cloud import storage


def list_service_attachments(parent_folder_ids):
    """
    Lists service attachments in a GCP folder hierarchy, details about their NAT subnets,
    forwarding rule counts, and available IP addresses (accounting for a reservation of 4 IPs).
    Prints a message if no forwarding rules are found in a project.
    """

    # Initialize clients for interacting with Google Cloud APIs
    folder_client = resourcemanager_v3.FoldersClient()
    project_client = resourcemanager_v3.ProjectsClient()
    asset_client = AssetServiceClient()
    compute_client = compute_v1.ServiceAttachmentsClient()
    compute_subnetworks_client = compute_v1.SubnetworksClient()

    all_projects = []

    # Recursively collect all projects under the parent folders
    def get_all_projects(parent_id):
        parent_path = f"folders/{parent_id}"
        for project in project_client.list_projects(parent=parent_path):
            all_projects.append(project)
            print(f"Found project: {project.project_id}")
        for folder in folder_client.list_folders(parent=parent_path):
            print(f"Found folder: {folder.name}")
            get_all_projects(folder.name.split("/")[-1])  # Recursively process subfolders

    # Get projects from all specified parent folders
    for parent_folder_id in parent_folder_ids:
        get_all_projects(parent_folder_id)

    print(f"Total projects found: {len(all_projects)}")
    output_data = []

    for project in all_projects:
        print(f"Processing project: {project.project_id}")
        found_forwarding_rules = False  # Flag to track if any forwarding rules were found

        try:
            assets = asset_client.search_all_resources(
                scope=f"projects/{project.project_id}",
                asset_types=["compute.googleapis.com/ServiceAttachment"],
            )

            for asset in assets:
                service_attachment = asset
                sa_name = service_attachment.name.split("/")[-1]
                sa_region = service_attachment.name.split("/")[-3]

                try:
                    response = compute_client.get(
                        project=project.project_id,
                        region=sa_region,
                        service_attachment=sa_name,
                    )
                    
                    rule_count = int(len(response.connected_endpoints))  # Convert rule_count to int

                    # Print forwarding rule count for each Service Attachment
                    if rule_count > 0:
                        found_forwarding_rules = True
                        print(f"  - Found {rule_count} forwarding rule(s) for service attachment: {service_attachment.name}")  
                    else:
                        print(f"  - No forwarding rules found for service attachment: {service_attachment.name}")

                    nat_subnets = []
                    nat_subnet_ranges = []
                    nat_subnet_ip_counts = []
                    available_ips = []
                    utilization_percentages = []

                    for endpoint in response.nat_subnets:
                        try:
                            subnet_name = endpoint.split("/")[-1]
                            subnet_region = endpoint.split("/")[-3]
                            subnet = compute_subnetworks_client.get(
                                project=project.project_id,
                                region=subnet_region,
                                subnetwork=subnet_name,
                            )

                            nat_subnets.append(subnet_name)
                            nat_subnet_ranges.append(subnet.ip_cidr_range)
                            network = ipaddress.ip_network(subnet.ip_cidr_range)

                            ip_count = network.num_addresses
                            reserved_ips = 4  # Reserve 4 IPs
                            available_ip_count = max(0, ip_count - rule_count - reserved_ips)
                            utilization = (1 - (available_ip_count / ip_count)) * 100 if ip_count > 0 else 0

                            nat_subnet_ip_counts.append(ip_count)
                            available_ips.append(available_ip_count)
                            # Calculate utilization, handling potential 'N/A' values
                            utilization_percentages.append(utilization if isinstance(utilization, float) else 0)

                            # Print detailed subnet information
                            print(f"   NAT Subnet Name: {subnet_name}, Range: {subnet.ip_cidr_range}, Total IPs: {ip_count}, Reserved IPs: {reserved_ips}, Available IPs: {available_ip_count}, Utilization: {utilization:.2f}%")

                        except Exception as subnet_error:
                            print(f"  - Error retrieving subnet details for {subnet_name}: {subnet_error}")
                            # Handle error by appending N/A values to the lists
                            nat_subnet_ranges.append("N/A")
                            nat_subnet_ip_counts.append("N/A")
                            available_ips.append("N/A")
                            utilization_percentages.append(0)  # Append 0 for error cases


                    # Calculate and print average utilization across subnets
                    avg_utilization = sum(utilization_percentages) / len(utilization_percentages) if utilization_percentages else "N/A"
                    print(f"   Average Utilization: {avg_utilization:.2f}%" if isinstance(avg_utilization, float) else avg_utilization)

                    # Store output data
                    output_data.append(
                        [
                            project.parent,
                            project.project_id,
                            service_attachment.name,
                            ",".join(nat_subnets),
                            ",".join(nat_subnet_ranges),
                            ",".join(map(str, nat_subnet_ip_counts)),
                            rule_count,
                            ",".join(map(str, available_ips)),  # Convert to string if needed
                            f"{avg_utilization:.2f}%" if isinstance(avg_utilization, float) else avg_utilization,
                        ]
                    )
                except Exception as sa_error:
                    print(f"  - Error getting service attachment details for {sa_name}: {sa_error}")  # Specific error message


        except Exception as e:
            print(f"  - Error processing project {project.project_id}: {e}")
        
        # Check if any forwarding rules were found in the project
        if not found_forwarding_rules:
            print(f"  - No forwarding rules found in project: {project.project_id}")
    # Write results to CSV
    with open("service_attachments.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Folder", "Project", "ServiceAttachment", "NATSubnets", "NATSubnetRanges", "NATSubnetIPCount", "ForwardingRuleCount", "AvailableIPs", "AvgUtilization(%)"])
        writer.writerows(output_data)
        print("Results written to service_attachments.csv")

    # Write results to JSON
    with open("service_attachments.json", "w") as jsonfile:
        json.dump(output_data, jsonfile, indent=2)  # indent for pretty-printing
        print("Results written to service_attachments.json")

def upload_to_gcs(bucket_name, file_name, file_path):
    """
    Uploads a file to Google Cloud Storage.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_path)
    print(f"Uploaded {file_path} to gs://{bucket_name}/{file_name}")

if __name__ == "__main__":
    parent_folder_ids = ["123456789"]  # Add the Folder IDs here 
    list_service_attachments(parent_folder_ids)

    # GCS Bucket and File Configuration
    gcs_bucket_name = "abc-bucket-name"   # Add the bucket name here
    csv_file_name = "service_attachments.csv"
    json_file_name = "service_attachments.json"

    # Upload to GCS
    upload_to_gcs(gcs_bucket_name, csv_file_name, csv_file_name)
    upload_to_gcs(gcs_bucket_name, json_file_name, json_file_name)