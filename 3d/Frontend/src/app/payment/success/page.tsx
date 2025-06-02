import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';

interface SessionData {
  id: string;
  customer_email: string;
  amount_total: number;
  currency: string;
  status: string;
}

const PaymentSuccess: React.FC = () => {
  const router = useRouter();
  const { session_id } = router.query;
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (session_id && typeof session_id === 'string') {
      fetchSessionData(session_id);
    }
  }, [session_id]);

  const fetchSessionData = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/get-checkout-session?session_id=${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch session data');
      }
      
      const data = await response.json();
      setSessionData(data);
    } catch (err) {
      console.error('Error fetching session:', err);
      setError('Unable to verify payment. Please contact support if you were charged.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="success-container">
        <div className="loading-spinner" />
        <p>Verifying your payment...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="success-container">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <h2>Payment Verification Error</h2>
          <p>{error}</p>
          <Link href="/support" className="support-link">
            Contact Support
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="success-container">
      <div className="success-card">
        <div className="success-icon">✅</div>
        
        <h1>Payment Successful!</h1>
        <p className="success-subtitle">
          Your Bluebox Live Consultation has been booked successfully.
        </p>

        {sessionData && (
          <div className="payment-details">
            <div className="detail-row">
              <span className="label">Amount Paid:</span>
              <span className="value">
                ${(sessionData.amount_total / 100).toFixed(2)} {sessionData.currency.toUpperCase()}
              </span>
            </div>
            <div className="detail-row">
              <span className="label">Email:</span>
              <span className="value">{sessionData.customer_email}</span>
            </div>
            <div className="detail-row">
              <span className="label">Session ID:</span>
              <span className="value session-id">{sessionData.id}</span>
            </div>
          </div>
        )}

        <div className="next-steps">
          <h3>What happens next?</h3>
          <div className="steps">
            <div className="step">
              <span className="step-number">1</span>
              <span className="step-text">You'll receive a confirmation email shortly</span>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <span className="step-text">A Bluebox physician will contact you within 24 hours</span>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <span className="step-text">Schedule your 1-hour video consultation</span>
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <Link href="/dashboard" className="primary-button">
            Go to Dashboard
          </Link>
          <Link href="/" className="secondary-button">
            Back to Home
          </Link>
        </div>
      </div>

      <style jsx>{`
        .success-container {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          font-family: system-ui, -apple-system, sans-serif;
        }

        .success-card {
          background: white;
          border-radius: 1rem;
          padding: 3rem 2rem;
          max-width: 500px;
          width: 100%;
          text-align: center;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .success-icon {
          font-size: 4rem;
          margin-bottom: 1.5rem;
        }

        .success-card h1 {
          color: #2d3748;
          margin-bottom: 0.5rem;
          font-size: 2rem;
        }

        .success-subtitle {
          color: #718096;
          font-size: 1.1rem;
          margin-bottom: 2rem;
        }

        .payment-details {
          background: #f7fafc;
          border-radius: 0.5rem;
          padding: 1.5rem;
          margin-bottom: 2rem;
          text-align: left;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }

        .detail-row:last-child {
          margin-bottom: 0;
        }

        .label {
          color: #718096;
          font-weight: 500;
        }

        .value {
          color: #2d3748;
          font-weight: 600;
        }

        .session-id {
          font-family: monospace;
          font-size: 0.85rem;
        }

        .next-steps {
          margin-bottom: 2rem;
          text-align: left;
        }

        .next-steps h3 {
          color: #2d3748;
          margin-bottom: 1rem;
          text-align: center;
        }

        .steps {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .step {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .step-number {
          background: #667eea;
          color: white;
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          flex-shrink: 0;
        }

        .step-text {
          color: #4a5568;
        }

        .action-buttons {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .primary-button, .secondary-button {
          flex: 1;
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          text-decoration: none;
          font-weight: 600;
          text-align: center;
          transition: all 0.2s;
          min-width: 140px;
        }

        .primary-button {
          background: #667eea;
          color: white;
        }

        .primary-button:hover {
          background: #5a67d8;
          transform: translateY(-1px);
        }

        .secondary-button {
          background: #e2e8f0;
          color: #4a5568;
        }

        .secondary-button:hover {
          background: #cbd5e0;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255,255,255,0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          text-align: center;
        }

        .error-icon {
          font-size: 3rem;
          display: block;
          margin-bottom: 1rem;
        }

        .support-link {
          display: inline-block;
          margin-top: 1rem;
          padding: 0.5rem 1rem;
          background: #e53e3e;
          color: white;
          text-decoration: none;
          border-radius: 0.25rem;
        }
      `}</style>
    </div>
  );
};

export default PaymentSuccess;