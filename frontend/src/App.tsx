import { useState, useEffect, useRef } from 'react';
import { PaperAirplaneIcon, MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';

interface ProcessingStatus {
  status: 'success' | 'error';
  message: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  file?: File;
  generatedPrompt?: string;
}

function App() {
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
    websocketRef.current = new WebSocket('ws://localhost:5173/ws');
    
    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.status === 'success') {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: data.message
        }]);
      }
    };

    return () => {
      websocketRef.current?.close();
    };
  }, []);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setCurrentFile(file);
      setMessages(prev => [...prev, {
        type: 'user',
        content: 'Can you help me extract information from this document?',
        file: file
      }]);
    }
  };

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
        type: 'user',
        content: inputText
      }]);
      setInputText('');
    }
  };

  const handleSubmit = async () => {
    if (!currentFile || !inputText) return;

    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', currentFile);
      formData.append('instruction_text', inputText);

      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: 'Here is the generated prompt:',
        generatedPrompt: data.generated_prompt
      }]);
      
      setCurrentFile(null);
      setInputText('');
    } catch (error) {
      console.error('Error processing document:', error);
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
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto py-3 px-4">
          <h1 className="text-xl font-semibold text-gray-800">BluApp</h1>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`py-6 px-4 ${
                message.type === 'assistant' ? 'bg-white' : 'bg-gray-50'
              }`}
            >
              <div className="max-w-3xl mx-auto flex gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'assistant' ? 'bg-green-500' : 'bg-blue-500'
                } text-white text-sm`}>
                  {message.type === 'assistant' ? 'A' : 'U'}
                </div>
                <div className="flex-1">
                  {message.file && (
                    <div className="mb-2 p-2 bg-gray-100 rounded-md inline-block">
                      <p className="text-sm text-gray-600">📎 {message.file.name}</p>
                    </div>
                  )}
                  <p className="text-gray-800">{message.content}</p>
                  {message.generatedPrompt && (
                    <pre className="mt-4 p-4 bg-gray-100 rounded-md text-sm whitespace-pre-wrap text-gray-800 font-mono">
                      {message.generatedPrompt}
                    </pre>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white">
        <div className="max-w-3xl mx-auto p-4">
          <div className="border rounded-lg bg-white shadow-sm">
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
                  disabled={isProcessing || !currentFile || !inputText}
                  className={`p-2 rounded-full ${
                    isProcessing || !currentFile || !inputText
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
          <p className="mt-2 text-xs text-center text-gray-500">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}

export default App; 