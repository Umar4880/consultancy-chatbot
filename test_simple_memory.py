from src.llms.memory import MemoryManagement
from langchain_core.messages.chat import ChatMessage
from langchain_core.messages import HumanMessage, AIMessage
import traceback

try:
    print('Testing MemoryManagement directly...')
    
    # Test with MemoryManagement directly
    memory = MemoryManagement(session_id="test_session_direct", user_id="test_user_direct", mode="consultant")
    print('Memory created successfully')
    
    # Test with ChatMessage (has role)
    print('\n=== Testing ChatMessage with role ===')
    msg1 = ChatMessage(role='student', content='Hello, I need help with university applications')
    memory.add_message(msg1)
    print('ChatMessage added successfully')
    
    # Test with HumanMessage (no role, should be inferred)
    print('\n=== Testing HumanMessage (no role) ===')
    msg2 = HumanMessage(content='What universities should I apply to?')
    memory.add_message(msg2)
    print('HumanMessage added successfully')
    
    # Test with AIMessage (no role, should be inferred)
    print('\n=== Testing AIMessage (no role) ===')
    msg3 = AIMessage(content='I can help you find the right universities based on your profile.')
    memory.add_message(msg3)
    print('AIMessage added successfully')
    
    # Check database
    print('\n=== Checking database ===')
    import sqlite3
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.execute('SELECT session_id, user_id, mode, role, content FROM chat_message WHERE session_id = "test_session_direct"')
    rows = cursor.fetchall()
    print(f'Total messages in DB: {len(rows)}')
    for i, row in enumerate(rows):
        print(f'Message {i+1}: session_id={row[0]}, user_id={row[1]}, mode={row[2]}, role={row[3]}, content={row[4][:50]}...')
    conn.close()
    
    print('\n✅ All tests completed successfully!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    traceback.print_exc()