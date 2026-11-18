import api from './api';

export const cryptoService = {
  async getChaosSensitivity(seedStr = 'HICE_SECRET_CHAOS_SEED_2026', delta = 1e-14) {
    const response = await api.get('/crypto/chaos/sensitivity', {
      params: { seed_str: seedStr, delta }
    });
    return response.data;
  },

  async testChaoticPermute(imageId, seed = 'HICE_CLINICAL_CHAOS_KEY') {
    const response = await api.post(`/crypto/chaos/test-permute/${imageId}`, null, {
      params: { seed }
    });
    return response.data;
  },

  async getCAAvalanche(rule = 30, length = 1000) {
    const response = await api.get('/crypto/ca/avalanche', {
      params: { rule, length }
    });
    return response.data;
  },

  async testCADiffuse(imageId, rule = 30, seed = 'HICE_CLINICAL_CA_KEY') {
    const response = await api.post(`/crypto/ca/test-diffuse/${imageId}`, null, {
      params: { rule, seed }
    });
    return response.data;
  },

  async testECDHKeyAgreement() {
    const response = await api.post('/crypto/ecdh/test-key-agreement');
    return response.data;
  },

  async testAESTamperSimulation() {
    const response = await api.post('/crypto/aes/test-tamper-simulation');
    return response.data;
  },

  async runHybridEncrypt(imageId, masterKey = 'HICE_CLINICAL_MASTER_KEY_2026', caRule = 30) {
    const response = await api.post(`/crypto/hybrid/encrypt/${imageId}`, null, {
      params: { master_key: masterKey, ca_rule: caRule }
    });
    return response.data;
  },

  async runHybridDecrypt(imageId, masterKey = 'HICE_CLINICAL_MASTER_KEY_2026', verifyBitExact = true) {
    const response = await api.post(`/crypto/hybrid/decrypt/${imageId}`, null, {
      params: { master_key: masterKey, verify_bit_exact: verifyBitExact }
    });
    return response.data;
  },

  getHybridPackageDownloadUrl(imageId) {
    return `/api/v1/crypto/hybrid/package/${imageId}`;
  },

  async directDecryptFile(file, masterKey = 'HICE_CLINICAL_MASTER_KEY_2026') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('master_key', masterKey);
    const response = await api.post('/crypto/hybrid/direct-decrypt-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
};
