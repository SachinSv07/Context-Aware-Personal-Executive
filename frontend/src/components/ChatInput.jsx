import { useState, useRef } from 'react';

function MicIcon({ recording }) {
  return recording ? (
    // Animated pulsing stop icon when recording
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
      <path d="M12 1a4 4 0 0 1 4 4v6a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm-1 17.93V21h-2a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2h-2v-2.07A8.001 8.001 0 0 0 20 11a1 1 0 0 0-2 0 6 6 0 0 1-12 0 1 1 0 0 0-2 0 8.001 8.001 0 0 0 7 7.93z" />
    </svg>
  );
}

function ChatInput({ onSend, isLoading }) {
  const [message, setMessage] = useState('');
  const [recording, setRecording] = useState(false);
  const recognitionRef = useRef(null);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setMessage('');
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const toggleSpeech = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (recording) {
      recognitionRef.current?.stop();
      setRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognitionRef.current = recognition;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const finalMessage = transcript.trim();
      if (finalMessage) {
        onSend(finalMessage);
        setMessage('');
      }
    };

    recognition.onerror = () => setRecording(false);
    recognition.onend = () => setRecording(false);

    recognition.start();
    setRecording(true);
  };

  return (
    <div className="border-t border-slate-800 bg-[var(--surface-2)]/90 px-3 py-3 backdrop-blur sm:px-4 sm:py-4 lg:px-6">
      <div className="mx-auto flex max-w-4xl items-end gap-2 sm:gap-3 rounded-xl sm:rounded-2xl border border-slate-700 bg-[var(--surface-1)] px-2 sm:px-3 py-2 shadow-lg">
        <textarea
          rows={1}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message ContextIQ"
          className="max-h-36 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
        />
        {/* Mic button */}
        <button
          type="button"
          onClick={toggleSpeech}
          disabled={isLoading}
          title={recording ? 'Stop recording' : 'Speak your message'}
          className={`rounded-lg sm:rounded-xl px-3 py-2 text-sm transition flex-shrink-0 disabled:cursor-not-allowed disabled:opacity-40 ${
            recording
              ? 'bg-red-500 text-white animate-pulse hover:bg-red-600'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <MicIcon recording={recording} />
        </button>
        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={isLoading}
          className="rounded-lg sm:rounded-xl bg-[var(--accent)] px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 flex-shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInput;

