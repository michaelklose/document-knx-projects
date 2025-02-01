#!/usr/bin/env python3
"""
This module extracts data from a KNX project file for documentation purposes.
It parses the project, dumps the full JSON, extracts device information and group addresses,
and exports them into CSV files.
"""

import csv
import json
from datetime import datetime
from typing import Any, Dict, Optional

from xknxproject.models import KNXProject
from xknxproject import XKNXProj

# Configuration constants
PROJECT_FILE = "sample.knxproj"
PROJECT_PASSWORD = ""  # optional
PROJECT_LANGUAGE = "de-DE"  # optional
FILE_JSON = "project.json"
FILE_DEVICES = "devices.csv"
FILE_GROUP_ADDRESSES = "group_addresses.csv"
FILE_GROUP_ADDRESSES_ETS = "group_addresses_ets.csv"


def load_project() -> KNXProject:
    """
    Load and parse the KNX project.

    Returns:
        The parsed KNX project.
    """
    knxproj = XKNXProj(
        path=PROJECT_FILE,
        password=PROJECT_PASSWORD,
        language=PROJECT_LANGUAGE,
    )
    return knxproj.parse()


def dump_project_json(project: KNXProject) -> None:
    """
    Dump the complete project to a JSON file.

    Args:
        project: The KNX project data.
    """
    with open(FILE_JSON, "w", encoding="utf-8") as fp:
        json.dump(project, fp, indent=4)


def format_last_modified(date_str: str) -> str:
    """
    Format the last modified timestamp from ISO format to a human-readable string.

    Args:
        date_str: The ISO formatted date string.

    Returns:
        A human-readable timestamp string.
    """
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return dt.strftime("%B %d, %Y, %H:%M:%S UTC")


