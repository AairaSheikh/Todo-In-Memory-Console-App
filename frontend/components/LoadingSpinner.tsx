/**Loading spinner component.*/

'use client';

import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className={styles.container}>
      <div className={styles.spinner}></div>
      <p>{message}</p>
    </div>
  );
}
