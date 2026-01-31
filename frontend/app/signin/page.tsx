/**Sign in page.*/

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import styles from './auth.module.css';

export default function SignIn() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already authenticated (for page refresh case)
  useEffect(() => {
    console.log('SignIn - isLoading:', isLoading, 'isAuthenticated:', isAuthenticated);
    if (!isLoading && isAuthenticated) {
      console.log('Already authenticated, redirecting to dashboard');
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('=== SIGNIN ATTEMPT START ===');
      console.log('Attempting signin with email:', email);
      const response = await authAPI.signin(email, password);
      console.log('=== SIGNIN RESPONSE RECEIVED ===');
      console.log('Signin response status:', response.status);
      console.log('Signin response data:', response.data);
      console.log('Response keys:', Object.keys(response.data));
      
      const { user_id, token } = response.data;
      
      console.log('Extracted from response - user_id:', user_id, 'token:', token);
      
      if (!user_id || !token) {
        const errorMsg = 'Invalid response: missing user_id or token';
        console.error(errorMsg);
        throw new Error(errorMsg);
      }
      
      console.log('=== CALLING LOGIN FUNCTION ===');
      console.log('Calling login with user_id:', user_id, 'token:', token);
      login(user_id, token);
      console.log('=== LOGIN FUNCTION COMPLETED ===');
      console.log('Login called successfully, redirecting to dashboard');
      
      // Wait a bit to ensure state is updated before redirecting
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Redirect after login
      console.log('Pushing to /dashboard');
      router.push('/dashboard');
      console.log('Router.push called');
    } catch (err: any) {
      console.error('=== SIGNIN ERROR ===');
      console.error('Signin error:', err);
      console.error('Error message:', err.message);
      console.error('Error response:', err.response);
      console.error('Error response data:', err.response?.data);
      const errorMessage = err.response?.data?.detail || err.message || 'Sign in failed';
      console.error('Final error message:', errorMessage);
      setError(errorMessage);
      setLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="loading"></div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1>Sign In</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p>
          Don't have an account? <Link href="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
