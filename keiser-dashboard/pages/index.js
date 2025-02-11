import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

export default function Dashboard() {
  const [bikeData, setBikeData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://cycle-brain:8000/ws");

    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setBikeData((prev) => [...prev.slice(-50), { time: new Date().toLocaleTimeString(), ...newData.data }]);
    };

    return () => ws.close();
  }, []);

  return (
    <div style={{ textAlign: "center" }}>
      <h1>Keiser M Series Live Dashboard</h1>
      <LineChart width={80000} height={400} data={bikeData}>
        <XAxis dataKey="time" />
        <YAxis />
        <CartesianGrid strokeDasharray="3 3" />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="power" stroke="#ff7300" />
        <Line type="monotone" dataKey="cadence" stroke="#387908" />
      </LineChart>
    </div>
  );
}
