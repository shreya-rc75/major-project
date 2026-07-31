import { useState } from "react";
import {
  Eye,
  EyeOff,
  ShieldCheck,
  Activity,
  Upload,
  UserPlus,
  LogOut,
  Stethoscope,
  FileText,
  Brain,
} from "lucide-react";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("login");
  const [user, setUser] = useState(null);
  const [tempLoginUser, setTempLoginUser] = useState(null);
  const [result, setResult] = useState(null);

  const handleCreateAccount = (formData) => {
    const { name, email, password, confirmPassword } = formData;

    if (!name || !email || !password || !confirmPassword) {
      alert("Please fill all fields.");
      return;
    }

    if (!email.includes("@")) {
      alert("Please enter a valid email.");
      return;
    }

    if (password.length < 6) {
      alert("Password must be at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    const newUser = {
      name,
      email,
      password,
      role: "Pathologist",
    };

    localStorage.setItem("cervivalUser", JSON.stringify(newUser));
    alert("Account created successfully. Please login.");
    setPage("login");
  };

  const handleLogin = (email, password) => {
    const savedUser = JSON.parse(localStorage.getItem("cervivalUser"));

    if (!savedUser) {
      alert("No account found. Please create an account first.");
      return;
    }

    if (email === savedUser.email && password === savedUser.password) {
      setTempLoginUser(savedUser);
      setPage("twofa");
    } else {
      alert("Invalid email or password.");
    }
  };

  const verify2FA = (otp) => {
    if (otp === "123456") {
      setUser(tempLoginUser);
      setPage("dashboard");
    } else {
      alert("Invalid OTP. Use 123456 for demo.");
    }
  };

  const generatePrediction = (data) => {
    let score = 0;

    if (Number(data.age) > 40) score += 2;
    if (data.hpv === "yes") score += 3;
    if (data.smoking === "yes") score += 1;
    if (data.symptoms === "yes") score += 2;
    if (data.history === "yes") score += 2;
    if (data.abnormalBleeding === "yes") score += 2;
    if (data.previousScreening === "yes") score += 1;
    
    const maxScore = 13;
    const riskPercentage = Math.round((score / maxScore) * 100);

    let stage = "Normal / Low Risk";
    let risk = "Low";
    let advice = "Routine screening and regular follow-up recommended.";

    if (score >= 3 && score <= 5) {
      stage = "Possible Pre-Cancerous Changes";
      risk = "Moderate";
      advice = "Further Pap smear/HPV review and clinical monitoring advised.";
    } else if (score >= 6 && score <= 8) {
      stage = "Possible Early Stage Cervical Cancer";
      risk = "High";
      advice = "Detailed examination and specialist consultation recommended.";
    } else if (score > 8) {
      stage = "Possible Advanced Risk Condition";
      risk = "Very High";
      advice = "Immediate clinical investigation and oncologist review advised.";
    }

    setResult({
      score,
      maxScore,
      riskPercentage,
      stage,
      risk,
      advice,
      patientName: data.patientName || "Not Provided",
      patientId: data.patientId || "Not Provided",
      screeningType: data.screeningType || "Pap Smear",
      age: data.age || "Not Provided",
      riskBreakdown: {
        age: Number(data.age) > 40 ? 2 : 0,
        hpv: data.hpv === "yes" ? 3 : 0,
        smoking: data.smoking === "yes" ? 1 : 0,
        symptoms: data.symptoms === "yes" ? 2 : 0,
        history: data.history === "yes" ? 2 : 0,
        abnormalBleeding: data.abnormalBleeding === "yes" ? 2 : 0,
        previousScreening: data.previousScreening === "yes" ? 1 : 0,
  },
});

    setPage("result");
  };

  const logout = () => {
    setUser(null);
    setTempLoginUser(null);
    setResult(null);
    setPage("login");
  };

  return (
    <>
      {page !== "login" && page !== "signup" && page !== "twofa" && (
        <Navbar user={user} logout={logout} />
      )}

      {page === "login" && (
        <Login
          onLogin={handleLogin}
          goToSignup={() => setPage("signup")}
        />
      )}

      {page === "signup" && (
        <Signup
          onSignup={handleCreateAccount}
          goToLogin={() => setPage("login")}
        />
      )}

      {page === "twofa" && (
        <TwoFA
          verify2FA={verify2FA}
          back={() => setPage("login")}
        />
      )}

      {page === "dashboard" && (
        <Dashboard
          user={user}
          startAssessment={() => setPage("assessment")}
        />
      )}

      {page === "assessment" && (
        <AssessmentForm 
          onPredict={generatePrediction} 
          goBack={() => setPage("dashboard")} 
          />
      )}

      {page === "result" && (
        <Result
          result={result}
          backToDashboard={() => setPage("dashboard")}
          newAssessment={() => setPage("assessment")}
        />
      )}
    </>
  );
}

