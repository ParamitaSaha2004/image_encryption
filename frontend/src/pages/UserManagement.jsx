import React, { useState, useEffect } from 'react';
import { Users, KeyRound, Shield, Search } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import api from '../services/api';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await api.get('/users');
        setUsers(res.data);
      } catch (err) {
        console.error('Failed to load user directory:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const filtered = users.filter(u =>
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.role_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <Users className="w-5 h-5 text-sky-400" />
            <span>Clinician & Identity Directory</span>
          </h2>
          <p className="text-xs text-slate-400">
            Registered doctors, researchers, and administrators authorized for ECDH image exchange
          </p>
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search clinicians..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-sky-500"
          />
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
            <tr>
              <th className="py-3 px-4">Clinician</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Work Email</th>
              <th className="py-3 px-4">NIST P-256 Public Key</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {loading ? (
              <tr>
                <td colSpan="5" className="py-8 text-center text-slate-500 font-mono">
                  Loading authorized clinician registry...
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan="5" className="py-8 text-center text-slate-500 font-mono">
                  No clinicians matching criteria.
                </td>
              </tr>
            ) : (
              filtered.map((u) => (
                <tr key={u.user_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    {u.username}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={u.role_name === 'SUPER_ADMIN' ? 'danger' : u.role_name === 'ADMIN' ? 'warning' : 'active'} text={u.role_name} />
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">
                    {u.email}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                    {u.public_key_pem ? (
                      <span className="text-emerald-400 flex items-center space-x-1">
                        <KeyRound className="w-3.5 h-3.5" />
                        <span>Available (secp256r1)</span>
                      </span>
                    ) : (
                      <span className="text-slate-600">Pending</span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-emerald-400">
                    ACTIVE
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
