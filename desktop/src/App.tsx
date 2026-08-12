import { useState } from "react";
import { fetch } from "@tauri-apps/plugin-http";

function App() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage() {
    if (!message.trim()) return;

    setIsLoading(true);
    setError("");
    setReply("");

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      setReply(data.reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main style={{ padding: "2rem", maxWidth: "600px", margin: "0 auto" }}>
      <h1>AI Workspace</h1>

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
        rows={4}
        style={{ width: "100%", padding: "0.5rem" }}
      />

      <button
        onClick={sendMessage}
        disabled={isLoading}
        style={{ marginTop: "0.5rem" }}
      >
        {isLoading ? "Sending..." : "Send"}
      </button>

      {error && (
        <p style={{ color: "red", marginTop: "1rem" }}>Error: {error}</p>
      )}

      {reply && (
        <div style={{ marginTop: "1rem", padding: "1rem", border: "1px solid #ccc" }}>
          {reply}
        </div>
      )}
    </main>
  );
}

export default App;