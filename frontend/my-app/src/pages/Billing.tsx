import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavBar from './NavBar';
import './PageStyles.css';
import './Billing.css';
import axios from 'axios';
import { getToken } from '../utils/auth';
import API_URL from '../utils/config';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ImageIcon from '@mui/icons-material/Image';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import ScheduleIcon from '@mui/icons-material/Schedule';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ReceiptIcon from '@mui/icons-material/Receipt';
import DescriptionIcon from '@mui/icons-material/Description';

interface ServiceFee {
  id: number;
  homeowner: number;
  bill_image?: string;
  receipt_image?: string;
  policy_image?: string;
  amount?: string;
  due_date?: string;
  status: 'unpaid' | 'paid' | 'delayed';
  month?: string;
  year?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
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

const Billing: React.FC = () => {
  const navigate = useNavigate();
  const [serviceFees, setServiceFees] = useState<ServiceFee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [uploadingReceipt, setUploadingReceipt] = useState<number | null>(null);
  const [receiptFile, setReceiptFile] = useState<{ [key: number]: File | null }>({});
  const [fileInputKeys, setFileInputKeys] = useState<{ [key: number]: number }>({});
  const [isVerified, setIsVerified] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [visibleImages, setVisibleImages] = useState<{ [key: number]: { bill: boolean; policy: boolean; receipt: boolean } }>({});

  useEffect(() => {
    checkVerification();
  }, []);

  const checkVerification = async () => {
    try {
      const token = getToken();
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.get(`${API_URL}/profile/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const isStaff = response.data.is_staff || false;
      setIsAdmin(isStaff);

      // If user is admin, redirect them away from homeowner billing page
      if (isStaff) {
        navigate('/admin-service-fee');
        return;
      }

      const verified = response.data.profile?.is_verified || response.data.is_verified || false;
      setIsVerified(verified);

      if (!verified) {
        setError('You must be a verified homeowner to view billing information.');
        setLoading(false);
        return;
      }

      // If verified homeowner (not admin), fetch service fees
      await fetchServiceFees();
    } catch (err: any) {
      console.error('Error checking verification:', err);
      if (err.response?.status === 401) {
        navigate('/login');
      } else {
        setError('Failed to verify your account status. Please try again later.');
        setLoading(false);
      }
    }
  };

  const fetchServiceFees = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = getToken();
      if (!token) {
        setError('You must be logged in to view your bills.');
        setLoading(false);
        return;
      }

      const response = await axios.get(`${API_URL}/service-fees/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        timeout: 10000,
      });

      const data = Array.isArray(response.data) ? response.data : (response.data.results || []);
      
      // Automatically mark bills as delayed if past due date
      const updatedData = data.map((fee: ServiceFee) => {
        if (fee.status === 'unpaid' && fee.due_date) {
          const dueDate = new Date(fee.due_date);
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          dueDate.setHours(0, 0, 0, 0);
          
          if (dueDate < today) {
            return { ...fee, status: 'delayed' as const };
          }
        }
        return fee;
      });
      
      setServiceFees(updatedData);
    } catch (err: any) {
      console.error('Error fetching service fees:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. Please check your connection and try again.');
      } else if (err.response?.status === 401) {
        setError('You must be logged in to view your bills.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to view bills. Please ensure your account is verified.');
      } else if (err.response) {
        setError(err.response.data?.detail || `Server error (${err.response.status})`);
      } else {
        setError('Failed to load your bills. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid':
        return <CheckCircleIcon className="status-icon paid" />;
      case 'delayed':
        return <ScheduleIcon className="status-icon delayed" />;
      case 'unpaid':
        return <CancelIcon className="status-icon unpaid" />;
      default:
        return null;
    }
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

  const toggleExpand = (id: number) => {
    const isExpanding = expandedId !== id;
    setExpandedId(isExpanding ? id : null);
    // When expanding, close all images for this service fee
    if (isExpanding) {
      setVisibleImages(prev => ({
        ...prev,
        [id]: { bill: false, policy: false, receipt: false }
      }));
    }
  };

  const toggleImageVisibility = (serviceFeeId: number, imageType: 'bill' | 'policy' | 'receipt') => {
    setVisibleImages(prev => {
      const current = prev[serviceFeeId];
      // If undefined, default to true (visible), then toggle
      const currentValue = current?.[imageType] ?? true;
      return {
        ...prev,
        [serviceFeeId]: {
          bill: imageType === 'bill' ? !currentValue : (current?.bill ?? true),
          policy: imageType === 'policy' ? !currentValue : (current?.policy ?? true),
          receipt: imageType === 'receipt' ? !currentValue : (current?.receipt ?? true)
        }
      };
    });
  };

  const handleReceiptFileChange = (serviceFeeId: number, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setReceiptFile({ ...receiptFile, [serviceFeeId]: file });
    } else {
      setReceiptFile({ ...receiptFile, [serviceFeeId]: null });
    }
  };

  const handleUploadReceipt = async (serviceFeeId: number) => {
    const file = receiptFile[serviceFeeId];
    if (!file) {
      alert('Please select a receipt image to upload.');
      return;
    }

    try {
      setUploadingReceipt(serviceFeeId);
      const token = getToken();
      if (!token) {
        setError('You must be logged in to upload receipts.');
        return;
      }

      const formData = new FormData();
      formData.append('receipt_image', file);

      await axios.patch(`${API_URL}/service-fees/${serviceFeeId}/`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      // Refresh the list
      fetchServiceFees();
      setReceiptFile({ ...receiptFile, [serviceFeeId]: null });
      setFileInputKeys({ ...fileInputKeys, [serviceFeeId]: (fileInputKeys[serviceFeeId] || 0) + 1 });
      alert('Receipt uploaded successfully!');
    } catch (err: any) {
      console.error('Error uploading receipt:', err);
      setError(err.response?.data?.detail || 'Failed to upload receipt. Please try again.');
    } finally {
      setUploadingReceipt(null);
    }
  };

  const formatCurrency = (amount: string | undefined) => {
    if (!amount) return 'N/A';
    return `₱${parseFloat(amount).toFixed(2)}`;
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const unpaidCount = serviceFees.filter((fee) => fee.status === 'unpaid').length;
  const delayedCount = serviceFees.filter((fee) => fee.status === 'delayed').length;
  const paidCount = serviceFees.filter((fee) => fee.status === 'paid').length;

  return (
    <>
      <NavBar />
      <div className="page-container">
        <div className="page-content">
        <div className="billing-container">
          <div className="billing-header">
            <h1>My Billing</h1>
            <p style={{color:'white'}} className="billing-subtitle">View and manage your service fee bills</p>
          </div>

          {error && <div className="error-message">{error}</div>}

          {loading ? (
            <div className="loading-message">Loading your bills...</div>
          ) : serviceFees.length === 0 ? (
            <div className="empty-message">
              <p>No bills found.</p>
              <p className="empty-subtitle">Your service fee bills will appear here once they are uploaded by the administration.</p>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              <div className="billing-summary">
                <div className="summary-card unpaid">
                  <div className="summary-icon">
                    <CancelIcon />
                  </div>
                  <div className="summary-content">
                    <h3>{unpaidCount}</h3>
                    <p>Unpaid</p>
                  </div>
                </div>
                <div className="summary-card delayed">
                  <div className="summary-icon">
                    <ScheduleIcon />
                  </div>
                  <div className="summary-content">
                    <h3>{delayedCount}</h3>
                    <p>Delayed</p>
                  </div>
                </div>
                <div className="summary-card paid">
                  <div className="summary-icon">
                    <CheckCircleIcon />
                  </div>
                  <div className="summary-content">
                    <h3>{paidCount}</h3>
                    <p>Paid</p>
                  </div>
                </div>
              </div>

              {/* Bills Table */}
              <div className="table-container">
                <table className="bills-table">
                  <thead>
                    <tr>
                      <th style={{width: '120px'}}>Reference #</th>
                      <th>Period</th>
                      <th>Amount</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Payment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {serviceFees.map((serviceFee) => (
                      <React.Fragment key={serviceFee.id}>
                        <tr 
                          className="bill-row"
                          onClick={() => toggleExpand(serviceFee.id)}
                        >
                          <td>
                            {serviceFee.latest_transaction ? (
                              <div>
                                <div style={{ 
                                  fontWeight: 'bold', 
                                  color: '#10b981', 
                                  fontSize: '0.9rem',
                                  marginBottom: '3px' 
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
                              <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>-</span>
                            )}
                          </td>
                          <td>{serviceFee.month || 'Monthly'} {serviceFee.year || ''}</td>
                          <td>{formatCurrency(serviceFee.amount)}</td>
                          <td>{formatDate(serviceFee.due_date)}</td>
                          <td>
                            <span
                              className="status-badge"
                              style={{ backgroundColor: getStatusColor(serviceFee.status) }}
                            >
                              {getStatusIcon(serviceFee.status)}
                              <span>{serviceFee.status.toUpperCase()}</span>
                            </span>
                          </td>
                          <td>
                            {serviceFee.latest_transaction ? (
                              serviceFee.latest_transaction.paid ? (
                                <span style={{ 
                                  color: '#10b981', 
                                  fontWeight: 'bold', 
                                  fontSize: '0.9rem',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '4px'
                                }}>
                                  ✅ PAID
                                </span>
                              ) : (
                                <a
                                  href={serviceFee.latest_transaction.checkout_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  style={{
                                    background: '#2c7c4b',
                                    color: 'white',
                                    padding: '6px 12px',
                                    borderRadius: '6px',
                                    textDecoration: 'none',
                                    fontSize: '0.85rem',
                                    fontWeight: 'bold',
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '4px'
                                  }}
                                  title="Click to see QR code for GCash/PayMaya payment"
                                >
                                  📱 Pay via QR
                                </a>
                              )
                            ) : (
                              <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>N/A</span>
                            )}
                          </td>
                        </tr>
                        {expandedId === serviceFee.id && (
                          <tr className="bill-details-row">
                            <td colSpan={6}>
                              <div className="bill-details-expanded">
                                {serviceFee.notes && (
                                  <div className="detail-item">
                                    <strong>Notes:</strong>
                                    <p>{serviceFee.notes}</p>
                                  </div>
                                )}
                                
                                {/* Payment Link Section */}
                                {serviceFee.latest_transaction && (
                                  <div style={{
                                    background: serviceFee.latest_transaction.paid ? '#f0fdf4' : '#f0f9ff',
                                    padding: '25px',
                                    borderRadius: '12px',
                                    border: serviceFee.latest_transaction.paid ? '2px solid #10b981' : '2px solid #3b82f6',
                                    marginTop: '15px'
                                  }}>
                                    <h4 style={{margin: '0 0 15px 0', color: serviceFee.latest_transaction.paid ? '#10b981' : '#1e40af', fontSize: '1.2rem'}}>
                                      {serviceFee.latest_transaction.paid ? '✅ Payment Completed' : '💳 Online Payment'}
                                    </h4>
                                    
                                    <div style={{
                                      fontSize: '1.4rem',
                                      fontWeight: 'bold',
                                      color: '#1e3a8a',
                                      margin: '15px 0'
                                    }}>
                                      Amount: ₱{serviceFee.latest_transaction.amount.toFixed(2)}
                                    </div>
                                    
                                    <div style={{
                                      fontSize: '0.95rem',
                                      color: '#6b7280',
                                      marginBottom: '20px'
                                    }}>
                                      Reference: <strong style={{ color: '#10b981', fontSize: '1.1rem' }}>
                                        {serviceFee.latest_transaction.reference_number}
                                      </strong>
                                    </div>
                                    
                                    {serviceFee.latest_transaction.paid ? (
                                      <div style={{
                                        background: '#10b981',
                                        color: 'white',
                                        padding: '15px 25px',
                                        borderRadius: '8px',
                                        fontWeight: 'bold',
                                        textAlign: 'center',
                                        fontSize: '1.1rem'
                                      }}>
                                        ✅ PAID - {serviceFee.latest_transaction.paid_at ? new Date(serviceFee.latest_transaction.paid_at).toLocaleString() : ''}
                                      </div>
                                    ) : (
                                      <div>
                                        <a
                                          href={serviceFee.latest_transaction.checkout_url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          style={{
                                                    display: 'inline-block',
                                                    background: '#2c7c4b',
                                                    color: 'white',
                                                    padding: '16px 40px',
                                                    borderRadius: '8px',
                                                    textDecoration: 'none',
                                                    fontWeight: 'bold',
                                                    fontSize: '1.2rem',
                                                    transition: 'all 0.2s',
                                                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                                                  }}
                                                  onMouseOver={(e) => e.currentTarget.style.background = '#1f5a35'}
                                                  onMouseOut={(e) => e.currentTarget.style.background = '#2c7c4b'}
                                                >
                                                  📱 Pay Now - Scan QR Code
                                                </a>
                                                
                                                <div style={{
                                                  marginTop: '15px',
                                                  padding: '12px',
                                                  background: '#fff7ed',
                                                  border: '2px solid #fb923c',
                                                  borderRadius: '8px',
                                                  fontSize: '0.9rem',
                                                  color: '#9a3412'
                                                }}>
                                                  <div style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '1rem' }}>
                                                    📱 How to Pay with QR Code:
                                                  </div>
                                                  <ol style={{ margin: '5px 0', paddingLeft: '20px' }}>
                                                    <li>Click "Pay Now - Scan QR Code" button above</li>
                                                    <li>You'll see a <strong>QR code</strong> on the payment page</li>
                                                    <li>Open your GCash or PayMaya app</li>
                                                    <li>Scan the QR code with your phone camera</li>
                                                    <li>Confirm payment - Status updates automatically!</li>
                                                  </ol>
                                                </div>
                                              </div>
                                            )}
                                            
                                            <div style={{
                                              marginTop: '20px',
                                              padding: '15px',
                                              background: '#f0fdf4',
                                              border: '2px solid #10b981',
                                              borderRadius: '8px',
                                              fontSize: '0.9rem',
                                              color: '#166534'
                                            }}>
                                              <p style={{margin: '5px 0', fontWeight: '600'}}>✅ Secure payment via PayMongo</p>
                                              <p style={{margin: '5px 0', fontWeight: '600'}}>✅ Scan QR Code with GCash/PayMaya/QR Ph</p>
                                              <p style={{margin: '5px 0', fontWeight: '600'}}>✅ Or pay with Credit Card, Online Banking</p>
                                              <p style={{margin: '5px 0', fontWeight: '600'}}>✅ Status updates automatically after payment</p>
                                              <p style={{margin: '5px 0', fontWeight: '600'}}>✅ Reference: <strong>{serviceFee.latest_transaction.reference_number}</strong></p>
                                            </div>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
      </div>
    </>
  );
};

export default Billing;

