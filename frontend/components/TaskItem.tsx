/**Individual task item component with edit/delete/complete actions.*/

'use client';

import { useState } from 'react';
import { Task, useTaskStore } from '@/lib/store';
import { tasksAPI } from '@/lib/api';
import styles from './TaskList.module.css';

interface TaskItemProps {
  userId: string;
  task: Task;
  onTasksChanged: () => void;
}

export default function TaskItem({ userId, task, onTasksChanged }: TaskItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editDescription, setEditDescription] = useState(task.description);
  const [editPriority, setEditPriority] = useState(task.priority);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const updateTask = useTaskStore((state) => state.updateTask);
  const deleteTaskFromStore = useTaskStore((state) => state.deleteTask);

  const handleEdit = async () => {
    if (!editDescription.trim()) {
      setError('Task description cannot be empty');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await tasksAPI.updateTask(
        userId,
        task.id,
        editDescription.trim(),
        editPriority
      );
      updateTask(task.id, {
        description: response.data.description,
        priority: response.data.priority,
      });
      setIsEditing(false);
      onTasksChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update task');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    setError('');

    try {
      await tasksAPI.deleteTask(userId, task.id);
      deleteTaskFromStore(task.id);
      setShowConfirm(false);
      onTasksChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete task');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleComplete = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await tasksAPI.toggleCompletion(userId, task.id);
      updateTask(task.id, { completed: response.data.completed });
      onTasksChanged();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update task');
    } finally {
      setLoading(false);
    }
  };

  if (isEditing) {
    return (
      <div className={styles.item}>
        <div className="form-group">
          <input
            type="text"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Task description"
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <select
            value={editPriority}
            onChange={(e) => setEditPriority(e.target.value)}
            disabled={loading}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="button-group">
          <button
            className="btn btn-primary"
            onClick={handleEdit}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => {
              setIsEditing(false);
              setEditDescription(task.description);
              setEditPriority(task.priority);
              setError('');
            }}
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.item} ${task.completed ? styles.completed : ''}`}>
      <div className={styles.content}>
        <div className={styles.description}>
          <input
            type="checkbox"
            checked={task.completed}
            onChange={handleToggleComplete}
            disabled={loading}
            aria-label="Mark task complete"
          />
          <span className={task.completed ? styles.strikethrough : ''}>
            {task.description}
          </span>
        </div>
        <span className={`${styles.priority} ${styles[`priority-${task.priority.toLowerCase()}`]}`}>
          {task.priority}
        </span>
      </div>
      <div className={styles.actions}>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => setIsEditing(true)}
          disabled={loading}
        >
          Edit
        </button>
        <button
          className="btn btn-sm btn-danger"
          onClick={() => setShowConfirm(true)}
          disabled={loading}
        >
          Delete
        </button>
      </div>
      {showConfirm && (
        <div className={styles.confirmation}>
          <p>Are you sure you want to delete this task?</p>
          <div className="button-group">
            <button
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={loading}
            >
              {loading ? 'Deleting...' : 'Delete'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setShowConfirm(false)}
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}
