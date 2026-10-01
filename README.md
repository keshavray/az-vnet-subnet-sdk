# az-vnet-subnet-sdk

A small Python script that creates an Azure Resource Group, Virtual Network (VNet) and Subnet using the Azure SDK for Python, and records what exists in a local JSON state file.

## What `provision_network.py` does

Running the script performs these steps in order. Each step checks first, so re-running it is safe and only creates what is missing.

1. **Resource Group** - checks whether the resource group exists and creates it in the configured location if it doesn't.
2. **Virtual Network** - lists the VNets in the resource group and creates the VNet with the configured address space if no VNet with that name exists.
3. **Subnet** - lists the subnets in the VNet, prints each name and CIDR, then:
   - skips creation if any subnet already uses the configured CIDR,
   - skips creation if a subnet with the configured name already exists,
   - otherwise creates the subnet.
4. **State file** - reads the resource group and VNet (including all its subnets) back from Azure and writes them to `state/<vnet_name>.json`. Each run increments a `version` counter in that file.

Azure API errors (`HttpResponseError`) are caught and printed instead of raising a traceback.

## Configuration

Settings are constants at the top of `provision_network.py`:

| Constant | Default |
| --- | --- |
| `SUBSCRIPTION_ID` | `""` (must be set) |
| `RG_NAME` | `exampleGroup` |
| `RG_LOCATION` | `eastus` |
| `VNET_NAME` | `exampleVnet` |
| `VNET_ADDRESS_PREFIX` | `10.0.0.0/16` |
| `SUBNET_NAME` | `exampleSubnet` |
| `SUBNET_ADDRESS_PREFIX` | `10.0.0.0/24` |
| `STATE_DIR` | `state` |

## Authentication

The script uses `DefaultAzureCredential`, so any supported login works, for example `az login`, environment variables for a service principal, or a managed identity.

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
az login
python provision_network.py
```

## State file format

```json
{
  "version": 1,
  "resource_group": { "name": "...", "location": "...", "id": "..." },
  "vnet": { "name": "...", "address_space": ["10.0.0.0/16"], "id": "..." },
  "subnets": [
    { "name": "...", "address_prefix": "10.0.0.0/24", "id": "..." }
  ]
}
```

The `state/` directory is git-ignored because it contains your subscription ID and Azure resource IDs.
