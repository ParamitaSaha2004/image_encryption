import api from './api';

export const shareService = {
  async listClinicians() {
    const res = await api.get('/shares/clinicians');
    return res.data;
  },

  async createShare(formData) {
    const res = await api.post('/shares/create', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  async listSentShares() {
    const res = await api.get('/shares/sent');
    return res.data;
  },

  async listReceivedShares() {
    const res = await api.get('/shares/received');
    return res.data;
  },

  async accessSharedScan(shareId) {
    const res = await api.post(`/shares/${shareId}/access`);
    return res.data;
  },

  async downloadSharedScan(shareId) {
    const res = await api.get(`/shares/${shareId}/download`, {
      responseType: 'blob'
    });
    return res.data;
  },

  async revokeShare(shareId) {
    const res = await api.delete(`/shares/${shareId}/revoke`);
    return res.data;
  }
};
