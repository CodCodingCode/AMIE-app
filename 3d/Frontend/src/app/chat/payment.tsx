import React, { useState, useEffect } from 'react';
import { loadStripe, Stripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface PaymentFormProps {
  onSuccess: (sessionId: string) => void;
  onError: (error: string) => void;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [clientSecret, setClientSecret] = useState<string>('');

  useEffect(() => {
    // Create PaymentIntent on component mount
    fetch('/api/create-payment-intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: 2900, // $29.00 CAD
        currency: 'cad',
        metadata: {
          consultation_type: 'bluebox_live',
          product_id: 'prod_SQ8bVU4D13hCdP'
        }
      }),
    })
      .then((res) => res.json())
      .then((data) => setClientSecret(data.client_secret))
      .catch((error) => onError('Failed to initialize payment'));
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) return;

    setLoading(true);

    const card = elements.getElement(CardElement);
    if (!card) return;

    const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
      payment_method: {
        card: card,
        billing_details: {
          name: 'Customer', // You can collect this from a form
        },
      },
    });

    if (error) {
      onError(error.message || 'Payment failed');
      setLoading(false);
    } else {
      onSuccess(paymentIntent.id);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="payment-form">
      <div className="card-element-container">
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                  color: '#aab7c4',
                },
                fontFamily: 'system-ui, -apple-system, sans-serif',
              },
              invalid: {
                color: '#9e2146',
              },
            },
          }}
        />
      </div>
      
      <button
        type="submit"
        disabled={!stripe || loading}
        className={`pay-button ${loading ? 'loading' : ''}`}
      >
        {loading ? (
          <div className="loading-spinner" />
        ) : (
          'Pay $29.00 CAD'
        )}
      </button>
    </form>
  );
};

interface BlueboxPaymentProps {
  onPaymentSuccess?: (sessionId: string) => void;
  onPaymentError?: (error: string) => void;
}