function Login({ onLogin, goToSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);

  return (
    <main className="auth-container clean-auth">
      <section className="auth-card">
        <h1 className="brand-title">CerviVal</h1>
        <h2>Login</h2>
        <p className="muted">Access your cervical cancer detection dashboard.</p>

        <label>Email</label>
        <input
          type="email"
          placeholder="Enter email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label>Password</label>
        <div className="password-box">
          <input
            type={showPass ? "text" : "password"}
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <span onClick={() => setShowPass(!showPass)}>
            {showPass ? <EyeOff size={20} /> : <Eye size={20} />}
          </span>
        </div>

        <button className="primary-btn" onClick={() => onLogin(email, password)}>
          Login
        </button>

        <div className="auth-switch">
          <span>New user?</span>
          <button onClick={goToSignup}>Create Account</button>
        </div>

        <div className="demo-box">
          <b>Testing OTP</b>
          <p>Use <b>123456</b> after login.</p>
        </div>
      </section>
    </main>
  );
}

function Signup({ onSignup, goToLogin }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const update = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <main className="auth-container clean-auth">
      <section className="auth-card">
        <h1 className="brand-title">CerviVal</h1>

        <div className="card-title-row">
          <UserPlus size={28} />
          <h2>Create Account</h2>
        </div>

        <p className="muted">Create your CerviVal account.</p>

        <label>Full Name</label>
        <input
          name="name"
          type="text"
          placeholder="Enter full name"
          value={formData.name}
          onChange={update}
        />

        <label>Email</label>
        <input
          name="email"
          type="email"
          placeholder="Enter email"
          value={formData.email}
          onChange={update}
        />

        <label>Password</label>
        <input
          name="password"
          type="password"
          placeholder="Create password"
          value={formData.password}
          onChange={update}
        />

        <label>Confirm Password</label>
        <input
          name="confirmPassword"
          type="password"
          placeholder="Confirm password"
          value={formData.confirmPassword}
          onChange={update}
        />

        <button className="primary-btn" onClick={() => onSignup(formData)}>
          Create Account
        </button>

        <div className="auth-switch">
          <span>Already have an account?</span>
          <button onClick={goToLogin}>Login</button>
        </div>
      </section>
    </main>
  );
}

function TwoFA({ verify2FA, back }) {
  const [otp, setOtp] = useState("");

  return (
    <main className="twofa-page">
      <section className="twofa-card">
        <ShieldCheck size={52} />
        <h1>Two-Factor Authentication</h1>
        <p>Enter the 6-digit verification code to continue.</p>

        <input
          type="text"
          placeholder="Enter OTP"
          maxLength="6"
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
        />

        <button className="primary-btn" onClick={() => verify2FA(otp)}>
          Verify & Continue
        </button>

        <button className="secondary-btn" onClick={back}>
          Back to Login
        </button>

        <p className="small-note">Demo OTP: 123456</p>
      </section>
    </main>
  );
}

function Navbar({ user, logout }) {
  return (
    <nav className="navbar">
      <div>
        <h2>CerviVal</h2>
        <span>Clinical Decision Support System</span>
      </div>

      <div className="nav-user">
        <p>{user?.name}</p>
        <button onClick={logout}>
          <LogOut size={17} />
          Logout
        </button>
      </div>
    </nav>
  );
}

function Dashboard({ user, startAssessment }) {
  return (
    <main className="dashboard">
      <section className="hero">
        <div>
          <p className="tag">Welcome back, {user?.name}</p>
          <h1>Cervical Cancer Screening Dashboard</h1>
          <p>
            Start patient assessment, review screening inputs, generate
            predicted stage, and estimate future risk level.
          </p>

          <button className="primary-btn hero-btn" onClick={startAssessment}>
            Start New Assessment
          </button>
        </div>

        <div className="hero-visual">
          <Stethoscope size={95} />
        </div>
      </section>

      <section className="stats-grid">
        <div className="stat-card">
          <Activity />
          <h3>Stage Detection</h3>
          <p>Classifies possible cervical abnormality stage from inputs.</p>
        </div>

        <div className="stat-card">
          <Brain />
          <h3>Risk Prediction</h3>
          <p>Estimates future risk based on clinical factors.</p>
        </div>

        <div className="stat-card">
          <FileText />
          <h3>Structured Report</h3>
          <p>Generates clean output suitable for project demonstration.</p>
        </div>
      </section>
    </main>
  );
}

