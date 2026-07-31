import { Link } from "react-router-dom";
import { useState } from "react";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    if (email === "pathologist@cervival.com" && password === "cervival123") {
      setError("");
      onLogin();
    } else {
      setError("Invalid hospital email or password. Please try again.");
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-info">
        <h1>CerviVal</h1>
        <h2>AI-Powered Clinical Decision Support System</h2>

        <p>
          Built to assist pathologists with Pap smear image analysis, cervical
          abnormality detection, future risk prediction, explainable AI outputs,
          and structured clinical review.
        </p>

        <div className="auth-feature-box">
          <p>✓ Hospital database-ready workflow</p>
          <p>✓ Two-factor authentication flow</p>
          <p>✓ AI diagnosis and risk prediction layout</p>
          <p>✓ Pathologist review and report generation</p>
        </div>
      </section>

      <section className="auth-card">
        <h2>Pathologist Login</h2>
        <p>Access requires hospital-authorized credentials.</p>

        <input
          type="email"
          placeholder="Hospital Email / Staff ID"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="error-message">{error}</p>}

        <button onClick={handleLogin}>Continue to 2FA</button>

        <div className="demo-box">
          <strong>Demo Login</strong>
          <p>Email: pathologist@cervival.com</p>
          <p>Password: cervival123</p>
        </div>

        <div className="auth-links">
          <Link to="/request-access">Request hospital access</Link>
          <a>Forgot password?</a>
        </div>
      </section>
    </div>
  );
}

export default Login;