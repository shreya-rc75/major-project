import { useState, useEffect } from "react";
import api from "./services/api.js";
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
  const [tempToken, setTempToken] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    // On mount, try to fetch current user if token present
    (async () => {
      try {
        const me = await api.me();
        if (me && me.id) {
          setUser(me);
          setPage("dashboard");
        }
      } catch (e) {
        // not logged in
        setUser(null);
      }
    })();
  }, []);

  const handleCreateAccount = async (formData) => {
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

    try {
      await api.signup(name, email, password);
      alert("Account created successfully. Please login.");
      setPage("login");
    } catch (err) {
      alert("Signup failed: " + err.message);
    }
  };

  const handleLogin = async (email, password) => {
    try {
      const res = await api.login(email, password);
      // backend returns temp_token and otp for demo
      if (res && res.temp_token) {
        setTempToken(res.temp_token);
        // keep demo OTP visible in UI
        setPage("twofa");
      } else {
        alert("Login failed: unexpected response from server.");
      }
    } catch (err) {
      alert("Login failed: " + err.message);
    }
  };

  const verify2FA = async (otp) => {
    try {
      const res = await api.verifyOtp(tempToken, otp);
      if (res && res.access_token) {
        // api.verifyOtp already saves token in localStorage
        // fetch user info
        const me = await api.me();
        setUser(me);
        setPage("dashboard");
        setTempToken(null);
      } else {
        alert("OTP verification failed: unexpected response");
      }
    } catch (err) {
      alert("OTP verification failed: " + err.message + " (Use 123456 for demo)");
    }
  };

  const generatePrediction = async (data) => {
    // Save patient -> case -> upload image -> predict
    try {
      // Create or ensure patient
      const patientPayload = {
        patient_identifier: data.patientId || `auto-${Date.now()}`,
        name: data.patientName || "",
        age: data.age ? Number(data.age) : null,
        gender: null,
      };
      const patient = await api.createPatient(patientPayload);

      // Create case
      const clinical = {
        patientName: data.patientName,
        patientId: data.patientId,
        age: data.age,
        screeningType: data.screeningType,
        hpv: data.hpv,
        smoking: data.smoking,
        symptoms: data.symptoms,
        history: data.history,
        abnormalBleeding: data.abnormalBleeding,
        previousScreening: data.previousScreening,
      };

      const casePayload = {
        patient_id: patient.id,
        created_by: user?.id || 0,
        clinical_data: JSON.stringify(clinical),
      };

      const createdCase = await api.createCase(casePayload);

      // Upload image if present
      if (data.image) {
        try {
          await api.uploadImage(createdCase.id, data.image);
        } catch (err) {
          // inform user but continue to prediction
          alert("Image upload failed: " + err.message);
        }
      }

      // Run prediction on backend
      const predictionRes = await api.predict(createdCase.id, clinical);
      const prediction = predictionRes.prediction || predictionRes;

      // Build result object compatible with existing Result UI
      const finalResult = {
        score: prediction.score || prediction.score || 0,
        maxScore: prediction.maxScore || prediction.maxScore || 13,
        riskPercentage: prediction.riskPercentage || 0,
        stage: prediction.stage || "",
        risk: prediction.risk || "",
        advice: prediction.advice || "",
        patientName: clinical.patientName || "Not Provided",
        patientId: clinical.patientId || "Not Provided",
        screeningType: clinical.screeningType || "Pap Smear",
        age: clinical.age || "Not Provided",
        riskBreakdown: prediction.riskBreakdown || {},
        model_version: prediction.model_version || "demo-v1",
      };

      setResult(finalResult);
      setPage("result");
    } catch (err) {
      alert("Prediction workflow failed: " + err.message);
    }
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setTempToken(null);
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

           (truncated) }