function AssessmentForm({ onPredict, goBack }) {
  const [data, setData] = useState({
    patientName: "",
    patientId: "",
    age: "",
    screeningType: "Pap Smear",
    hpv: "no",
    smoking: "no",
    symptoms: "no",
    history: "no",
    abnormalBleeding: "no",
    previousScreening: "no",
    image: null,
  });

  const update = (e) => {
    const { name, value, files } = e.target;

    if (name === "image") {
      setData({ ...data, image: files[0] });
    } else {
      setData({ ...data, [name]: value });
    }
  };

  const submit = () => {
    if (!data.patientName || !data.patientId || !data.age) {
      alert("Please enter patient name, patient ID and age.");
      return;
    }

    onPredict(data);
  };

  return (
    <main className="assessment-page upgraded-assessment">
      <section className="assessment-shell">
        <button 
          type="button"
          className="top-back-btn"
          onClick={goBack}
      >
         ← Back to Dashboard
        </button>
        <div className="assessment-top">
          <div>
            <p className="eyebrow">New Screening Case</p>
            <h1>Patient Assessment</h1>
            <p>
              Enter patient details, screening history and risk indicators to
              generate a structured CerviVal prediction report.
            </p>
          </div>

          <div className="case-badge">
            <span>Case Status</span>
            <b>Draft</b>
          </div>
        </div>

        <div className="assessment-layout">
          <section className="clinical-card main-form-card">
            <div className="section-heading">
              <span>01</span>
              <div>
                <h2>Patient Information</h2>
                <p>Basic identification and screening details</p>
              </div>
            </div>

            <div className="form-grid fancy-grid">
              <div>
                <label>Patient Name</label>
                <input
                  name="patientName"
                  type="text"
                  placeholder="Eg: Ananya Sharma"
                  value={data.patientName}
                  onChange={update}
                />
              </div>

              <div>
                <label>Patient ID</label>
                <input
                  name="patientId"
                  type="text"
                  placeholder="Eg: CV-1024"
                  value={data.patientId}
                  onChange={update}
                />
              </div>

              <div>
                <label>Age</label>
                <input
                  name="age"
                  type="number"
                  placeholder="Eg: 45"
                  value={data.age}
                  onChange={update}
                />
              </div>

              <div>
                <label>Screening Type</label>
                <select
                  name="screeningType"
                  value={data.screeningType}
                  onChange={update}
                >
                  <option value="Pap Smear">Pap Smear</option>
                  <option value="HPV Test">HPV Test</option>
                  <option value="Colposcopy">Colposcopy</option>
                  <option value="Biopsy Review">Biopsy Review</option>
                </select>
              </div>
            </div>
          </section>

          <section className="clinical-card">
            <div className="section-heading">
              <span>02</span>
              <div>
                <h2>Clinical Risk Factors</h2>
                <p>Select the observed patient indicators</p>
              </div>
            </div>

            <div className="risk-option-grid">
              <RiskOption
                title="HPV Positive"
                name="hpv"
                value={data.hpv}
                onChange={update}
              />

              <RiskOption
                title="Smoking Habit"
                name="smoking"
                value={data.smoking}
                onChange={update}
              />

              <RiskOption
                title="Symptoms Present"
                name="symptoms"
                value={data.symptoms}
                onChange={update}
              />

              <RiskOption
                title="Family / Medical History"
                name="history"
                value={data.history}
                onChange={update}
              />

              <RiskOption
                title="Abnormal Bleeding"
                name="abnormalBleeding"
                value={data.abnormalBleeding}
                onChange={update}
              />

              <RiskOption
                title="Previous Screening Issue"
                name="previousScreening"
                value={data.previousScreening}
                onChange={update}
              />
            </div>
          </section>

          <aside className="clinical-card upload-card">
            <div className="section-heading">
              <span>03</span>
              <div>
                <h2>Cell Image Upload</h2>
                <p>Attach Pap smear or cervical cell image</p>
              </div>
            </div>

            <label className="upload-zone">
              <Upload size={34} />
              <h3>Upload Screening Image</h3>
              <p>PNG, JPG or JPEG file accepted</p>
              <input
                name="image"
                type="file"
                accept="image/*"
                onChange={update}
              />
            </label>

            {data.image ? (
              <div className="file-pill">
                <span>Selected file</span>
                <b>{data.image.name}</b>
              </div>
            ) : (
              <div className="file-pill empty">
                <span>No image selected</span>
                <b>Image upload is optional for demo</b>
              </div>
            )}

            <div className="summary-mini">
              <h3>Live Case Summary</h3>
              <p>
                Patient: <b>{data.patientName || "Not entered"}</b>
              </p>
              <p>
                Age: <b>{data.age || "--"}</b>
              </p>
              <p>
                Screening: <b>{data.screeningType}</b>
              </p>
            </div>
          </aside>
        </div>

        <div className="assessment-actions">
          <button className="secondary-btn previous-btn" onClick={goBack}>
            Previous
          </button>

          <button className="primary-btn generate-btn" onClick={submit}>
            Generate Prediction Report
          </button>
        </div>
      </section>
    </main>
  );
}

