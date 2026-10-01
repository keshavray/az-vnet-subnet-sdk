import json
import os

from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient

VNET_NAME = "exampleVnet"
VNET_ADDRESS_PREFIX = "10.0.0.0/16"
SUBNET_NAME = "exampleSubnet"
SUBNET_ADDRESS_PREFIX = "10.0.0.0/24"
RG_NAME = "exampleGroup"
RG_LOCATION = "eastus"
SUBSCRIPTION_ID = ""
STATE_DIR = "state"


def state_file(vnet_name):
    return os.path.join(STATE_DIR, f"{vnet_name}.json")


def get_vnet_state(vnet_name):
    if not os.path.exists(state_file(vnet_name)):
        return None
    with open(state_file(vnet_name)) as f:
        return json.load(f)

def create_rg_vnet_subnet(subscription_id, rg_name, rg_location, vnet_name, vnet_address_prefix, subnet_name, subnet_address_prefix):
    credential = DefaultAzureCredential()
    client = ResourceManagementClient(credential, subscription_id)
    network = NetworkManagementClient(credential, subscription_id)
    if client.resource_groups.check_existence(rg_name):
        print("RG already exist")
    else:
        print("RG does not exist, creating...")
        group = client.resource_groups.create_or_update(rg_name, {"location": rg_location})
        print(f"Resource group created: {group.id}")

    if any(vnet.name == vnet_name for vnet in network.virtual_networks.list(rg_name)):
        print("VNET already exist")
    else:
        print("VNET does not exist, creating...")
        vnet = network.virtual_networks.begin_create_or_update(rg_name, vnet_name, {
            "location": rg_location,
            "address_space": {"address_prefixes": [vnet_address_prefix]},
        }).result()
        print(f"VNET created: {vnet.id}")

    subnets = list(network.subnets.list(rg_name, vnet_name))
    for subnet in subnets:
        print(subnet.name, subnet.address_prefix)
    if any(subnet.address_prefix == subnet_address_prefix for subnet in subnets):
        print("Subnet with given CIDR already exist")
    elif any(subnet.name == subnet_name for subnet in subnets):
        print("Subnet already exist")
    else:
        print("Subnet does not exist, creating...")
        subnet = network.subnets.begin_create_or_update(rg_name, vnet_name, subnet_name, {
            "address_prefix": subnet_address_prefix
        }).result()
        print(f"Subnet created: {subnet.id}")

    group = client.resource_groups.get(rg_name)
    vnet = network.virtual_networks.get(rg_name, vnet_name)
    old_state = get_vnet_state(vnet_name)
    version = old_state.get("version", 0) + 1 if old_state else 1
    state = {
        "version": version,
        "resource_group": {"name": group.name, "location": group.location, "id": group.id},
        "vnet": {"name": vnet.name, "address_space": vnet.address_space.address_prefixes, "id": vnet.id},
        "subnets": [{"name": s.name, "address_prefix": s.address_prefix, "id": s.id} for s in vnet.subnets],
    }
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_file(vnet_name), "w") as f:
        json.dump(state, f, indent=2)
    print(f"State written: {state_file(vnet_name)} (version {version})")

if __name__ == "__main__":
    try:
        create_rg_vnet_subnet(SUBSCRIPTION_ID, RG_NAME, RG_LOCATION, VNET_NAME, VNET_ADDRESS_PREFIX, SUBNET_NAME, SUBNET_ADDRESS_PREFIX)
    except HttpResponseError as e:
        print(f"Azure error: {e.message}")







  


