import { NextRequest, NextResponse } from 'next/server';
import { SignJWT } from 'jose';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

interface LoginRequest {
  email: string;
  password: string;
}

export async function POST(request: NextRequest) {
  try {
    const { email, password }: LoginRequest = await request.json();

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // TODO: Replace with actual database/user authentication
    // For now, accept any email/password combination for demo purposes
    if (email && password.length >= 8) {
      // Create JWT token
      const token = await new SignJWT({
        email,
        userId: 'demo-user-id',
        role: 'user',
      })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .setExpirationTime('24h')
        .sign(new TextEncoder().encode(JWT_SECRET));

      // Mock user data
      const user = {
        id: 'demo-user-id',
        email,
        name: email.split('@')[0],
        subscription: {
          plan: 'premium',
          status: 'active' as const,
        },
      };

      return NextResponse.json({
        user,
        token,
        message: 'Login successful',
      });
    } else {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}