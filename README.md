# document-knx-projects

Extract data like devices, group addresses, ... from a KNX Project File for documentation purposes.

```console
# python3 document_knxproj.py
Project Name: Sample
Last Modified: December 11, 2024, 12:23:19 UTC
Tool Version: 6.2.7302.0
XKNXProject Version: 3.8.1
```

Currently the following output files will be generated:

- JSON file with complete dictionary exported by xknxproject (project.json)
- CSV file for all devices (devices.csv)
- CSV file for all group addresses (group_addresses.csv)
- CSV file for importing group addresses in ETS (group_addresses_ets.csv)

The import file for ETS corresponds to the ETS export with the following parameters:

- Output format: CSV
- CSV format: 3/1
- CSV seperator: semicolon
