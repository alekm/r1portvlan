import sys
import csv
import requests
import logging
import os

# --- Logging Setup ---
# Configure logging to output to a file with timestamps and log levels.
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

def get_bearer_token(tenant_id, client_id, client_secret):
    """
    Authenticate with RUCKUS Cloud API and return a JWT bearer token.
    Exits the script if authentication fails.
    """
    auth_url = f"https://api.ruckus.cloud/oauth2/token/{tenant_id}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": "https://api.ruckus.cloud"
    }
    try:
        logger.info("Requesting JWT token from %s", auth_url)
        response = requests.post(auth_url, headers=headers, data=data)
        logger.info("Auth response: %s %s", response.status_code, response.text)
        response.raise_for_status()
        token = response.json().get('access_token')
        if not token:
            logger.error("No access_token in response: %s", response.text)
            sys.exit("Authentication failed: No access_token in response.")
        logger.info("Successfully obtained JWT token.")
        return token
    except requests.RequestException as e:
        logger.error("Authentication failed: %s", e)
        sys.exit("Authentication failed. Check app.log for details.")

def configure_ap_port(tenant_id, venue_id, ap_serial, port, vlan_id, bearer_token):
    """
    Configure an AP port on RUCKUS Cloud using the provided parameters.
    Logs both the request and response for debugging.
    """
    base_url = f"https://api.ruckus.cloud/venues/{venue_id}/aps/{ap_serial}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    port_settings_url = f"{base_url}/lanPorts/{port}/settings"
    payload = {
        "useVenueSettings": False,
        "enabled": True,
        "overwriteUntagId": vlan_id,
        "overwriteVlanMembers": str(vlan_id)
    }
    try:
        logger.info(
            "PUT %s | Payload: %s", port_settings_url, payload
        )
        response = requests.put(
            port_settings_url,
            headers=headers,
            json=payload
        )
        logger.info(
            "Response [%s]: %s", response.status_code, response.text
        )
        response.raise_for_status()
        logger.info(
            "Successfully configured AP %s port %s at venue %s", ap_serial, port, venue_id
        )
        print(f"Configured AP {ap_serial} port {port} at venue {venue_id}")
    except requests.RequestException as e:
        logger.error(
            "Failed to configure port %s on %s at venue %s: %s",
            port, ap_serial, venue_id, e
        )
        print(f"Failed to configure port {port} on {ap_serial} at venue {venue_id}: {e}")

def skip_comments(file_obj):
    """
    Generator that skips initial commented lines (starting with '#') in a file.
    Yields lines starting from the first non-comment line.
    """
    for line in file_obj:
        if not line.lstrip().startswith('#'):
            yield line
            break
    yield from file_obj

def main():
    """
    Main script logic:
    - Loads credentials from file or prompts user.
    - Authenticates to get a JWT token.
    - Processes the CSV file, skipping commented headers.
    - For each row, validates fields and configures the AP port via API.
    - Logs all actions and errors.
    """
    # Check for correct usage
    if len(sys.argv) != 2:
        print("Usage: python configure_ap_ports.py <filename.csv>")
        logger.error("Incorrect usage: missing CSV filename argument.")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    credentials_file = "credentials"
    tenant_id = client_id = client_secret = None

    # --- Credential Handling ---
    if os.path.isfile(credentials_file):
        logger.info("Loading credentials from file: %s", credentials_file)
        try:
            with open(credentials_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]
                if len(lines) >= 3:
                    tenant_id = lines[0]
                    client_id = lines[1]
                    client_secret = lines[2]
                else:
                    logger.error("Credentials file missing required lines.")
                    sys.exit("Credentials file must have at least 3 lines: Tenant ID, Client ID, Client Secret.")
        except Exception as e:
            logger.error("Error reading credentials file: %s", e)
            sys.exit("Error reading credentials file. Check app.log for details.")
    else:
        logger.info("Prompting user for credentials.")
        tenant_id = input("Enter Tenant ID: ")
        client_id = input("Enter Client ID: ")
        client_secret = input("Enter Client Secret: ")
        if not all([tenant_id, client_id, client_secret]):
            logger.error("Missing credential input from user.")
            sys.exit("Tenant ID, Client ID, and Client Secret are required.")

    # --- Authenticate and get JWT token ---
    bearer_token = get_bearer_token(tenant_id, client_id, client_secret)

    # Define the expected CSV columns
    FIELDNAMES = ['venue_id', 'ap_serial', 'port_id', 'vlan_id']

    # --- CSV Processing ---
    try:
        with open(csv_file, newline='') as csvfile:
            logger.info("Opened CSV file: %s", csv_file)
            reader = csv.DictReader(skip_comments(csvfile), fieldnames=FIELDNAMES)
            for idx, row in enumerate(reader, 1):
                try:
                    logger.info("Processing row %d: %s", idx, row)
                    # Extract and validate each field
                    venue_id = row['venue_id'].strip()
                    ap_serial = row['ap_serial'].strip()
                    port = int(row['port_id'])
                    vlan_id = int(row['vlan_id'])
                    # Check for required fields and valid VLAN range
                    if not venue_id or not ap_serial:
                        logger.warning("Missing venue_id or ap_serial in row %d: %s", idx, row)
                        print(f"Skipping row {idx}: Missing venue_id or ap_serial.")
                        continue
                    if not 1 <= vlan_id <= 4094:
                        logger.warning("Invalid VLAN ID in row %d: %s", idx, row)
                        print(f"Skipping row {idx}: Invalid VLAN ID {vlan_id}.")
                        continue
                    # Make the API call to configure the AP port
                    configure_ap_port(tenant_id, venue_id, ap_serial, port, vlan_id, bearer_token)
                except (KeyError, ValueError) as e:
                    logger.error("Error processing row %d: %s | Row: %s", idx, e, row)
                    print(f"Skipping row {idx}: {e}")
    except FileNotFoundError:
        logger.error("CSV file not found: %s", csv_file)
        print(f"CSV file {csv_file} not found")
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error opening CSV: %s", e)
        print(f"Unexpected error opening CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
