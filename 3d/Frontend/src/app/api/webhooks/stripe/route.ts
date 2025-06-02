import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-05-28.basil',
});

const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(request: NextRequest) {
  const body = await request.text();
  const sig = request.headers.get('stripe-signature') as string;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, sig, endpointSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json(
      { error: `Webhook Error: ${err}` },
      { status: 400 }
    );
  }

  // Handle the event
  try {
    switch (event.type) {
      case 'payment_intent.succeeded':
        const paymentIntent = event.data.object as Stripe.PaymentIntent;
        console.log('✅ Payment succeeded:', paymentIntent.id);
        
        // TODO: Add your business logic here
        // - Update database with successful payment
        // - Send confirmation email
        // - Schedule consultation
        // - Create user account if needed
        
        await handlePaymentSuccess(paymentIntent);
        break;

      case 'payment_intent.payment_failed':
        const failedPayment = event.data.object as Stripe.PaymentIntent;
        console.log('❌ Payment failed:', failedPayment.id);
        
        await handlePaymentFailure(failedPayment);
        break;

      case 'checkout.session.completed':
        const session = event.data.object as Stripe.Checkout.Session;
        console.log('✅ Checkout session completed:', session.id);
        
        await handleCheckoutSuccess(session);
        break;

      case 'checkout.session.expired':
        const expiredSession = event.data.object as Stripe.Checkout.Session;
        console.log('🕐 Checkout session expired:', expiredSession.id);
        break;

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Error handling webhook:', error);
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 500 }
    );
  }
}

async function handlePaymentSuccess(paymentIntent: Stripe.PaymentIntent) {
  try {
    // Example: Save to database
    // const consultation = await createConsultation({
    //   paymentIntentId: paymentIntent.id,
    //   amount: paymentIntent.amount,
    //   currency: paymentIntent.currency,
    //   customerEmail: paymentIntent.receipt_email,
    //   metadata: paymentIntent.metadata,
    // });

    // Example: Send confirmation email
    // await sendConsultationConfirmationEmail({
    //   email: paymentIntent.receipt_email,
    //   consultationId: consultation.id,
    //   amount: paymentIntent.amount / 100, // Convert from cents
    // });

    console.log('Payment success handling completed');
  } catch (error) {
    console.error('Error handling payment success:', error);
    throw error;
  }
}

async function handlePaymentFailure(paymentIntent: Stripe.PaymentIntent) {
  try {
    // Example: Log failure, maybe send email to customer with payment link
    console.log('Payment failed for:', paymentIntent.id);
    
    // You might want to:
    // - Send an email with a new payment link
    // - Log the failure for analysis
    // - Update user's payment status in your database
    
  } catch (error) {
    console.error('Error handling payment failure:', error);
    throw error;
  }
}

async function handleCheckoutSuccess(session: Stripe.Checkout.Session) {
  try {
    // Retrieve the full session with line items
    const fullSession = await stripe.checkout.sessions.retrieve(session.id, {
      expand: ['line_items', 'customer'],
    });

    console.log('Checkout completed:', {
      sessionId: session.id,
      customerEmail: session.customer_details?.email,
      amount: session.amount_total,
      customFields: session.custom_fields,
    });

    // TODO: Add your business logic here
    // This is similar to handlePaymentSuccess but for Checkout sessions
    
  } catch (error) {
    console.error('Error handling checkout success:', error);
    throw error;
  }
}