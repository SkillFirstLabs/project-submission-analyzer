import React from 'react';
import { 
  ResponsiveContainer, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  RadialBarChart, 
  RadialBar,
  Cell
} from 'recharts';

// Radial Score Gauge Chart
export const OverallScoreGauge = ({ score }) => {
  const data = [
    { name: 'Score', value: score, fill: '#5c4fe5' },
    { name: 'Remaining', value: 100 - score, fill: '#1b203e' }
  ];

  return (
    <div className="relative w-36 h-36 flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart 
          cx="50%" 
          cy="50%" 
          innerRadius="75%" 
          outerRadius="100%" 
          barSize={12} 
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <RadialBar
            minAngle={15}
            background
            clockWise
            dataKey="value"
            cornerRadius={10}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </RadialBar>
        </RadialBarChart>
      </ResponsiveContainer>
      
      {/* Inner score label */}
      <div className="absolute flex flex-col items-center justify-center select-none">
        <span className="text-3xl font-extrabold text-white font-mono leading-none">{score}</span>
        <span className="text-[10px] font-bold text-dark-400 uppercase tracking-widest mt-1">Overall</span>
      </div>
    </div>
  );
};

// Authenticity Radar Chart
export const AuthenticityRadar = ({ breakdown }) => {
  if (!breakdown) return null;

  const data = [
    { subject: 'Backend', A: breakdown.backend, fullMark: 100 },
    { subject: 'Frontend', A: breakdown.frontend, fullMark: 100 },
    { subject: 'Database', A: breakdown.database, fullMark: 100 },
    { subject: 'Auth', A: breakdown.authentication, fullMark: 100 },
    { subject: 'Business Logic', A: breakdown.businessLogic, fullMark: 100 },
    { subject: 'Deployment', A: breakdown.deployment, fullMark: 100 }
  ];

  return (
    <div className="w-full h-64 font-sans text-xs">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="#272d54" strokeWidth={1} />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 500 }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={{ fill: '#64748b' }}
            stroke="#272d54"
          />
          <Radar
            name="Authenticity"
            dataKey="A"
            stroke="#5c4fe5"
            fill="#5c4fe5"
            fillOpacity={0.25}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
