import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Wifi, Shield, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function Login() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [setupPassword, setSetupPassword] = useState('');
  const [setupConfirm, setSetupConfirm] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Check if setup is needed
  useEffect(() => {
    fetch('/api/auth/check-setup')
      .then(r => r.json())
      .then(data => setNeedsSetup(data.needs_setup))
      .catch(() => {});
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const success = await login(username, password);
      if (success) {
        navigate('/dashboard');
      } else {
        setError('Invalid username or password');
      }
    } catch {
      setError('Connection failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (setupPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (setupPassword !== setupConfirm) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    try {
      const res = await fetch('/api/auth/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username: 'admin', password: setupPassword }),
      });
      
      if (res.ok) {
        const success = await login('admin', setupPassword);
        if (success) navigate('/dashboard');
      } else {
        const data = await res.json();
        setError(data.detail || 'Setup failed');
      }
    } catch {
      setError('Connection failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-4">
            <Wifi className="w-7 h-7 text-indigo-400" />
          </div>
          <h1 className="text-xl font-bold text-white">
            {needsSetup ? 'Initial Setup' : 'WiFi Admin'}
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            {needsSetup ? 'Create your admin account' : 'Voucher Management System'}
          </p>
        </div>

        {/* Card */}
        <div className="bg-[#111118] border border-[#2a2a3a] rounded-xl p-6">
          {needsSetup ? (
            <form onSubmit={handleSetup} className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">Username</label>
                <Input
                  value="admin"
                  disabled
                  className="bg-[#1a1a24] border-[#2a2a3a] text-zinc-500"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">Password</label>
                <Input
                  type="password"
                  value={setupPassword}
                  onChange={(e) => setSetupPassword(e.target.value)}
                  placeholder="Min 6 characters"
                  className="bg-[#1a1a24] border-[#2a2a3a] text-white placeholder:text-zinc-600"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">Confirm Password</label>
                <Input
                  type="password"
                  value={setupConfirm}
                  onChange={(e) => setSetupConfirm(e.target.value)}
                  placeholder="Confirm password"
                  className="bg-[#1a1a24] border-[#2a2a3a] text-white placeholder:text-zinc-600"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                disabled={isLoading}
              >
                {isLoading ? 'Setting up...' : 'Create Account'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">Username</label>
                <div className="relative">
                  <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="admin"
                    className="pl-10 bg-[#1a1a24] border-[#2a2a3a] text-white placeholder:text-zinc-600"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">Password</label>
                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="pr-10 bg-[#1a1a24] border-[#2a2a3a] text-white placeholder:text-zinc-600"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <Button
                type="submit"
                className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                disabled={isLoading || !username || !password}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          )}

          {error && (
            <p className="mt-4 text-sm text-red-400 text-center">{error}</p>
          )}

          {!needsSetup && (
            <p className="mt-4 text-xs text-zinc-500 text-center">
              Default: admin / admin123
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
