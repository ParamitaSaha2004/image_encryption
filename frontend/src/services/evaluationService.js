import api from './api';

export const evaluationService = {
  async runBenchmark(imageId, masterKey = 'HICE_CLINICAL_MASTER_KEY_2026') {
    const res = await api.post(`/evaluation/run/${imageId}`, null, {
      params: { master_key: masterKey }
    });
    return res.data;
  },

  async getComparativeMetrics(imageId) {
    const res = await api.get(`/evaluation/comparative/${imageId}`);
    return res.data;
  }
};
