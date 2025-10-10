import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Authorization header missing or invalid' },
        { status: 401 }
      );
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify JWT token
    const { payload } = await jwtVerify(token, new TextEncoder().encode(JWT_SECRET));

    // TODO: Replace with actual database lookup
    // For now, return mock user data based on token payload
    const user = {
      id: payload.userId as string,
      email: payload.email as string,
      name: (payload.email as string).split('@')[0],
      subscription: {
        plan: 'premium',
        status: 'active' as const,
      },
    };

    return NextResponse.json(user);
  } catch (error) {
    console.error('Token verification error:', error);
    return NextResponse.json(
      { error: 'Invalid or expired token' },
      { status: 401 }
    );
  }
}