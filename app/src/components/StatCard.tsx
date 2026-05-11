import { type LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: 'indigo' | 'emerald' | 'amber' | 'blue' | 'red' | 'purple';
  subtitle?: string;
}

const colorMap = {
  indigo: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  red: 'bg-red-500/10 text-red-400 border-red-500/20',
  purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

export function StatCard({ title, value, icon: Icon, color, subtitle }: StatCardProps) {
  return (
    <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-zinc-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-xs text-zinc-500">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-lg border ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
