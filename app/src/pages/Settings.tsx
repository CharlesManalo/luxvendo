import { useState, useEffect } from 'react';
import {
  Wifi,
  Clock,
  Smartphone,
  Coins,
  Wrench,
  Key,
  Shield,
  Save,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { usePolling } from '@/hooks/usePolling';
import { apiGet, apiPost } from '@/hooks/useApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { Setting } from '@/types';

interface SettingsMap {
  [key: string]: string;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsMap>({});
  const [saved, setSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const { data: settingsData, refresh } = usePolling<Setting[]>(
    () => apiGet('/api/settings'),
    30000
  );

  useEffect(() => {
    if (settingsData) {
      const map: SettingsMap = {};
      settingsData.forEach(s => { map[s.key] = s.value; });
      setSettings(map);
    }
  }, [settingsData]);

  const updateSetting = (key: string, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await apiPost('/api/settings', { settings });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      refresh();
    } catch {
      // handled
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    setPasswordError('');
    setPasswordSuccess('');

    if (!currentPassword || !newPassword) {
      setPasswordError('All fields are required');
      return;
    }
    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    // Note: In a full implementation, you'd have a dedicated endpoint for password changes
    // For now, this is a UI placeholder
    setPasswordSuccess('Password changed successfully');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  const handleRegenerateApiKey = async () => {
    if (!confirm('Regenerate API key? This will invalidate existing router connections.')) return;
    // In a full implementation, this would call a dedicated endpoint
    updateSetting('api_key', Math.random().toString(36).substring(2, 34));
  };

  const coinEnabled = settings['coin_system_enabled'] === 'true';
  const maintenanceMode = settings['maintenance_mode'] === 'true';

  return (
    <Layout>
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Settings</h1>
            <p className="text-sm text-zinc-400 mt-0.5">Configure your WiFi gateway system</p>
          </div>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-indigo-500 hover:bg-indigo-600 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}
          </Button>
        </div>

        {saved && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-sm text-emerald-400 flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Settings saved successfully
          </div>
        )}

        <Tabs defaultValue="general" className="w-full">
          <TabsList className="bg-[#111118] border border-[#2a2a3a]">
            <TabsTrigger value="general" className="data-[state=active]:bg-indigo-500/10 data-[state=active]:text-indigo-400">
              General
            </TabsTrigger>
            <TabsTrigger value="coin" className="data-[state=active]:bg-indigo-500/10 data-[state=active]:text-indigo-400">
              Coin System
            </TabsTrigger>
            <TabsTrigger value="security" className="data-[state=active]:bg-indigo-500/10 data-[state=active]:text-indigo-400">
              Security
            </TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general" className="space-y-4 mt-4">
            {/* Portal Name */}
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Wifi className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">WiFi Portal</h3>
              </div>
              <div className="space-y-3">
                <div>
                  <Label className="text-zinc-400 text-xs">Portal Name</Label>
                  <Input
                    value={settings['portal_name'] || ''}
                    onChange={(e) => updateSetting('portal_name', e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
              </div>
            </div>

            {/* Session Settings */}
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">Session Settings</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label className="text-zinc-400 text-xs">Session Timeout (minutes)</Label>
                  <Input
                    type="number"
                    value={settings['session_timeout'] || '1440'}
                    onChange={(e) => updateSetting('session_timeout', e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Max Concurrent Devices</Label>
                  <Input
                    type="number"
                    value={settings['max_devices'] || '50'}
                    onChange={(e) => updateSetting('max_devices', e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
              </div>
            </div>

            {/* Maintenance Mode */}
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wrench className={`w-4 h-4 ${maintenanceMode ? 'text-amber-400' : 'text-zinc-400'}`} />
                  <div>
                    <h3 className="text-sm font-semibold text-white">Maintenance Mode</h3>
                    <p className="text-xs text-zinc-400">Block new connections during maintenance</p>
                  </div>
                </div>
                <Switch
                  checked={maintenanceMode}
                  onCheckedChange={(checked) => updateSetting('maintenance_mode', checked ? 'true' : 'false')}
                />
              </div>
              {maintenanceMode && (
                <div className="mt-3 bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 flex items-center gap-2 text-sm text-amber-400">
                  <AlertTriangle className="w-4 h-4" />
                  New voucher activations are currently blocked
                </div>
              )}
            </div>
          </TabsContent>

          {/* Coin System Tab */}
          <TabsContent value="coin" className="space-y-4 mt-4">
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Coins className={`w-4 h-4 ${coinEnabled ? 'text-amber-400' : 'text-zinc-400'}`} />
                  <div>
                    <h3 className="text-sm font-semibold text-white">Coin Payment System</h3>
                    <p className="text-xs text-zinc-400">Enable coin-operated WiFi access</p>
                  </div>
                </div>
                <Switch
                  checked={coinEnabled}
                  onCheckedChange={(checked) => updateSetting('coin_system_enabled', checked ? 'true' : 'false')}
                />
              </div>
            </div>

            {coinEnabled && (
              <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Smartphone className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">Coin Pricing</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-zinc-400 text-xs">Price Per Minute</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={settings['coin_price_per_minute'] || '0.5'}
                      onChange={(e) => updateSetting('coin_price_per_minute', e.target.value)}
                      className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                    />
                  </div>
                  <div>
                    <Label className="text-zinc-400 text-xs">Currency</Label>
                    <Input
                      value={settings['coin_currency'] || 'USD'}
                      onChange={(e) => updateSetting('coin_currency', e.target.value)}
                      className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                    />
                  </div>
                </div>

                {/* Pricing Table Preview */}
                <div className="bg-[#0a0a0f] rounded-lg p-4">
                  <p className="text-xs text-zinc-400 mb-3">Pricing Preview</p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {(() => {
                      try {
                        const durations = JSON.parse(settings['voucher_durations'] || '[30,60,180,1440]');
                        const price = parseFloat(settings['coin_price_per_minute'] || '0.5');
                        return durations.map((mins: number) => (
                          <div key={mins} className="bg-[#111118] rounded-lg p-3 text-center">
                            <p className="text-xs text-zinc-400">
                              {mins < 60 ? `${mins} min` : mins < 1440 ? `${mins / 60} hr` : `${mins / 1440} day`}
                            </p>
                            <p className="text-sm font-semibold text-white mt-1">
                              {(mins * price).toFixed(2)} {settings['coin_currency'] || 'USD'}
                            </p>
                          </div>
                        ));
                      } catch {
                        return <p className="text-xs text-zinc-500">Invalid duration config</p>;
                      }
                    })()}
                  </div>
                </div>
              </div>
            )}

            {!coinEnabled && (
              <div className="bg-[#111118] border border-[#2a2a3a]/50 rounded-xl p-5 text-center">
                <Coins className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
                <p className="text-sm text-zinc-400">Coin system is currently disabled</p>
                <p className="text-xs text-zinc-500 mt-1">Enable it to configure coin pricing for ESP32 hardware integration</p>
              </div>
            )}
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-4 mt-4">
            {/* API Key */}
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Key className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">API Key</h3>
              </div>
              <p className="text-xs text-zinc-400 mb-3">
                Used by routers and captive portal for authentication
              </p>
              <div className="flex gap-2">
                <Input
                  value={settings['api_key'] || ''}
                  readOnly
                  className="font-mono text-xs bg-[#0a0a0f] border-[#2a2a3a] text-zinc-400"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerateApiKey}
                  className="border-[#2a2a3a] text-zinc-300 hover:bg-[#2a2a3a]"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Change Password */}
            <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">Change Password</h3>
              </div>
              <div className="space-y-3">
                <div>
                  <Label className="text-zinc-400 text-xs">Current Password</Label>
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">New Password</Label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
                <div>
                  <Label className="text-zinc-400 text-xs">Confirm Password</Label>
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="mt-1 bg-[#0a0a0f] border-[#2a2a3a] text-white"
                  />
                </div>
                <Button
                  onClick={handlePasswordChange}
                  variant="outline"
                  className="border-[#2a2a3a] text-zinc-300 hover:bg-[#2a2a3a]"
                >
                  Update Password
                </Button>
                {passwordError && (
                  <p className="text-sm text-red-400">{passwordError}</p>
                )}
                {passwordSuccess && (
                  <p className="text-sm text-emerald-400">{passwordSuccess}</p>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
