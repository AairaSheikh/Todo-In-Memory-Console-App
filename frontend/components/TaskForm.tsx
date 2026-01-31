/**Task creation form component.*/

'use client';

import { useState } from 'react';
import { tasksAPI } from '@/lib/api';
import styles from './TaskForm.module.css';

interface TaskFormProps {
  userId: string;
  onTaskCreated: () => void;
}

export default function TaskForm({ userId, onTaskCreated }: TaskFormProps) {
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('Medium');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!description.trim()) {
      setError('Task description is required');
      return;
    }

    setLoading(true);

    try {
      await tasksAPI.createTask(userId, description.trim(), priority);
      setDescription('');
      setPriority('Medium');
      onTaskCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.form}>
      <h2>Add New Task</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="description">Task Description</label>
          <input
            id="description"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter task description"
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            disabled={loading}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Adding...' : 'Add Task'}
        </button>
      </form>
    </div>
  );
}
