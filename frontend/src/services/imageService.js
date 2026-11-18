import api from './api';

export const imageService = {
  async uploadImage(formData) {
    const response = await api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getImages() {
    const response = await api.get('/images');
    return response.data;
  },

  async getSampleScans() {
    const response = await api.get('/images/samples/list');
    return response.data;
  },

  async loadSampleScan(sampleName) {
    const response = await api.post(`/images/samples/load/${sampleName}`);
    return response.data;
  }
};
