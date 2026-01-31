/**Task list component.*/

'use client';

import { Task } from '@/lib/store';
import TaskItem from './TaskItem';
import styles from './TaskList.module.css';

interface TaskListProps {
  userId: string;
  tasks: Task[];
  onTasksChanged: () => void;
}

export default function TaskList({ userId, tasks, onTasksChanged }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No tasks yet. Create one to get started!</p>
      </div>
    );
  }

  return (
    <div className={styles.list}>
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          userId={userId}
          task={task}
          onTasksChanged={onTasksChanged}
        />
      ))}
    </div>
  );
}
