import React, { useState, useRef } from 'react';
import axios from 'axios';
import RecordRTC from 'recordrtc';
import ChatLayout from './ChatLayout';

interface Message {
  type: 'user' | 'bot';
  content: string;
}

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const VoiceQuery = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [kql, setKql] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const recorderRef = useRef<any>(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new RecordRTC(stream, {
      type: 'audio',
      mimeType: 'audio/wav',
      recorderType: RecordRTC.StereoAudioRecorder,
    });
    recorder.startRecording();
    recorderRef.current = recorder;
    setIsRecording(true);
  };

  const stopRecording = async () => {
    setIsRecording(false);
    recorderRef.current.stopRecording(async () => {
      const blob = recorderRef.current.getBlob();
      const file = new File([blob], 'query.wav', { type: 'audio/wav' });

      const formData = new FormData();
      formData.append('file', file);

      try {
        setIsLoading(true);
        const response = await axios.post(`${API_BASE}/api/voice-query`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        const data = response.data;
        setKql(data.kql);
        setAudioUrl(`${API_BASE}${data.audio_url}`);

        setMessages((prev) => [
          ...prev,
          { type: 'user', content: data.spoken_text },
          { type: 'bot', content: data.summary },
        ]);
      } catch (err) {
        alert('Error processing voice query.');
      } finally {
        setIsLoading(false);
      }
    });
  };

  return (
    <div>
      <ChatLayout
        messages={messages}
        kql={kql}
        isLoading={isLoading}
        onReset={() => {
          setMessages([]);
          setKql('');
          setAudioUrl('');
        }}
      />

      <div className="flex justify-center mt-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-5 py-3 rounded-md font-semibold shadow-md ${
            isRecording
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {isRecording ? '⏹️ Stop Recording' : '🎙️ Ask Voice Query'}
        </button>
      </div>

      {audioUrl && (
        <audio
          src={audioUrl}
          autoPlay
          hidden
          onError={() => console.error('⚠️ Failed to load or play audio')}
        />
      )}
    </div>
  );
};

export default VoiceQuery;
