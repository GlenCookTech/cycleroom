
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const App = () => {
    const [bikes, setBikes] = useState([]);
    const [selectedBike, setSelectedBike] = useState('');
    const [selectedNumber, setSelectedNumber] = useState('');
    const [showConfirmation, setShowConfirmation] = useState(false);

    useEffect(() => {
        // Fetch available bikes from FastAPI
        const fetchBikes = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/bikes');
                setBikes(Object.entries(response.data));
            } catch (error) {
                console.error('Error fetching bikes:', error);
            }
        };
        fetchBikes();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (selectedBike && selectedNumber) {
            try {
                await axios.post('http://localhost:8000/api/bike-selection', {
                    bike_number: selectedNumber,
                    device_address: selectedBike
                });
                setShowConfirmation(true);
                setTimeout(() => setShowConfirmation(false), 3000);
            } catch (error) {
                console.error('Error saving bike selection:', error);
            }
        } else {
            alert('Please select a bike and enter a number.');
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-6">Bike Selection</h1>
            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 w-11/12 md:w-1/2 lg:w-1/3">
                <label className="block text-gray-700 font-bold mb-2">
                    Select a Bike:
                    <select
                        value={selectedBike}
                        onChange={(e) => setSelectedBike(e.target.value)}
                        className="block w-full mt-2 p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    >
                        <option value="">Select a bike</option>
                        {bikes.map(([address, info]) => (
                            <option key={address} value={address}>
                                {info.device_name} ({address})
                            </option>
                        ))}
                    </select>
                </label>
                <label className="block text-gray-700 font-bold mt-4 mb-2">
                    Enter Bike Number:
                    <input
                        type="text"
                        value={selectedNumber}
                        onChange={(e) => setSelectedNumber(e.target.value)}
                        placeholder="e.g. 1, 2, 3..."
                        className="block w-full mt-2 p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                </label>
                <button
                    type="submit"
                    className="w-full mt-6 bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 transition-all duration-300"
                >
                    Save Selection
                </button>
            </form>

            {showConfirmation && (
                <div className="fixed bottom-5 right-5 bg-green-500 text-white p-4 rounded-lg shadow-lg">
                    ✅ Bike selection saved!
                </div>
            )}
        </div>
    );
};

export default App;
