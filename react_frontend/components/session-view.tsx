'use client';

import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  type AgentState,
  type ReceivedChatMessage,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import { ChartBar, Chat, Gear } from '@phosphor-icons/react';
import { toastAlert } from '@/components/alert-toast';
import { AgentControlBar } from '@/components/livekit/agent-control-bar/agent-control-bar';
import { ChatEntry } from '@/components/livekit/chat/chat-entry';
import { ChatMessageView } from '@/components/livekit/chat/chat-message-view';
import { MediaTiles } from '@/components/livekit/media-tiles';
import { MCPUIDashboardComponent } from '@/components/mcp-ui-dashboard';
import { Button } from '@/components/ui/button';
import useChatAndTranscription from '@/hooks/useChatAndTranscription';
import { useDebugMode } from '@/hooks/useDebug';
import { useMCPUI } from '@/hooks/useMCPUI';
import type { AppConfig } from '@/lib/types';
import { cn } from '@/lib/utils';

function isAgentAvailable(agentState: AgentState) {
  return agentState == 'listening' || agentState == 'thinking' || agentState == 'speaking';
}

interface SessionViewProps {
  appConfig: AppConfig;
  disabled: boolean;
  sessionStarted: boolean;
}

export const SessionView = ({
  appConfig,
  disabled,
  sessionStarted,
  ref,
}: React.ComponentProps<'div'> & SessionViewProps) => {
  const { state: agentState } = useVoiceAssistant();
  const [chatOpen, setChatOpen] = useState(false);
  const [dashboardOpen, setDashboardOpen] = useState(false);
  const { messages, send } = useChatAndTranscription();
  const room = useRoomContext();

  const mcpUI = useMCPUI();

  // Set a demo auth token for development
  React.useEffect(() => {
    if (sessionStarted && !mcpUI.authToken) {
      mcpUI.setAuthToken('demo-token-123');
    }
  }, [sessionStarted, mcpUI]);

  useDebugMode({
    enabled: process.env.NODE_END !== 'production',
  });

  async function handleSendMessage(message: string) {
    await send(message);
  }

  useEffect(() => {
    if (sessionStarted) {
      const timeout = setTimeout(() => {
        if (!isAgentAvailable(agentState)) {
          const reason =
            agentState === 'connecting'
              ? 'Agent did not join the room. '
              : 'Agent connected but did not complete initializing. ';

          toastAlert({
            title: 'Session ended',
            description: (
              <p className="w-full">
                {reason}
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://docs.livekit.io/agents/start/voice-ai/"
                  className="whitespace-nowrap underline"
                >
                  See quickstart guide
                </a>
                .
              </p>
            ),
          });
          room.disconnect();
        }
      }, 20_000);

      return () => clearTimeout(timeout);
    }
  }, [agentState, sessionStarted, room]);

  const { supportsChatInput, supportsVideoInput, supportsScreenShare } = appConfig;
  const capabilities = {
    supportsChatInput,
    supportsVideoInput,
    supportsScreenShare,
  };

  return (
    <section
      ref={ref}
      inert={disabled}
      className={cn(
        'flex opacity-0',
        // prevent page scrollbar
        // when !chatOpen due to 'translate-y-20'
        !chatOpen && !dashboardOpen && 'max-h-svh overflow-hidden'
      )}
    >
      {/* Dashboard Panel */}
      <div
        className={cn(
          'flex-1 transition-[opacity,transform] duration-300 ease-out',
          dashboardOpen ? 'translate-x-0 opacity-100' : '-translate-x-full opacity-0',
          dashboardOpen ? 'block' : 'hidden md:block md:flex-1'
        )}
      >
        <div className="bg-muted/20 h-full overflow-y-auto p-4">
          {mcpUI.currentView === 'banking' && mcpUI.bankingDashboard && (
            <MCPUIDashboardComponent dashboard={mcpUI.bankingDashboard} />
          )}
          {mcpUI.currentView === 'crypto' && mcpUI.cryptoDashboard && (
            <MCPUIDashboardComponent dashboard={mcpUI.cryptoDashboard} />
          )}
          {(!mcpUI.currentView || mcpUI.loading) && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <ChartBar className="text-muted-foreground mx-auto mb-4 h-12 w-12" />
                <p className="text-muted-foreground">
                  {mcpUI.loading ? 'Loading dashboard...' : 'Select Banking or Crypto to view data'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat Panel */}
      <ChatMessageView
        className={cn(
          'mx-auto min-h-svh w-full max-w-2xl px-3 pt-32 pb-40 transition-[opacity,translate] duration-300 ease-out md:px-0 md:pt-36 md:pb-48',
          chatOpen
            ? 'flex-1 translate-y-0 opacity-100 delay-200'
            : 'flex-1 translate-y-20 opacity-0 md:flex-none',
          dashboardOpen ? 'md:flex-1' : 'md:flex-none'
        )}
      >
        <div className="space-y-3 whitespace-pre-wrap">
          <AnimatePresence>
            {messages.map((message: ReceivedChatMessage) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 1, height: 'auto', translateY: 0.001 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              >
                <ChatEntry hideName entry={message} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </ChatMessageView>

      <div className="bg-background mp-12 fixed top-0 right-0 left-0 h-32 md:h-36">
        {/* skrim */}
        <div className="from-background absolute bottom-0 left-0 h-12 w-full translate-y-full bg-gradient-to-b to-transparent" />
      </div>

      <MediaTiles chatOpen={chatOpen} />

      <div className="bg-background fixed right-0 bottom-0 left-0 z-50 px-3 pt-2 pb-3 md:px-12 md:pb-12">
        <motion.div
          key="control-bar"
          initial={{ opacity: 0, translateY: '100%' }}
          animate={{
            opacity: sessionStarted ? 1 : 0,
            translateY: sessionStarted ? '0%' : '100%',
          }}
          transition={{ duration: 0.3, delay: sessionStarted ? 0.5 : 0, ease: 'easeOut' }}
        >
          <div className="relative z-10 mx-auto w-full max-w-2xl">
            {appConfig.isPreConnectBufferEnabled && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{
                  opacity: sessionStarted && messages.length === 0 ? 1 : 0,
                  transition: {
                    ease: 'easeIn',
                    delay: messages.length > 0 ? 0 : 0.8,
                    duration: messages.length > 0 ? 0.2 : 0.5,
                  },
                }}
                aria-hidden={messages.length > 0}
                className={cn(
                  'absolute inset-x-0 -top-12 text-center',
                  sessionStarted && messages.length === 0 && 'pointer-events-none'
                )}
              >
                <p className="animate-text-shimmer inline-block !bg-clip-text text-sm font-semibold text-transparent">
                  Agent is listening, ask it a question
                </p>
              </motion.div>
            )}

            <div className="flex flex-col space-y-2">
              {/* Dashboard Toggle Buttons */}
              <div className="mb-2 flex justify-center space-x-2">
                <Button
                  size="sm"
                  variant={mcpUI.currentView === 'banking' ? 'default' : 'outline'}
                  onClick={() => {
                    if (mcpUI.currentView !== 'banking') {
                      mcpUI.switchToBanking();
                    }
                    setDashboardOpen(true);
                  }}
                  className="flex items-center space-x-1"
                >
                  <ChartBar className="h-4 w-4" />
                  <span className="hidden sm:inline">Banking</span>
                </Button>
                <Button
                  size="sm"
                  variant={mcpUI.currentView === 'crypto' ? 'default' : 'outline'}
                  onClick={() => {
                    if (mcpUI.currentView !== 'crypto') {
                      mcpUI.switchToCrypto();
                    }
                    setDashboardOpen(true);
                  }}
                  className="flex items-center space-x-1"
                >
                  <ChartBar className="h-4 w-4" />
                  <span className="hidden sm:inline">Crypto</span>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setDashboardOpen(!dashboardOpen)}
                  className="flex items-center space-x-1"
                >
                  <Gear className="h-4 w-4" />
                  <span className="hidden sm:inline">Dashboard</span>
                </Button>
              </div>

              <AgentControlBar
                capabilities={capabilities}
                onChatOpenChange={setChatOpen}
                onSendMessage={handleSendMessage}
              />
            </div>
          </div>
          {/* skrim */}
          <div className="from-background border-background absolute top-0 left-0 h-12 w-full -translate-y-full bg-gradient-to-t to-transparent" />
        </motion.div>
      </div>
    </section>
  );
};
