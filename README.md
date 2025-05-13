# RUCKUS One AP Port Configuration Script

This Python script automates the configuration of Access Point (AP) LAN ports on the RUCKUS One platform using data from a CSV file and the RUCKUS One API.

## Features

- Reads AP port configuration data from a CSV file (with support for commented headers).
- Authenticates with the RUCKUS One API using OAuth2 client credentials.
- Configures AP LAN ports with specific VLAN and port settings.
- Logs all actions, API requests, responses, and errors to `app.log`.
- Supports credentials via a file or interactive prompt.

## Prerequisites

- Python 3.7+
- [requests](https://pypi.org/project/requests/) library

Install dependencies with:

`pip install requests`


You also need:
- A RUCKUS One account with API access
- A client ID and client secret (see [RUCKUS Cloud API documentation](https://docs.ruckus.cloud/api))

## Setup

1. **Clone this repository or copy the script.**

2. **Create a `credentials` file** in the script directory with the following contents:
    ```
    tenant_id
    client_id
    client_secret
    ```

    - Each value should be on its own line.
    - If the file is missing, the script will prompt you for these values.

3. **Prepare your CSV file** (example: `ap_ports.csv`):

    ```
    # venue_id,ap_serial,port_id,vlan_id
    VENUE123,AP123456,1,100
    VENUE456,AP654321,2,200
    ```

    - The first line can be a comment (starts with `#`).
    - The columns must be in this order: `venue_id`, `ap_serial`, `port_id`, `vlan_id`.

## Usage

`python r1portvlan.py ap_ports.csv`

- The script will read your credentials, authenticate, and process each row in the CSV.
- Progress and errors are printed to the console and logged in `app.log`.

## Logging

- All significant actions, API requests, responses, and errors are logged to `app.log` in the script directory.
- Review this file for troubleshooting and auditing.

## Troubleshooting

- **Authentication errors:** Check your client ID/secret and tenant ID in the `credentials` file.
- **CSV errors:** Ensure your CSV matches the required format and contains valid data.
- **API errors:** Review `app.log` for detailed error messages and API responses.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
