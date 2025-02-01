import React from 'react';
import { UserIcon } from '@heroicons/react/24/solid';
import { SparklesIcon } from '@heroicons/react/24/solid';

interface ChatMessageProps {
    message: {
        role: 'user' | 'assistant';
        content: string;
    };
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const isUser = message.role === 'user';
    
    return (
        <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center 
                ${isUser ? 'bg-blue-500' : 'bg-purple-500'}`}>
                {isUser ? (
                    <UserIcon className="w-5 h-5 text-white" />
                ) : (
                    <SparklesIcon className="w-5 h-5 text-white" />
                )}
            </div>
            <div className={`flex-1 max-w-2xl rounded-lg p-3 
                ${isUser ? 'bg-blue-100 dark:bg-blue-900' : 'bg-gray-100 dark:bg-gray-800'}`}>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
}; 