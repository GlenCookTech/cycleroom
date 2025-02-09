import { useEffect, useState } from "react";
import axios from "axios";

export default function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8888/leaderboard").then((res) => setLeaderboard(res.data));
  }, []);

  return (
    <div>
      <h1>Leaderboard</h1>
      <table border="1">
        <thead>
          <tr>
            <th>Device</th>
            <th>Max Power</th>
            <th>Max Cadence</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map((rider, index) => (
            <tr key={index}>
              <td>{rider.device}</td>
              <td>{rider.max_power}</td>
              <td>{rider.max_cadence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
