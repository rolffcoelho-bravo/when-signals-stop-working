import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, AlertTriangle, ShieldCheck, TrendingDown } from 'lucide-react';

export default function App() {
  const [data, setData] = useState([]);
  const [current, setCurrent] = useState({
    symbol: 'SOL/USDT:USDT',
    order_book_imbalance: 1.0,
    funding_rate: 0,
    crash_hazard_percent: 0,
    status: 'SAFE'
  });
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/feed');
        if (!res.ok) return;
        
        const json = await res.json();
        setCurrent(json);
        
        setData(prev => {
          const newData = [...prev, {
            time: new Date().toLocaleTimeString([], { hour12: false }),
            hazard: json.crash_hazard_percent,
            imbalance: json.order_book_imbalance
          }];
          return newData.slice(-30); // keep last 30 points
        });
      } catch (err) {
        console.error("Failed to fetch V5 feed", err);
      }
    };
    
    // Poll every 3 seconds for the live feel
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const isDanger = current.status === 'DANGER';

  return (
    <div className="min-h-screen bg-dark text-white p-8">
      
      {/* Header */}
      <header className="flex items-center justify-between mb-8 pb-4 border-b border-gray-800">
        <div>
          <h1 className="text-3xl font-bold text-primary flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" />
            ShockBridge V5
          </h1>
          <p className="text-gray-400 mt-1">Live Quantitative Microstructure Feed (Forward Testing)</p>
        </div>
        
        {/* Status Badge */}
        <div className={`px-6 py-3 rounded-full font-bold flex items-center gap-2 border ${
            isDanger ? 'bg-danger/20 text-danger border-danger pulse-danger' 
            : current.status === 'WARNING' ? 'bg-warning/20 text-warning border-warning'
            : 'bg-safe/20 text-safe border-safe'
          }`}>
          {isDanger ? <AlertTriangle className="w-5 h-5"/> : <ShieldCheck className="w-5 h-5"/>}
          {current.status}
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Metric Cards */}
        <div className="flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">V5 Crash Hazard</h3>
            <div className="flex items-end gap-2">
              <span className={`text-5xl font-black ${isDanger ? 'text-danger' : 'text-white'}`}>
                {current.crash_hazard_percent}%
              </span>
            </div>
            <p className="text-gray-500 text-sm mt-2">Probability of imminent liquidation cascade</p>
          </div>
          
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Order Book Imbalance (L2)</h3>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-bold text-white">{current.order_book_imbalance}x</span>
            </div>
            <p className="text-gray-500 text-sm mt-2">Bids: {current.total_bids} | Asks: {current.total_asks}</p>
          </div>
          
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Funding Rate</h3>
            <div className="flex items-end gap-2">
              <span className={`text-4xl font-bold ${current.funding_rate < 0 ? 'text-danger' : 'text-primary'}`}>
                {current.funding_rate.toFixed(6)}
              </span>
            </div>
            <p className="text-gray-500 text-sm mt-2">Perpetual Swap Premium</p>
          </div>
        </div>
        
        {/* Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl flex flex-col">
          <div className="flex items-center gap-2 mb-6">
            <TrendingDown className="w-6 h-6 text-gray-400" />
            <h2 className="text-xl font-bold">Real-Time Hazard Trajectory</h2>
          </div>
          
          <div className="flex-1 min-h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
                <XAxis dataKey="time" stroke="#6b7280" />
                <YAxis stroke="#6b7280" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#151520', border: '1px solid #374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="hazard" 
                  name="Crash Hazard %"
                  stroke="#ef4444" 
                  strokeWidth={3}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="imbalance" 
                  name="L2 Imbalance"
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
      </div>
    </div>
  );
}
