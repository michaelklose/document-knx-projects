"""Script for extracting data from a KNX Project File for documentation purposes."""

import csv
import json
from datetime import datetime
from xknxproject.models import KNXProject
from xknxproject import XKNXProj

# Variables
PROJECT_FILE = "sample.knxproj"
PROJECT_PASSWORD = ""  # optional
PROJECT_LANGUAGE = "de-DE"  # optional
FILE_JSON = "project.json"
FILE_DEVICES = "devices.csv"
FILE_GROUP_ADDRESSES = "group_addresses.csv"
FILE_GROUP_ADDRESSES_ETS = "group_addresses_ets.csv"

knxproj: XKNXProj = XKNXProj(
    path=PROJECT_FILE,
    password=PROJECT_PASSWORD,  # optional
    language=PROJECT_LANGUAGE,  # optional
)
project: KNXProject = knxproj.parse()

# pprint(project["devices"])

# Dump complete project file to json
with open(FILE_JSON, "w", encoding="utf-8") as fp:
    json.dump(project, fp, indent=4)

datetime_str = project["info"]["last_modified"]
dt = datetime.fromisoformat(
    datetime_str.replace("Z", "+00:00")
)  # Replace Z with timezone info
formatted_dt = dt.strftime("%B %d, %Y, %H:%M:%S UTC")

print("Project Name:", project["info"]["name"])
print("Last Modified:", formatted_dt)
print("Tool Version:", project["info"]["tool_version"])
print("XKNXProject Version:", project["info"]["xknxproject_version"])


# Helper function to recursively parse locations and collect device data
def extract_device_data(
    location, building=None, floor=None, room=None, distribution_board=None
):
    """Recursively parse locations and collect device data."""
    device_info = {}
    if location.get("type") == "Building":
        building = location.get("name")
    elif location.get("type") == "Floor":
        floor = location.get("name")
    elif location.get("type") == "Room":
        room = location.get("name")
    elif location.get("type") == "DistributionBoard":
        distribution_board = location.get("name")

    # Collect devices
    for device in location.get("devices", []):
        device_info[device] = {
            "Building": building,
            "Floor": floor,
            "Room": room,
            "DistributionBoard": distribution_board,
        }

    # Recurse into subspaces
    for subspace in location.get("spaces", {}).values():
        device_info.update(
            extract_device_data(subspace, building, floor, room, distribution_board)
        )

    return device_info


# Extract data starting from root locations
all_devices = {}
for b, building_data in project.get("locations", {}).items():
    all_devices.update(extract_device_data(building_data))

# Export Devices to CSV
with open(FILE_DEVICES, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = [
        "individual_address",
        "description",
        "manufacturer_name",
        "name",
        "hardware_name",
        "order_number",
        "building",
        "floor",
        "room",
        "distribution_board",
    ]
    devices_csv = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
    )
    devices_csv.writeheader()

    for d, value in project["devices"].items():
        devices_csv.writerow(
            {
                "individual_address": value["individual_address"],
                "description": value["description"],
                "manufacturer_name": value["manufacturer_name"],
                "name": value["name"],
                "hardware_name": value["hardware_name"],
                "order_number": value["order_number"],
                "building": all_devices[value["individual_address"]]["Building"],
                "floor": all_devices[value["individual_address"]]["Floor"],
                "room": all_devices[value["individual_address"]]["Room"],
                "distribution_board": all_devices[value["individual_address"]][
                    "DistributionBoard"
                ],
            }
        )


# Recursive function to extract group ranges hierarchy as a dictionary
def extract_group_ranges_dict(group_range):
    """Recursive function to extract group ranges hierarchy as a dictionary."""
    hierarchy = {}
    for address, details in group_range.items():
        full_address = f"{address}".strip("/")

        # Add the current level entry
        hierarchy[full_address] = details.get("name", "Unknown")

        # Add third-level group addresses with name from group_addresses
        for group_address in details.get("group_addresses", []):
            hierarchy[group_address] = project["group_addresses"][group_address]["name"]

        # Recurse into nested group ranges
        hierarchy.update(
            extract_group_ranges_dict(details.get("group_ranges", {}))
        )

    return dict(
        sorted(hierarchy.items(), key=lambda item: [int(x) for x in item[0].split("/")])
    )


# Extract data into a dictionary
group_ranges = project.get("group_ranges", {})
hierarchy_dict = extract_group_ranges_dict(group_ranges)

# Export Group Addresses to CSV
with open(FILE_GROUP_ADDRESSES, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = [
        "address",
        "name",
        "dpt",
    ]
    group_addresses_csv = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
    )
    group_addresses_csv.writeheader()

    for address, name in hierarchy_dict.items():
        if address.count("/") == 2:
            if project["group_addresses"][address]["dpt"] is not None:
                DPT = (
                    str(project["group_addresses"][address]["dpt"]["main"])
                    + "."
                    + str(f"{project['group_addresses'][address]['dpt']['sub']:04}")
                )
            else:
                DPT = ""

        else:
            DPT = ""
        group_addresses_csv.writerow({"address": address, "name": name, "dpt": DPT})

# Export Group Addresses to CSV for ETS Import
with open(FILE_GROUP_ADDRESSES_ETS, "w", newline="", encoding="cp1252") as csvfile:
    fieldnames = [
        "Main",
        "Middle",
        "Sub",
        "Address",
        "Central",
        "Unfiltered",
        "Description",
        "DatapointType",
        "Security",
    ]

    group_addresses_ets_csv = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
    )

    group_addresses_ets_csv.writeheader()

    for address, name in hierarchy_dict.items():
        if address.count("/") == 0:
            group_addresses_ets_csv.writerow(
                {"Main": name, "Address": (address + "/-/-"), "Security": "Auto"}
            )
        elif address.count("/") == 1:
            group_addresses_ets_csv.writerow(
                {"Middle": name, "Address": (address + "/-"), "Security": "Auto"}
            )
        elif address.count("/") == 2:
            if project["group_addresses"][address]["dpt"] is not None:
                group_addresses_ets_csv.writerow(
                    {
                        "Sub": name,
                        "Address": address,
                        "DatapointType": (
                            "DPST-"
                            + str(project["group_addresses"][address]["dpt"]["main"])
                            + "-"
                            + str(project["group_addresses"][address]["dpt"]["sub"])
                        ),
                        "Security": "Auto",
                    }
                )
            else:
                group_addresses_ets_csv.writerow(
                    {"Sub": name, "Address": address, "Security": "Auto"}
                )
