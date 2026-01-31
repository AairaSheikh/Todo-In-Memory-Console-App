/**API client for backend communication.*/

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('API_URL configured as:', API_URL);

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log('API Request:', config.method?.toUpperCase(), config.url, 'with token:', !!token);
  return config;
});

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.config?.url, error.message);
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user_id');
        window.location.href = '/signin';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (email: string, password: string) =>
    apiClient.post('/auth/signup', { email, password }),
  signin: (email: string, password: string) =>
    apiClient.post('/auth/signin', { email, password }),
  logout: () => apiClient.post('/auth/logout'),
  getCurrentUser: () => apiClient.get('/auth/me'),
};

export const tasksAPI = {
  createTask: (userId: string, description: string, priority: string = 'Medium') =>
    apiClient.post(`/api/${userId}/tasks`, { description, priority }),
  getTasks: (userId: string) =>
    apiClient.get(`/api/${userId}/tasks`),
  getTask: (userId: string, taskId: string) =>
    apiClient.get(`/api/${userId}/tasks/${taskId}`),
  updateTask: (userId: string, taskId: string, description?: string, priority?: string) =>
    apiClient.put(`/api/${userId}/tasks/${taskId}`, { description, priority }),
  deleteTask: (userId: string, taskId: string) =>
    apiClient.delete(`/api/${userId}/tasks/${taskId}`),
  toggleCompletion: (userId: string, taskId: string) =>
    apiClient.patch(`/api/${userId}/tasks/${taskId}/complete`),
};

export const chatAPI = {
  sendMessage: (userId: string, message: string) =>
    apiClient.post(`/api/${userId}/chat`, { message }),
  getHistory: (userId: string, limit: number = 50, offset: number = 0) =>
    apiClient.get(`/api/${userId}/chat/history`, { params: { limit, offset } }),
};

export default apiClient;
