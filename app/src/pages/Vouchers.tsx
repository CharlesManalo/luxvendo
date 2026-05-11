import { useState } from 'react';
import {
  Ticket,
  Plus,
  Search,
  Copy,
  Trash2,
  Ban,
  Download,
  Check,
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { StatusBadge } from '@/components/StatusBadge';
import { usePolling } from '@/hooks/usePolling';
import { apiGet, apiPost, apiDelete } from '@/hooks/useApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { Voucher } from '@/types';

const DURATIONS = [
  { value: '30', label: '30 Minutes' },
  { value: '60', label: '1 Hour' },
  { value: '180', label: '3 Hours' },
  { value: '1440', label: '1 Day' },
];

export function VouchersPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [generateOpen, setGenerateOpen] = useState(false);
  const [genDuration, setGenDuration] = useState('60');
  const [genQuantity, setGenQuantity] = useState(1);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const { data, refresh } = usePolling<{ vouchers: Voucher[]; total: number }>(
    () => apiGet(`/api/vouchers?${
      statusFilter ? `status=${statusFilter}&` : ''
    }${search ? `search=${encodeURIComponent(search)}&` : ''}limit=200`),
    15000
  );

  const handleGenerate = async () => {
    try {
      await apiPost('/api/vouchers/bulk-generate', {
        duration_minutes: parseInt(genDuration),
        quantity: genQuantity,
      });
      setGenerateOpen(false);
      setGenQuantity(1);
      refresh();
    } catch {
      // handled
    }
  };

  const handleDisable = async (id: number) => {
    try {
      await apiPost(`/api/vouchers/${id}/disable`);
      refresh();
    } catch {}
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this voucher permanently?')) return;
    try {
      await apiDelete(`/api/vouchers/${id}`);
      refresh();
    } catch {}
  };

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleExport = () => {
    if (!data?.vouchers.length) return;
    const csv = [
      'Code,Duration,Status,Created,Used At,Used By MAC,Used By IP',
      ...data.vouchers.map(v =>
        `${v.code},${v.duration_minutes},${v.status},"${v.created_at}","${v.used_at || ''}","${v.used_by_mac || ''}","${v.used_by_ip || ''}"`
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vouchers-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString() + ' ' + new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (mins: number) => {
    if (mins < 60) return `${mins} min`;
    if (mins < 1440) return `${mins / 60} hr`;
    return `${mins / 1440} day`;
  };

  return (
    <Layout>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white">Vouchers</h1>
            <p className="text-sm text-zinc-400 mt-0.5">
              {data?.total ?? 0} total vouchers
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="border-[#2a2a3a] bg-[#1a1a24] text-zinc-300 hover:bg-[#2a2a3a]"
            >
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Dialog open={generateOpen} onOpenChange={setGenerateOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="bg-indigo-500 hover:bg-indigo-600 text-white">
                  <Plus className="w-4 h-4 mr-2" />
                  Generate
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#111118] border-[#2a2a3a] text-white max-w-sm">
                <DialogHeader>
                  <DialogTitle className="text-white">Generate Vouchers</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 pt-2">
                  <div>
                    <label className="text-sm text-zinc-400 block mb-1.5">Duration</label>
                    <Select value={genDuration} onValueChange={setGenDuration}>
                      <SelectTrigger className="bg-[#1a1a24] border-[#2a2a3a] text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-[#1a1a24] border-[#2a2a3a]">
                        {DURATIONS.map(d => (
                          <SelectItem key={d.value} value={d.value} className="text-white">
                            {d.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm text-zinc-400 block mb-1.5">Quantity</label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={genQuantity}
                      onChange={(e) => setGenQuantity(parseInt(e.target.value) || 1)}
                      className="bg-[#1a1a24] border-[#2a2a3a] text-white"
                    />
                  </div>
                  <Button
                    onClick={handleGenerate}
                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                  >
                    Generate {genQuantity > 1 ? `${genQuantity} Vouchers` : '1 Voucher'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input
              placeholder="Search voucher code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-[#111118] border-[#2a2a3a] text-white placeholder:text-zinc-600"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40 bg-[#111118] border-[#2a2a3a] text-white">
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent className="bg-[#1a1a24] border-[#2a2a3a]">
              <SelectItem value="">All Statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="used">Used</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
              <SelectItem value="disabled">Disabled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Table */}
        <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#2a2a3a] bg-[#0a0a0f]/50">
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Code</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Duration</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden md:table-cell">Created</th>
                  <th className="text-left text-xs font-medium text-zinc-400 px-5 py-3 hidden lg:table-cell">Used By</th>
                  <th className="text-right text-xs font-medium text-zinc-400 px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(!data || !data.vouchers.length) ? (
                  <tr>
                    <td colSpan={6} className="text-center text-sm text-zinc-500 py-12">
                      {data ? 'No vouchers found' : 'Loading...'}
                    </td>
                  </tr>
                ) : (
                  data.vouchers.map((voucher) => (
                    <tr
                      key={voucher.id}
                      className="border-b border-[#2a2a3a]/50 hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <Ticket className="w-3.5 h-3.5 text-zinc-500" />
                          <span className="font-mono text-sm text-white">{voucher.code}</span>
                          <button
                            onClick={() => handleCopy(voucher.code)}
                            className="text-zinc-500 hover:text-indigo-400 transition-colors"
                          >
                            {copiedCode === voucher.code ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-sm text-zinc-300">
                        {formatDuration(voucher.duration_minutes)}
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={voucher.status} />
                      </td>
                      <td className="px-5 py-3 text-xs text-zinc-400 hidden md:table-cell">
                        {formatDate(voucher.created_at)}
                      </td>
                      <td className="px-5 py-3 hidden lg:table-cell">
                        {voucher.used_by_mac ? (
                          <span className="font-mono text-xs text-zinc-300">{voucher.used_by_mac}</span>
                        ) : (
                          <span className="text-xs text-zinc-500">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center justify-end gap-1">
                          {voucher.status === 'active' && (
                            <button
                              onClick={() => handleDisable(voucher.id)}
                              className="p-1.5 rounded-md text-amber-400 hover:bg-amber-500/10 transition-colors"
                              title="Disable"
                            >
                              <Ban className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(voucher.id)}
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
    </Layout>
  );
}
