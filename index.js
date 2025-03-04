import { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import axios from "axios";

export default function Home() {
  const [ticker, setTicker] = useState("");
  const [chartData, setChartData] = useState(null);
  const [valuation, setValuation] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    if (!ticker) return;
    setLoading(true);
    try {
      const response = await axios.post("/api/analyze", { ticker });
      setChartData(response.data.chartData);
      setValuation(response.data.valuation);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">AI-Powered Stock Valuation</h1>
      <input
        type="text"
        placeholder="Enter Stock Ticker (e.g., AAPL)"
        className="p-2 border rounded w-full mb-4"
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
      />
      <button
        onClick={fetchData}
        className="bg-blue-500 text-white px-4 py-2 rounded"
        disabled={loading}
      >
        {loading ? "Analyzing..." : "Get Valuation"}
      </button>
      
      {chartData && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold">EPS vs Price Chart</h2>
          <Line data={chartData} />
        </div>
      )}
      
      {valuation && (
        <div className="mt-6 p-4 border rounded">
          <h2 className="text-xl font-semibold">Valuation Summary</h2>
          <p><strong>Intrinsic Value:</strong> ${valuation.fairValue.toFixed(2)}</p>
          <p><strong>Expected Growth:</strong> {valuation.growthRate}% per year</p>
        </div>
      )}
    </div>
  );
}
