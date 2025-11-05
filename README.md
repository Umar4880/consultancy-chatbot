# Few-Shot Consultancy Chatbot

A robust, extensible chatbot platform for consultancy and document writing, leveraging LangChain, FastAPI, and modern frontend technologies. This project supports session-based chat, memory management, and dynamic mode switching between consultant and document writer roles.

## Features

- **Session-based Chat**: Each chat session is uniquely identified and persists history in a database.
- **Role & Mode Management**: Supports multiple chat modes (consultant, docs_writer) with automatic mode tracking and switching.
- **Memory Management**: Custom memory classes for windowed and summary memory, ensuring context-aware responses.
- **Frontend-Backend Sync**: Seamless synchronization of chat history, session, and mode between frontend and backend.
- **Extensible LLM Integration**: Easily plug in different LLMs and prompt strategies.
- **User-Friendly UI**: Simple, responsive frontend for managing multiple chat sessions and modes.

## Project Structure

```
.
├── envorienment.txt
├── requirements.txt
├── test_openrouter.py
├── fewshort-consultancy-cahtboat/
│   ├── data/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── llms/
│   │   │   ├── __init__.py
│   │   │   ├── memory.py
│   │   │   ├── model.py
│   │   │   ├── chains/
│   │   │   │   ├── __init__.py
│   │   │   │   └── consultant_chain.py
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       └── system_prompts.py
│   │   └── test/
│   │       ├── ___init__.py
│   │       ├── test_db.py
│   │       ├── test_prompts.py
│   │       └── test_summary.py
│   └── utils/
│       ├── config.py
│       ├── summary_prompt.yaml
│       └── system_prompt.yaml
├── prompt_engineering/
│   ├── few-shot.py
│   └── zero-shot.py
├── structured_output/
│   ├── pydentic.py
│   ├── typedict.py
│   └── output_parser/
│       ├── JsonOutputParser.py
│       └── StrOutputParser.py
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for frontend development, if applicable)

### Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/Umar4880/consultancy-chatbot.git
   cd consultancy-chatbot
   ```
2. **Set up Python environment:**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Edit `utils/config.py` and YAML files as needed for API keys and settings.

4. **Run the backend server:**
   ```sh
   cd fewshort-consultancy-cahtboat/src
   python main.py
   ```

5. **(Optional) Run frontend:**
   - Open `static/index.html` in your browser, or serve with a simple HTTP server.

### Running Tests
```sh
pytest fewshort-consultancy-cahtboat/src/test/
```

## Usage
- Start a new chat session or switch between existing sessions.
- Select the desired mode (consultant or docs_writer).
- Messages and session state are persisted and synchronized.
- Extend prompts and LLM logic in `llms/prompts/` and `llms/model.py`.

## Key Files & Directories
- `src/llms/memory.py`: Memory management logic.
- `src/llms/chains/consultant_chain.py`: Chain logic for consultant mode.
- `src/llms/prompts/system_prompts.py`: System prompt templates.
- `src/main.py`: FastAPI app entry point.
- `static/js/app.js`: Frontend logic for chat and session management.
- `requirements.txt`: Python dependencies.

## Extending the Project
- Add new LLMs or prompt strategies in `llms/model.py` and `llms/prompts/`.
- Implement new chat modes by extending backend and frontend logic.
- Integrate additional memory strategies in `llms/memory.py`.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE)

## Acknowledgements
- [LangChain](https://github.com/hwchase17/langchain)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI](https://openai.com/)

---
*Project maintained by Umar4880 and contributors.*
