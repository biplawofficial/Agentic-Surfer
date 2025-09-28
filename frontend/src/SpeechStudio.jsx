import React, { useState, useRef, useEffect, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { Mic, Send } from "lucide-react";
import * as THREE from "three";

// 🎤 Wave Particle Effect
function VoiceParticles({ audioData }) {
  const pointsRef = useRef();
  const particleCount = 4000;
  const positions = useRef(new Float32Array(particleCount * 3));
  const color = useMemo(() => new THREE.Color("#9b59b6"), []);

  useEffect(() => {
    for (let i = 0; i < particleCount; i++) {
      positions.current[i * 3] = (Math.random() - 0.5) * 25;
      positions.current[i * 3 + 1] = (Math.random() - 0.5) * 3;
      positions.current[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
  }, []);

  useFrame(() => {
    if (!pointsRef.current) return;
    const time = Date.now() * 0.002;
    const amp = (audioData.current || 0) / 150;

    for (let i = 0; i < particleCount; i++) {
      const ix = i * 3;
      positions.current[ix + 1] =
        Math.sin(time + positions.current[ix] * 0.3) * amp * 8 +
        Math.sin(time * 0.5 + ix) * 0.3;
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
      </bufferGeometry>
      <pointsMaterial
        size={0.07}
        vertexColors={false}
        color={color}
        transparent
        opacity={0.9}
      />
    </points>
  );
}

export default function SpeechStudio() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);
  const [lang, setLang] = useState("en-US");
  const [mode, setMode] = useState("single");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioData = useRef(0);
  const recogRef = useRef(null);
  const boxRef = useRef(null);

  const API_URL = "http://127.0.0.1:8000/query";

  // 🎙️ Microphone + Audio Analyzer
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
        console.warn("Mic access denied");
      }
    }
    initMic();
  }, []);

  // 🌟 Box glow animation
  useEffect(() => {
    let animationFrameId;
    const animateGlow = () => {
      if (boxRef.current) {
        const amp = (audioData.current || 0) / 50;
        const wave = Math.sin(Date.now() * 0.005) * amp * 40;
        boxRef.current.style.boxShadow = `
          0 0 ${25 + wave}px rgba(155,89,182,0.8),
          0 0 ${50 + wave}px rgba(155,89,182,0.5),
          0 0 ${75 + wave}px rgba(155,89,182,0.3)
        `;
      }
      animationFrameId = requestAnimationFrame(animateGlow);
    };
    animateGlow();
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  // 🗣️ Text-to-Speech
  const speakText = (message) => {
    const ttsLang = lang === "bho-IN" ? "hi-IN" : lang;
    const utter = new SpeechSynthesisUtterance(message);
    utter.lang = ttsLang;
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang === ttsLang);
    if (voice) utter.voice = voice;
    setIsSpeaking(true);
    utter.onend = () => setIsSpeaking(false);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  };

  // 🔗 Backend fetch (Single/Multi task)
  const sendToBackend = async (userMessage) => {
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: mode === "single" ? 0 : 1, query: userMessage })
      });
      const data = await res.json();
      console.log("Backend:", data);

      let botReply = "";
      if (mode === "single") {
        botReply =
          data.result?.response ||
          data.result?.text ||
          data.reply ||
          data.message ||
          JSON.stringify(data, null, 2);
      } else {
        botReply = JSON.stringify(data.result || data || "No data from backend", null, 2);
      }

      setMessages((prev) => [...prev, { role: "bot", content: botReply }]);
      speakText(botReply);

    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "bot", content: "❌ Backend error" }]);
    }
  };

  const handleSend = () => {
    if (!text.trim()) return;
    const userMessage = text.trim();
    setText("");
    sendToBackend(userMessage);
  };

  const startRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Speech recognition not supported.");
    if (!recogRef.current) {
      recogRef.current = new SpeechRecognition();
      recogRef.current.continuous = false;
      recogRef.current.interimResults = false;
      recogRef.current.lang = lang;
      recogRef.current.onresult = (e) => sendToBackend(e.results[0][0].transcript);
      recogRef.current.onerror = (e) => console.warn(e.error);
      recogRef.current.onend = () => {
        try { recogRef.current.stop(); } catch {}
      };
    }
    try { recogRef.current.start(); } catch { console.warn("Recognition already started"); }
  };

  return (
    <div className="min-h-screen relative bg-black text-purple-400 flex flex-col items-center justify-center p-6 overflow-hidden font-mono">

      {/* Language Selector */}
      <div className="absolute top-4 right-6 z-20">
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          className="px-3 py-1 rounded-lg border border-purple-700 bg-black text-purple-400 text-sm focus:outline-none focus:ring-2 focus:ring-purple-700 shadow-lg"
        >
          <option value="en-US">English (US)</option>
          <option value="en-GB">English (UK)</option>
          <option value="hi-IN">Hindi</option>
          <option value="bho-IN">Bhojpuri</option>
        </select>
      </div>

      {/* Chat UI */}
      <div
        ref={boxRef}
        className="w-full max-w-2xl rounded-3xl flex flex-col overflow-hidden mb-6 z-10 relative backdrop-blur-md transition-all duration-500 bg-black/80 border border-purple-700"
      >
        <div className="flex-1 p-4 overflow-y-auto max-h-96 space-y-3">
          {messages.length === 0 && <p className="text-purple-600 text-center">No messages yet...</p>}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`px-4 py-2 rounded-lg max-w-xs break-words ${
                m.role === "user"
                  ? "bg-purple-700 text-black self-end ml-auto"
                  : "bg-gray-800 text-purple-400 self-start"
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 p-3 border-t border-purple-700 bg-black/70">
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="px-3 py-1 rounded-lg border border-purple-700 bg-black text-purple-400 text-sm focus:outline-none focus:ring-2 focus:ring-purple-700"
          >
            <option value="single">Single Task</option>
            <option value="multi">Multi Task</option>
          </select>

          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-2xl bg-black text-purple-300 border border-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-700"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />

          <button
            onClick={handleSend}
            className="p-3 rounded-full bg-purple-700 hover:bg-purple-700 text-black transition-transform transform hover:scale-105"
          >
            <Send size={20} />
          </button>

          <button
            onClick={startRecognition}
            className="p-3 rounded-full bg-purple-700 hover:bg-purple-700 text-white transition-transform transform hover:scale-105"
          >
            <Mic size={20} />
          </button>
        </div>
      </div>

      {/* Wave Particle Canvas */}
      <Canvas
        className="absolute top-0 left-0 w-full h-full"
        camera={{ position: [0, 5, 20], fov: 55 }}
      >
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1.2} color={"#9b59b6"} />
        <VoiceParticles audioData={audioData} />
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
    </div>
  );
}
