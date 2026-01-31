/**Dashboard page - main task management interface.*/

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useTaskStore } from '@/lib/store';
import { tasksAPI, authAPI } from '@/lib/api';
import ProtectedRoute from '@/components/ProtectedRoute';
import TaskList from '@/components/TaskList';
import TaskForm from '@/components/TaskForm';
import ChatComponent from '@/components/ChatComponent';
import LoadingSpinner from '@/components/LoadingSpinner';
import styles from './dashboard.module.css';

function DashboardContent() {
  const router = useRouter();
  const { userId, logout } = useAuth();
  const { tasks, setTasks } = useTaskStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (userId) {
      loadTasks();
    }
  }, [userId]);

  const loadTasks = async () => {
    if (!userId) return;
    setLoading(true);
    setError('');

    try {
      const response = await tasksAPI.getTasks(userId);
      setTasks(response.data);
    } catch (err: any) {
      setError('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (err) {
      // Ignore logout errors
    }
    logout();
    router.push('/signin');
  };

  if (!userId) {
    return null;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>My Tasks</h1>
        <button onClick={handleLogout} className="btn btn-secondary">
          Logout
        </button>
      </header>

      <main className={styles.main}>
        <div className={styles.taskSection}>
          <TaskForm userId={userId} onTaskCreated={loadTasks} />

          {error && <div className="error">{error}</div>}

          {loading ? (
            <LoadingSpinner message="Loading tasks..." />
          ) : (
            <TaskList userId={userId} tasks={tasks} onTasksChanged={loadTasks} />
          )}
        </div>

        <div className={styles.chatSection}>
          <ChatComponent userId={userId} token={useAuth().token || ''} onTasksModified={loadTasks} />
        </div>
      </main>
    </div>
  );
}

export default function Dashboard() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
