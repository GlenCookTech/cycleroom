import csv
import json

# Specify the file paths
csv_file_path = 'bluetooth-E55EF073F27A.csv'
json_file_path = 'filtered_output.json'

# Read CSV file and convert rows to a list of dictionaries
data = []
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        data.append(row)

# Write the list of dictionaries to a JSON file with pretty formatting
with open(json_file_path, mode='w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4)

logger.info(f"Data from {csv_file_path} has been converted to JSON and saved to {json_file_path}")
