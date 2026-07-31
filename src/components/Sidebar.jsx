import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <h1>CerviVal</h1>
        <p>Cervical Health Intelligence</p>
      </div>

      <nav className="side-nav">
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/new-analysis">New Analysis</NavLink>
        <NavLink to="/diagnosis-results">Diagnosis Results</NavLink>
        <NavLink to="/patient-records">Patient Records</NavLink>
        <NavLink to="/reports">Reports</NavLink>
      </nav>

      <div className="sidebar-footer">
        <p>Hospital DB</p>
        <strong>Connected</strong>
      </div>
    </aside>
  );
}

export default Sidebar;