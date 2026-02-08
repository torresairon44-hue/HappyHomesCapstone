import React, { useState } from 'react';
import axios from 'axios';
import { getToken } from '../utils/auth';
import API_URL from '../utils/config';
import './PayMongoPayment.css';

interface PayMongoPaymentProps {
  serviceFeeId: number;
  amount: number;
  onPaymentCreated?: (checkoutUrl: string) => void;
  onError?: (error: string) => void;
}

const PayMongoPayment: React.FC<PayMongoPaymentProps> = ({
  serviceFeeId,
  amount,
  onPaymentCreated,
  onError
}) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    billing_name: '',
    billing_email: '',
    billing_phone: '',
    payment_method: 'qrph' // Default to QRPh
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/service-fees/${serviceFeeId}/paymongo-payment/`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data.success && response.data.checkout_url) {
        // Redirect to PayMongo checkout
        window.location.href = response.data.checkout_url;
        if (onPaymentCreated) {
          onPaymentCreated(response.data.checkout_url);
        }
      }
    } catch (error: any) {
      console.error('Payment error:', error);
      const errorMsg = error.response?.data?.error || 'Failed to create payment';
      if (onError) {
        onError(errorMsg);
      } else {
        alert(`Payment error: ${errorMsg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="paymongo-payment-container">
      <h3>💳 Pay via QRPh/E-Wallet</h3>
      <div className="payment-amount">
        <strong>Amount:</strong> ₱{amount.toFixed(2)}
      </div>

      <form onSubmit={handleSubmit} className="payment-form">
        <div className="form-group">
          <label>Payment Method</label>
          <select
            value={formData.payment_method}
            onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
            required
          >
            <option value="qrph">QRPh (Scan with any bank app)</option>
            <option value="gcash">GCash</option>
            <option value="grab_pay">GrabPay</option>
            <option value="paymaya">PayMaya</option>
          </select>
        </div>

        <div className="form-group">
          <label>Full Name *</label>
          <input
            type="text"
            placeholder="Juan Dela Cruz"
            value={formData.billing_name}
            onChange={(e) => setFormData({ ...formData, billing_name: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Email *</label>
          <input
            type="email"
            placeholder="juan@example.com"
            value={formData.billing_email}
            onChange={(e) => setFormData({ ...formData, billing_email: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Phone Number *</label>
          <input
            type="tel"
            placeholder="+639171234567"
            value={formData.billing_phone}
            onChange={(e) => setFormData({ ...formData, billing_phone: e.target.value })}
            pattern="\+639[0-9]{9}"
            required
          />
          <small>Format: +639XXXXXXXXX</small>
        </div>

        <button
          type="submit"
          className="pay-button"
          disabled={loading}
        >
          {loading ? 'Processing...' : `Pay ₱${amount.toFixed(2)}`}
        </button>
      </form>

      <div className="payment-info">
        <p>✓ Secure payment via PayMongo</p>
        <p>✓ Works with all QRPh-enabled banks</p>
        <p>✓ Instant payment verification</p>
      </div>
    </div>
  );
};

export default PayMongoPayment;
