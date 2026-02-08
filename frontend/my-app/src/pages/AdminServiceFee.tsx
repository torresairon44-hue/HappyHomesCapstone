import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import logo from '../images/logo.png';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './PageStyles.css';
import './AdminServiceFee.css';
import './AdminDashboard.css';
import Sidebar from './Sidebar';
import axios from 'axios';
import { getToken } from '../utils/auth';
import API_URL from '../utils/config';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import PersonIcon from '@mui/icons-material/Person';

interface ServiceFee {
  id?: number;
  homeowner: number;
  homeowner_id?: number;
  homeowner_name?: string;
  homeowner_email?: string;
  bill_image?: string;
  receipt_image?: string;
  policy_image?: string;
  amount?: string;
  due_date?: string;
  status: 'unpaid' | 'paid' | 'delayed';
  month?: string;
  year?: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
  has_paymongo_transaction?: boolean;
  latest_transaction?: {
    reference_number: string;
    checkout_url: string;
    amount: number;
    paid: boolean;
    paid_at?: string;
    status_icon: string;
    created_at: string;
  };
}

interface Homeowner {
  id: number;
  username: string;
  email: string;
}

const AdminServiceFee: React.FC = () => {
  const [serviceFees, setServiceFees] = useState<ServiceFee[]>([]);
  const [homeowners, setHomeowners] = useState<Homeowner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState<'name' | 'id'>('name');
  const [formData, setFormData] = useState<ServiceFee>({
    homeowner: 0,
    amount: '',
    due_date: '',
    status: 'unpaid',
    month: '',
    year: new Date().getFullYear(),
    notes: '',
  });


  useEffect(() => {
    fetchServiceFees();
    fetchHomeowners();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      fetchServiceFees();
    } else {
      fetchServiceFees();
    }
  }, [searchTerm, searchType]);

  const fetchHomeowners = async () => {
    try {
      const token = getToken();
      const headers: any = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      // Fetch verified homeowners (non-admin users)
      const response = await axios.get(`${API_URL}/admin/users/`, { headers });
      const users = Array.isArray(response.data) ? response.data : (response.data.results || []);
      // Filter to only verified, non-admin users
      const verifiedHomeowners = users
        .filter((user: any) => !user.is_staff && (user.profile?.is_verified || user.is_verified))
        .map((user: any) => ({
          id: user.id,
          username: user.username || user.user?.username || 'Unknown',
          email: user.email || user.user?.email || '',
        }));
      setHomeowners(verifiedHomeowners);
    } catch (err: any) {
      console.error('Error fetching homeowners:', err);
    }
  };

  const fetchServiceFees = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = getToken();
      const headers: any = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      let url = `${API_URL}/service-fees/`;
      if (searchTerm) {
        if (searchType === 'id') {
          url += `?homeowner_id=${searchTerm}`;
        } else {
          url += `?homeowner_name=${searchTerm}`;
        }
      }

      const response = await axios.get(url, { headers, timeout: 10000 });
      const data = Array.isArray(response.data) ? response.data : (response.data.results || []);
      setServiceFees(data);
    } catch (err: any) {
      console.error('Error fetching service fees:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. Please check your connection and try again.');
      } else if (err.response) {
        setError(err.response.data?.detail || `Server error (${err.response.status})`);
      } else {
        setError('Failed to load service fees. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'homeowner' || name === 'year' ? parseInt(value) || 0 : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = getToken();
      if (!token) {
        setError('You must be logged in to perform this action.');
        return;
      }

      const formDataToSend = new FormData();
      formDataToSend.append('homeowner', formData.homeowner.toString());
      if (formData.amount) formDataToSend.append('amount', formData.amount);
      if (formData.due_date) formDataToSend.append('due_date', formData.due_date);
      formDataToSend.append('status', formData.status);
      if (formData.month) formDataToSend.append('month', formData.month);
      if (formData.year) formDataToSend.append('year', formData.year.toString());
      if (formData.notes) formDataToSend.append('notes', formData.notes);

      if (editingId) {
        await axios.patch(`${API_URL}/service-fees/${editingId}/`, formDataToSend, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        });
      } else {
        await axios.post(`${API_URL}/service-fees/`, formDataToSend, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        });
      }

      setShowAddForm(false);
      setEditingId(null);
      setFormData({
        homeowner: 0,
        amount: '',
        due_date: '',
        status: 'unpaid',
        month: '',
        year: new Date().getFullYear(),
        notes: '',
      });
      fetchServiceFees();
    } catch (err: any) {
      console.error('Error saving service fee:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          (err.response?.data && typeof err.response.data === 'object' ? JSON.stringify(err.response.data) : null) ||
                          err.message || 
                          'Failed to save service fee. Please try again.';
      setError(errorMessage);
      console.error('Full error response:', err.response?.data);
    }
  };

  const handleEdit = (serviceFee: ServiceFee) => {
    setEditingId(serviceFee.id || null);
    setFormData({
      homeowner: serviceFee.homeowner_id || serviceFee.homeowner,
      amount: serviceFee.amount || '',
      due_date: serviceFee.due_date || '',
      status: serviceFee.status,
      month: serviceFee.month || '',
      year: serviceFee.year || new Date().getFullYear(),
      notes: serviceFee.notes || '',
    });
    setShowAddForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this service fee?')) {
      return;
    }
    try {
      const token = getToken();
      if (!token) {
        setError('You must be logged in to perform this action.');
        return;
      }
      await axios.delete(`${API_URL}/service-fees/${id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchServiceFees();
    } catch (err: any) {
      console.error('Error deleting service fee:', err);
      setError(err.response?.data?.detail || 'Failed to delete service fee. Please try again.');
    }
  };

  const handleCancel = () => {
    setShowAddForm(false);
    setEditingId(null);
    setFormData({
      homeowner: 0,
      amount: '',
      due_date: '',
      status: 'unpaid',
      month: '',
      year: new Date().getFullYear(),
      notes: '',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return '#4caf50';
      case 'delayed':
        return '#ff9800';
      case 'unpaid':
        return '#f44336';
      default:
        return '#757575';
    }
  };

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const navigate = useNavigate();

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="dashboard-layout">
        <Sidebar />

        <main className="dashboard-main">
        <div className="admin-service-fee-container">
          {/* Header Section */}
          <div className="header-section">
            <h1>Service Fee Management</h1>
          </div>

          {/* Stats Cards */}
          <div className="stats-cards">
            <div className="stat-card">
              <div className="stat-value">{serviceFees.length}</div>
              <div className="stat-label">Total Fees</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#4caf50' }}>
                {serviceFees.filter(f => f.status === 'paid').length}
              </div>
              <div className="stat-label">Paid</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#f44336' }}>
                {serviceFees.filter(f => f.status === 'unpaid').length}
              </div>
              <div className="stat-label">Unpaid</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: '#ff9800' }}>
                {serviceFees.filter(f => f.status === 'delayed').length}
              </div>
              <div className="stat-label">Delayed</div>
            </div>
          </div>

          {/* Controls Section */}
          <div className="controls-section">
            <div className="search-section">
            <div className="search-controls">
              <select
                className="search-type-select"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value as 'name' | 'id')}
              >
                <option value="name">Search by Name</option>
                <option value="id">Search by ID</option>
              </select>
              <div className="search-input-wrapper">
                <SearchIcon className="search-icon" />
                <input
                  type="text"
                  className="search-input"
                  placeholder={searchType === 'id' ? 'Enter homeowner ID...' : 'Enter homeowner name...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searchTerm && (
                  <button
                    className="clear-search-button"
                    onClick={() => setSearchTerm('')}
                  >
                    <ClearIcon />
                  </button>
                )}
              </div>
            </div>
            </div>
            <button
              className="add-button"
              onClick={() => {
                setShowAddForm(true);
                setEditingId(null);
                setFormData({
                  homeowner: 0,
                  amount: '',
                  due_date: '',
                  status: 'unpaid',
                  month: '',
                  year: new Date().getFullYear(),
                  notes: '',
                });
                setBillImageFile(null);
                setImagePreview(null);
                setPolicyImageFile(null);
                setPolicyImagePreview(null);
                setReceiptImageFile(null);
                setReceiptImagePreview(null);
              }}
            >
              <AddIcon /> Add Service Fee
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {showAddForm && (
            <div className="form-container">
              <h2>{editingId ? 'Edit Service Fee' : 'Add New Service Fee'}</h2>
              <form onSubmit={handleSubmit}>
                <table className="form-table">
                  <tbody>
                    <tr>
                      <td><label><PersonIcon /> Homeowner *</label></td>
                      <td>
                        <select
                          name="homeowner"
                          value={formData.homeowner}
                          onChange={handleInputChange}
                          required
                        >
                          <option value={0}>Select Homeowner</option>
                          {homeowners.map((homeowner) => (
                            <option key={homeowner.id} value={homeowner.id}>
                              {homeowner.username} (ID: {homeowner.id}) - {homeowner.email}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                    <tr>
                      <td><label> Amount</label></td> 
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <span style={{ marginRight: '8px', color: '#666' }}>₱</span>
                          <input
                            type="number"
                            name="amount"
                            step="0.01"
                            value={formData.amount}
                            onChange={handleInputChange}
                            placeholder="0.00"
                            style={{ flex: 1 }}
                          />
                        </div>
                      </td>
                    </tr>
                    <tr>
                      <td><label>Due Date</label></td>
                      <td>
                        <input
                          type="date"
                          name="due_date"
                          value={formData.due_date}
                          onChange={handleInputChange}
                        />
                      </td>
                    </tr>
                    <tr>
                      <td><label>Month</label></td>
                      <td>
                        <select
                          name="month"
                          value={formData.month}
                          onChange={handleInputChange}
                        >
                          <option value="">Select Month</option>
                          {months.map((month) => (
                            <option key={month} value={month}>
                              {month}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                    <tr>
                      <td><label>Year</label></td>
                      <td>
                        <input
                          type="number"
                          name="year"
                          value={formData.year}
                          onChange={handleInputChange}
                          min="2020"
                          max="2100"
                        />
                      </td>
                    </tr>
                    <tr>
                      <td><label>Notes</label></td>
                      <td>
                        <textarea
                          name="notes"
                          value={formData.notes}
                          onChange={handleInputChange}
                          rows={3}
                          placeholder="Additional notes or description..."
                          style={{ width: '100%' }}
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div className="form-actions">
                  <button type="submit" className="save-button">
                    <SaveIcon /> {editingId ? 'Update' : 'Create'} Service Fee
                  </button>
                  <button type="button" className="cancel-button" onClick={handleCancel}>
                    <CancelIcon /> Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {loading ? (
            <div className="loading-message">
              <div style={{
                border: '4px solid #f3f3f3',
                borderTop: '4px solid #2e6F40',
                borderRadius: '50%',
                width: '50px',
                height: '50px',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 20px'
              }}></div>
              Loading service fees...
            </div>
          ) : serviceFees.length === 0 ? (
            <div className="empty-message">
              <div style={{ fontSize: '3rem', marginBottom: '15px', opacity: 0.5 }}>📋</div>
              <h3 style={{ marginBottom: '10px', color: '#333' }}>No Service Fees Found</h3>
              <p style={{ margin: 0, color: '#666' }}>
                {searchTerm ? 'No service fees match your search criteria.' : 'Start by adding a new service fee.'}
              </p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="service-fee-table">
                <thead>
                  <tr>
                    <th style={{ width: '150px' }}>Reference #</th>
                    <th>Homeowner</th>
                    <th>Period</th>
                    <th>Amount</th>
                    <th>Due Date</th>
                    <th>Status</th>
                    <th>Payment Link</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {serviceFees.map((serviceFee) => (
                    <tr key={serviceFee.id}>
                      <td>
                        {serviceFee.latest_transaction ? (
                          <div>
                            <div style={{ 
                              fontWeight: 'bold', 
                              color: '#10b981', 
                              fontSize: '0.95rem',
                              marginBottom: '4px' 
                            }}>
                              {serviceFee.latest_transaction.reference_number}
                            </div>
                            <div style={{ 
                              fontSize: '0.7rem', 
                              color: '#6b7280' 
                            }}>
                              {serviceFee.latest_transaction.created_at && 
                                new Date(serviceFee.latest_transaction.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        ) : (
                          <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>No Ref</span>
                        )}
                      </td>
                      <td>
                        {serviceFee.homeowner_name ? (
                          <div>
                            <div style={{ fontWeight: '500' }}>{serviceFee.homeowner_name}</div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '2px' }}>
                              {serviceFee.homeowner_email || 'No email'}
                            </div>
                          </div>
                        ) : (
                          `ID: ${serviceFee.homeowner_id || serviceFee.homeowner}`
                        )}
                      </td>
                      <td>{serviceFee.month || 'N/A'} {serviceFee.year || ''}</td>
                      <td>{serviceFee.amount ? `₱${parseFloat(serviceFee.amount).toFixed(2)}` : 'N/A'}</td>
                      <td>{serviceFee.due_date ? new Date(serviceFee.due_date).toLocaleDateString() : 'N/A'}</td>
                      <td>
                        <span
                          className="status-badge"
                          style={{ backgroundColor: getStatusColor(serviceFee.status) }}
                        >
                          {serviceFee.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        {serviceFee.latest_transaction ? (
                          serviceFee.latest_transaction.paid ? (
                            <div style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                              backgroundColor: '#10b981',
                              color: 'white',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              fontWeight: 'bold',
                              fontSize: '0.85rem'
                            }}>
                              ✅ PAID
                              {serviceFee.latest_transaction.paid_at && (
                                <div style={{ 
                                  fontSize: '0.7rem', 
                                  opacity: 0.9,
                                  marginLeft: '4px',
                                  fontWeight: 'normal'
                                }}>
                                  ({new Date(serviceFee.latest_transaction.paid_at).toLocaleDateString()})
                                </div>
                              )}
                            </div>
                          ) : (
                            <a 
                              href={serviceFee.latest_transaction.checkout_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                backgroundColor: '#3b82f6',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '6px',
                                fontSize: '0.85rem',
                                textDecoration: 'none',
                                fontWeight: '500'
                              }}
                            >
                              📋 View Link
                            </a>
                          )
                        ) : (
                          <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>N/A</span>
                        )}
                      </td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="edit-button"
                            onClick={() => handleEdit(serviceFee)}
                            title="Edit"
                          >
                            <EditIcon />
                          </button>
                          <button
                            className="delete-button"
                            onClick={() => serviceFee.id && handleDelete(serviceFee.id)}
                            title="Delete"
                          >
                            <DeleteIcon />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        </main>
      </div>
    </>
  );
};

export default AdminServiceFee;