def extract_device_data(
    location: Dict[str, Any],
    building: Optional[str] = None,
    floor: Optional[str] = None,
    room: Optional[str] = None,
    distribution_board: Optional[str] = None,
) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Recursively extract device data along with their context 
    (Building, Floor, Room, DistributionBoard).

    Args:
        location: The current location dictionary.
        building: The building name (if available).
        floor: The floor name (if available).
        room: The room name (if available).
        distribution_board: The distribution board name (if available).

    Returns:
        A dictionary mapping device individual addresses to their context.
    """
    device_info: Dict[str, Dict[str, Optional[str]]] = {}
    location_type = location.get("type")
    if location_type == "Building":
        building = location.get("name")
    elif location_type == "Floor":
        floor = location.get("name")
    elif location_type == "Room":
        room = location.get("name")
    elif location_type == "DistributionBoard":
        distribution_board = location.get("name")

    # Collect devices from the current location
    for device in location.get("devices", []):
        device_info[device] = {
            "Building": building,
            "Floor": floor,
            "Room": room,
            "DistributionBoard": distribution_board,
        }

    # Recursively process subspaces
    for subspace in location.get("spaces", {}).values():
        device_info.update(
            extract_device_data(subspace, building, floor, room, distribution_board)
        )
    return device_info


def export_devices_csv(
    project: KNXProject, all_devices: Dict[str, Dict[str, Optional[str]]]
) -> None:
    """
    Export device data to a CSV file.

    Args:
        project: The KNX project data.
        all_devices: A dictionary mapping device addresses to their context.
    """
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
    with open(FILE_DEVICES, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for device_addr, dev_data in project.get("devices", {}).items():
            context = all_devices.get(dev_data.get("individual_address"), {})
            writer.writerow(
                {
                    "individual_address": dev_data.get("individual_address"),
                    "description": dev_data.get("description"),
                    "manufacturer_name": dev_data.get("manufacturer_name"),
                    "name": dev_data.get("name"),
                    "hardware_name": dev_data.get("hardware_name"),
                    "order_number": dev_data.get("order_number"),
                    "building": context.get("Building", ""),
                    "floor": context.get("Floor", ""),
                    "room": context.get("Room", ""),
                    "distribution_board": context.get("DistributionBoard", ""),
                }
            )


def extract_group_ranges_dict(
    group_range: Dict[str, Any], project: Dict[str, Any]
) -> Dict[str, str]:
    """
    Recursively extract the hierarchy of group addresses and return it as a sorted dictionary.

    Args:
        group_range: The current group range dictionary.
        project: The complete project dictionary.

    Returns:
        A sorted dictionary mapping group addresses to their names.
    """
    hierarchy: Dict[str, str] = {}
    for address, details in group_range.items():
        full_address = address.strip("/")
        hierarchy[full_address] = details.get("name", "Unknown")

        # Add individual group addresses
        for group_address in details.get("group_addresses", []):
            group_data = project.get("group_addresses", {}).get(group_address, {})
            hierarchy[group_address] = group_data.get("name", "Unknown")

        # Recursively process nested group ranges
        hierarchy.update(
            extract_group_ranges_dict(details.get("group_ranges", {}), project)
        )

    # Sort the hierarchy based on numeric values (fallback to lexicographical sort)
    try:
        sorted_hierarchy = dict(
            sorted(
                hierarchy.items(), key=lambda item: [int(x) for x in item[0].split("/")]
            )
        )
    except ValueError:
        sorted_hierarchy = dict(sorted(hierarchy.items()))
    return sorted_hierarchy


def export_group_addresses_csv(
    project: Dict[str, Any], hierarchy_dict: Dict[str, str]
) -> None:
    """
    Export group addresses to a CSV file.

    Args:
        project: The complete project dictionary.
        hierarchy_dict: A dictionary mapping group addresses to their names.
    """
    fieldnames = ["address", "name", "dpt"]
    with open(FILE_GROUP_ADDRESSES, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for address, name in hierarchy_dict.items():
            dpt = ""
            if address.count("/") == 2:
                group_addr_data = project.get("group_addresses", {}).get(address, {})
                dpt_info = group_addr_data.get("dpt")
                if dpt_info:
                    dpt = f"{dpt_info.get('main')}.{dpt_info.get('sub'):04}"
            writer.writerow({"address": address, "name": name, "dpt": dpt})


def export_group_addresses_ets_csv(
    project: Dict[str, Any], hierarchy_dict: Dict[str, str]
) -> None:
    """
    Export group addresses to a CSV file for ETS import.

    Args:
        project: The complete project dictionary.
        hierarchy_dict: A dictionary mapping group addresses to their names.
    """
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
    with open(FILE_GROUP_ADDRESSES_ETS, "w", newline="", encoding="cp1252") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for address, name in hierarchy_dict.items():
            row: Dict[str, Any] = {"Address": address, "Security": "Auto"}
            if address.count("/") == 0:
                row["Main"] = name
                row["Address"] = f"{address}/-/-"
            elif address.count("/") == 1:
                row["Middle"] = name
                row["Address"] = f"{address}/-"
            elif address.count("/") == 2:
                row["Sub"] = name
                group_addr_data = project.get("group_addresses", {}).get(address, {})
                dpt_info = group_addr_data.get("dpt")
                if dpt_info:
                    row["DatapointType"] = (
                        f"DPST-{dpt_info.get('main')}-{dpt_info.get('sub')}"
                    )
                else:
                    row["DatapointType"] = ""
            writer.writerow(row)


def main() -> None:
    """
    Main function to load the project, export JSON, extract and export devices and group addresses.
    """
    # Load the project and create a JSON dump
    project = load_project()
    dump_project_json(project)

    info = project.get("info", {})
    print("Project Name:", info.get("name", "Unknown"))
    if last_modified := info.get("last_modified"):
        print("Last Modified:", format_last_modified(last_modified))
    print("Tool Version:", info.get("tool_version", ""))
    print("XKNXProject Version:", info.get("xknxproject_version", ""))

    # Extract device data from locations
    all_devices: Dict[str, Dict[str, Optional[str]]] = {}
    for building_data in project.get("locations", {}).values():
        all_devices.update(extract_device_data(building_data))
    export_devices_csv(project, all_devices)

    # Process and export group addresses
    group_ranges = project.get("group_ranges", {})
    hierarchy_dict = extract_group_ranges_dict(group_ranges, project)
    export_group_addresses_csv(project, hierarchy_dict)
    export_group_addresses_ets_csv(project, hierarchy_dict)


if __name__ == "__main__":
    main()
