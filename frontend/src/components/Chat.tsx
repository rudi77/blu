import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { AgentMessage } from '../types/agent';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080';
        const ws = new WebSocket(`${wsUrl}/api/agent/ws`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('Connected to agent');
            setIsConnected(true);
        };

        ws.onclose = () => {
            console.log('Disconnected from agent');
            setIsConnected(false);
        };

        ws.onmessage = (event) => {
            const agentMessage: AgentMessage = JSON.parse(event.data);
            
            switch (agentMessage.type) {
                case 'message':
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: agentMessage.content
                    }]);
                    setIsProcessing(false);
                    break;
                    
                case 'error':
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: `Error: ${agentMessage.content}`
                    }]);
                    setIsProcessing(false);
                    break;
                    
                case 'status':
                    // Handle status updates (optional)
                    console.log('Status:', agentMessage.content);
                    break;
            }
        };

        return () => {
            ws.close();
        };
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !isConnected || isProcessing) return;

        const userMessage = input.trim();
        setMessages(prev => [...prev, {
            role: 'user',
            content: userMessage
        }]);
        
        wsRef.current?.send(JSON.stringify({
            type: 'message',
            content: userMessage
        }));
        
        setIsProcessing(true);
        setInput('');
    };

    const handleFileUpload = async (file: File) => {
        if (!isConnected || isProcessing) return;
        
        try {
            // Read file as base64
            const reader = new FileReader();
            reader.readAsDataURL(file);  // This will give us a data URI
            
            reader.onload = () => {
                const base64Content = reader.result as string;
                
                wsRef.current?.send(JSON.stringify({
                    type: 'document',
                    content: 'Analyze this document',
                    metadata: {
                        file: {
                            content: base64Content,  // Already includes data URI prefix
                            type: file.type
                        }
                    }
                }));
                
                setIsProcessing(true);
            };
            
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `Error processing file: ${error}`
            }]);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                ))}
            </div>
            
            {!isConnected && (
                <div className="p-2 text-center bg-red-100 dark:bg-red-900">
                    <span className="text-red-600 dark:text-red-300">
                        Connecting to agent...
                    </span>
                </div>
            )}
            
            <form onSubmit={handleSubmit} className="p-4 border-t dark:border-gray-700">
                <div className="flex space-x-4">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        className="flex-1 rounded-lg border dark:border-gray-700 dark:bg-gray-800 p-2"
                        placeholder={!isConnected ? "Connecting..." : "Type your message..."}
                        disabled={!isConnected || isProcessing}
                    />
                    <button
                        type="submit"
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={!isConnected || isProcessing}
                    >
                        Send
                    </button>
                </div>
            </form>
        </div>
    );
}; 