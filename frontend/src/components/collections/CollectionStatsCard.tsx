/**
 * Collection Stats Card - Apple Design Language
 * Enhanced with color variants and better visual design
 */

'use client';

import React from 'react';
import { FolderOpen, Layers, Award, Clock, BarChart3 } from 'lucide-react';

interface CollectionStatsCardProps {
  label: string;
  value: number | string;
  subtext?: string;
  icon: string;
  color?: string;
}

const COLOR_STYLES: Record<string, { bg: string; icon: string; value: string }> = {
  blue: { bg: 'bg-blue-50', icon: 'text-blue-600', value: 'text-blue-600' },
  purple: { bg: 'bg-purple-50', icon: 'text-purple-600', value: 'text-purple-600' },
  green: { bg: 'bg-green-50', icon: 'text-green-600', value: 'text-green-600' },
  orange: { bg: 'bg-orange-50', icon: 'text-orange-600', value: 'text-orange-600' },
  red: { bg: 'bg-red-50', icon: 'text-red-600', value: 'text-red-600' },
};

export default function CollectionStatsCard({ label, value, subtext, icon, color = 'blue' }: CollectionStatsCardProps) {
  const styles = COLOR_STYLES[color] || COLOR_STYLES.blue;
  
  const getIcon = () => {
    const iconClass = `w-5 h-5 ${styles.icon}`;
    switch (icon) {
      case 'folder': return <FolderOpen className={iconClass} />;
      case 'layers': return <Layers className={iconClass} />;
      case 'award': return <Award className={iconClass} />;
      case 'clock': return <Clock className={iconClass} />;
      case 'chart': return <BarChart3 className={iconClass} />;
      default: return <FolderOpen className={iconClass} />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
        <div className={`p-2 rounded-lg ${styles.bg}`}>
          {getIcon()}
        </div>
      </div>
      {typeof value === 'number' ? (
        <div className="flex items-baseline gap-1">
          <span className={`text-2xl font-bold ${styles.value}`}>{value}</span>
          {subtext && (
            <span className="text-xs text-gray-500 truncate max-w-[100px]">— {subtext}</span>
          )}
        </div>
      ) : (
        <div>
          <span className={`text-base font-semibold ${styles.value} block`}>{value}</span>
          {subtext && (
            <span className="text-xs text-gray-500 block mt-0.5">{subtext}</span>
          )}
        </div>
      )}
    </div>
  );
}
