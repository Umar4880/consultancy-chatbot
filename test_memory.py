from src.llms.memory import MemoryManagement
from langchain_core.messages.chat import ChatMessage
import traceback
from src.llms.chains.chain import ChainManagement
from src.llms.model import ModelManagement

try:
    print('Testing MemoryManagement...')
    session_id = "test_session"
    user_id = "test_user"
    model = ModelManagement()
    chain_manager = ChainManagement(
        mode="consultant",
        session_id=session_id,
        user_id=user_id,
        model=model
    )
    print('Memory created successfully')

    
    # Test adding a message
    msg = ChatMessage(role='student', content='test message')
    print('ChatMessage created')
    chain_manager.invoke(msg)
    
    
    # Check if it was saved
    import sqlite3
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.execute('SELECT * FROM chat_message WHERE session_id = "test123"')
    result = cursor.fetchall()
    print(f'Messages in DB for test123: {result}')
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()