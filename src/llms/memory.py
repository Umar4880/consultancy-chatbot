from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.messages.chat import ChatMessage
from typing import List, Literal
import json, yaml, sqlite3
from pathlib import Path
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model import ModelManagement
from src.llms.utils.db_config import DatabaseConfig
from src.llms.utils.db_utils import retry_on_lock
from src.llms.utils.db_exceptions import DatabaseError, DatabaseConnectionError, DatabaseQueryError

class MemoryManagement(BaseChatMessageHistory):

    def __init__(self, session_id: str = None, user_id: str = None, mode: str = "consultant", db_config: DatabaseConfig = None):
        self.session_id: str = session_id or "default"
        self.user_id: str = user_id or "anonymous"
        self.mode: str = mode or "consultant"
        self.keywords_args: str = None
        self.message: List[BaseMessage] = []
        self.db_config = db_config or DatabaseConfig()
        self._init_database()

    @retry_on_lock(max_retries=3, delay=0.1)
    def _init_database(self):
        """Initialize database and create tables"""
        try:
            with self.db_config.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_message(
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        mode TEXT NOT NULL DEFAULT 'consultant',
                        session_name TEXT DEFAULT 'New Chat',
                        role TEXT NOT NULL,
                        additional_kwargs TEXT,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_user_mode ON chat_message (session_id, user_id, mode)
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_summary(
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        last_message_count INT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_user_summary ON chat_summary (session_id, user_id)
                """)
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Can't initialize database: {e}")
        
    @retry_on_lock(max_retries=3, delay=0.1)
    def get_session_name(self, session_id, user_id, mode=None):
        """get session name for specific mode"""
        if mode is None:
            mode = self.mode
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT session_name FROM chat_message WHERE
                    user_id = ? AND session_id = ? AND mode = ?
                    LIMIT 1
                """, (user_id, session_id, mode))
                result = cursor.fetchone()
                return result[0] if result else "New Chat"
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to fetch session name: {e}")

    @retry_on_lock(max_retries=3, delay=0.1)
    def update_session_name(self, session_name: str):
        """Update session name for all messages in this session with specific mode"""
        try:
            with self.db_config.get_connection() as conn:
                conn.execute("""
                    UPDATE chat_message SET session_name = ?
                    WHERE session_id = ? AND user_id = ? AND mode = ?
                """, (session_name, self.session_id, self.user_id, self.mode))
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to update session name: {e}")


    def add_message(self, message: BaseMessage) -> None:
        """Add message to list"""
        try:
            print(f"DEBUG: add_message called with class={message.__class__.__name__}, content={message.content[:50]}...", flush=True)
            
            # Get or infer the role
            role = None
            
            # Check if message already has a role
            if hasattr(message, 'role') and message.role:
                role = message.role
            elif hasattr(message, 'type') and message.type:
                role = message.type
            else:
                # Determine role based on message type and mode
                if message.__class__.__name__ == 'HumanMessage':
                    role = 'student'  # Always student for human messages
                elif message.__class__.__name__ == 'AIMessage':
                    # AI role depends on mode
                    if self.mode == 'consultant':
                        role = 'consultant'
                    elif self.mode == 'docs_writer':
                        role = 'docs_writer'
                    else:
                        role = 'consultant'
                else:
                    # For any other message type, infer from content or use default
                    role = 'student'  # Default fallback
            
            # Ensure message has role attribute
            if not hasattr(message, 'role'):
                message.role = role
            elif not message.role:
                message.role = role
            
            print(f"DEBUG: Message role set to: {message.role}", flush=True)
            
            self.message.append(message)
            print(f"DEBUG: Message appended to list, now calling save_messages...", flush=True)
            self.save_messages()
            print(f"DEBUG: save_messages completed", flush=True)
            
        except Exception as e:
            print(f"ERROR in add_message: {e}", flush=True)
            print(f"Message class: {message.__class__.__name__}", flush=True)
            print(f"Message content: {getattr(message, 'content', 'NO CONTENT')}", flush=True)
            print(f"Message attributes: {dir(message)}", flush=True)
            # Don't re-raise, just log the error to avoid breaking the chain
            pass

    @retry_on_lock(max_retries=3, delay=0.1)
    def clear(self):
        """Clear session history for specific mode"""
        try:
            with self.db_config.get_connection() as conn:
                conn.execute("""
                    DELETE FROM chat_message WHERE
                    user_id = ? AND session_id = ? AND mode = ?
                """, (self.user_id, self.session_id, self.mode))
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to delete chat session: {e}")

    @retry_on_lock(max_retries=3, delay=0.1)
    def get_messages(self):
        """Load chat history of session from database for specific mode"""
        if self.session_id is None or self.user_id is None:
            raise ValueError(f"Session id or user id not given: {self.user_id}")
        
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT role, additional_kwargs, content FROM chat_message
                    WHERE session_id = ? AND user_id = ? AND mode = ?
                    ORDER BY timestamp ASC
                """, (self.session_id, self.user_id, self.mode))

                for role, additional_kwargs, content in cursor.fetchall():
                    try:
                        additional_kwargs_dict = json.loads(additional_kwargs) if additional_kwargs and additional_kwargs.strip() else {}

                        message = ChatMessage(
                            content=content,
                            role=role,
                            additional_kwargs=additional_kwargs_dict,
                        )
                        self.message.append(message)
                    except json.JSONDecodeError as e:
                        raise DatabaseQueryError(f"Error parsing message data: {e}")
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Error loading chat history: {e}")

    @retry_on_lock(max_retries=3, delay=0.1)
    def save_messages(self):
        """Save chat history to storage"""
        try:
            print(f"DEBUG: save_messages called for session_id={self.session_id}, user_id={self.user_id}, mode={self.mode}", flush=True)
            print(f"DEBUG: Current message list length: {len(self.message)}", flush=True)
            
            if not self.message:
                print(f"DEBUG: No messages to save, returning", flush=True)
                return
            
            latest_message = self.message[-1]
            
            # Get role safely with multiple fallbacks
            role = getattr(latest_message, 'role', None)
            if not role:
                role = getattr(latest_message, 'type', None)
            if not role:
                # Last resort inference
                if latest_message.__class__.__name__ == 'HumanMessage':
                    role = 'student'
                elif latest_message.__class__.__name__ == 'AIMessage':
                    role = 'consultant' if self.mode == 'consultant' else 'docs_writer'
                else:
                    role = 'student'  # Safe default
            
            print(f"DEBUG: Latest message role: {role}, content: {latest_message.content[:50]}...", flush=True)
            
            if not role or role == 'unknown':
                print(f"ERROR: Message missing valid role!\n  Class: {latest_message.__class__.__name__}\n  Dir: {dir(latest_message)}\n  Vars: {vars(latest_message) if hasattr(latest_message, '__dict__') else 'no __dict__'}\n  Content: {getattr(latest_message, 'content', None)}", flush=True)
                # Don't raise error, just use a default role to prevent blocking
                role = 'student'
                print(f"DEBUG: Using fallback role: {role}", flush=True)

            with self.db_config.get_connection() as conn:
                print(f"DEBUG: About to insert into database...", flush=True)
                conn.execute("""
                    INSERT INTO chat_message 
                    (session_id, user_id, mode, session_name, role, additional_kwargs, content, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.session_id, self.user_id, self.mode, self.get_session_name(self.session_id, self.user_id, self.mode), role, json.dumps(getattr(latest_message, 'additional_kwargs', {})),
                       latest_message.content, datetime.now().isoformat()))
                print(f"DEBUG: Message saved to database successfully", flush=True)
                
        except sqlite3.Error as e:
            print(f"DEBUG: Database error: {e}", flush=True)
            raise DatabaseQueryError(f"Unable to store session in storage: {e}")
        except Exception as e:
            print(f"DEBUG: Unexpected error in save_messages: {e}", flush=True)
            # Don't raise to avoid breaking the chain
            pass

    def get_messages_by_role(self, role: str):
        """Get message by specific role"""
        if role is None:
            raise ValueError("Role is not specified")
        
        return [msg for msg in self.message if getattr(msg, 'role', msg.type) == role]
    
    @retry_on_lock(max_retries=3, delay=0.1)
    def get_window_message(self, window: int = 10, order: Literal['ASC', 'DESC'] = 'DESC', mode:Literal['consultant', 'docs_writer'] = None):
        """Get k messages from database and return in chat format, filtered by mode."""
        if mode is None:
            mode = self.mode
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.execute(f"""
                    SELECT role, content, additional_kwargs FROM chat_message 
                    WHERE session_id = ? AND user_id = ? AND mode = ?
                    ORDER BY timestamp {order}
                    LIMIT ?
                """, (self.session_id, self.user_id, mode, window))
                rows = cursor.fetchall()

            chat = []
            for role, content, additional_kwargs in rows:
                try:
                    additional_kwargs_dict = json.loads(additional_kwargs) if additional_kwargs and additional_kwargs.strip() else {}
                    message = ChatMessage(
                        content=content,
                        role=role,
                        additional_kwargs=additional_kwargs_dict,
                    )
                    chat.append(message)
                except json.JSONDecodeError as e:
                    raise DatabaseQueryError(f"Error making chat from window messages: {e}")
            return chat
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to get k window messages from storage: {e}")

    @property
    def messages(self):
        return self.message
    
    @retry_on_lock(max_retries=3, delay=0.1)
    def _get_message_count(self):
        """Get message count from storage for specific mode"""
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM chat_message 
                    WHERE session_id = ? AND user_id = ? AND mode = ?
                """, (self.session_id, self.user_id, self.mode))
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Couldn't count messages: {e}")


class SummaryMemory(MemoryManagement):
    def __init__(self, session_id: str = None, user_id: str = None, mode: str = "consultant", window:int = None, prompt_filepath: str = None):
        super().__init__(session_id, user_id, mode)

        if prompt_filepath is None:
            prompt_filepath = Path(__file__).parent / "utils" / "summary_prompt.yaml"

        self.window = window if window is not None else 10  # Default window size
        self.filepath = prompt_filepath
        self.parser = StrOutputParser()
        self.summary_prompt = self._load_summary_prompt()
        self.summary_template = self._create_summary_template()
        self.summary_model = self._init_summarize_model()

    def _load_summary_prompt(self):
        """load summary prompt"""

        try: 
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"File not found at: {self.filepath}")  # 
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")  
        
    def _create_summary_template(self):
        """create template for summary"""
        # Expecting YAML to have a 'template' key
        if isinstance(self.summary_prompt, dict) and "summary_prompt" in self.summary_prompt:
            template_str = self.summary_prompt["summary_prompt"]
        else:
            template_str = self.summary_prompt  # fallback, may error if not string
        template = ChatPromptTemplate.from_template(template_str)
        return template

    from src.llms.model import ModelManagement

    def _init_summarize_model(self):
        return ModelManagement()._chat_model
    
    def generat_summary(self, window_messages):
        """summarize chat"""

        chain = self.summary_template | self.summary_model | self.parser

        return chain.invoke({"Generate summary": window_messages}) 

    def merge_summary(self, existing_summary: str, new_summary: str) -> str:
        """Merge existing summary with new summary"""
        if not existing_summary:
            return new_summary
        if not new_summary:
            return existing_summary
        
        # Simple merge - concatenate with separator
        return f"{existing_summary}\n\nRecent developments:\n{new_summary}" 


    def generate_session_name(self, first_message: str) -> str:
        """Generate a meaningful session name using the model based on the first user message"""
        try:
            # Create a specific prompt for generating session titles
            from langchain_core.prompts import ChatPromptTemplate
            
            name_prompt_template = ChatPromptTemplate.from_template("""
            Based on this user message, generate a short, descriptive title for this conversation.
            Keep it under 6 words and make it clear what the conversation is about.

            User message: "{message}"

            Examples:
            - "Help with university applications" 
            - "Career advice for engineering"
            - "Study abroad questions"
            - "Course selection help"

            Generate only the title, nothing else:""")

            # Create a chain for name generation
            name_chain = name_prompt_template | self.summary_model | self.parser
            generated_name = name_chain.invoke({"message": first_message})
            
            # Clean up the generated name
            name = generated_name.strip().replace('"', '').replace("'", "")
            # Remove common prefixes that models might add
            prefixes_to_remove = ["Title:", "Chat title:", "Session:", "Conversation:"]
            for prefix in prefixes_to_remove:
                if name.lower().startswith(prefix.lower()):
                    name = name[len(prefix):].strip()
            
            if len(name) > 60:  # Limit length
                name = name[:57] + "..."
                
            return name if name else "New Chat"
            
        except Exception as e:
            print(f"ERROR generating session name with model: {e}")
            # Fallback to intelligent pattern matching if model fails
            name = self._generate_simple_name(first_message)
            print(f"Using fallback name: {name}")
            return name
    
    def _generate_simple_name(self, first_message: str) -> str:
        """Generate a simple but meaningful name from the first message"""
        # Clean the message
        message = first_message.strip().lower()
        
        # Common patterns and their names
        if "university" in message or "admission" in message or "college" in message:
            return "University Admission Help"
        elif "career" in message or "job" in message:
            return "Career Guidance"
        elif "study abroad" in message or "international" in message:
            return "Study Abroad Advice"
        elif "course" in message or "subject" in message:
            return "Course Selection"
        elif "scholarship" in message:
            return "Scholarship Information"
        elif "application" in message:
            return "Application Help"
        else:
            # Take first meaningful words
            words = first_message.strip().split()[:4]
            name = " ".join(words)
            if len(name) > 40:
                name = name[:37] + "..."
            return name.title() if name else "New Chat"

    @retry_on_lock(max_retries=3, delay=0.1)
    def _save_summary_to_storage(self, summary: str = None, message_count: int = None):
        """Save summary to storage"""
        try:
            with self.db_config.get_connection() as conn:
                conn.execute("""
                    INSERT INTO chat_summary (session_id, user_id, summary, last_message_count, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.session_id, self.user_id, summary, message_count, datetime.now().isoformat()))
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to store summary in storage: {e}")
    
    @retry_on_lock(max_retries=3, delay=0.1)
    def _get_existing_summary(self):
        """Load summary from storage"""
        try:
            with self.db_config.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT summary, last_message_count FROM chat_summary
                    WHERE session_id = ? AND user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (self.session_id, self.user_id))
               
                result = cursor.fetchone()
                if result:
                    return {"summary": result[0], "last_message_count": result[1]}
                return {"summary": "", "last_message_count": 0}
        except sqlite3.Error as e:
            raise DatabaseQueryError(f"Unable to get summary: {e}")