import api from './api';

export const authService = {
  async login(username, password) {
    const response = await api.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('hice_token', response.data.access_token);
      localStorage.setItem('hice_user', JSON.stringify({
        userId: response.data.user_id,
        username: response.data.username,
        role: response.data.role
      }));
    }
    return response.data;
  },

  async register(username, email, password, roleName = 'USER') {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
      role_name: roleName
    });
    if (response.data.access_token) {
      localStorage.setItem('hice_token', response.data.access_token);
      localStorage.setItem('hice_user', JSON.stringify({
        userId: response.data.user_id,
        username: response.data.username,
        role: response.data.role
      }));
    }
    return response.data;
  },

  async getProfile() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('hice_token');
    localStorage.removeItem('hice_user');
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('hice_user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return !!localStorage.getItem('hice_token');
  }
};
