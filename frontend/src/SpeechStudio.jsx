import React, { useState, useRef, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Mic, Send } from "lucide-react";
import * as THREE from "three";

// Particle effect
function VoiceParticles({ audioData, chatBoxRef }) {
  const pointsRef = useRef();
  const particleCount = 600;
  const positions = useRef(new Float32Array(particleCount * 3));
  const colors = useRef(new Float32Array(particleCount * 3));
  const velocities = useRef(new Float32Array(particleCount));

  // Initialize particles
  useEffect(() => {
    const chatBox = chatBoxRef.current;
    const rect = chatBox?.getBoundingClientRect() || { bottom: 0 };
    const startY = (rect.bottom / window.innerHeight) * 5 - 2.5;

    for (let i = 0; i < particleCount; i++) {
      positions.current[i * 3] = (Math.random() - 0.5) * 6;
      positions.current[i * 3 + 1] = startY;
      positions.current[i * 3 + 2] = (Math.random() - 0.5) * 1;
      velocities.current[i] = 0.02 + Math.random() * 0.02;

      const color = new THREE.Color();
      color.setHSL(Math.random(), 1, 0.5);
      colors.current[i * 3] = color.r;
      colors.current[i * 3 + 1] = color.g;
      colors.current[i * 3 + 2] = color.b;
    }
  }, [chatBoxRef]);

  useFrame(() => {
    if (!pointsRef.current) return;
    const amp = (audioData.current || 0) / 80;

    for (let i = 0; i < particleCount; i++) {
      const ix = i * 3;
      positions.current[ix + 1] += velocities.current[i] * (1 + amp * 4);
      positions.current[ix + 0] += Math.sin(Date.now() * 0.001 + ix) * 0.002;
      positions.current[ix + 2] += Math.cos(Date.now() * 0.001 + ix) * 0.002;

      if (positions.current[ix + 1] > 5) {
        const chatBox = chatBoxRef.current;
        const rect = chatBox?.getBoundingClientRect() || { bottom: 0 };
        positions.current[ix + 1] = (rect.bottom / window.innerHeight) * 5 - 2.5;
        positions.current[ix + 0] = (Math.random() - 0.5) * 6;
        positions.current[ix + 2] = (Math.random() - 0.5) * 1;
      }
    }

    pointsRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions.current}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={particleCount}
          array={colors.current}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial vertexColors size={0.15} transparent opacity={0.9} />
    </points>
  );
}

export default function SpeechStudio() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);
  const [lang, setLang] = useState("en-US");
  const audioData = useRef(0);
  const chatBoxRef = useRef();

  // Microphone & audio analyser
  useEffect(() => {
    async function initMic() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        const updateAudio = () => {
          analyser.getByteFrequencyData(dataArray);
          audioData.current = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
          requestAnimationFrame(updateAudio);
        };
        updateAudio();
      } catch {
        alert("Allow microphone access for live particle effects.");
      }
    }
    initMic();
  }, []);

  const speakText = (message) => {
    const ttsLang = lang === "bho-IN" ? "hi-IN" : lang;
    const utter = new SpeechSynthesisUtterance(message);
    utter.lang = ttsLang;
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang === ttsLang);
    if (voice) utter.voice = voice;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  };

  // ✅ Backend call
  const sendToBackend = async (query) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/ask/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query }),
      });
      const data = await res.json();

      const reply = typeof data.reply === "string" ? data.reply : JSON.stringify(data.reply);
      setMessages((prev) => [...prev, { role: "bot", content: reply }]);
      speakText(reply);
    } catch (err) {
      console.error("Error:", err);
      setMessages((prev) => [...prev, { role: "bot", content: "❌ Backend error" }]);
    }
  };

  const handleSend = () => {
    if (!text.trim()) return;
    const userMessage = text;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setText("");
    sendToBackend(userMessage);
  };

  const startRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech recognition not supported.");
    const recog = new SpeechRecognition();
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = lang;
    recog.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setMessages((prev) => [...prev, { role: "user", content: transcript }]);
      sendToBackend(transcript);
    };
    recog.start();
  };

  return (
    <div className="min-h-screen relative bg-gray-900 flex flex-col items-center justify-center p-6 overflow-hidden">
      {/* Chat UI */}
      <div
        ref={chatBoxRef}
        className="w-full max-w-2xl bg-white rounded-3xl shadow-xl flex flex-col overflow-hidden border border-gray-200 mb-6 z-10 relative"
      >
        <div className="flex-1 p-4 overflow-y-auto max-h-96 space-y-3">
          {messages.length === 0 && <p className="text-gray-400 text-center">No messages yet...</p>}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`px-4 py-2 rounded-lg max-w-xs break-words ${
                m.role === "user"
                  ? "bg-indigo-600 text-white self-end ml-auto"
                  : "bg-gray-200 text-gray-900 self-start"
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 p-3 border-t bg-gray-50">
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="px-3 py-1 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            <option value="en-US">English (US)</option>
            <option value="hi-IN">Hindi</option>
            <option value="bho-IN">Bhojpuri</option>
          </select>

          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-2xl bg-gray-100 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />

          <button
            onClick={handleSend}
            className="p-3 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white transition-transform transform hover:scale-105"
          >
            <Send size={20} />
          </button>

          <button
            onClick={startRecognition}
            className="p-3 rounded-full bg-green-600 hover:bg-green-500 text-white transition-transform transform hover:scale-105"
          >
            <Mic size={20} />
          </button>
        </div>
      </div>

      {/* Particle Canvas */}
      <Canvas
        className="absolute top-0 left-0 w-full h-full -z-0 pointer-events-none"
        camera={{ position: [0, 0, 10], fov: 50 }}
      >
        <VoiceParticles audioData={audioData} chatBoxRef={chatBoxRef} />
      </Canvas>
    </div>
  );
}
