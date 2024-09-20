// frontend/components/RealtimeUpdates.js

import React from 'react';
import { Card, CardHeader, CardContent, Badge } from '@shadcn/ui';

const RealtimeUpdates = ({ updates }) => {
  return (
    <Card className="mt-8">
      <CardHeader>
        <h2 className="text-xl">Real-time Updates</h2>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {updates.map((update, index) => {
            const isError = update.toLowerCase().includes('error');
            return (
              <div key={index} className="flex items-start">
                <Badge variant={isError ? 'destructive' : 'default'} className="mr-2">
                  {isError ? 'Error' : 'Info'}
                </Badge>
                <p>{new Date().toLocaleTimeString()}: {update}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default RealtimeUpdates;
