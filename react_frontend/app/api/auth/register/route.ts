import { NextRequest, NextResponse } from 'next/server';
import { SignJWT } from 'jose';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

interface RegisterRequest {
  email: string;
  password: string;
}

export async function POST(request: NextRequest) {
  try {
    const { email, password }: RegisterRequest = await request.json();

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: 'Password must be at least 8 characters long' },
        { status: 500 }
      );
    }

    // TODO: Replace with actual database/user creation
    // For now, accept any email/password combination for demo purposes
    if (email && password) {
      // Create JWT token
      const token = await new SignJWT({
        email,
        userId: `user-${Date.now()}`,
        role: 'user',
      })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .setExpirationTime('24h')
        .sign(new TextEncoder().encode(JWT_SECRET));

      // Mock user data
      const user = {
        id: `user-${Date.now()}`,
        email,
        name: email.split('@')[0],
        subscription: {
          plan: 'free',
          status: 'active' as const,
        },
      };

      return NextResponse.json({
        user,
        token,
        message: 'Registration successful',
      });
    } else {
      return NextResponse.json(
        { error: 'Registration failed' },
        { status: 400 }
      );
    }
  } catch (error) {
    console.error('Registration error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}