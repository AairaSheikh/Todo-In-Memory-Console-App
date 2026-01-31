/**Confirmation dialog component for destructive actions.*/

'use client';

import styles from './ConfirmationDialog.module.css';

interface ConfirmationDialogProps {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
  isDangerous?: boolean;
}

export default function ConfirmationDialog({
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isLoading = false,
  isDangerous = false,
}: ConfirmationDialogProps) {
  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <h2>{title}</h2>
        <p>{message}</p>
        <div className={styles.actions}>
          <button
            className={isDangerous ? 'btn btn-danger' : 'btn btn-primary'}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : confirmText}
          </button>
          <button
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelText}
          </button>
        </div>
      </div>
    </div>
  );
}
