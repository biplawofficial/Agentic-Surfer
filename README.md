# Agentic-Surfer: LLM-Powered Speech Studio

**Agentic-Surfer** is a full-stack application that pairs a powerful **FastAPI** agent backend with a dynamic **React/Three.js** frontend. The backend, leveraging large language models (LLMs) and advanced browser automation with Playwright, performs complex web research and data extraction. The frontend provides a "Speech Studio" chat interface with real-time audio visualization using a 3D particle effect.

---

## ✨ Features

* **Intelligent Web Agent:** Uses an LLM (Ollama) to plan and execute multi-step web browsing tasks for robust data collection.
* **Prompt Compression:** Integrates `llmlingua` to compress long prompts, saving on token usage for multi-step agent tasks.
* **Asynchronous Browsing:** Utilizes `playwright` for high-level, human-like, and robust browser automation.
* **Speech Studio Frontend:** A modern, responsive chat interface built with **React** and **Tailwind CSS**.
* **3D Voice Visualization:** Uses **Three.js** via `@react-three/fiber` to display real-time particle effects based on microphone input.
* **Speech-to-Text & Text-to-Speech:** Native browser API integration for voice interaction in multiple languages (English, Hindi, Bhojpuri).

---

## 💻 Installation and Setup

This project requires setting up **two separate environments**: the Python Backend and the JavaScript Frontend.

### **Prerequisites**

1.  **Python 3.11+**
2.  **Node.js (LTS recommended)**
3.  **Ollama Server:** The backend relies on an active Ollama instance running locally.

    * *Note for Garuda Linux users:* Follow standard practices for installing and running Ollama on Arch/Linux.

### **Part 1: Python Backend Setup**

1.  **Create a Virtual Environment** and activate it (recommended practice):

    ```bash
    python -m venv venv-backend
    source venv-backend/bin/activate
    ```

2.  **Install Dependencies** from the `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browser Drivers:** The `playwright` module needs browser drivers to run.

    ```bash
    playwright install
    ```

4.  **Configure Ollama Model:** Ensure the model specified in `agent.py` (`gemma3:4b`) is pulled and ready.

    ```bash
    ollama pull gemma3:4b
    ```

5.  **Run the Backend API:** This starts the FastAPI server.

    ```bash
    python main.py
    ```
    The API will be available at `http://0.0.0.0:8000`.

### **Part 2: Frontend Setup**

1.  **Navigate to the Frontend Directory:**

    ```bash
    cd frontend
    ```

2.  **Install Node Dependencies:** Use your preferred package manager (npm, yarn, or pnpm).

    ```bash
    npm install
    # or yarn install
    # or pnpm install
    ```

3.  **Run the Frontend Development Server:**

    ```bash
    npm run dev
    ```
    The application will typically be available at `http://localhost:5173/`.

---

## 🚀 How It Works

### **Frontend (`frontend/src/SpeechStudio.jsx`)**

The user interacts with a React component (`SpeechStudio.jsx`) that handles:
1.  **Microphone Input:** Uses the browser's `navigator.mediaDevices.getUserMedia` to get audio data, which is then analyzed to control the **3D particle system** rendered by `@react-three/fiber`.
2.  **Speech & Text:** Captures user input via text box or **Speech Recognition API** (`window.webkitSpeechRecognition`).
3.  **API Call:** Sends the user query to the backend's `/query` endpoint.

### **Backend (FastAPI, LLM Agents)**

The Python backend manages the complex agent logic:
1.  **API Endpoint (`main.py`):** The `/query` endpoint receives the user's task.
2.  **Agent Logic (`main.py` / `agent.py`):**
    * **Single-Step (Mode 0):** A custom `SimpleAgent` uses pre-defined tools (`search_google_safely`, `smart_click`, `extract_data`) guided by an LLM plan.
    * **Multi-Step (Mode 1):** Uses a sophisticated `Agent` class (`browser_use` module not provided but inferred) with a `ChatOllama` LLM for a more autonomous, sequential browsing loop.
3.  **Prompt Compression (`compressor.py`):** Before sending the final task to the LLM, the `Compressor` class uses **llmlingua-2** to reduce the prompt size, optimizing token usage.
4.  **Browser Automation (`helper.py`):** The `Helper` class uses `playwright` with anti-bot measures (random delays, user-agent rotation, mouse movements) to simulate human browsing and fetch content from the web.
5.  **Final Response:** The LLM agent processes the collected web content and formats the final answer into a **strict JSON** response, which is sent back to the frontend.

---

## 🛠️ Project Structure Summary

| Path | Purpose |
| :--- | :--- |
| `main.py` | FastAPI application entry point, defines the `/query` endpoint and agent execution modes. |
| `agent.py` | Defines the `mainLLM` class for generating action plans and final responses using Ollama. |
| `helper.py` | Contains the `Helper` (and `SimpleAgent`) class for browser automation with Playwright. |
| `compressor.py` | Implements the `Compressor` class using `llmlingua` for prompt size reduction. |
| `requirements.txt` | Python dependencies for the backend. |
| `frontend/` | The root directory for the React application. |
| `frontend/package.json` | Node.js/React dependencies (incl. `@react-three/fiber`, `framer-motion`, `three`). |
| `frontend/src/SpeechStudio.jsx` | The main frontend component for chat, microphone, TTS, and 3D visualization. |
| `frontend/src/index.css` | Imports Tailwind CSS directives. |
