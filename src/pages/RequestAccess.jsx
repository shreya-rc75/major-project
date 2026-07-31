import { Link } from "react-router-dom";
import { useState } from "react";

function RequestAccess() {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className="auth-page single-auth">
        <section className="auth-card success-card">
          <h2>Access Request Submitted</h2>
          <p>
            Your request has been sent for hospital administrator verification.
            Account activation will be allowed only after approval.
          </p>

          <Link to="/">
            <button>Back to Login</button>
          </Link>
        </section>
      </div>
    );
  }

  return (
    <div className="auth-page single-auth">
      <section className="auth-card wide-card">
        <h2>Request Hospital Access</h2>
        <p>New accounts require hospital administrator approval.</p>

        <div className="form-grid">
          <input placeholder="Full Name" />
          <input placeholder="Hospital Email" />
          <input placeholder="Hospital Name" />
          <input placeholder="Hospital ID" />
          <input placeholder="Department" />
          <input placeholder="Medical Registration Number" />

          <select>
            <option>Role</option>
            <option>Pathologist</option>
            <option>Lab Technician</option>
            <option>Hospital Admin</option>
          </select>

          <input type="password" placeholder="Create Password" />
        </div>

        <button onClick={() => setSubmitted(true)}>Submit Access Request</button>

        <Link className="back-link" to="/">
          Back to login
        </Link>
      </section>
    </div>
  );
}

export default RequestAccess;