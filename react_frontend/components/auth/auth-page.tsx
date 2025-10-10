'use client';

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { LoginForm } from './login-form';
import { RegisterForm } from './register-form';
import { useAuth } from '@/lib/auth-context';
import { toastAlert } from '@/components/alert-toast';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const { login, register, isLoading } = useAuth();

  const handleLogin = async (email: string, password: string) => {
    try {
      await login(email, password);
      toastAlert({
        title: 'Welcome back!',
        description: 'You have been successfully logged in.',
      });
    } catch (error) {
      toastAlert({
        title: 'Login Failed',
        description: error instanceof Error ? error.message : 'An error occurred during login.',
      });
      throw error;
    }
  };

  const handleRegister = async (email: string, password: string, confirmPassword: string) => {
    try {
      await register(email, password);
      toastAlert({
        title: 'Welcome to Felicia\'s Finance!',
        description: 'Your account has been created successfully.',
      });
    } catch (error) {
      toastAlert({
        title: 'Registration Failed',
        description: error instanceof Error ? error.message : 'An error occurred during registration.',
      });
      throw error;
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />

      <motion.div
        key={isLogin ? 'login' : 'register'}
        initial={{ opacity: 0, x: isLogin ? -20 : 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: isLogin ? 20 : -20 }}
        transition={{ duration: 0.3 }}
        className="relative z-10"
      >
        {isLogin ? (
          <LoginForm
            onLogin={handleLogin}
            onSwitchToRegister={() => setIsLogin(false)}
            isLoading={isLoading}
          />
        ) : (
          <RegisterForm
            onRegister={handleRegister}
            onSwitchToLogin={() => setIsLogin(true)}
            isLoading={isLoading}
          />
        )}
      </motion.div>
    </div>
  );
}