import { useState, useRef } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  async function sendMessage() {
    if (!message.trim()) return;

    setIsLoading(true);
    setError("");
    setReply("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setReply((prev) => prev + decoder.decode(value, { stream: true }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }

  async function startRecording() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        await transcribeRecording();
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? `Microphone access failed: ${err.message}`
          : "Microphone access failed"
      );
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  async function transcribeRecording() {
    const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
      const response = await fetch("http://127.0.0.1:8000/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.status}`);
      }

      const data = await response.json();
      setMessage(data.text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed");
    }
  }

  async function speakReply() {
    if (!reply.trim()) return;

    setIsSpeaking(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: reply }),
      });

      if (!response.ok) {
        throw new Error(`Speak failed: ${response.status}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speak failed");
    } finally {
      setIsSpeaking(false);
    }
  }

  return (
    <main style={{ padding: "2rem", maxWidth: "600px", margin: "0 auto" }}>
      <h1>AI Workspace</h1>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message, or record your voice..."
        rows={4}
        style={{ width: "100%", padding: "0.5rem" }}
      />

      <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem" }}>
        <button onClick={sendMessage} disabled={isLoading}>
          {isLoading ? "Sending..." : "Send"}
        </button>

        <button
          onClick={isRecording ? stopRecording : startRecording}
          style={{ background: isRecording ? "#fdd" : undefined }}
        >
          {isRecording ? "Stop Recording" : "Record"}
        </button>
      </div>

      {error && (
        <p style={{ color: "red", marginTop: "1rem" }}>Error: {error}</p>
      )}

      {reply && (
        <div style={{ marginTop: "1rem" }}>
          <div style={{ padding: "1rem", border: "1px solid #ccc" }}>
            {reply}
          </div>
          <button onClick={speakReply} disabled={isSpeaking} style={{ marginTop: "0.5rem" }}>
            {isSpeaking ? "Generating speech..." : "Speak"}
          </button>
        </div>
      )}
    </main>
  );
}

export default App;