import { useEffect, useState } from "react";
import axios from "axios";

export default function Sessions() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    axios.get("http://localhost:8888/sessions").then((res) => setSessions(res.data));
  }, []);

  return (
    <div>
      <h1>Past Sessions</h1>
      <table border="1">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Device</th>
            <th>Power</th>
            <th>Cadence</th>
            <th>Heart Rate</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.id}>
              <td>{new Date(session.timestamp).toLocaleString()}</td>
              <td>{session.device}</td>
              <td>{session.power}</td>
              <td>{session.cadence}</td>
              <td>{session.heart_rate || "N/A"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
