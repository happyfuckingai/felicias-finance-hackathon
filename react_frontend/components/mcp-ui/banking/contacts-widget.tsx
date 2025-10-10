import React from 'react';
import { Link, Plus, User } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface ContactsWidgetProps {
  component: MCPUIComponent;
}

export function ContactsWidget({ component }: ContactsWidgetProps) {
  const { title, items = [], actions = [], emptyState } = component;

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {title || 'Contacts'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <div className="py-6 text-center">
            <User className="text-muted-foreground mx-auto mb-2 h-8 w-8" />
            <p className="text-muted-foreground text-sm">{emptyState || 'No contacts found'}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((contact: any, index: number) => (
              <div
                key={index}
                className="bg-muted/50 flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center space-x-3">
                  <div className="bg-primary/10 flex h-8 w-8 items-center justify-center rounded-full">
                    <User className="text-primary h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{contact.name || contact.label}</p>
                    <p className="text-muted-foreground text-xs">
                      {contact.account}
                      {contact.routing && ` • ${contact.routing}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  {contact.type === 'external' && (
                    <Link className="text-muted-foreground h-3 w-3" />
                  )}
                  {contact.actions?.includes('pay') && (
                    <Button size="sm" variant="outline">
                      Pay
                    </Button>
                  )}
                  {contact.actions?.includes('transfer') && (
                    <Button size="sm" variant="outline">
                      Transfer
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {actions.length > 0 && (
          <div className="mt-4 flex gap-2">
            {actions.map((action: any, index: number) => (
              <Button
                key={index}
                size="sm"
                variant={action.type === 'button' ? 'outline' : 'default'}
                className="flex-1"
              >
                {action.id === 'add_contact' && <Plus className="mr-2 h-4 w-4" />}
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
