import {
  Users,
  Ticket,
  Clock,
  Wifi,
  Activity,
  Pause,
  Power,
  Timer,
} from 'lucide-react';
import { useNavigate } from 'react-router';
import { Layout } from '@/components/Layout';
import { StatCard } from '@/components/StatCard';
import { StatusBadge } from '@/components/StatusBadge';
import { usePolling } from '@/hooks/usePolling';
import { apiGet, apiPost } from '@/hooks/useApi';

import { Button } from '@/components/ui/button';
import type { DashboardStats, Session, ActivityItem } from '@/types';

export function Dashboard() {
  const navigate = useNavigate();

  const { data: stats, refresh: refreshStats } = usePolling<DashboardStats>(
    () => apiGet('/api/dashboard/stats'),
    10000
  );

  const { data: sessions } = usePolling<{ sessions: Session[]; total: number }>(
    () => apiGet('/api/sessions?status=active'),
    10000
  );

  const { data: activity } = usePolling<ActivityItem[]>(
    () => apiGet('/api/dashboard/activity?limit=10'),
    10000
  );

  const handleKick = async (sessionId: number) => {
    try {
      await apiPost(`/api/sessions/${sessionId}/terminate`);
      refreshStats();
    } catch {
      // handled by api
    }
  };

  const handlePause = async (sessionId: number) => {
    try {
      await apiPost(`/api/sessions/${sessionId}/pause`);
      refreshStats();
    } catch {}
  };

  const handleExtend = async (sessionId: number) => {
    try {
      await apiPost(`/api/sessions/${sessionId}/extend`, { additional_minutes: 30 });
      refreshStats();
    } catch {}
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${Math.round(minutes)}m`;
    if (minutes < 1440) return `${(minutes / 60).toFixed(1)}h`;
    return `${(minutes / 1440).toFixed(1)}d`;
  };

  const formatTime = (iso: string) => {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-zinc-400 mt-0.5">Monitor your WiFi network in real-time</p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              stats?.system_status === 'online' ? 'bg-emerald-400 animate-pulse' :
              stats?.system_status === 'maintenance' ? 'bg-amber-400' : 'bg-red-400'
            }`} />
            <span className="text-sm text-zinc-400 capitalize">{stats?.system_status || 'Loading...'}</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Active Sessions"
            value={stats?.active_sessions ?? '...'}
            icon={Users}
            color="indigo"
            subtitle={`${sessions?.sessions.filter(s => s.is_paused).length || 0} paused`}
          />
          <StatCard
            title="Available Vouchers"
            value={stats?.available_vouchers ?? '...'}
            icon={Ticket}
            color="emerald"
            subtitle={`${stats?.used_today || 0} used today`}
          />
          <StatCard
            title="Total Users"
            value={stats?.total_users ?? '...'}
            icon={Wifi}
            color="blue"
          />
          <StatCard
            title="Expired Today"
            value={stats?.expired_sessions_today ?? '...'}
            icon={Clock}
            color="amber"
          />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Sessions */}
          <div className="lg:col-span-2 bg-[#111118] border border-[#2a2a3a] rounded-xl">
            <div className="px-5 py-4 border-b border-[#2a2a3a] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                <h2 className="text-sm font-semibold text-white">Active Sessions</h2>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-indigo-400 hover:text-indigo-300"
                onClick={() => navigate('/users')}
              >
                View All
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#2a2a3a]">
                    <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">MAC Address</th>
                    <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">IP</th>
                    <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden md:table-cell">Login</th>
                    <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Remaining</th>
                    <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Status</th>
                    <th className="text-right text-xs font-medium text-zinc-400 px-5 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(!sessions || !sessions.sessions.length) ? (
                    <tr>
                      <td colSpan={6} className="text-center text-sm text-zinc-500 py-8">
                        {sessions ? 'No active sessions' : 'Loading...'}
                      </td>
                    </tr>
                  ) : (
                    sessions.sessions.map((session) => (
                      <tr key={session.id} className="border-b border-[#2a2a3a]/50 hover:bg-white/[0.02]">
                        <td className="px-5 py-3">
                          <span className="font-mono text-xs text-white">{session.mac_address}</span>
                        </td>
                        <td className="px-5 py-3 text-xs text-zinc-400">{session.ip_address}</td>
                        <td className="px-5 py-3 text-xs text-zinc-400 hidden md:table-cell">
                          {formatTime(session.login_time)}
                        </td>
                        <td className="px-5 py-3">
                          <span className="text-xs text-zinc-300">
                            {session.remaining_minutes !== undefined
                              ? formatDuration(session.remaining_minutes)
                              : '--'}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <StatusBadge status={session.status} />
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={() => handlePause(session.id)}
                              className="p-1.5 rounded-md text-amber-400 hover:bg-amber-500/10 transition-colors"
                              title="Pause"
                            >
                              <Pause className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleExtend(session.id)}
                              className="p-1.5 rounded-md text-blue-400 hover:bg-blue-500/10 transition-colors"
                              title="Extend +30min"
                            >
                              <Timer className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleKick(session.id)}
                              className="p-1.5 rounded-md text-red-400 hover:bg-red-500/10 transition-colors"
                              title="Kick"
                            >
                              <Power className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Activity Feed */}
          <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl">
            <div className="px-5 py-4 border-b border-[#2a2a3a]">
              <h2 className="text-sm font-semibold text-white">Recent Activity</h2>
            </div>
            <div className="p-4 space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
              {(!activity || !activity.length) ? (
                <p className="text-sm text-zinc-500 text-center py-4">
                  {activity ? 'No activity yet' : 'Loading...'}
                </p>
              ) : (
                activity.map((item) => (
                  <div key={item.id} className="flex gap-3 items-start">
                    <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${
                      item.level === 'error' ? 'bg-red-400' :
                      item.level === 'warning' ? 'bg-amber-400' :
                      item.category === 'auth' ? 'bg-blue-400' :
                      item.category === 'voucher' ? 'bg-emerald-400' :
                      'bg-indigo-400'
                    }`} />
                    <div className="min-w-0">
                      <p className="text-xs text-zinc-300 leading-relaxed">{item.message}</p>
                      <p className="text-[10px] text-zinc-500 mt-0.5">
                        {new Date(item.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
