import React from 'react';
import { UserIcon } from '@heroicons/react/24/solid';
import { SparklesIcon } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
            <div className={`flex-1 max-w-3xl rounded-lg p-4 
                ${isUser ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-gray-100 dark:bg-gray-800/50'}`}>
                <ReactMarkdown
                    className="prose dark:prose-invert max-w-none text-sm"
                    remarkPlugins={[remarkGfm]}
                    components={{
                        code({ node, inline, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || '');
                            const language = match ? match[1] : '';
                            
                            if (!inline && language) {
                                let content = String(children).replace(/\n$/, '');
                                
                                // Try to format JSON if the language is json
                                if (language === 'json') {
                                    try {
                                        const parsed = JSON.parse(content);
                                        content = JSON.stringify(parsed, null, 2);
                                    } catch (e) {
                                        console.error('Failed to parse JSON:', e);
                                    }
                                }

                                return (
                                    <div className="relative rounded-lg overflow-hidden border border-gray-700">
                                        <div className="flex justify-between items-center bg-gray-800 px-4 py-2">
                                            <span className="text-xs text-gray-400">
                                                {language.toUpperCase()}
                                            </span>
                                            <button
                                                onClick={() => navigator.clipboard.writeText(content)}
                                                className="text-xs text-gray-400 hover:text-white transition-colors"
                                            >
                                                Copy
                                            </button>
                                        </div>
                                        <div className="bg-gray-900">
                                            <SyntaxHighlighter
                                                language={language}
                                                style={oneDark}
                                                customStyle={{
                                                    margin: 0,
                                                    padding: '1rem',
                                                    background: 'transparent',
                                                }}
                                            >
                                                {content}
                                            </SyntaxHighlighter>
                                        </div>
                                    </div>
                                );
                            }

                            return (
                                <code className={className} {...props}>
                                    {children}
                                </code>
                            );
                        },
                        // Style other markdown elements
                        p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-4 last:mb-0">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-4 last:mb-0">{children}</ol>,
                        li: ({ children }) => <li className="mb-1">{children}</li>,
                        a: ({ children, href }) => (
                            <a href={href} className="text-blue-500 hover:text-blue-600 dark:text-blue-400" target="_blank" rel="noopener noreferrer">
                                {children}
                            </a>
                        ),
                    }}
                >
                    {message.content}
                </ReactMarkdown>
            </div>
        </div>
    );
}; 