import struct
from datetime import datetime, timezone

class KeiserM3BLEBroadcast:
    def __init__(self, manufacture_data: bytes):
        """Parses Keiser M3 BLE advertisement data into structured format."""
        if len(manufacture_data) > 17:
            manufacture_data = manufacture_data[2:]  # Trim first 2 bytes

        self.build_major = None
        self.build_minor = None
        self.data_type = None
        self.ordinal_id = 0
        self.interval = None
        self.real_time = False
        self.cadence = None
        self.heart_rate = None
        self.power = None
        self.caloric_burn = None
        self.duration = None
        self.trip_distance = None
        self.gear = None
        temp_distance = None

        for index, byte in enumerate(manufacture_data):
            self.build_major, self.build_minor, self.data_type = struct.unpack(">BBB", manufacture_data[:3])
                self.build_major = byte
            elif index == 1:
                self.build_minor = byte
            elif index == 2:
                self.data_type = byte
            elif index == 3:
                self.ordinal_id = byte
            elif index == 4:
                self.cadence = byte
            elif index == 5:
                self.cadence = (byte << 8) | self.cadence
            elif index == 6:
                self.heart_rate = byte
            elif index == 7:
                self.heart_rate = (byte << 8) | self.heart_rate
            elif index == 8:
                self.power = byte
            elif index == 9:
                self.power = (byte << 8) | self.power
            elif index == 10:
                self.caloric_burn = byte
            elif index == 11:
                self.caloric_burn = (byte << 8) | self.caloric_burn
            elif index == 12:
                self.duration = byte * 60  # Convert minutes to seconds
            elif index == 13:
                self.duration += byte  # Add seconds
            elif index == 14:
                temp_distance = byte
            elif index == 15:
                temp_distance = (byte << 8) | temp_distance
            elif index == 16:
                self.gear = byte

        # ✅ Convert cadence and heart rate
        if self.cadence is not None:
            self.cadence /= 10  # Convert to RPM
        if self.heart_rate is not None:
            self.heart_rate /= 10  # Convert to BPM

        # ✅ Determine real-time or review mode
        if self.data_type in [0, 255]:
            self.interval = 0
        elif 0 < self.data_type < 128:
            self.interval = self.data_type
        elif 128 < self.data_type < 255:
            self.interval = self.data_type - 128

        self.real_time = self.data_type == 0 or (128 < self.data_type < 255)

        # ✅ Convert tripDistance to miles/km
        if temp_distance is not None:
            if temp_distance & 32768 != 0:  # MSB is 1 → Distance in KM, convert to Miles
                self.trip_distance = ((temp_distance & 32767) * 0.62137119) / 10.0
            else:
                self.trip_distance = temp_distance / 10.0  # Already in miles

        # ✅ Timestamp
        self.timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    def to_dict(self):
        """Convert parsed data to a dictionary."""
        return {
            "timestamp": self.timestamp,
            "build_major": self.build_major,
            "build_minor": self.build_minor,
            "data_type": self.data_type,
            "ordinal_id": self.ordinal_id,
            "interval": self.interval,
            "real_time": self.real_time,
            "cadence": self.cadence,
            "heart_rate": self.heart_rate,
            "power": self.power,
            "caloric_burn": self.caloric_burn,
            "duration": self.duration,
            "trip_distance": self.trip_distance,
            "gear": self.gear,
        }
