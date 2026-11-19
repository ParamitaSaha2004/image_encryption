import api from './api';

export const auditService = {
  async getLogs(params = {}) {
    const res = await api.get('/audit/logs', { params });
    return res.data;
  },

  async verifyIntegrity() {
    const res = await api.get('/audit/verify');
    return res.data;
  },

  async simulateTampering(logId = null) {
    const res = await api.post('/audit/simulate-tamper', null, {
      params: logId ? { log_id: logId } : {}
    });
    return res.data;
  }
};
