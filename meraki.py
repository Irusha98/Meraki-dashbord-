# app.py
import os
import requests
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Meraki API configuration
# IMPORTANT: Replace 'YOUR_MERAKI_API_KEY' with your actual Meraki API key.
# It's recommended to store this in an environment variable for security.
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
if not MERAKI_API_KEY:
    print("WARNING: MERAKI_API_KEY environment variable not set. Please set it to your Meraki API key.")
    # Fallback for demonstration if env var isn't set, but strongly discourage in production
    MERAKI_API_KEY = "YOUR_MERAKI_API_KEY"

MERAKI_API_BASE_URL = "https://api.meraki.com/api/v1"

HEADERS = {
    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
    "Content-Type": "application/json"
}

# --- Helper functions for Meraki API calls ---

def get_organizations():
    """Fetches Meraki organizations."""
    try:
        response = requests.get(f"{MERAKI_API_BASE_URL}/organizations", headers=HEADERS)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching organizations: {e}")
        return None

def get_networks(organization_id):
    """Fetches networks for a given organization ID."""
    try:
        response = requests.get(f"{MERAKI_API_BASE_URL}/organizations/{organization_id}/networks", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching networks for org {organization_id}: {e}")
        return None

def get_network_devices(network_id):
    """Fetches devices for a given network ID."""
    try:
        response = requests.get(f"{MERAKI_API_BASE_URL}/networks/{network_id}/devices", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching devices for network {network_id}: {e}")
        return None

def get_network_clients(network_id, timespan=3600):
    """
    Fetches clients connected to a network.
    timespan: The timespan in seconds for the query. Default is 1 hour (3600 seconds).
    """
    try:
        params = {"timespan": timespan}
        response = requests.get(f"{MERAKI_API_BASE_URL}/networks/{network_id}/clients", headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching clients for network {network_id}: {e}")
        return None

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main dashboard page."""
    return render_template('index.html')

@app.route('/api/meraki-data')
def get_meraki_data():
    """
    API endpoint to fetch Meraki device and client data.
    This function will attempt to find the first organization and first network
    and then fetch data for them.
    """
    organizations = get_organizations()
    if not organizations:
        return jsonify({"error": "Could not fetch organizations. Check API key and network connectivity."}), 500

    if not organizations:
        return jsonify({"error": "No Meraki organizations found."}), 404

    organization_id = organizations[0]['id']
    organization_name = organizations[0]['name']

    networks = get_networks(organization_id)
    if not networks:
        return jsonify({"error": f"No networks found for organization {organization_name}."}), 404

    network_id = networks[0]['id']
    network_name = networks[0]['name']

    devices = get_network_devices(network_id)
    clients = get_network_clients(network_id, timespan=86400) # Get clients for last 24 hours

    # Process data for dashboard
    device_names = [device.get('name', 'N/A') for device in devices] if devices else []
    device_statuses = [device.get('status', 'N/A') for device in devices] if devices else []

    # Simple client count
    client_count = len(clients) if clients else 0

    # You can add more complex data processing here for usage stats per device/client type
    # For now, let's just count device types and client count
    device_type_counts = {}
    if devices:
        for device in devices:
            device_type = device.get('model', 'Unknown')
            device_type_counts[device_type] = device_type_counts.get(device_type, 0) + 1

    dashboard_data = {
        "organizationName": organization_name,
        "networkName": network_name,
        "deviceCount": len(devices) if devices else 0,
        "clientCount": client_count,
        "deviceTypes": list(device_type_counts.keys()),
        "deviceTypeCounts": list(device_type_counts.values()),
        "devices": devices, # Raw device data for more detailed display if needed
        "clients": clients # Raw client data for more detailed display if needed
    }

    return jsonify(dashboard_data)

if __name__ == '__main__':
    # Ensure a 'templates' directory exists
    os.makedirs('templates', exist_ok=True)
    # The app will run on http://127.0.0.1:5000/ by default
    app.run(debug=True) # debug=True allows for automatic reloading on code changes





