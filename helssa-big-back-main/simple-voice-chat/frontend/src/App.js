import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [sessionId] = useState('session_' + Date.now());
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    // Check if the browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus('مرورگر شما از ضبط صدا پشتیبانی نمی‌کند');
    }
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToServer(audioBlob);
        
        // Stop all tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus('در حال ضبط صدا...');
    } catch (error) {
      setStatus('خطا در دسترسی به میکروفون: ' + error.message);
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('در حال پردازش صوت...');
    }
  };

  const sendAudioToServer = async (audioBlob) => {
    try {
      setIsLoading(true);
      
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await axios.post(`${API_BASE_URL}/api/speech-to-text`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.status === 'success') {
        const text = response.data.text;
        setTranscribedText(text);
        setChatInput(text);
        setStatus('متن تبدیل شد: ' + text);
        
        // Automatically send to chat
        await sendToChat(text);
      } else {
        setStatus('خطا در تبدیل صوت به متن');
      }
    } catch (error) {
      setStatus('خطا در ارسال فایل صوتی: ' + error.message);
      console.error('Error sending audio:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendToChat = async (message = chatInput) => {
    if (!message.trim()) return;

    try {
      setIsLoading(true);
      
      // Add user message to chat history
      const newUserMessage = { role: 'user', content: message };
      setChatHistory(prev => [...prev, newUserMessage]);

      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message: message,
        session_id: sessionId
      });

      if (response.data.status === 'success') {
        const aiResponse = { role: 'assistant', content: response.data.response };
        setChatHistory(prev => [...prev, aiResponse]);
        setStatus('پاسخ دریافت شد');
      } else {
        setStatus('خطا در دریافت پاسخ');
      }
      
      setChatInput('');
    } catch (error) {
      setStatus('خطا در ارسال پیام: ' + error.message);
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await axios.post(`${API_BASE_URL}/api/chat/clear`, {
        session_id: sessionId
      });
      setChatHistory([]);
      setStatus('تاریخچه چت پاک شد');
    } catch (error) {
      setStatus('خطا در پاک کردن چت: ' + error.message);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendToChat();
    }
  };

  return (
    <div className="App">
      <div className="container">
        <div className="header">
          <h1>🎤 چت صوتی هوشمند</h1>
          <p>صحبت کنید یا تایپ کنید و با هوش مصنوعی گفتگو کنید</p>
        </div>

        <div className="controls">
          <button
            className={`btn ${isRecording ? 'btn-danger recording' : 'btn-primary'}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
          >
            {isRecording ? '⏹️ توقف ضبط' : '🎤 شروع ضبط'}
          </button>
          
          <button
            className="btn btn-success"
            onClick={() => sendToChat()}
            disabled={isLoading || !chatInput.trim()}
          >
            📤 ارسال پیام
          </button>
          
          <button
            className="btn btn-danger"
            onClick={clearChat}
            disabled={isLoading}
          >
            🗑️ پاک کردن چت
          </button>
        </div>

        {status && (
          <div className={`status ${status.includes('خطا') ? 'error' : status.includes('در حال') ? 'info' : 'success'}`}>
            {status}
          </div>
        )}

        {isLoading && (
          <div className="loading">
            در حال پردازش
          </div>
        )}

        <div className="chat-section">
          {chatHistory.length > 0 && (
            <div className="chat-history">
              {chatHistory.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <strong>{message.role === 'user' ? 'شما:' : 'دستیار:'}</strong>
                  <br />
                  {message.content}
                </div>
              ))}
            </div>
          )}

          <textarea
            className="chat-input"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="پیام خود را اینجا تایپ کنید یا از ضبط صدا استفاده کنید..."
            rows="3"
          />
        </div>
      </div>
    </div>
  );
}

export default App;