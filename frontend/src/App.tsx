import { useState, useEffect, useRef } from 'react';

interface ProcessingStatus {
  status: 'success' | 'error';
  message: string;
  document_url?: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    websocketRef.current = new WebSocket('ws://localhost:5173/ws');
    
    websocketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };

    return () => {
      websocketRef.current?.close();
    };
  }, []);

  // Handle file selection
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  // Handle voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await transcribeAudio(audioBlob);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  // Transcribe audio using Whisper
  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      // TODO: Implement client-side Whisper transcription
      // For now, we'll just simulate transcription
      setTranscribedText('Sample transcribed text...');
    } catch (error) {
      console.error('Error transcribing audio:', error);
    }
  };

  // Handle form submission
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!file || !transcribedText) {
      alert('Please select a file and provide voice instructions');
      return;
    }

    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('instruction_text', transcribedText);

      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setGeneratedPrompt(data.generated_prompt);
    } catch (error) {
      console.error('Error processing document:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-2xl font-bold mb-8">BluDoc Integration Demo</h1>
                
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* File Upload */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Upload Document
                    </label>
                    <input
                      type="file"
                      accept=".pdf,image/*"
                      onChange={handleFileChange}
                      className="mt-1 block w-full"
                    />
                  </div>

                  {/* Voice Recording */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Voice Instructions
                    </label>
                    <div className="mt-1 flex items-center space-x-4">
                      <button
                        type="button"
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`px-4 py-2 rounded-md ${
                          isRecording
                            ? 'bg-red-500 hover:bg-red-600'
                            : 'bg-blue-500 hover:bg-blue-600'
                        } text-white`}
                      >
                        {isRecording ? 'Stop Recording' : 'Start Recording'}
                      </button>
                    </div>
                  </div>

                  {/* Transcribed Text */}
                  {transcribedText && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Transcribed Instructions
                      </label>
                      <div className="mt-1 p-2 border rounded-md">
                        {transcribedText}
                      </div>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isProcessing || !file || !transcribedText}
                    className="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50"
                  >
                    {isProcessing ? 'Processing...' : 'Process Document'}
                  </button>
                </form>

                {/* Status Messages */}
                {status && (
                  <div
                    className={`mt-4 p-4 rounded-md ${
                      status.status === 'success'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {status.message}
                  </div>
                )}

                {/* Generated Prompt */}
                {generatedPrompt && (
                  <div className="mt-6">
                    <h2 className="text-lg font-medium text-gray-900">
                      Generated Prompt
                    </h2>
                    <div className="mt-2 p-4 bg-gray-50 rounded-md">
                      <pre className="whitespace-pre-wrap">{generatedPrompt}</pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 