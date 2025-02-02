import { useState, useEffect, useRef } from 'react';
import { PaperAirplaneIcon, MicrophoneIcon, StopIcon, SunIcon, MoonIcon } from '@heroicons/react/24/solid';
import { useTheme } from './contexts/ThemeContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ProcessingStatus {
  status: 'success' | 'error';
  message: string;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  file?: File;
}

function App() {
  const { theme, toggleTheme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [inputText, setInputText] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Add thumbnail preview URL state
  const [filePreview, setFilePreview] = useState<string | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputText]);

  // Scroll to bottom when messages update
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize WebSocket connection
  useEffect(() => {
    websocketRef.current = new WebSocket('ws://localhost:8080/ws');
    
    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === 'error') {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${data.message}`
        }]);
      }
    };

    return () => {
      websocketRef.current?.close();
    };
  }, []);

  // Update handleFileSelect to create preview URL
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setCurrentFile(file);
      
      // Create preview URL for images
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setFilePreview(url);
      } else if (file.type === 'application/pdf') {
        // Use a PDF icon for PDFs
        setFilePreview('/pdf-icon.svg'); // You'll need to add this icon to your public folder
      }
    }
  };

  // Cleanup preview URL when component unmounts
  useEffect(() => {
    return () => {
      if (filePreview && filePreview.startsWith('blob:')) {
        URL.revokeObjectURL(filePreview);
      }
    };
  }, [filePreview]);

  const handleRecordingStart = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await handleTranscription(audioBlob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const handleRecordingStop = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const handleTranscription = async (audioBlob: Blob) => {
    // TODO: Implement actual Whisper transcription
    // For now, we'll just use the input text
    if (inputText) {
      setMessages(prev => [...prev, {
        role: 'user',
        content: inputText
      }]);
      setInputText('');
    }
  };

  const handleSubmit = async () => {
    if (!inputText && !currentFile) return;
    if (isProcessing) return;

    setIsProcessing(true);

    try {
      // Add user message to chat immediately
      const userMessage: Message = {
        role: 'user',
        content: inputText,
        file: currentFile || undefined
      };
      setMessages(prev => [...prev, userMessage]);

      // Prepare the request
      const requestBody: any = {
        content: inputText || "Please analyze this document",
        role: 'user'
      };

      // If there's a file, include it
      if (currentFile) {
        const fileContent = await currentFile.arrayBuffer();
        requestBody.file = {
          content: Array.from(new Uint8Array(fileContent)),
          type: currentFile.type,
          name: currentFile.name
        };
      }

      // Send to backend
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant's response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response
      }]);
      
      // Clear input and file only after successful submission
      setCurrentFile(null);
      setFilePreview(null);
      setInputText('');
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

    } catch (error) {
      console.error('Error in chat:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Failed to process your message. Please try again.'
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-3xl mx-auto py-3 px-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-800 dark:text-white" text-center>BluApp</h1>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? (
              <MoonIcon className="h-5 w-5 text-gray-600" />
            ) : (
              <SunIcon className="h-5 w-5 text-gray-300" />
            )}
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto dark:bg-gray-900">
        <div className="max-w-3xl mx-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`py-6 px-4 ${
                message.role === 'assistant' 
                  ? 'bg-white dark:bg-gray-800' 
                  : 'bg-gray-50 dark:bg-gray-900'
              }`}
            >
              <div className="max-w-3xl mx-auto flex gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'assistant' ? 'bg-green-500' : 'bg-blue-500'
                } text-white text-sm`}>
                  {message.role === 'assistant' ? 'A' : 'U'}
                </div>
                <div className="flex-1">
                  {message.file && (
                    <div className="mb-4">
                      <div className="flex items-center gap-2 p-2 bg-gray-100 dark:bg-gray-700 rounded-md inline-block">
                        <div className="w-12 h-12 rounded-md overflow-hidden border border-gray-200">
                          {message.file.type.startsWith('image/') ? (
                            <img
                              src={URL.createObjectURL(message.file)}
                              alt="Uploaded file"
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <img
                              src="/pdf-icon.svg"
                              alt="PDF file"
                              className="w-full h-full p-2"
                            />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {message.file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(message.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="prose dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          const language = match ? match[1] : '';
                          
                          if (!inline && language) {
                            return (
                              <SyntaxHighlighter
                                style={oneDark}
                                language={language}
                                PreTag="div"
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            );
                          }
                          
                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-3xl mx-auto p-4">
          <div className="border dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
            {/* File Preview Area */}
            {filePreview && (
              <div className="p-4 border-b">
                <div className="flex items-center gap-2">
                  <div className="relative w-16 h-16 rounded-md overflow-hidden border border-gray-200">
                    <img
                      src={filePreview}
                      alt="File preview"
                      className="w-full h-full object-cover"
                    />
                    <button
                      onClick={() => {
                        setCurrentFile(null);
                        setFilePreview(null);
                      }}
                      className="absolute top-0 right-0 p-1 bg-gray-800/50 hover:bg-gray-800/75 text-white rounded-bl"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {currentFile?.name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {(currentFile?.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Input Area */}
            <div className="flex items-end gap-2 p-2">
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your instructions..."
                className="flex-1 max-h-36 p-2 focus:outline-none resize-none"
                style={{ minHeight: '44px' }}
              />
              <div className="flex items-center gap-2 px-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".pdf,image/*"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-500 hover:text-gray-700"
                  title="Attach file"
                >
                  📎
                </button>
                <button
                  onClick={isRecording ? handleRecordingStop : handleRecordingStart}
                  className={`p-2 rounded-full ${
                    isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'
                  }`}
                  title={isRecording ? 'Stop recording' : 'Start recording'}
                >
                  {isRecording ? (
                    <StopIcon className="h-5 w-5" />
                  ) : (
                    <MicrophoneIcon className="h-5 w-5" />
                  )}
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isProcessing || (!currentFile && !inputText)}
                  className={`p-2 rounded-full ${
                    isProcessing || (!currentFile && !inputText)
                      ? 'text-gray-400'
                      : 'text-blue-500 hover:text-blue-600'
                  }`}
                  title="Send message"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
          <p className="mt-2 text-xs text-center text-gray-500 dark:text-gray-400">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}

export default App; 