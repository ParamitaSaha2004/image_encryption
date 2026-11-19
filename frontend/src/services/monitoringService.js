import api from './api';

export const monitoringService = {
  async getAlerts(resolved = null, limit = 50) {
    const params = { limit };
    if (resolved !== null) params.resolved = resolved;
    const res = await api.get('/monitoring/alerts', { params });
    return res.data;
  },

  async getStats() {
    const res = await api.get('/monitoring/stats');
    return res.data;
  },

  async resolveAlert(alertId) {
    const res = await api.post(`/monitoring/resolve/${alertId}`);
    return res.data;
  },

  async simulateAttack(attackType) {
    const res = await api.post('/monitoring/simulate-attack', null, {
      params: { attack_type: attackType }
    });
    return res.data;
  }
};
