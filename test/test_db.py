import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llms.memory import MemoryManagement
from langchain_core.messages.chat import ChatMessage

def test_init_database():

    manager = MemoryManagement('test_session_1', 'test_user_1')
    try:
        print(manager.session_id, 'and', manager.user_id)
        manager._init_database()
        print("Test pass, Database initalize successfully!")
        return True
    except Exception as e:
        raise ValueError(f"Test Fail: {e}")
    
def test_clear():

    manager = MemoryManagement('test_session_1', 'test_user_1')

    try:
        manager.clear()
        print("Test pass, Database clear successfully!")
        return True
    except Exception as e:
        raise ValueError(f"Test Fail: {e}")
    
def test_load_database():

    manager = MemoryManagement('test_session_1', 'test_user_1')

    try:
        manager._load_from_storage()
        print("Test pass, Database load successfully!")
        return True
    except Exception as e:
        raise ValueError(f"Test Fail: {e}")
    
def test_save_database():

    manager = MemoryManagement('test_session_1', 'test_user_1')
    list_of_messages = [{'role':'student', 'content':'hello, how are you'},
                       {'role':'consultant', 'content':'i am doing well. i am here to consult you.'},
                       {'role':'document_writer', 'content':'i am nova document writer.'}]
    
    for msg in list_of_messages:
        manager.message.append(
            ChatMessage(
                role=msg['role'],
                content=msg['content'],
                additional_kwargs={}
            )
        )

    try:
        manager._save_to_storage()
        print("Test pass, Database save successfully!")
        return True
    except Exception as e:
        raise ValueError(f"Test Fail: {e}")
    
def test_add_message():

    manager = MemoryManagement(session_id="test_session_1", user_id="test_user_1")
    try:
        message = ChatMessage(
            content="test_add_message",
            role = "student",
            additional_kwargs={}
        )
        manager.add_message(message)
        print("Test pass, message add to Database successfully!")
    except Exception as e:
        raise ValueError("couldn't add message: ", e)

def test_get_message_by_role():
    manager = MemoryManagement(session_id="test_session_1", user_id="test_user_1")
    try:
        manager.get_messages_by_role('student')
        print("Test pass, get message by role from Database successfully!")
    except Exception as e:
        raise ValueError("conldn't get message by role: ", e)
    
def test_get_window_message():
    manager = MemoryManagement(session_id="test_session_1", user_id="test_user_1")
    try:
        manager.get_window_message(window=10, order='DESC')
        print("Test pass, get k messaage from Database successfully!")
    except Exception as e:
        raise ValueError("conldn't get message by role: ", e)
    
    
def run_all_test():
    print("running all test")

    test_list = [
        test_init_database,
        test_save_database,
        test_load_database,
        test_clear,
        test_add_message,
        test_get_message_by_role,
        test_get_window_message,
    ]
    passed = 0
    for test in test_list:
        if test():
            passed += 1

    if len(test_list) == passed:
        print(f"all test passed {passed}/{len(test_list)}")
    else:
        print("Some tests failed.")

if __name__ == "__main__":
    run_all_test()