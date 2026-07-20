# ♟️ AI Chess Platform

An AI-powered full-stack Chess application built using **React**, **TypeScript**, and **FastAPI**. The platform provides an interactive chess-playing experience with AI-assisted gameplay, multiple difficulty levels, and real-time game management powered by the Stockfish chess engine.

---

## 🚀 Features

- ♟️ Interactive chessboard with modern UI
- 🤖 AI-powered opponent using Stockfish
- 💡 AI move suggestions and hints
- 🎯 Multiple AI difficulty levels
- 🔄 Real-time game state management
- 📜 Move validation and legal move generation
- 👥 User and game management APIs
- 🗄️ Database integration with SQLAlchemy
- 🔄 Database migrations using Alembic
- 🐳 Docker support for easy deployment
- 📱 Responsive interface for desktop and mobile

---

## 🛠️ Tech Stack

### Frontend
- React
- TypeScript
- CSS

### Backend
- FastAPI
- Python
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn

### AI Engine
- Stockfish Chess Engine

### Deployment
- Docker
- Docker Compose
- GitHub Actions (CI)

---

## 📂 Project Structure

```
Chess/
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── db.py
│   │   ├── game_manager.py
│   │   ├── stockfish_utils.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── styles/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/chandradipta/Chess.git
cd Chess
```

---

## Backend Setup

```bash
cd backend

python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the backend

```bash
uvicorn app.main:app --reload
```

Backend runs on

```
http://localhost:8000
```

---

## Frontend Setup

Open another terminal

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on

```
http://localhost:5173
```

---

## Docker Deployment

Run the complete application using Docker.

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | API Status |
| POST | `/games` | Create a new game |
| GET | `/games/{id}` | Retrieve game state |
| POST | `/games/{id}/move` | Make a move |
| POST | `/games/{id}/hint` | Get AI suggestion |

---

## Future Enhancements

- 🌐 Online multiplayer
- 🔐 User authentication
- 🏆 Player rankings
- ⏱️ Chess clock
- 🎥 Game replay
- 📈 Match analytics
- ♔ PGN import/export
- 💬 Live chat
- 📊 Performance dashboard

---

## Screenshots

Add screenshots of the application here.

```
screenshots/
│── home.png
│── gameplay.png
│── ai-hint.png
│── difficulty.png
```

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```
git checkout -b feature-name
```

3. Commit changes

```
git commit -m "Add feature"
```

4. Push to GitHub

```
git push origin feature-name
```

5. Open a Pull Request

---

## License

This project is developed for educational and learning purposes.

---

## Author

**Chandradipta**

GitHub: https://github.com/chandradipta