function RiskOption({ title, name, value, onChange }) {
  return (
    <div className={`risk-option ${value === "yes" ? "active" : ""}`}>
      <div>
        <h3>{title}</h3>
        <p>{value === "yes" ? "Marked positive" : "Marked negative"}</p>
      </div>

      <select name={name} value={value} onChange={onChange}>
        <option value="no">No</option>
        <option value="yes">Yes</option>
      </select>
    </div>
  );
}

function Result({ result, backToDashboard, newAssessment }) {
  const riskClass = result.risk.toLowerCase().replace(" ", "-");

  return (
    <main className="result-page upgraded-result">
      <section className="report-shell">
        <div className="report-title">
          <div>
            <p className="eyebrow">CerviVal AI Report</p>
            <h1>Prediction Report Generated</h1>
            <p>
              Structured clinical summary based on patient assessment inputs and
              weighted risk scoring logic.
            </p>
          </div>

          <div className={`risk-stamp ${riskClass}`}>
            <span>Risk Level</span>
            <b>{result.risk}</b>
          </div>
        </div>

        <div className="report-grid">
          <section className="report-panel patient-panel">
            <h2>Patient Summary</h2>

            <div className="patient-details">
              <div>
                <span>Patient Name</span>
                <b>{result.patientName || "Not Provided"}</b>
              </div>

              <div>
                <span>Patient ID</span>
                <b>{result.patientId || "Not Provided"}</b>
              </div>

              <div>
                <span>Age</span>
                <b>{result.age || "Not Provided"}</b>
              </div>

              <div>
                <span>Screening Type</span>
                <b>{result.screeningType || "Pap Smear"}</b>
              </div>

              <div>
                <span>Risk Score</span>
                <b>
                  {result.score} / {result.maxScore || 13}
                </b>
              </div>

              <div>
                <span>Risk Percentage</span>
                <b>{result.riskPercentage || 0}%</b>
              </div>
            </div>
          </section>

          <section className={`report-panel stage-panel ${riskClass}`}>
            <span className="panel-label">Predicted Stage</span>
            <h2>{result.stage}</h2>
            <p>
              This output is generated using weighted clinical parameters entered
              during patient screening.
            </p>
          </section>

          <section className="report-panel score-panel">
            <h2>Risk Score Overview</h2>

            <div className="score-circle">
              <span>{result.riskPercentage || 0}%</span>
              <p>Risk</p>
            </div>

            <div className="score-bar">
              <div style={{ width: `${result.riskPercentage || 0}%` }}></div>
            </div>

            <p className="score-note">
              Risk percentage is calculated as: obtained score divided by maximum
              score multiplied by 100.
            </p>
          </section>

          <section className="report-panel basis-panel">
            <h2>Risk Calculation Basis</h2>

            <div className="basis-list">
              <p>
                Age above 40 <b>{result.riskBreakdown?.age || 0} / 2</b>
              </p>
              <p>
                HPV Positive <b>{result.riskBreakdown?.hpv || 0} / 3</b>
              </p>
              <p>
                Smoking Habit <b>{result.riskBreakdown?.smoking || 0} / 1</b>
              </p>
              <p>
                Symptoms Present <b>{result.riskBreakdown?.symptoms || 0} / 2</b>
              </p>
              <p>
                Family / Medical History{" "}
                <b>{result.riskBreakdown?.history || 0} / 2</b>
              </p>
              <p>
                Abnormal Bleeding{" "}
                <b>{result.riskBreakdown?.abnormalBleeding || 0} / 2</b>
              </p>
              <p>
                Previous Screening Issue{" "}
                <b>{result.riskBreakdown?.previousScreening || 0} / 1</b>
              </p>
            </div>
          </section>

          <section className="report-panel recommendation-panel">
            <h2>Clinical Recommendation</h2>
            <p>{result.advice}</p>

            <div className="recommendation-list">
              <span>Suggested next step</span>
              <b>
                {result.risk === "Low"
                  ? "Routine screening follow-up"
                  : result.risk === "Moderate"
                  ? "Clinical review advised"
                  : result.risk === "High"
                  ? "Specialist consultation advised"
                  : "Immediate medical investigation advised"}
              </b>
            </div>
          </section>
        </div>

        <div className="disclaimer-card">
          <b>Project Disclaimer</b>
          <p>
            This report is generated for academic project demonstration only. It
            is not a substitute for certified medical diagnosis or treatment.
          </p>
        </div>

        <div className="result-actions">
          <button className="primary-btn" onClick={newAssessment}>
            New Assessment
          </button>

          <button className="secondary-btn" onClick={backToDashboard}>
            Back to Dashboard
          </button>
        </div>
      </section>
    </main>
  );
}