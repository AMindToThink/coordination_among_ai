import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';

const PerformanceBarGraph = () => {
  const data = [
    { name: '4o-Mini Collaboration', value: 92 },
    { name: '4o-Mini', value: 90 },
    { name: '3 Saboteurs', value: 20.27 },
    { name: 'Expected Saboteurs', value: 8 },
    { name: 'Worst-Case Collaborators vs Saboteurs', value: 86 }
  ];

  return (
    <div className="w-full h-96 mx-auto">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 100
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            angle={-45} 
            textAnchor="end" 
            height={100} 
            interval={0}
          />
          <YAxis 
            label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} 
            domain={[0, 100]}
          />
          <Tooltip formatter={(value) => [`${value}%`, 'Value']} />
          <Legend />
          <ReferenceLine y={25} label="Random Baseline" stroke="#ff7300" strokeDasharray="3 3" />
          <Bar dataKey="value" fill="#8884d8" name="Performance (%)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceBarGraph;
