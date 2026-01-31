/**Zustand store for authentication and task state.*/

import { create } from 'zustand';

export interface Task {
  id: string;
  description: string;
  completed: boolean;
  priority: string;
  created_at: string;
}

export interface AuthState {
  userId: string | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (userId: string, token: string) => void;
  clearAuth: () => void;
  loadAuth: () => void;
}

export interface TaskState {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, task: Partial<Task>) => void;
  deleteTask: (taskId: string) => void;
  clearTasks: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  userId: null,
  token: null,
  isAuthenticated: false,
  setAuth: (userId: string, token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_id', userId);
      localStorage.setItem('token', token);
    }
    set({ userId, token, isAuthenticated: true });
  },
  clearAuth: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user_id');
      localStorage.removeItem('token');
    }
    set({ userId: null, token: null, isAuthenticated: false });
  },
  loadAuth: () => {
    if (typeof window !== 'undefined') {
      const userId = localStorage.getItem('user_id');
      const token = localStorage.getItem('token');
      if (userId && token) {
        set({ userId, token, isAuthenticated: true });
      }
    }
  },
}));

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  setTasks: (tasks: Task[]) => set({ tasks }),
  addTask: (task: Task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (taskId: string, updates: Partial<Task>) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, ...updates } : task
      ),
    })),
  deleteTask: (taskId: string) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== taskId),
    })),
  clearTasks: () => set({ tasks: [] }),
}));
