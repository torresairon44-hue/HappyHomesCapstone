import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './GuardDashboard.css';

interface WalkInVisitor {
  id?: number;
  name: string;
  gmail: string;
  contact_number: string;
  address: string;
  homeowner_name: string;
  reason: string;
  status: 'pending' | 'approved' | 'declined';
  time_in?: string;
  time_out?: string;
  created_at?: string;
}

interface VisitorRequest {
  id: number;
  visitor_name: string;
  visitor_email: string;
  visitor_contact_number: string;
  one_time_pin: string;
  visit_date: string;
  visit_start_time: string;
  visit_end_time: string;
  status: string;
  resident_name: string;
  is_valid: boolean;
  pin_entered_at?: string;
}

const GuardDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [guardUser, setGuardUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'walkin' | 'pin' | 'active'>('walkin');
  
  // Walk-in form
  const [walkInForm, setWalkInForm] = useState<WalkInVisitor>({
    name: '',
    gmail: '',
    contact_number: '',
    address: '',
    homeowner_name: '',
    reason: '',
    status: 'approved'
  });
  
  // PIN verification
  const [pinInput, setPinInput] = useState('');
  const [verifiedVisitor, setVerifiedVisitor] = useState<VisitorRequest | null>(null);
  
  // Active visitors
  const [activeVisitors, setActiveVisitors] = useState<WalkInVisitor[]>([]);
  const [activeScheduled, setActiveScheduled] = useState<VisitorRequest[]>([]);
  
  const token = localStorage.getItem('guard_token');

  useEffect(() => {
    const user = localStorage.getItem('guard_user');
    if (!token || !user) {
      navigate('/guard-login');
      return;
    }
    setGuardUser(JSON.parse(user));
    fetchActiveVisitors();
  }, [token, navigate]);

  const fetchActiveVisitors = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/guard/active-visitors/', {
        headers: { Authorization: `Token ${token}` }
      });
      setActiveVisitors(response.data.walk_ins || []);
      setActiveScheduled(response.data.scheduled || []);
    } catch (error) {
      console.error('Error fetching active visitors:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('guard_token');
    localStorage.removeItem('guard_user');
    navigate('/guard-login');
  };

  const handleWalkInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/api/guard/walk-in/',
        { ...walkInForm, time_in: new Date().toISOString() },
        { headers: { Authorization: `Token ${token}` } }
      );
      
      toast.success('Walk-in visitor registered successfully!');
      setWalkInForm({
        name: '',
        gmail: '',
        contact_number: '',
        address: '',
        homeowner_name: '',
        reason: '',
        status: 'approved'
      });
      fetchActiveVisitors();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to register visitor');
    }
  };

  const handlePINVerify = async () => {
    if (pinInput.length !== 6) {
      toast.error('Please enter a 6-digit PIN');
      return;
    }

    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/api/visitor-requests/verify_pin/',
        { pin: pinInput },
        { headers: { Authorization: `Token ${token}` } }
      );

      if (response.data.valid) {
        setVerifiedVisitor(response.data.visitor_request);
        
        // Auto check-in
        await axios.post(
          `http://127.0.0.1:8000/api/guard/checkin-pin/${response.data.visitor_request.id}/`,
          {},
          { headers: { Authorization: `Token ${token}` } }
        );
        
        const visitor = response.data.visitor_request;
        const visitDate = new Date(visitor.visit_date).toLocaleDateString();
        const timeRange = `${visitor.visit_start_time} - ${visitor.visit_end_time}`;
        toast.success(`✅ PIN is valid! Scheduled for ${visitDate} at ${timeRange}. ${visitor.visitor_name} checked in successfully!`);
        setPinInput('');
        fetchActiveVisitors();
      } else {
        // Handle different invalid scenarios
        const details = response.data.details;
        const visitor = details?.visitor_request;
        
        if (details?.reason === 'not_yet_valid') {
          const visitDate = new Date(visitor.visit_date).toLocaleDateString();
          const startTime = visitor.visit_start_time;
          toast.warning(`⏰ PIN is not yet valid. This visitor is scheduled for ${visitDate} at ${startTime}. Please check in at the scheduled time.`);
        } else if (details?.reason === 'expired') {
          const visitDate = new Date(visitor.visit_date).toLocaleDateString();
          const endTime = visitor.visit_end_time;
          toast.error(`⏱️ PIN has expired. The visit was scheduled until ${visitDate} at ${endTime}. Please request a new visitor PIN.`);
        } else if (details?.reason === 'already_used') {
          toast.error('❌ This PIN has already been used for check-in.');
        } else {
          toast.error(details?.status_message || 'Invalid PIN');
        }
        
        // Clear the verified visitor display if showing invalid
        setVerifiedVisitor(null);
      }
    } catch (error: any) {
      if (error.response?.data?.error === 'PIN not found') {
        toast.error('❌ Invalid PIN. Please check the code and try again.');
      } else {
        toast.error(error.response?.data?.error || 'PIN verification failed');
      }
      setVerifiedVisitor(null);
    }
  };

  const handleCheckout = async (visitorId: number, type: 'walkin' | 'scheduled') => {
    try {
      await axios.post(
        `http://127.0.0.1:8000/api/guard/checkout/${visitorId}/?type=${type}`,
        {},
        { headers: { Authorization: `Token ${token}` } }
      );
      
      const checkoutTime = new Date();
      const formattedDate = checkoutTime.toLocaleDateString();
      const formattedTime = checkoutTime.toLocaleTimeString();
      toast.success(`Visitor checked out on ${formattedDate} at ${formattedTime}`);
      fetchActiveVisitors();
    } catch (error) {
      toast.error('Failed to checkout visitor');
    }
  };

  return (
    <div className="guard-dashboard">
      <ToastContainer position="top-right" autoClose={3000} />
      
      {/* Header */}
      <header className="guard-header">
        <div className="guard-header-left">
          <h1>🛡️ Guard Station</h1>
          <p>Welcome, {guardUser?.username}</p>
        </div>
        <button onClick={handleLogout} className="guard-logout-btn">Logout</button>
      </header>

      {/* Tab Navigation */}
      <div className="guard-tabs">
        <button
          className={activeTab === 'walkin' ? 'active' : ''}
          onClick={() => setActiveTab('walkin')}
        >
          🚶 Walk-in Registration
        </button>
        <button
          className={activeTab === 'pin' ? 'active' : ''}
          onClick={() => setActiveTab('pin')}
        >
          🔢 PIN Verification
        </button>
        <button
          className={activeTab === 'active' ? 'active' : ''}
          onClick={() => setActiveTab('active')}
        >
          👥 Active Visitors ({activeVisitors.length + activeScheduled.length})
        </button>
      </div>

      {/* Content */}
      <div className="guard-content">
        {/* Walk-in Tab */}
        {activeTab === 'walkin' && (
          <div className="walkin-section">
            <h2>Register Walk-in Visitor</h2>
            <form onSubmit={handleWalkInSubmit} className="walkin-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input
                    type="text"
                    value={walkInForm.name}
                    onChange={(e) => setWalkInForm({ ...walkInForm, name: e.target.value })}
                    placeholder="Visitor's full name"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Contact Number *</label>
                  <input
                    type="tel"
                    value={walkInForm.contact_number}
                    onChange={(e) => setWalkInForm({ ...walkInForm, contact_number: e.target.value })}
                    placeholder="09XXXXXXXXX"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Address of Visit *</label>
                  <input
                    type="text"
                    value={walkInForm.address}
                    onChange={(e) => setWalkInForm({ ...walkInForm, address: e.target.value })}
                    placeholder="Block/Lot/Street Address"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Name of Homeowner to Visit *</label>
                  <input
                    type="text"
                    value={walkInForm.homeowner_name}
                    onChange={(e) => setWalkInForm({ ...walkInForm, homeowner_name: e.target.value })}
                    placeholder="Homeowner's full name"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Purpose of Visit *</label>
                  <input
                    type="text"
                    value={walkInForm.reason}
                    onChange={(e) => setWalkInForm({ ...walkInForm, reason: e.target.value })}
                    placeholder="e.g., Visiting family"
                    required
                  />
                </div>
              </div>

              <button type="submit" className="submit-btn">
                ✅ Register & Check-in
              </button>
            </form>
          </div>
        )}

        {/* PIN Verification Tab */}
        {activeTab === 'pin' && (
          <div className="pin-section">
            <h2>Verify Visitor PIN</h2>
            <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
              Enter the 6-digit PIN code provided to the visitor
            </p>
            <div className="pin-input-container">
              <div style={{ marginBottom: '15px', color: '#666', fontSize: '0.9rem' }}>
                <strong>📱 PIN Code</strong>
              </div>
              <input
                type="text"
                maxLength={6}
                value={pinInput}
                onChange={(e) => setPinInput(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="pin-input"
                autoFocus
              />
              <button 
                onClick={handlePINVerify} 
                className="verify-btn"
                disabled={pinInput.length !== 6}
              >
                ✓ Verify & Check-in
              </button>
              <div style={{ marginTop: '15px', color: '#999', fontSize: '0.85rem' }}>
                PIN must be exactly 6 digits
              </div>
            </div>

            {verifiedVisitor && (
              <div className="verified-card">
                <h3>✅ Visitor Verified & Checked In</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '20px' }}>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Visitor Name</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{verifiedVisitor.visitor_name}</p>
                  </div>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Contact</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{verifiedVisitor.visitor_contact_number}</p>
                  </div>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Email</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{verifiedVisitor.visitor_email}</p>
                  </div>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Visiting</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{verifiedVisitor.resident_name}</p>
                  </div>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Visit Date</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{new Date(verifiedVisitor.visit_date).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9rem' }}>Scheduled Time</p>
                    <p style={{ margin: '5px 0', fontWeight: '600' }}>{verifiedVisitor.visit_start_time} - {verifiedVisitor.visit_end_time}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Active Visitors Tab */}
        {activeTab === 'active' && (
          <div className="active-section">
            <h2>Currently Inside</h2>
            
            {/* Walk-in visitors */}
            {activeVisitors.length > 0 && (
              <div className="visitor-group">
                <h3>Walk-in Visitors</h3>
                <table className="visitors-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Contact</th>
                      <th>Address</th>
                      <th>Homeowner</th>
                      <th>Purpose</th>
                      <th>Date In</th>
                      <th>Time In</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeVisitors.map((visitor) => (
                      <tr key={visitor.id}>
                        <td>{visitor.name}</td>
                        <td>{visitor.contact_number}</td>
                        <td>{visitor.address || '-'}</td>
                        <td>{visitor.homeowner_name || '-'}</td>
                        <td>{visitor.reason}</td>
                        <td>{visitor.time_in ? new Date(visitor.time_in).toLocaleDateString() : '-'}</td>
                        <td>{visitor.time_in ? new Date(visitor.time_in).toLocaleTimeString() : '-'}</td>
                        <td>
                          <button
                            onClick={() => handleCheckout(visitor.id!, 'walkin')}
                            className="checkout-btn"
                          >
                            Check Out
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Scheduled visitors */}
            {activeScheduled.length > 0 && (
              <div className="visitor-group">
                <h3>Scheduled Visitors (PIN)</h3>
                <table className="visitors-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Visiting</th>
                      <th>Contact</th>
                      <th>Date In</th>
                      <th>Time In</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeScheduled.map((visitor) => (
                      <tr key={visitor.id}>
                        <td>{visitor.visitor_name}</td>
                        <td>{visitor.resident_name}</td>
                        <td>{visitor.visitor_contact_number}</td>
                        <td>{visitor.pin_entered_at ? new Date(visitor.pin_entered_at).toLocaleDateString() : '-'}</td>
                        <td>{visitor.pin_entered_at ? new Date(visitor.pin_entered_at).toLocaleTimeString() : '-'}</td>
                        <td>
                          <button
                            onClick={() => handleCheckout(visitor.id, 'scheduled')}
                            className="checkout-btn"
                          >
                            Check Out
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeVisitors.length === 0 && activeScheduled.length === 0 && (
              <p className="no-visitors">No visitors currently inside</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GuardDashboard;
