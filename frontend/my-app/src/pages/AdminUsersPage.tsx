import React, { useEffect, useState } from 'react';
import { getToken } from '../utils/auth';
import './AdminUsersPage.css';
import { useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import { useNotifications } from './NotificationContext';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Link } from 'react-router-dom';
import defaultUserImage from '../images/user.png';

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff: boolean;
  profile?: {
    contact_number?: string;
    profile_image?: string;
    document?: string;
    is_verified?: boolean;
    billing_records?: string[];
  };
}

// Billing modal component
interface BillingModalProps {
  records: string[];
  onClose: () => void;
  startIndex: number;
}

const BillingModal: React.FC<BillingModalProps> = ({ records, onClose, startIndex }) => {
  const [currentIndex, setCurrentIndex] = useState(startIndex);

  const handlePrev = () => setCurrentIndex(prev => (prev === 0 ? records.length - 1 : prev - 1));
  const handleNext = () => setCurrentIndex(prev => (prev === records.length - 1 ? 0 : prev + 1));

const currentRecordRaw = records[currentIndex]; // might be undefined
const currentRecord = currentRecordRaw
  ? currentRecordRaw.startsWith('http')
    ? currentRecordRaw
    : `http://127.0.0.1:8000${currentRecordRaw}`
  : ''; // fallback to empty string

const isPDF = currentRecord.endsWith('.pdf');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <div className="modal-body">
          {isPDF ? (
            <iframe src={currentRecord} style={{ width: '100%', height: '80vh' }} title="PDF Viewer" />
          ) : (
            <img src={currentRecord} alt={`Billing ${currentIndex}`} style={{ maxWidth: '100%', maxHeight: '80vh' }} />
          )}
        </div>
        {records.length > 1 && (
          <div className="modal-controls">
            <button onClick={handlePrev}>Prev</button>
            <span>{currentIndex + 1} / {records.length}</span>
            <button onClick={handleNext}>Next</button>
          </div>
        )}
      </div>
    </div>
  );
};

const AdminUsersPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showGraph, setShowGraph] = useState(false);
  const [search, setSearch] = useState('');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  // const [formData, setFormData] = useState<Partial<User>>({});
  const [formData, setFormData] = useState<any>({
  new_password: '',
  confirm_password: '',
});
  const token = getToken();
  const { addNotification } = useNotifications();

  // Billing modal states
  const [modalOpen, setModalOpen] = useState(false);
  const [modalRecords, setModalRecords] = useState<string[]>([]);
  const [modalStartIndex, setModalStartIndex] = useState(0);

  // Add user modal states
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [newUserData, setNewUserData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    contact_number: '',
  });

  // Fetch users
  const fetchUsers = async () => {
    const currentToken = getToken();
    if (!currentToken) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/users/', {
        headers: { Authorization: `Bearer ${currentToken}` },
      });
      if (res.status === 401) {
        const data = await res.json();
        if (data.detail?.includes('token')) {
          toast.error('Session expired. Please login again.');
          localStorage.removeItem('access');
          navigate('/login');
        } else {
          toast.error('Unauthorized: Admin only');
        }
        setLoading(false);
        return;
      }
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      console.error('Error fetching users:', err);
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Verify user
  const verifyUser = async (user: User) => {
    const currentToken = getToken();
    if (!currentToken || !user.profile) {
      toast.error('You are not authenticated. Please login again.');
      return;
    }
    
    // Check if user has uploaded a document
    if (!user.profile.document) {
      toast.error('❌ User must upload a document first before verification.');
      return;
    }
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/verify-user/${user.id}/`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      if (res.ok) {
        setUsers(users.map(u =>
          u.id === user.id
            ? { ...u, profile: { ...u.profile, is_verified: true } }
            : u
        ));
        toast.success('✅ User verified successfully');
        fetchUsers(); // Refresh to get updated data
      } else {
        const data = await res.json();
        if (res.status === 401 || data.detail?.includes('token')) {
          toast.error('Session expired. Please login again.');
          localStorage.removeItem('access');
          navigate('/login');
        } else {
          toast.error(`❌ Failed: ${data.error || data.detail || 'Unknown error'}`);
        }
      }
    } catch (err) {
      toast.error('❌ Network error while verifying user');
    }
  };

  // Reject user
  const rejectUser = async (user: User) => {
    const currentToken = getToken();
    if (!currentToken || !user.profile) {
      toast.error('You are not authenticated. Please login again.');
      return;
    }
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/reject-user/${user.id}/`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      if (res.ok) {
        setUsers(users.map(u =>
          u.id === user.id
            ? { ...u, profile: { ...u.profile, is_verified: false } }
            : u
        ));
        toast.success('❌ User rejected successfully');
        fetchUsers(); // Refresh to get updated data
      } else {
        const data = await res.json();
        if (res.status === 401 || data.detail?.includes('token')) {
          toast.error('Session expired. Please login again.');
          localStorage.removeItem('access');
          navigate('/login');
        } else {
          toast.error(`❌ Failed: ${data.detail || 'Unknown error'}`);
        }
      }
    } catch (err) {
      toast.error('❌ Network error while rejecting user');
    }
  };

  // Unverify user
  const unverifyUser = async (user: User) => {
    const currentToken = getToken();
    if (!currentToken || !user.profile) {
      toast.error('You are not authenticated. Please login again.');
      return;
    }
    
    // Show confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to unverify ${user.username}? This action will send an email notification to the user.`
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/reject-user/${user.id}/`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      if (res.ok) {
        setUsers(users.map(u =>
          u.id === user.id
            ? { ...u, profile: { ...u.profile, is_verified: false } }
            : u
        ));
        toast.success('❌ User unverified successfully. Email notification sent.');
        fetchUsers(); // Refresh to get updated data
      } else {
        const data = await res.json();
        if (res.status === 401 || data.detail?.includes('token')) {
          toast.error('Session expired. Please login again.');
          localStorage.removeItem('access');
          navigate('/login');
        } else {
          toast.error(`❌ Failed: ${data.error || data.detail || 'Unknown error'}`);
        }
      }
    } catch (err) {
      toast.error('❌ Network error while unverifying user');
    }
  };

  // Delete user
  const handleDelete = async (id: number, isStaff: boolean) => {
    if (isStaff) {
      toast.error('❌ Cannot delete an admin user.');
      return;
    }
    if (!window.confirm('Are you sure you want to delete this user?')) return;

    const currentToken = getToken();
    if (!currentToken) {
      toast.error('You are not authenticated. Please login again.');
      navigate('/login');
      return;
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/users/${id}/delete/`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${currentToken}` },
      });
      if (res.ok) {
        setUsers(users.filter(u => u.id !== id));
        addNotification('User deleted successfully');
        toast.success('User deleted successfully');
      } else {
        const data = await res.json();
        if (res.status === 401 || data.detail?.includes('token')) {
          toast.error('Session expired. Please login again.');
          localStorage.removeItem('access');
          navigate('/login');
        } else {
          const msg = data?.detail || 'Failed to delete user';
          addNotification(`❌ ${msg}`);
          toast.error(`❌ ${msg}`);
        }
      }
    } catch (err) {
      addNotification('❌ Failed to delete user');
      toast.error('❌ Failed to delete user');
    }
  };

  // Edit user
const handleEditClick = (user: User) => {
  setEditingUser(user);
  setFormData({
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    profile: { contact_number: user.profile?.contact_number || '' },
    new_password: '',
    confirm_password: '',
  });
};
const handleEditSave = async () => {
  if (!editingUser) return;

  const currentToken = getToken();
  if (!currentToken) {
    toast.error('You are not authenticated. Please login again.');
    navigate('/login');
    return;
  }

  /** ✔ PASSWORD VALIDATION **/
  if (formData.new_password || formData.confirm_password) {
    if (formData.new_password !== formData.confirm_password) {
      toast.error("❌ Passwords do not match");
      return;
    }
  }

  /** ✔ MAIN PROFILE UPDATE PAYLOAD **/
  const payload: any = {
    first_name: formData.first_name,
    last_name: formData.last_name,
    email: formData.email,
    profile: {
      contact_number: formData.profile?.contact_number || "",
    },
  };

  // Only include password if admin entered one
  if (formData.new_password) {
    payload.password = formData.new_password;
  }

  try {
    /** 🔹 STEP 1: UPDATE USER INFO **/
    const res = await fetch(
      `http://127.0.0.1:8000/api/admin/users/${editingUser.id}/update/`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${currentToken}`,
        },
        body: JSON.stringify(payload),
      }
    );

    const data = await res.json();

    if (!res.ok) {
      if (res.status === 401 || data.detail?.includes('token')) {
        toast.error('Session expired. Please login again.');
        localStorage.removeItem('access');
        navigate('/login');
      } else {
        toast.error(`❌ Update failed: ${data.detail || "Unknown error"}`);
      }
      return;
    }

    /** 🔹 Update state immediately */
    setUsers(users.map(u =>
      u.id === editingUser.id
        ? {
            ...u,
            first_name: payload.first_name,
            last_name: payload.last_name,
            email: payload.email,
            profile: {
              ...u.profile,
              contact_number: payload.profile.contact_number,
            },
          }
        : u
    ));

    /** 🔹 STEP 2: If password was provided, update with admin endpoint */
    if (formData.new_password) {
      const passRes = await fetch(
        `http://127.0.0.1:8000/api/admin/users/${editingUser.id}/change-password/`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${currentToken}`,
          },
          body: JSON.stringify({ new_password: formData.new_password }),
        }
      );

      const passData = await passRes.json();

      if (!passRes.ok) {
        toast.error(`⚠ User updated BUT password failed: ${passData.detail}`);
      } else {
        toast.success("Password updated successfully");
      }
    }

    toast.success("User updated successfully");

    /** 🔹 Reset modal */
    setFormData({ new_password: "", confirm_password: "" });
    setEditingUser(null);

  } catch (err) {
    toast.error("Network error while updating user");
  }
};
  // const handleEditSave = async () => {
  //   if (!editingUser) return;

  //   try {
  //     const res = await fetch(`http://127.0.0.1:8000/api/admin/users/${editingUser.id}/update/`, {
  //       method: 'PUT',
  //       headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  //       body: JSON.stringify(formData),
  //     });

  //     const data = await res.json();
  //     if (res.ok) {
  //       toast.success('✅ User updated successfully');
  //       setUsers(users.map(u => u.id === editingUser.id ? { ...u, ...formData } as User : u));
  //       setEditingUser(null);
  //     } else {
  //       toast.error(`❌ Failed to update user: ${data.detail || 'Error'}`);
  //     }
  //   } catch (err) {
  //     toast.error('❌ Network error while updating user');
  //   }
  // };

  if (loading) {
    return (
      <div className="dashboard-layout">
        <Sidebar />
        <main className="dashboard-main">
          <div className="admin-dashboard-container">
            <div style={{ 
              textAlign: 'center', 
              padding: '60px 20px',
              background: 'white',
              borderRadius: '12px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              <div style={{
                border: '4px solid #f3f3f3',
                borderTop: '4px solid #2e6F40',
                borderRadius: '50%',
                width: '50px',
                height: '50px',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 20px'
              }}></div>
              <p style={{ color: '#666', fontSize: '1.1rem' }}>Loading users...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Graph data
  const totalUsers = users.length;
  const staffUsers = users.filter(u => u.is_staff).length;
  const regularUsers = totalUsers - staffUsers;

  const barData = [
    { type: 'Staff', count: staffUsers },
    { type: 'Regular', count: regularUsers },
  ];

  const pieData = [
    { name: 'Staff', value: staffUsers },
    { name: 'Regular', value: regularUsers },
  ];

  const COLORS = ['#2b2b2b', 'rgb(46, 111, 64)'];

  // Search filter
  const filteredUsers = users.filter(u =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    `${u.first_name} ${u.last_name}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="dashboard-layout">
        <Sidebar />

        <div className="admin-dashboard-container">
          <div className="header-section">
            <h1>Manage Users</h1>
          </div>

          {/* Stats Cards */}
          <div className="stats-cards">
            <div className="stat-card">
              <div className="stat-value">{users.length}</div>
              <div className="stat-label">Total Users</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#2b2b2b' }}>
                {users.filter(u => u.is_staff).length}
              </div>
              <div className="stat-label">Staff/Admin</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#2e6F40' }}>
                {users.filter(u => u.profile?.is_verified).length}
              </div>
              <div className="stat-label">Verified</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#f0ad4e' }}>
                {users.filter(u => !u.profile?.is_verified).length}
              </div>
              <div className="stat-label">Pending</div>
            </div>
          </div>

          <div className="search-container">
            <input
              type="text"
              placeholder="Search users by name, username or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="search-input"
            />
            <button className="toggle-graph-btn" onClick={() => setShowGraph(!showGraph)}>
              {showGraph ? 'Hide Graph' : 'Show Graph'}
            </button>
            <button
              onClick={() => setShowAddUserModal(true)}
              style={{
                padding: '12px 24px',
                background: '#2e6F40',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '14px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#255a35';
                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#2e6F40';
                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
              }}
            >
              + Add New User
            </button>
          </div>

          <div className={`dashboard-flex ${showGraph ? 'graph-visible' : ''}`}>
            <div className="dashboard-table">
              <div className="table-wrapper">
                <table className="admin-users-table">
                  <thead>
                    <tr>
                      <th>Profile</th>
                      <th>ID</th>
                      <th>Username</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Contact Number</th>
                      <th>Admin</th>
                      <th>Verified</th>
                      
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map(user => (
                      <tr key={user.id} className={user.is_staff ? 'admin-row' : ''}>
                        <td>
                          <img
                            src={user.profile?.profile_image || defaultUserImage}
                            alt={user.username}
                            className="profile-thumb"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = defaultUserImage;
                            }}
                          />
                        </td>
                        <td style={{ fontWeight: 600, color: '#2c3e50' }}>{user.id}</td>
                        <td style={{ fontWeight: 500 }}>{user.username}</td>
                        <td style={{ fontWeight: 500 }}>{user.first_name || '-'} {user.last_name || ''}</td>
                        <td style={{ color: '#555', fontSize: '0.85rem' }}>{user.email}</td>
                        <td style={{ color: '#666', fontFamily: 'monospace' }}>{user.profile?.contact_number || '-'}</td>
                        <td>
                          <span style={{
                            display: 'inline-block',
                            padding: '4px 10px',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            backgroundColor: user.is_staff ? '#d4edda' : '#e2e3e5',
                            color: user.is_staff ? '#155724' : '#383d41'
                          }}>
                            {user.is_staff ? 'Admin' : 'User'}
                          </span>
                        </td>
                        <td>
                          <div style={{ 
                            display: 'flex', 
                            flexDirection: 'column', 
                            gap: '6px', 
                            alignItems: 'center',
                            width: '100%',
                            overflow: 'hidden'
                          }}>
                            {user.profile?.document && (
                              <a
                                href={user.profile.document.startsWith('http')
                                  ? user.profile.document
                                  : `http://127.0.0.1:8000${user.profile.document}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  padding: '4px 10px',
                                  background: '#007bff',
                                  color: 'white',
                                  textDecoration: 'none',
                                  borderRadius: '6px',
                                  fontSize: '0.7rem',
                                  fontWeight: 600,
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                  transition: 'all 0.2s ease',
                                  display: 'inline-block',
                                  whiteSpace: 'nowrap',
                                  maxWidth: '100%',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.background = '#0056b3';
                                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = '#007bff';
                                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                }}
                              >
                                View Doc
                              </a>
                            )}
                            <span 
                              style={{ 
                                display: 'inline-block',
                                padding: '4px 10px',
                                borderRadius: '20px',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                                whiteSpace: 'nowrap',
                                ...(user.profile?.is_verified 
                                  ? { 
                                      backgroundColor: '#d4edda', 
                                      color: '#155724',
                                      border: '1px solid #c3e6cb'
                                    }
                                  : user.profile?.document 
                                  ? { 
                                      backgroundColor: '#fff3cd', 
                                      color: '#856404',
                                      border: '1px solid #ffeaa7'
                                    }
                                  : { 
                                      backgroundColor: '#f8d7da', 
                                      color: '#721c24',
                                      border: '1px solid #f5c6cb'
                                    })
                              }}
                            >
                              {user.profile?.is_verified 
                                ? 'Verified' 
                                : user.profile?.document 
                                ? 'Pending' 
                                : 'Not Verified'}
                            </span>
                          </div>
                        </td>

                        {/* Billing Column */}
                        {/* <td>
                          {user.profile?.billing_records && user.profile.billing_records.length > 0 ? (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                              {user.profile.billing_records.slice(0, 3).map((bill, i) => {
                                const url = bill.startsWith('http') ? bill : `http://127.0.0.1:8000${bill}`;
                                const isPDF = url.endsWith('.pdf');
                                return isPDF ? (
                                  <img
                                    key={i}
                                    src="/images/document.png"
                                    alt="PDF"
                                    style={{ width: '50px', height: '50px', cursor: 'pointer' }}
                                    onClick={() => { setModalRecords(user.profile!.billing_records!); setModalStartIndex(i); setModalOpen(true); }}
                                  />
                                ) : (
                                  <img
                                    key={i}
                                    src={url}
                                    alt={`Bill ${i}`}
                                    style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px', cursor: 'pointer' }}
                                    onClick={() => { setModalRecords(user.profile!.billing_records!); setModalStartIndex(i); setModalOpen(true); }}
                                  />
                                );
                              })}
                              {user.profile.billing_records.length > 3 && (
                                <div
                                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '50px', height: '50px', background: '#eee', borderRadius: '4px', cursor: 'pointer' }}
                                  onClick={() => { setModalRecords(user.profile!.billing_records!); setModalStartIndex(3); setModalOpen(true); }}
                                >
                                  +{user.profile.billing_records.length - 3}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span>No bills uploaded</span>
                          )}
                        </td> */}

                        <td>
                          <div style={{ 
                            display: 'flex', 
                            gap: '6px', 
                            flexWrap: 'wrap', 
                            justifyContent: 'center',
                            width: '100%',
                            maxWidth: '100%'
                          }}>
                            <button 
                              onClick={() => handleEditClick(user)}
                              className="edit-btn"
                              style={{
                                padding: '8px 16px',
                                background: '#007bff',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                                fontWeight: 600,
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.background = '#0056b3';
                                e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.background = '#007bff';
                                e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                              }}
                              >
                                Edit
                              </button>
                            {!user.is_staff && (
                              <button 
                                onClick={() => handleDelete(user.id, user.is_staff)}
                                className="delete-btn"
                                style={{
                                  padding: '8px 16px',
                                  background: '#dc3545',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  fontSize: '0.8rem',
                                  fontWeight: 600,
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                  transition: 'all 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.background = '#c82333';
                                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = '#dc3545';
                                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                }}
                              >
                                Delete
                              </button>
                            )}
                            {!user.profile?.is_verified && (
                              <>
                                <button 
                                  onClick={() => verifyUser(user)}
                                  className="verify-btn"
                                  style={{
                                    padding: '8px 16px',
                                    background: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem',
                                    fontWeight: 600,
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                    transition: 'all 0.2s ease'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.background = '#218838';
                                    e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.background = '#28a745';
                                    e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                  }}
                                >
                                  {user.profile?.document ? 'Approve' : 'Verify'}
                                </button>
                                {user.profile?.document && (
                                  <button 
                                    onClick={() => {
                                      if (window.confirm('Are you sure you want to reject this user?')) {
                                        rejectUser(user);
                                      }
                                    }}
                                    className="reject-btn"
                                    style={{
                                      padding: '8px 16px',
                                      background: '#dc3545',
                                      color: 'white',
                                      border: 'none',
                                      borderRadius: '6px',
                                      cursor: 'pointer',
                                      fontSize: '0.8rem',
                                      fontWeight: 600,
                                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                      transition: 'all 0.2s ease'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.background = '#c82333';
                                      e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.background = '#dc3545';
                                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                    }}
                                  >
                                    Reject
                                  </button>
                                )}
                              </>
                            )}
                            {user.profile?.is_verified && (
                              <button 
                                onClick={() => unverifyUser(user)}
                                className="unverify-btn"
                                style={{
                                  padding: '8px 16px',
                                  background: '#ffc107',
                                  color: '#212529',
                                  border: 'none',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  fontSize: '0.8rem',
                                  fontWeight: 600,
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                  transition: 'all 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.background = '#e0a800';
                                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = '#ffc107';
                                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                }}
                              >
                                Unverify
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filteredUsers.length === 0 && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '40px 20px',
                    color: '#666',
                    background: 'white',
                    borderRadius: '12px',
                    marginTop: '20px'
                  }}>
                    <p style={{ fontSize: '1.1rem', margin: 0 }}>No users found matching your search.</p>
                  </div>
                )}
              </div>
            </div>
            
            {showGraph && (
              <div className="dashboard-graph">
                <h3 style={{ color: 'rgb(46, 111, 64)' }}>User Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={barData}>
                    <XAxis dataKey="type" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="rgb(46, 111, 64)" />
                  </BarChart>
                </ResponsiveContainer>

                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={false}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>

                <p style={{ textAlign: 'center', marginTop: '10px', fontWeight: 'bold', color: 'rgb(46, 111, 64)' }}>
                  Total Users:
                  <p className="total-users">{totalUsers}</p>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit modal */}
      {editingUser && (
        <div className="edit-modal-overlay">
          <div className="edit-modal">
            <h2>Edit User: {editingUser.username}</h2>
            <input
              type="text"
              placeholder="First Name"
              value={formData.first_name || ''}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            />
            <input
              type="text"
              placeholder="Last Name"
              value={formData.last_name || ''}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            />
            <input
              type="email"
              placeholder="Email"
              value={formData.email || ''}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <input
              type="text"
              placeholder="Contact Number"
              value={formData.profile?.contact_number || ''}
              onChange={(e) => setFormData({
                ...formData,
                profile: { ...formData.profile, contact_number: e.target.value }
              })}
            />
            <input
  type="password"
  placeholder="New Password (optional)"
  value={formData.new_password || ''}
  onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
/>

<input
  type="password"
  placeholder="Confirm Password"
  value={formData.confirm_password || ''}
  onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
/>
            <div className="modal-buttons">
              <button onClick={handleEditSave}>Save</button>
              <button onClick={() => setEditingUser(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Billing modal */}
      {modalOpen && (
        <BillingModal
          records={modalRecords}
          startIndex={modalStartIndex}
          onClose={() => setModalOpen(false)}
        />
      )}

      {/* Add User Modal */}
      {showAddUserModal && (
        <div className="modal-overlay" onClick={() => setShowAddUserModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px', width: '90%' }}>
            <button className="modal-close" onClick={() => setShowAddUserModal(false)}>×</button>
            <h2 style={{ marginTop: 0, marginBottom: '20px' }}>Add New User</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                // Get fresh token
                const currentToken = getToken();
                if (!currentToken) {
                  toast.error('You are not authenticated. Please login again.');
                  navigate('/login');
                  return;
                }

                // Validate required fields
                if (!newUserData.username || !newUserData.email) {
                  toast.error('Username and Email are required fields.');
                  return;
                }

                try {
                  const res = await fetch('http://127.0.0.1:8000/api/admin/users/create/', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      Authorization: `Bearer ${currentToken}`,
                    },
                    body: JSON.stringify(newUserData),
                  });

                  const data = await res.json();
                  if (res.ok) {
                    toast.success(`✅ User created successfully! Default password: user123`);
                    setShowAddUserModal(false);
                    setNewUserData({
                      username: '',
                      email: '',
                      first_name: '',
                      last_name: '',
                      contact_number: '',
                    });
                    fetchUsers(); // Refresh the user list
                  } else {
                    // Handle token expiration
                    if (res.status === 401 || data.detail?.includes('token')) {
                      toast.error('Session expired. Please login again.');
                      localStorage.removeItem('access');
                      navigate('/login');
                    } else {
                      toast.error(`❌ Failed: ${data.detail || 'Unknown error'}`);
                    }
                  }
                } catch (err: any) {
                  console.error('Error creating user:', err);
                  toast.error(`❌ Network error: ${err.message || 'Failed to create user'}`);
                }
              }}
            >
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Username <span style={{ color: 'red' }}>*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newUserData.username}
                  onChange={(e) => setNewUserData({ ...newUserData, username: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Email <span style={{ color: 'red' }}>*</span>
                </label>
                <input
                  type="email"
                  required
                  value={newUserData.email}
                  onChange={(e) => setNewUserData({ ...newUserData, email: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  First Name
                </label>
                <input
                  type="text"
                  value={newUserData.first_name}
                  onChange={(e) => setNewUserData({ ...newUserData, first_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Last Name
                </label>
                <input
                  type="text"
                  value={newUserData.last_name}
                  onChange={(e) => setNewUserData({ ...newUserData, last_name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Contact Number
                </label>
                <input
                  type="text"
                  value={newUserData.contact_number}
                  onChange={(e) => setNewUserData({ ...newUserData, contact_number: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc',
                  }}
                />
              </div>

              <div style={{ 
                padding: '10px', 
                backgroundColor: '#fff3cd', 
                borderRadius: '4px', 
                marginBottom: '20px',
                border: '1px solid #ffc107'
              }}>
                <strong>Note:</strong> The user will be created with the default password: <strong>user123</strong>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddUserModal(false);
                    setNewUserData({
                      username: '',
                      email: '',
                      first_name: '',
                      last_name: '',
                      contact_number: '',
                    });
                  }}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#2e6F40',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                  }}
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default AdminUsersPage;
