import { useState, useEffect } from "react";

const API_URL = "http://localhost:8000"; // ✅ Update this if needed

const App = () => {
  const [bikes, setBikes] = useState([]);
  const [selectedBike, setSelectedBike] = useState("");
  const [userName, setUserName] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/bikes`)
      .then(res => res.json())
      .then(data => setBikes(data))
      .catch(err => console.error("❌ Error fetching bikes:", err));
  }, []);

  const handleSubmit = async () => {
    if (!userName || !selectedBike) {
      alert("Please enter your name and select a bike!");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/update_grafana`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_name: userName, equipment_id: selectedBike }),
      });

      if (response.ok) {
        alert("✅ Selection saved and updated in Grafana!");
      } else {
        alert("❌ Failed to update Grafana.");
      }
    } catch (error) {
      console.error("❌ Error:", error);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      <h1 className="text-2xl font-bold mb-4">Select Your Bike</h1>

      <input
        type="text"
        placeholder="Enter Your Name"
        className="p-2 border border-gray-300 text-black mb-3"
        value={userName}
        onChange={(e) => setUserName(e.target.value)}
      />

      <select
        className="p-2 border border-gray-300 text-black"
        value={selectedBike}
        onChange={(e) => setSelectedBike(e.target.value)}
      >
        <option value="">-- Select a Bike --</option>
        {bikes.map((bike) => (
          <option key={bike.equipment_id} value={bike.equipment_id}>
            {bike.name} (ID: {bike.equipment_id})
          </option>
        ))}
      </select>

      <button
        onClick={handleSubmit}
        className={`mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white font-bold rounded ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
        disabled={loading}
      >
        {loading ? "Saving..." : "Save Selection"}
      </button>
    </div>
  );
};

export default App;
