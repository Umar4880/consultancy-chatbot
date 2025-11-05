import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fixed import path
from src.llms.prompts.system_prompts import PromptManager

def test_prompt_loading():
    """Test if prompts load correctly"""
    print("🧪 Testing prompt loading...")
    
    try:
        prompt_manager = PromptManager()
        print(f"📁 Prompts file path: {prompt_manager.prompts_file}")
        print(f"📄 Available keys: {list(prompt_manager.prompts.keys())}")
        
        # Test if all required prompts exist
        consultant_prompt = prompt_manager.get_consultant_prompt()
        document_prompt = prompt_manager.get_document_prompt()
        
        assert consultant_prompt is not None, "Consultant prompt is None"
        assert document_prompt is not None, "Document prompt is None"
        assert len(consultant_prompt) > 0, "Consultant prompt is empty"
        assert len(document_prompt) > 0, "Document prompt is empty"
        
        print("✅ Prompt loading test passed")
        return True
        
    except Exception as e:
        print(f"❌ Prompt loading test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_template_creation():
    """Test if templates are created correctly"""
    print("🧪 Testing template creation...")
    
    try:
        prompt_manager = PromptManager()
        
        # Test both template types
        consultant_template = prompt_manager.create_chat_template('consultant')
        document_template = prompt_manager.create_chat_template('document')
        
        print(f"✅ Templates created: {type(consultant_template).__name__}")
        
        # Test template formatting
        test_input = "Hello, who are you?"
        
        cons_messages = consultant_template.format_messages(user_input=test_input)
        doc_messages = document_template.format_messages(user_input=test_input)
        
        assert len(cons_messages) == 2, f"Consultant template should have 2 messages, got {len(cons_messages)}"
        assert len(doc_messages) == 2, f"Document template should have 2 messages, got {len(doc_messages)}"
        
        print("✅ Template creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Template creation test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_error_handling():
    """Test error handling for invalid inputs"""
    print("🧪 Testing error handling...")
    
    try:
        prompt_manager = PromptManager()
        
        # Test invalid template type
        try:
            prompt_manager.create_chat_template('invalid_type')
            print("❌ Should have raised an error for invalid template type")
            return False
        except ValueError as ve:
            print(f"✅ Error handling for invalid template type works: {ve}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def debug_prompt_manager():
    """Debug the PromptManager to see what's available"""
    print("🔍 Debugging PromptManager...")
    
    try:
        prompt_manager = PromptManager()
        
        print(f"📁 File path: {prompt_manager.prompts_file}")
        print(f"📄 File exists: {prompt_manager.prompts_file.exists()}")
        print(f"🗂️ Loaded prompts keys: {list(prompt_manager.prompts.keys())}")
        
        # Show first 100 chars of each prompt
        for key, value in prompt_manager.prompts.items():
            if isinstance(value, str):
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {type(value)} - {value}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        print(f"Error type: {type(e).__name__}")

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting prompt tests...\n")
    
    # First debug
    debug_prompt_manager()
    print()
    
    tests = [
        test_prompt_loading,
        test_template_creation,
        test_error_handling
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    run_all_tests()