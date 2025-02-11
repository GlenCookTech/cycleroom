const express = require("express");
const cors = require("cors");
const { InfluxDB } = require("@influxdata/influxdb-client");

const app = express();
const PORT = 3000;

// InfluxDB Configuration
const INFLUX_URL = "http://cycle-brain:8086";
const INFLUX_TOKEN = "4IUS9-XeFEMCK9feAL57AWcl2Cbr2I4Jlvd5Hf_2P1Fgwv7FAZwAUszc5riJRBhLP8EmPlud_9-85MzjaTYF8Q==";
const ORG = "GlenCookTech";
const BUCKET = "keiser_data";
const client = new InfluxDB({ url: INFLUX_URL, token: INFLUX_TOKEN });
const queryApi = client.getQueryApi(ORG);

// Enable CORS and JSON parsing
app.use(cors());
app.use(express.json());
app.use(express.static("public"));
app.set("view engine", "ejs");

// Function to fetch data from InfluxDB
async function fetchData(field) {
    const query = `
        from(bucket: "${BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r["_measurement"] == "keiser_m3")
        |> filter(fn: (r) => r["_field"] == "${field}")
        |> last()
    `;

    const data = [];
    await queryApi.collectRows(query).then(rows => {
        rows.forEach(row => {
            data.push({
                time: row._time,
                value: row._value,
                equipment_id: row.equipment_id
            });
        });
    });

    return data;
}

// API Endpoints
app.get("/api/total-power", async (req, res) => {
    const data = await fetchData("power");
    res.json(data);
});

app.get("/api/distance", async (req, res) => {
    const data = await fetchData("distance");
    res.json(data);
});

app.get("/api/gear", async (req, res) => {
    const data = await fetchData("gear");
    res.json(data[0] || { value: 0 });
});

// Serve the frontend
app.get("/", (req, res) => {
    res.render("dashboard");
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});

// Mock API - Distance (Timeseries)
app.get("/api/distance", (req, res) => {
  res.json([
    { time: "2025-02-11T20:24:38.618Z", distance: Math.random() * 10 },
    { time: "2025-02-11T20:25:38.618Z", distance: Math.random() * 10 },
    { time: "2025-02-11T20:26:38.618Z", distance: Math.random() * 10 },
  ]);
});

// Mock API - Power Output (Timeseries)
app.get("/api/power-output", (req, res) => {
  res.json([
    { time: "2025-02-11T20:24:38.618Z", power: Math.random() * 200 },
    { time: "2025-02-11T20:25:38.618Z", power: Math.random() * 200 },
    { time: "2025-02-11T20:26:38.618Z", power: Math.random() * 200 },
  ]);
});

// Mock API - Current Gear (Gauge)
app.get("/api/gear", (req, res) => {
  res.json({ gear: Math.floor(Math.random() * 25) });
});

// Serve the frontend
app.get("/", (req, res) => {
  res.render("dashboard");
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
