import React from 'react';

interface SimilarityGaugeProps {
  score: number; // 0.0 to 1.0
  size?: number;
}

export const SimilarityGauge: React.FC<SimilarityGaugeProps> = ({ score, size = 180 }) => {
  const percentage = Math.round(score * 100);
  const radius = size * 0.4;
  const strokeWidth = size * 0.08;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Determine color based on risk levels
  let color = 'stroke-emerald-500 text-emerald-400';
  let bgColor = 'bg-emerald-500/10';
  let riskText = 'Safe';
  
  if (percentage >= 30) {
    color = 'stroke-rose-500 text-rose-400';
    bgColor = 'bg-rose-500/10';
    riskText = 'High Risk';
  } else if (percentage >= 15) {
    color = 'stroke-amber-500 text-amber-400';
    bgColor = 'bg-amber-500/10';
    riskText = 'Moderate';
  }

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-slate-900/60 border border-slate-800 rounded-3xl backdrop-blur-xl shadow-2xl">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Track Circle */}
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className="stroke-slate-800 fill-none"
            strokeWidth={strokeWidth}
          />
          {/* Progress Circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className={`fill-none transition-all duration-1000 ease-out ${color}`}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        {/* Percentage Label in Center */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold tracking-tight text-white">{percentage}%</span>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Similarity</span>
        </div>
      </div>
      
      {/* Risk Badge */}
      <div className={`mt-4 px-4 py-1.5 rounded-full text-xs font-bold tracking-wide uppercase ${bgColor} ${color.split(' ')[1]}`}>
        {riskText}
      </div>
    </div>
  );
};
