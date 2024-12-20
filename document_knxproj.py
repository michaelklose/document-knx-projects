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

# Export Devices to CSV
with open(FILE_DEVICES, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = [
        "individual_address",
        "description",
        "manufacturer_name",
        "name",
        "hardware_name",
        "order_number",
    ]
    devices_csv = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
    )
    devices_csv.writeheader()

    for device, value in project["devices"].items():
        devices_csv.writerow(
            {
                "individual_address": value["individual_address"],
                "description": value["description"],
                "manufacturer_name": value["manufacturer_name"],
                "name": value["name"],
                "hardware_name": value["hardware_name"],
                "order_number": value["order_number"],
            }
        )

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

    for group_address, value in project["group_addresses"].items():
        if value["dpt"] is not None:
            FORMATTED_DPT = (
                str(value["dpt"]["main"]) + "." + str(f"{value['dpt']['sub']:04}")
            )
        else:
            FORMATTED_DPT = "null"
        group_addresses_csv.writerow(
            {
                "address": value["address"],
                "name": value["name"],
                "dpt": FORMATTED_DPT,
            }
        )
