import { redirect } from 'next/navigation';

export default function HomePage() {
  // For now, redirect to dashboard
  // In a real app, this would check authentication status
  redirect('/dashboard');
}