const BlueboxPayment: React.FC<BlueboxPaymentProps> = ({
  onPaymentSuccess,
  onPaymentError,
}) => {
  const [paymentMethod, setPaymentMethod] = useState<'checkout' | 'elements'>('checkout');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);

  const handleCheckoutPayment = async () => {
    try {
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_ID, // Your price ID from Stripe
          quantity: 1,
          metadata: {
            consultation_type: 'bluebox_live'
          }
        }),
      });

      const session = await response.json();
      
      const stripe = await stripePromise;
      if (!stripe) throw new Error('Stripe failed to load');

      const result = await stripe.redirectToCheckout({
        sessionId: session.id,
      });

      if (result.error) {
        setError(result.error.message || 'Payment failed');
        onPaymentError?.(result.error.message || 'Payment failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Payment failed';
      setError(errorMessage);
      onPaymentError?.(errorMessage);
    }
  };

  const handleElementsSuccess = (sessionId: string) => {
    setSuccess(true);
    onPaymentSuccess?.(sessionId);
  };

  const handleElementsError = (error: string) => {
    setError(error);
    onPaymentError?.(error);
  };

  if (success) {
    return (
      <div className="payment-container">
        <div className="success-message">
          <div className="success-icon">✓</div>
          <h2>Payment Successful!</h2>
          <p>Your Bluebox Live Consultation has been booked.</p>
          <p>You will receive a confirmation email shortly with next steps.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-container">
      <div className="consultation-header">
        <div className="consultation-icon">🩺</div>
        <h1>Bluebox Live Consultation</h1>
        <p className="consultation-tagline">Talk to certified Bluebox Physicians!</p>
      </div>

      <div className="pricing-card">
        <div className="price-header">
          <span className="price">$29.00</span>
          <span className="currency">CAD</span>
        </div>
        <div className="price-details">
          <div className="detail-item">
            <span className="detail-label">Duration:</span>
            <span className="detail-value">1 Hour</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Type:</span>
            <span className="detail-value">Live Video Call</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Available:</span>
            <span className="detail-value">24/7</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      <div className="payment-methods">
        <div className="method-selector">
          <button
            className={`method-tab ${paymentMethod === 'checkout' ? 'active' : ''}`}
            onClick={() => setPaymentMethod('checkout')}
          >
            Quick Checkout
          </button>
          <button
            className={`method-tab ${paymentMethod === 'elements' ? 'active' : ''}`}
            onClick={() => setPaymentMethod('elements')}
          >
            Custom Payment
          </button>
        </div>

        {paymentMethod === 'checkout' ? (
          <div className="checkout-method">
            <p className="method-description">
              Secure checkout powered by Stripe. Supports all major payment methods.
            </p>
            <button className="checkout-button" onClick={handleCheckoutPayment}>
              <span className="button-icon">🔒</span>
              Pay with Stripe Checkout
            </button>
          </div>
        ) : (
          <div className="elements-method">
            <p className="method-description">
              Enter your payment details directly below.
            </p>
            <Elements stripe={stripePromise}>
              <PaymentForm
                onSuccess={handleElementsSuccess}
                onError={handleElementsError}
              />
            </Elements>
          </div>
        )}
      </div>

      <div className="security-badges">
        <div className="badge">
          <span className="badge-icon">🔒</span>
          <span>256-bit SSL</span>
        </div>
        <div className="badge">
          <span className="badge-icon">💳</span>
          <span>PCI Compliant</span>
        </div>
        <div className="badge">
          <span className="badge-icon">🛡️</span>
          <span>Stripe Secure</span>
        </div>
      </div>

      <style jsx>{`
        .payment-container {
          max-width: 500px;
          margin: 0 auto;
          padding: 2rem;
          font-family: system-ui, -apple-system, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .consultation-header {
          text-align: center;
          margin-bottom: 2rem;
          color: white;
        }

        .consultation-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .consultation-header h1 {
          margin: 0 0 0.5rem 0;
          font-size: 2rem;
          font-weight: 700;
        }

        .consultation-tagline {
          opacity: 0.9;
          font-size: 1.1rem;
          margin: 0;
        }

        .pricing-card {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .price-header {
          text-align: center;
          margin-bottom: 1.5rem;
        }

        .price {
          font-size: 3rem;
          font-weight: 800;
          color: #2d3748;
        }

        .currency {
          font-size: 1.5rem;
          color: #718096;
          margin-left: 0.5rem;
        }

        .price-details {
          border-top: 1px solid #e2e8f0;
          padding-top: 1.5rem;
        }

        .detail-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }

        .detail-label {
          color: #718096;
          font-weight: 500;
        }

        .detail-value {
          color: #2d3748;
          font-weight: 600;
        }

        .error-message {
          background: #fed7d7;
          color: #c53030;
          padding: 1rem;
          border-radius: 0.5rem;
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .payment-methods {
          background: white;
          border-radius: 1rem;
          overflow: hidden;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
          margin-bottom: 2rem;
        }

        .method-selector {
          display: flex;
          background: #f7fafc;
        }

        .method-tab {
          flex: 1;
          padding: 1rem;
          border: none;
          background: transparent;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .method-tab.active {
          background: white;
          color: #667eea;
          border-bottom: 2px solid #667eea;
        }

        .checkout-method,
        .elements-method {
          padding: 2rem;
        }

        .method-description {
          color: #718096;
          margin-bottom: 1.5rem;
          text-align: center;
        }

        .checkout-button {
          width: 100%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 1rem 2rem;
          border-radius: 0.75rem;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .checkout-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .payment-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .card-element-container {
          padding: 1rem;
          border: 2px solid #e2e8f0;
          border-radius: 0.5rem;
          transition: border-color 0.2s;
        }

        .card-element-container:focus-within {
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .pay-button {
          background: #48bb78;
          color: white;
          border: none;
          padding: 1rem 2rem;
          border-radius: 0.75rem;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 52px;
        }

        .pay-button:hover {
          background: #38a169;
          transform: translateY(-1px);
        }

        .pay-button:disabled {
          background: #a0aec0;
          cursor: not-allowed;
          transform: none;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid transparent;
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .security-badges {
          display: flex;
          justify-content: center;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .badge {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          color: white;
          opacity: 0.8;
          font-size: 0.9rem;
        }

        .success-message {
          background: white;
          border-radius: 1rem;
          padding: 3rem 2rem;
          text-align: center;
          box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        .success-icon {
          width: 4rem;
          height: 4rem;
          background: #48bb78;
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
          margin: 0 auto 1.5rem;
        }

        .success-message h2 {
          color: #2d3748;
          margin-bottom: 1rem;
        }

        .success-message p {
          color: #718096;
          margin-bottom: 0.5rem;
        }
      `}</style>
    </div>
  );
};

export default BlueboxPayment;