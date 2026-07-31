function Topbar() {
  return (
    <header className="topbar">
      <div>
        <h2>CerviVal Clinical Dashboard</h2>
        <p>AI-assisted cervical cancer detection and future risk prediction</p>
      </div>

      <div className="doctor-card">
        <span>Logged in as</span>
        <strong>Pathologist</strong>
      </div>
    </header>
  );
}

export default Topbar;