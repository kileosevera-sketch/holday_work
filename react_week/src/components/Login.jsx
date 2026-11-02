import { useState } from 'react';
import {
  ArrowUpRight,
  Eye,
  EyeOff,
  Leaf,
  LockKeyhole,
  UserRound,
} from 'lucide-react';
import { apiRequest, setAccessToken } from '../api';

function Login({ onLogin }) {
  const [username, setUsername] = useState(
    () => localStorage.getItem('customer-intelligence-username') || ''
  );
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [rememberUsername, setRememberUsername] = useState(
    () => Boolean(localStorage.getItem('customer-intelligence-username'))
  );

  const handleUsernameChange = (event) => {
    const value = event.target.value;
    setUsername(value);
    if (rememberUsername) {
      localStorage.setItem('customer-intelligence-username', value);
    }
  };

  const toggleRememberUsername = (event) => {
    const checked = event.target.checked;
    setRememberUsername(checked);
    if (checked && username) {
      localStorage.setItem('customer-intelligence-username', username);
    } else {
      localStorage.removeItem('customer-intelligence-username');
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      const result = await apiRequest('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      setAccessToken(result.access_token);
      onLogin();
    } catch (loginError) {
      setError(loginError.message || 'Unable to sign in. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <span className="login-ribbon login-ribbon--one" aria-hidden="true" />
      <span className="login-ribbon login-ribbon--two" aria-hidden="true" />
      <span className="login-ribbon login-ribbon--three" aria-hidden="true" />
      <span className="login-orbit login-orbit--one" aria-hidden="true" />
      <span className="login-orbit login-orbit--two" aria-hidden="true" />
      <span className="login-sparkle login-sparkle--one" aria-hidden="true" />
      <span className="login-sparkle login-sparkle--two" aria-hidden="true" />
      <section className="login-card" aria-label="Sign in to Customer Intelligence">
        <header className="login-card__brand">
          <a className="login-brand" href="/" aria-label="Customer Intelligence home">
            <span className="login-brand__mark"><Leaf size={22} strokeWidth={1.8} /></span>
            <span className="login-brand__name">
              <strong>Customer Intelligence</strong>
              <small>AI POST-SALES INTELLIGENCE</small>
            </span>
          </a>
        </header>

        <div className="login-form-wrap">
          <div className="login-form-heading">
            <span className="login-form-heading__eyebrow">YOUR CUSTOMER INTELLIGENCE HUB</span>
            <h1>Welcome back<span>.</span></h1>
            <p>Sign in to continue to your dashboard.</p>
          </div>

          <form onSubmit={submit} className="login-form">
            <label htmlFor="login-username">Username or email</label>
            <div className="login-input-wrap">
              <UserRound size={18} aria-hidden="true" />
              <input
                id="login-username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={handleUsernameChange}
                placeholder="name@company.com"
                required
              />
            </div>
            <label htmlFor="login-password">Password</label>
            <div className="login-input-wrap">
              <LockKeyhole size={18} aria-hidden="true" />
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                className="login-password-toggle"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <div className="login-form__options">
              <label className="login-remember">
                <input
                  type="checkbox"
                  checked={rememberUsername}
                  onChange={toggleRememberUsername}
                />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                className="login-forgot"
                onClick={() => setError('Password reset is managed by your workspace administrator.')}
              >
                Forgot password?
              </button>
            </div>
            {error && <p className="login-error" role="alert">{error}</p>}
            <button type="submit" className="login-submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : <>Sign in to your account <ArrowUpRight size={17} /></>}
            </button>
          </form>

          <p className="login-security"><LockKeyhole size={13} /> Your workspace is private and secure</p>
          <footer className="login-form-bottom">Need access? <span>Contact your workspace administrator.</span></footer>
        </div>
      </section>
      <p className="login-page__caption">Thoughtful insights. Better experiences.</p>
    </main>
  );
}

export default Login;
