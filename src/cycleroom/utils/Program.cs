using System;
using System.IO;
using System.Linq;

class Program
{
    static void Main()
    {
        string filePath = "bluetooth-C0F6E019EECE.csv";

        using (StreamReader reader = new StreamReader(filePath))
        {
            string headerLine = reader.ReadLine(); // Read and ignore the header

            while (!reader.EndOfStream)
            {
                string line = reader.ReadLine();
                string[] values = line.Split(','); // Adjust if CSV uses different separators

                string address = values[0].Trim(); // Assuming first column is the address
                byte[] advertisingData = ConvertHexStringToByteArray(values[1].Trim()); // Second column (hex data)
                int rssi = int.Parse(values[2].Trim()); // Third column (RSSI)

                // Call the parser
                var parsedBroadcast = Keiser.M3i.BLE_Parser.Parser.Parse(address, advertisingData, rssi);

                // Output the parsed result
                Console.WriteLine($"Parsed Data: UUID={parsedBroadcast.UUID}, Power={parsedBroadcast.Power}, Cadence={parsedBroadcast.Cadence}, Valid={parsedBroadcast.IsValid}");
            }
        }
    }

    static byte[] ConvertHexStringToByteArray(string hex)
    {
        return Enumerable.Range(0, hex.Length / 2)
                         .Select(i => Convert.ToByte(hex.Substring(i * 2, 2), 16))
                         .ToArray();
    }
}
