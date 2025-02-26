import csv
import binascii

class Broadcast:
    def __init__(self):
        self.IsValid = False
        self.UUID = ""
        self.RSSI = 0
        self.BuildMajor = 0
        self.BuildMinor = 0
        self.Interval = 0
        self.ID = 0
        self.Cadence = 0
        self.HeartRate = 0
        self.Power = 0
        self.Energy = 0
        self.Time = 0
        self.Trip = 0
        self.Gear = None

def two_byte_concat(lower, higher):
    return (higher << 8) | lower

def build_value_convert(value):
    try:
        return int(format(value, 'X'))  # Convert byte to hex, then to int
    except ValueError:
        return 0

def parse(address, advertising_data, rssi):
    broadcast = Broadcast()
    broadcast.UUID = address
    broadcast.RSSI = rssi
    broadcast.IsValid = False  # Start as invalid

    # Validate length
    if len(advertising_data) < 4 or len(advertising_data) > 19:
        return broadcast

    index = 0

    # Skip prefix bits if they exist
    if advertising_data[index] == 2 and advertising_data[index + 1] == 1:
        index += 2

    # Assign build values
    broadcast.BuildMajor = build_value_convert(advertising_data[index])
    index += 1
    broadcast.BuildMinor = build_value_convert(advertising_data[index])
    index += 1

    if broadcast.BuildMajor == 6 and len(advertising_data) > (index + 13):
        broadcast.Interval = advertising_data[index]
        broadcast.ID = advertising_data[index + 1]
        broadcast.Cadence = two_byte_concat(advertising_data[index + 2], advertising_data[index + 3]) / 10
        broadcast.HeartRate = two_byte_concat(advertising_data[index + 4], advertising_data[index + 5]) / 10
        broadcast.Power = two_byte_concat(advertising_data[index + 6], advertising_data[index + 7])
        broadcast.Energy = two_byte_concat(advertising_data[index + 8], advertising_data[index + 9])
        broadcast.Time = advertising_data[index + 10] * 60 + advertising_data[index + 11]
        broadcast.Trip = two_byte_concat(advertising_data[index + 12], advertising_data[index + 13])

        # Convert miles to km if necessary
        if (broadcast.Trip & 32768) != 0:
            broadcast.Trip = int(broadcast.Trip * 1.60934)

        # Additional parameters (if BuildMinor >= 21)
        if broadcast.BuildMinor >= 21 and len(advertising_data) > (index + 14):
            broadcast.Gear = advertising_data[index + 14]

        broadcast.IsValid = True

    return broadcast

def hex_string_to_byte_array(hex_string):
    """Convert a hex string to a byte array"""
    return binascii.unhexlify(hex_string)

# Read and process the CSV file
csv_file = "bluetooth-E55EF073F27A.csv"

with open(csv_file, newline='') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip header row

    for row in reader:
        address = row[0].strip()
        advertising_data = hex_string_to_byte_array(row[1].strip())  # Convert hex string to bytes
        rssi = int(row[2].strip())

        parsed_data = parse(address, advertising_data, rssi)

        print(f"Parsed Data -> UUID: {parsed_data.UUID}, Power: {parsed_data.Power}, Cadence: {parsed_data.Cadence}, Valid: {parsed_data.IsValid}")
