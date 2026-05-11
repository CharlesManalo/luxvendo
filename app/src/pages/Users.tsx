import { useState } from 'react';
import {
  Search,
  Shield,
  ShieldOff,
  Trash2,
  Wifi,
  WifiOff,
  Monitor,
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { usePolling } from '@/hooks/usePolling';
import { apiGet, apiPost, apiDelete } from '@/hooks/useApi';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { User } from '@/types';

interface UserDetail extends User {
  session_history: {
    id: number;
    login_time: string;
    expiry_time: string | null;
    status: string;
    data_usage_mb: number;
  }[];
}

export function UsersPage() {
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data, refresh } = usePolling<{ users: User[]; total: number }>(
    () => apiGet(`/api/users?${search ? `search=${encodeURIComponent(search)}&` : ''}limit=200`),
    15000
  );

  const handleViewDetail = async (userId: number) => {
    try {
      const detail = await apiGet<UserDetail>(`/api/users/${userId}`);
      setSelectedUser(detail);
      setDetailOpen(true);
    } catch {}
  };

  const handleBlacklist = async (id: number) => {
    try {
      await apiPost(`/api/users/${id}/blacklist`);
      refresh();
    } catch {}
  };

  const handleUnblacklist = async (id: number) => {
    try {
      await apiPost(`/api/users/${id}/unblacklist`);
      refresh();
    } catch {}
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this user record?')) return;
    try {
      await apiDelete(`/api/users/${id}`);
      refresh();
    } catch {}
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString() + ' ' + new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (mins: number) => {
    if (mins < 60) return `${mins} min`;
    if (mins < 1440) return `${Math.round(mins / 60)} hr`;
    return `${(mins / 1440).toFixed(1)} day`;
  };

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Users</h1>
            <p className="text-sm text-zinc-400 mt-0.5">
              {data?.total ?? 0} connected devices
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <Input
            placeholder="Search MAC, IP, device..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-[#111118] border-[#2a2a3a] text-white placeholder:text-zinc-600"
          />
        </div>

        {/* Table */}
        <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#2a2a3a] bg-[#0a0a0f]/50">
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">MAC Address</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden md:table-cell">IP Address</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden lg:table-cell">Device</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden lg:table-cell">Sessions</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden md:table-cell">Last Seen</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Status</th>
                  <th className="text-right text-xs font-medium text-zinc-400 px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(!data || !data.users.length) ? (
                  <tr>
                    <td colSpan={7} className="text-center text-sm text-zinc-500 py-12">
                      {data ? 'No users found' : 'Loading...'}
                    </td>
                  </tr>
                ) : (
                  data.users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-[#2a2a3a]/50 hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          {user.is_blacklisted ? (
                            <WifiOff className="w-3.5 h-3.5 text-red-400" />
                          ) : (
                            <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                          )}
                          <span className="font-mono text-sm text-white">{user.mac_address}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-sm text-zinc-300 hidden md:table-cell">{user.ip_address}</td>
                      <td className="px-5 py-3 hidden lg:table-cell">
                        {user.device_name ? (
                          <span className="text-sm text-zinc-300">{user.device_name}</span>
                        ) : (
                          <span className="text-xs text-zinc-500">Unknown</span>
                        )}
                      </td>
                      <td className="px-5 py-3 hidden lg:table-cell">
                        <span className="text-sm text-zinc-300">{user.total_sessions}</span>
                        {user.total_time_used > 0 && (
                          <span className="text-xs text-zinc-500 ml-2">
                            ({formatDuration(user.total_time_used)})
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-xs text-zinc-400 hidden md:table-cell">
                        {formatDate(user.last_seen)}
                      </td>
                      <td className="px-5 py-3">
                        {user.is_blacklisted ? (
                          <span className="status-badge status-expired">
                            <ShieldOff className="w-3 h-3 mr-1" />
                            Blocked
                          </span>
                        ) : (
                          <span className="status-badge status-active">Active</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleViewDetail(user.id)}
                            className="p-1.5 rounded-md text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                            title="View Details"
                          >
                            <Monitor className="w-3.5 h-3.5" />
                          </button>
                          {user.is_blacklisted ? (
                            <button
                              onClick={() => handleUnblacklist(user.id)}
                              className="p-1.5 rounded-md text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                              title="Unblock"
                            >
                              <Shield className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleBlacklist(user.id)}
                              className="p-1.5 rounded-md text-amber-400 hover:bg-amber-500/10 transition-colors"
                              title="Block"
                            >
                              <ShieldOff className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(user.id)}
                            className="p-1.5 rounded-md text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
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
      </div>

      {/* User Detail Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="bg-[#111118] border-[#2a2a3a] text-white max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Monitor className="w-5 h-5 text-indigo-400" />
              User Details
            </DialogTitle>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#0a0a0f] rounded-lg p-3">
                  <p className="text-xs text-zinc-400">MAC Address</p>
                  <p className="font-mono text-sm text-white mt-1">{selectedUser.mac_address}</p>
                </div>
                <div className="bg-[#0a0a0f] rounded-lg p-3">
                  <p className="text-xs text-zinc-400">IP Address</p>
                  <p className="font-mono text-sm text-white mt-1">{selectedUser.ip_address}</p>
                </div>
                <div className="bg-[#0a0a0f] rounded-lg p-3">
                  <p className="text-xs text-zinc-400">Device</p>
                  <p className="text-sm text-white mt-1">{selectedUser.device_name || 'Unknown'}</p>
                </div>
                <div className="bg-[#0a0a0f] rounded-lg p-3">
                  <p className="text-xs text-zinc-400">Total Sessions</p>
                  <p className="text-sm text-white mt-1">{selectedUser.total_sessions}</p>
                </div>
              </div>

              <div className="bg-[#0a0a0f] rounded-lg p-3">
                <p className="text-xs text-zinc-400 mb-2">Time Online</p>
                <p className="text-sm text-white">{formatDuration(selectedUser.total_time_used)}</p>
              </div>

              <div>
                <p className="text-xs text-zinc-400 mb-2">Session History</p>
                <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
                  {selectedUser.session_history?.map((s) => (
                    <div key={s.id} className="bg-[#0a0a0f] rounded-lg p-2.5 flex items-center justify-between">
                      <div>
                        <p className="text-xs text-zinc-300">
                          {new Date(s.login_time).toLocaleDateString()}
                        </p>
                        <p className="text-[10px] text-zinc-500 mt-0.5">{s.status}</p>
                      </div>
                      {s.data_usage_mb > 0 && (
                        <span className="text-xs text-zinc-400">{s.data_usage_mb.toFixed(1)} MB</span>
                      )}
                    </div>
                  )) || (
                    <p className="text-xs text-zinc-500 py-2">No session history</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
