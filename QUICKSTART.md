# Quick Start Guide 🚀

Get the Cricket AI Council running in **5 minutes**.

---

## Prerequisites

- Python 3.11+
- Docker (optional, for one-command deploy)
- Google Gemini API key: https://aistudio.google.com/app/apikey

---

## Option A: Local Install (No Docker)

### 1. Install Dependencies

```bash
git clone https://github.com/ATULPS2001/cricket-ai-council.git
cd cricket-ai-council
pip3 install -r requirements.txt
```

### 2. Set API Key

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### 3. Test Workflow

```bash
python3 workflow.py
```

Expected output:
```
Final Response:
"Given CSK's strong home record..."

Citations: ['match_1426261.json']
```

### 4. Run API + UI

```bash
# Terminal 1: API
python3 -m uvicorn app.main:app --reload

# Terminal 2: UI
streamlit run ui/streamlit_app.py
```

Open: http://localhost:8501

---

## Option B: Docker (One Command)

### 1. Set API Key

Create `.env` file:

```bash
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 2. Run Everything

```bash
docker-compose up --build
```

### 3. Access

- **UI:** http://localhost:8501
- **API:** http://localhost:8000/docs
- **Chroma:** http://localhost:8001

---

## 🧪 Test Queries

Try these in the UI:

1. **Tactical Agent:**
   ```
   Playing CSK at Chepauk, what's our batting strategy?
   ```

2. **Data Agent:**
   ```
   Show me MI's death over batting stats vs KKR's bowling
   ```

3. **Evaluator Agent:**
   ```
   Should we bat or field first at Wankhede if we win the toss?
   ```

---

## 🐛 Troubleshooting

### "GOOGLE_API_KEY not set"

```bash
export GOOGLE_API_KEY="your-key"
# Or add to .env file
```

### "Cannot connect to API"

Check if backend is running:

```bash
curl http://localhost:8000/health
```

### Docker build fails

Clear cache and rebuild:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## ✅ What You Just Built

- ✅ **LangGraph workflow** with 3 nodes (Research → Strategy → Critic)
- ✅ **MCP server** with 3 cricket data tools
- ✅ **RAG pipeline** with Chroma for source-grounded responses
- ✅ **FastAPI backend** with `/query` endpoint
- ✅ **Streamlit UI** with role selection and citations
- ✅ **Docker deployment** with one-command setup
- ✅ **GitHub Actions CI** for automated testing

---

## 📈 Next Steps

1. **Index your data:**
   ```bash
   python3 rag/index.py
   ```

2. **Add more tools:** Edit `mcp_server.py`

3. **Customize agents:** Edit `workflow.py` prompts

4. **Deploy to production:**
   - Railway: https://railway.app
   - Render: https://render.com

---

**Need help?** Open an issue on GitHub.
