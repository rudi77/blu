import React, { useEffect, useRef, useState } from 'react';
import { AgentStep, AgentWebSocketMessage } from '../../types/agent';
import { AgentProgress } from './AgentProgress';

interface AgentWebSocketProps {
    onMessage: (message: string) => void;
    onError: (error: string) => void;
    onSendMessage: (sendFn: (message: string, context?: Record<string, any>) => void) => void;
}

export const AgentWebSocket: React.FC<AgentWebSocketProps> = ({ 
    onMessage, 
    onError,
    onSendMessage 
}) => {
    const [steps, setSteps] = useState<AgentStep[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        // Get WebSocket URL from environment
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        
        // Connect to WebSocket with retry logic
        const connectWebSocket = () => {
            try {
                const ws = new WebSocket(`${wsUrl}/api/agent/ws`);
                wsRef.current = ws;

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    setIsConnected(true);
                };

                ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    setIsConnected(false);
                    // Retry connection after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    onError('Connection error. Retrying...');
                };

                ws.onmessage = (event) => {
                    const message: AgentWebSocketMessage = JSON.parse(event.data);
                    
                    if (message.type === 'error') {
                        onError(message.detail || 'Unknown error occurred');
                        setIsLoading(false);
                        return;
                    }
                    
                    if (message.type === 'step_update' && message.step) {
                        setSteps(prev => [...prev, message.step!]);
                        
                        // If this step has a final answer, we're done
                        if (message.step.action_output) {
                            setIsLoading(false);
                            onMessage(message.step.action_output);
                        }
                    }
                };

            } catch (error) {
                console.error('WebSocket connection error:', error);
                onError('Failed to connect. Retrying...');
                setTimeout(connectWebSocket, 3000);
            }
        };

        connectWebSocket();

        // Expose sendMessage function to parent
        onSendMessage(sendMessage);

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [onMessage, onError, onSendMessage]);

    const sendMessage = (message: string, context?: Record<string, any>) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            setIsLoading(true);
            setSteps([]);
            wsRef.current.send(JSON.stringify({
                message,
                context
            }));
        } else {
            onError('WebSocket is not connected. Please wait...');
        }
    };

    return (
        <div className="space-y-4">
            {!isConnected && (
                <div className="text-red-500 text-sm flex items-center space-x-2">
                    <div className="animate-pulse h-2 w-2 rounded-full bg-red-500" />
                    <span>Connecting to agent service...</span>
                </div>
            )}
            <AgentProgress steps={steps} isLoading={isLoading} />
        </div>
    );
}; 