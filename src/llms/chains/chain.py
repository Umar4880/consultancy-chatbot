from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from src.llms.memory import MemoryManagement, SummaryMemory
from langchain.chat_models import BaseChatModel
from langchain_core.messages.chat import ChatMessage
from langchain_core.output_parsers import StrOutputParser
import yaml
from pathlib import Path
from typing import Literal

class ChainManagement():
    def __init__(self, mode:Literal['consultant', 'docs_writer'] =None, session_id:str = None, user_id:str = None,  
                 template_filepath:str = None, model:BaseChatModel = None):

        # Input validation
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if mode not in ["consultant", "docs_writer"]:
            raise ValueError(f"mode must be 'consultant' or 'docs_writer', got: {mode}")
        if model is None:
            raise ValueError("model cannot be None")

        if template_filepath is None:
            self.filepath = Path(__file__).parent.parent / "utils" / "system_prompt.yaml"
        else:
            self.filepath = Path(template_filepath)

        self.model = model
        self.parser = StrOutputParser()
        self.mode = mode
        self.session_id = session_id
        self.user_id = user_id
        self.system_prompt = self._load_template_prompt()

    def _load_template_prompt(self):
        """load template for specific mode, e.g. consultant, docs writer"""

        try:
            with open(self.filepath, 'r', encoding="utf-8") as f:
                all_prompts = yaml.safe_load(f)
                return  all_prompts.get("system_prompt", {})
        except FileNotFoundError:
            raise ValueError("Unable to load file with path: ",self.filepath)
        except yaml.YAMLError as e:
            raise ValueError("Error parsin yaml file: ", e)


    def _create_prompt_template(self):
        """create chat template"""
        
        if self.mode not in ["consultant", "docs_writer"]:
            raise ValueError("Provided mode is not valid: ", self.mode)
        prompt = None
        if isinstance(self.system_prompt, dict) and self.mode in self.system_prompt:
            prompt = self.system_prompt[self.mode]

            return ChatPromptTemplate.from_messages([
                ('system', prompt),
                ('placeholder', "{history}"),
                ('human', "{input}")
            ])
        else:
            raise ValueError(f"Mode '{self.mode}' not found in system prompts")
        
    def get_session_history(self, session_id: str):
        print(f"DEBUG: get_session_history called with session_id={session_id}", flush=True)
        memory = MemoryManagement(session_id=session_id, user_id=self.user_id, mode=self.mode)
        memory.get_messages()
        print(f"DEBUG: Loaded {len(memory.message)} messages from history", flush=True)
        print(f"DEBUG: Returning memory object of type: {type(memory)}", flush=True)
        return memory

    def invoke(self, user_input):

        memory_mng = SummaryMemory(session_id=self.session_id, user_id=self.user_id, mode=self.mode, window=10)
        last_message_count = memory_mng._get_message_count()
        exsisting_summary = memory_mng._get_existing_summary()
        # Fix: Don't filter by role, get all messages
        window_message = memory_mng.get_window_message(window=10, order="DESC", mode=self.mode)

        formatted_window = []                                 
        for message in window_message:
            role = getattr(message, 'role', None)
            content = getattr(message, 'content', None)
            additional_kwargs = getattr(message, 'additional_kwargs', {})
            message = ChatMessage(
                role = role,
                content = content,
                additional_kwargs=additional_kwargs
            )
            formatted_window.append(message)

        combine_summary = None
        if window_message and memory_mng.window is not None:
            if last_message_count - exsisting_summary['last_message_count'] > memory_mng.window:
                recent_summary = memory_mng.generat_summary(window_messages=formatted_window)
                combine_summary = memory_mng.merge_summary(exsisting_summary['summary'], recent_summary)
                memory_mng._save_summary_to_storage(combine_summary, last_message_count+memory_mng.window)
        
        history = []
        if combine_summary:
            history.append(ChatMessage(content=combine_summary, role=self.mode))
        elif exsisting_summary:
            history.append(ChatMessage(content=exsisting_summary['summary'], role=self.mode))

        history.extend(formatted_window)

        prompt = self._create_prompt_template()
        chain = prompt | self.model._chat_model | self.parser

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history=self.get_session_history,
            input_key="input",
            history_key="history"
        )

        variables = {
            "input": user_input
        }

        # Get the response from the chain
        response = chain_with_history.invoke(
            variables,
            config={"configurable": {"session_id": self.session_id}})
        
        print(f"DEBUG: Got response: {response}")
        
        # Check if this is the first exchange for session naming
        try:
            memory = MemoryManagement(session_id=self.session_id, user_id=self.user_id, mode=self.mode)
            message_count = memory._get_message_count()
            print(f"DEBUG: Message count after exchange: {message_count}")

            # Only generate session name if not already set (i.e., still 'New Chat' or empty)
            current_session_name = memory.get_session_name(self.session_id, self.user_id, self.mode)
            print(f"DEBUG: Current session name: {current_session_name}")
            if message_count == 2 and (not current_session_name or current_session_name == "New Chat"):
                print(f"DEBUG: First exchange completed, generating session name...")
                summary_memory = SummaryMemory(session_id=self.session_id, user_id=self.user_id, mode=self.mode)
                session_name = summary_memory.generate_session_name(user_input)
                print(f"DEBUG: Generated session name: {session_name}")
                memory.update_session_name(session_name)
                print(f"DEBUG: Updated session name to: {session_name}")
        except Exception as name_error:
            print(f"DEBUG ERROR: Failed to process session name: {name_error}")
            import traceback
            traceback.print_exc()
        
        return response