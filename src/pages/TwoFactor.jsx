import { useState } from "react";

function TwoFactor({ onVerify }) {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");

  const handleVerify = () => {
    if (otp === "123456") {
      setError("");
      onVerify();
    } else {
      setError("Invalid OTP. Please enter the correct verification code.");
    }
  };

  return (
    <div className="auth-page single-auth">
      <section className="auth-card">
        <h2>Two-Factor Authentication</h2>

        <p>
          Enter the 6-digit verification code sent to the registered hospital
          email or mobile number.
        </p>

        <input
          placeholder="Enter OTP"
          maxLength="6"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
        />

        {error && <p className="error-message">{error}</p>}

        <button onClick={handleVerify}>Verify & Continue</button>

        <div className="demo-box">
          <strong>Demo OTP</strong>
          <p>123456</p>
        </div>
      </section>
    </div>
  );
}

export default TwoFactor;