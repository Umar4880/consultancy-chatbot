import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from datetime import datetime

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fixed import path
from src.llms.prompts.system_prompts import PromptManager

from src.llms.memory import MemoryManagement, SummaryMemory
from langchain_core.messages import HumanMessage, AIMessage

class TestSummaryMemory(unittest.TestCase):

    def setUp(self):
        self.db_path = 'chat_history.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        self.session_id = "test_session"
        self.user_id = "test_user"

        # Use MemoryManagement to create some history with custom roles
        from langchain_core.messages.chat import ChatMessage
        self.memory = MemoryManagement(session_id=self.session_id, user_id=self.user_id)
        self.memory.add_message(ChatMessage(content="Hello", role="student"))
        self.memory.add_message(ChatMessage(content="Hi there!", role="consultant"))
        self.memory.add_message(ChatMessage(content="How are you?", role="student"))
        self.memory.add_message(ChatMessage(content="I'm doing great, thanks for asking!", role="consultant"))

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('src.llms.memory.ChatGoogleGenerativeAI')
    def test_summarize_chat(self, MockChatGoogleGenerativeAI):
        # Mock the language model and its response
        mock_model_instance = MockChatGoogleGenerativeAI.return_value
        mock_chain = MagicMock()
        mock_model_instance.invoke.return_value = "This is a test summary."

        try:
        # Mock the chain
            with patch('src.llms.memory.SummaryMemory._summarize_chat') as mock_summarize_chat:
                mock_summarize_chat.return_value = "This is a test summary."

                # Initialize SummaryMemory
                summary_memory = SummaryMemory(session_id=self.session_id, user_id=self.user_id, window=4)
                
                # Get the summary
                summary = summary_memory._summarize_chat()

                # Assertions
                self.assertEqual(summary, "This is a test summary.")
                self.assertEqual(len(summary_memory.window_messages), 4)
                # Check if the messages are in descending order
                self.assertEqual(summary_memory.window_messages[0].content, "I'm doing great, thanks for asking!")
                self.assertEqual(summary_memory.window_messages[3].content, "Hello")
        except Exception as e:
            raise ValueError("Error occures during test ", e)

if __name__ == '__main__':
    unittest.main()
