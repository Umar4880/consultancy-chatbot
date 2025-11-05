from src.llms.memory import SummaryMemory, MemoryManagement
import traceback

try:
    print('Testing session name generation...')
    
    # Test session name generation
    summary_memory = SummaryMemory(session_id='test_name', user_id='user_test')
    test_message = "hello, i wana you help to get admission in uni."
    
    print(f'Testing with message: "{test_message}"')
    generated_name = summary_memory.generate_session_name(test_message)
    print(f'Generated name: "{generated_name}"')
    
    # Test saving with session name
    memory = MemoryManagement(session_id='test_name', user_id='user_test')
    memory.update_session_name(generated_name)
    print('Session name updated successfully')
    
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()