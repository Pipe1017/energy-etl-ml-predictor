// frontend/src/components/Sidebar.tsx
import { Link } from 'react-router-dom';
import { useState } from 'react';

interface SidebarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
}

const Sidebar = ({ isOpen, toggleSidebar }: SidebarProps) => {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <nav className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      <div className="sidebar-header">
        <h2>Energy Analytics</h2>
        <button className="toggle-btn" onClick={toggleSidebar}>
          {isOpen ? '◀' : '▶'}
        </button>
      </div>

      <div className="sidebar-sections">
        {/* Descriptive Analysis Section */}
        <div className="sidebar-section">
          <div className="section-header" onClick={() => toggleSection('descriptive')}>
            <h3>📊 Descriptive Analysis</h3>
            <span>{expandedSection === 'descriptive' ? '▼' : '▶'}</span>
          </div>
          {expandedSection === 'descriptive' && (
            <div className="subsection-links">
              <Link to="/descriptive-analysis/energy">Energy</Link>
              <Link to="/descriptive-analysis/demand">Demand</Link>
              <Link to="/descriptive-analysis/reservoirs">Reservoirs</Link>
              <Link to="/descriptive-analysis/rivers">Rivers</Link>
            </div>
          )}
        </div>

        {/* Predictive Analysis Section */}
        <div className="sidebar-section">
          <div className="section-header" onClick={() => toggleSection('predictive')}>
            <h3>🔮 Predictive Analysis</h3>
            <span>{expandedSection === 'predictive' ? '▼' : '▶'}</span>
          </div>
          {expandedSection === 'predictive' && (
            <div className="subsection-links">
              <Link to="/predictive-analysis/energy">Energy</Link>
              <Link to="/predictive-analysis/demand">Demand</Link>
              <Link to="/predictive-analysis/reservoirs">Reservoirs</Link>
              <Link to="/predictive-analysis/rivers">Rivers</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;