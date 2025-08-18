# AI Voice Chatbot with LLM & RAG for Healthcare 💬🤖
<img width="1000" height="200" alt="Screenshot 2025-08-19 at 2 26 52 AM" src="https://github.com/user-attachments/assets/656774ae-abad-4c4b-b8d3-22ef60a7c58f" />




## 🎯 Objective

#### 💬🤖 An AI Voice Assistant that leverages 🧠 Large Language Models (LLMs) and 📚 Retrieval-Augmented Generation (RAG) to act as a 🏥👩‍⚕️ virtual medical receptionist. The assistant can ❓ answer patient queries, 📅 book appointments, and 📖✅ provide guideline-based responses while ensuring 🛡️ safety, 🎯 accuracy, and 📜⚖️ compliance with healthcare standards.

## 🏗️ Architecture Overview

- **Input Layer**: Speech-to-Text (STT) using Azure Cognitive Services + Text fallback
- **Processing Layer**: LLM + RAG Pipeline with vector database for NHS docs
- **Response Layer**: Text-to-Speech (TTS) + Chat UI
- **Cloud Infrastructure**: Azure Functions + App Services with Docker support

## 🔧 Core Features

- LLM + RAG Querying with NHS knowledge base
- Voice Agent Dialogues with safety compliance
- Multi-channel support (phone + web app)
- Performance monitoring and logging
- GDPR/NHS compliance and data de-identification
## 📸 Pictures 

<img width="400" height="500" alt="Screenshot 2025-08-19 at 2 36 26 AM" src="https://github.com/user-attachments/assets/6153fbe1-5db5-4ebb-b502-80baf2429042" />
<img width="400" height="500" alt="Screenshot 2025-08-19 at 2 21 21 AM" src="https://github.com/user-attachments/assets/1c3b22e8-1189-43cb-983a-6eaca7193dde" />
<img width="400" height="500" alt="Screenshot 2025-08-19 at 2 21 28 AM" src="https://github.com/user-attachments/assets/af7b0583-5a4e-497f-a387-ca8018c24438" />
<img width="400" height="500" alt="Screenshot 2025-08-19 at 2 21 46 AM" src="https://github.com/user-attachments/assets/bb34a221-ec2c-4928-bfe1-1266edcc5848" />




## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Fill in your API keys and configuration
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access Web Interface**
   - Open http://localhost:5000 in your browser
   - Use the voice chat interface or text input

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── config/               # Configuration files
├── core/                 # Core chatbot logic
├── models/               # LLM and embedding models
├── rag/                  # RAG pipeline components
├── voice/                # Speech processing modules
├── web/                  # Web interface components
├── data/                 # Sample NHS data and embeddings
├── tests/                # Test suite
├── docker/               # Docker configuration
└── docs/                 # Documentation
```

## 🔐 Environment Variables

- `AZURE_SPEECH_KEY`: Azure Cognitive Services Speech API key
- `AZURE_SPEECH_REGION`: Azure region for speech services
- `OPENAI_API_KEY`: OpenAI API key for LLM
- `PINECONE_API_KEY`: Pinecone vector database API key
- `DATABASE_URL`: Database connection string

## 🧪 Testing

```bash
python -m pytest tests/
```

## 🐳 Docker Deployment

```bash
docker build -t healthcare-chatbot .
docker run -p 5000:5000 healthcare-chatbot
```

## 📚 Documentation

See the `docs/` folder for detailed API documentation and deployment guides.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 
