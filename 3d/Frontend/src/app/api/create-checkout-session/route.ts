import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-05-28.basil',
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { priceId, quantity = 1, metadata = {} } = body;

    // Get the base URL for redirects
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 
                   `https://${request.headers.get('host')}` || 
                   'http://localhost:3000';

    let sessionConfig: Stripe.Checkout.SessionCreateParams;

    if (priceId) {
      // Use existing Stripe Price ID
      sessionConfig = {
        line_items: [
          {
            price: priceId,
            quantity: quantity,
          },
        ],
      };
    } else {
      // Create price on-the-fly for Bluebox consultation
      sessionConfig = {
        line_items: [
          {
            price_data: {
              currency: 'cad',
              product_data: {
                name: 'Bluebox Live Consultation',
                description: '1-hour video consultation with certified Bluebox physicians',
                images: [],
                metadata: {
                  product_type: 'consultation',
                  duration: '1_hour',
                  availability: '24_7',
                },
              },
              unit_amount: 2900, // $29.00 CAD in cents
            },
            quantity: 1,
          },
        ],
      };
    }

    const session = await stripe.checkout.sessions.create({
      ...sessionConfig,
      mode: 'payment',
      success_url: `${baseUrl}/payment/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${baseUrl}/payment/cancel`,
      metadata: {
        ...metadata,
        created_at: new Date().toISOString(),
      },
      customer_creation: 'always',
      phone_number_collection: {
        enabled: true,
      },
      payment_method_types: ['card'],
      custom_fields: [
        {
          key: 'consultation_reason',
          label: {
            type: 'custom',
            custom: 'What would you like to discuss?',
          },
          type: 'text',
          optional: true,
        },
      ],
    });

    return NextResponse.json({ 
      id: session.id,
      url: session.url 
    });
  } catch (error) {
    console.error('Checkout Session Error:', error);
    
    if (error instanceof Stripe.errors.StripeError) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}