'use client';

import React from 'react';
import { AuthProvider } from '@/lib/auth-context';
import { Provider as LiveKitProvider } from './provider';
import { AppConfig } from '@/lib/types';

export function AppProvider({
  appConfig,
  children,
}: {
  appConfig: AppConfig;
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <LiveKitProvider appConfig={appConfig}>
        {children}
      </LiveKitProvider>
    </AuthProvider>
  );
}