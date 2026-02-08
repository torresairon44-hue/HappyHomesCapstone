import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './GuardLogin.css';
import logoImage from '../images/logo.png';

const GuardLogin: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/guard-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Store guard token
        localStorage.setItem('guard_token', data.token);
        localStorage.setItem('guard_user', JSON.stringify(data.user));
        navigate('/guard-dashboard');
      } else {
        setError(data.error || 'Invalid credentials');
      }
    } catch (err) {
      setError('Connection error. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="guard-login-container">
      <div className="guard-login-box">
        <img src={logoImage} alt="Logo" className="guard-logo" />
        <h1>🛡️ Guard Station</h1>
        <p className="guard-subtitle">Visitor Tracking System</p>
        
        <form onSubmit={handleLogin} className="guard-login-form">
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter guard username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="guard-login-btn" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="guard-footer">
          <p>Guard Access Only</p>
          <button onClick={() => navigate('/login')} className="back-link">
            ← Back to Main Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default GuardLogin;
