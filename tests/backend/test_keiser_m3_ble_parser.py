
import pytest
from cycleroom.backend.keiser_m3_ble_parser import KeiserM3BLEBroadcast

def test_parser_valid_data():
    # Example of a valid BLE data packet (adjust this to match your real data)
    manufacture_data = bytes([0x00, 0x01, 0x02, 0x03, 0x00, 0x64, 0x00, 0x50, 0x00, 0x32, 0x00, 0x28, 0x00, 0x3C, 0x00, 0x10, 0x06])
    
    # Initialize the parser
    parser = KeiserM3BLEBroadcast(manufacture_data)
    parsed_data = parser.to_dict()
    
    # Check if the values are parsed correctly
    assert parsed_data["cadence"] == 100
    assert parsed_data["heart_rate"] == 80
    assert parsed_data["power"] == 50
    assert parsed_data["caloric_burn"] == 40
    assert parsed_data["duration"] == (60 * 0x3C)
    assert parsed_data["trip_distance"] == 1.6
    assert parsed_data["gear"] == 6

def test_parser_empty_data():
    # Test with empty data
    manufacture_data = bytes()
    parser = KeiserM3BLEBroadcast(manufacture_data)
    parsed_data = parser.to_dict()
    
    # Expect all values to be zero or None
    assert parsed_data["cadence"] == 0
    assert parsed_data["heart_rate"] == 0
    assert parsed_data["power"] == 0
    assert parsed_data["caloric_burn"] == 0
    assert parsed_data["duration"] == 0
    assert parsed_data["trip_distance"] == 0
    assert parsed_data["gear"] == 0

def test_parser_malformed_data():
    # Test with malformed data (less than required length)
    manufacture_data = bytes([0x00, 0x01, 0x02])
    parser = KeiserM3BLEBroadcast(manufacture_data)
    parsed_data = parser.to_dict()
    
    # Expect all values to be zero or None
    assert parsed_data["cadence"] == 0
    assert parsed_data["heart_rate"] == 0
    assert parsed_data["power"] == 0
    assert parsed_data["caloric_burn"] == 0
    assert parsed_data["duration"] == 0
    assert parsed_data["trip_distance"] == 0
    assert parsed_data["gear"] == 0

def test_parser_boundary_values():
    # Test with maximum possible values for each metric
    manufacture_data = bytes([0x00, 0x01, 0x02, 0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    parser = KeiserM3BLEBroadcast(manufacture_data)
    parsed_data = parser.to_dict()
    
    # Check the upper boundaries
    assert parsed_data["cadence"] == 65535
    assert parsed_data["heart_rate"] == 65535
    assert parsed_data["power"] == 65535
    assert parsed_data["caloric_burn"] == 65535
    assert parsed_data["duration"] == (60 * 255) + 255
    assert parsed_data["trip_distance"] == 6553.5  # Max value with one decimal
    assert parsed_data["gear"] == 255
