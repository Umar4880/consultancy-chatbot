from langchain_core.prompts import ChatPromptTemplate
import yaml
from pathlib import Path
from typing import Dict, Any

class PromptManager:
    def __init__(self, prompts_file: str = None):
        """set prompt file path"""
        if prompts_file is None:
            # Default path relative to this file
            self.prompts_file = Path(__file__).parent.parent / "utils" / "system_prompt.yaml"
        else:
            self.prompts_file = Path(prompts_file)
        
        self.prompts = self._load_prompts()
        self.system_prompt = self._load_system_prompt()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompt file"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(f"File not found at: {self.prompts_file}")  # ✅ RAISE instead of RETURN
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")  # ✅ RAISE instead of RETURN
        
    def _load_system_prompt(self, prompt_type: str = "system_prompt") -> Dict[str, Any]:
        """load system prompt"""
        system_prompt = self.prompts.get(prompt_type, {})
        return system_prompt
        
    def get_consultant_prompt(self) -> str:
        """Get consultant prompt"""
        consultant_prompt = self.system_prompt.get("consultant")
        if consultant_prompt is None:
            raise ValueError("consultant prompt not available in prompt file")  # ✅ RAISE instead of RETURN
        return consultant_prompt
    
    def get_document_prompt(self) -> str:
        """Get document prompt"""
        document_prompt = self.system_prompt.get("document_prompt")
        if document_prompt is None:
            raise ValueError("document prompt not available in prompt file")  # ✅ RAISE instead of RETURN
        return document_prompt
    
    def get_example_prompt(self) -> list:
        """Get example prompt"""
        example_prompt = self.system_prompt.get("example_prompt")
        if example_prompt is None:
            raise ValueError("example prompt not available in prompt file")  # ✅ RAISE instead of RETURN
        return example_prompt
    
    def create_chat_template(self, template_type: str = "consultant") -> ChatPromptTemplate:
        """Create simple chat template"""
        
        if template_type == "document":
            system_message = self.get_document_prompt()
        elif template_type == "consultant":
            system_message = self.get_consultant_prompt()
        else:
            raise ValueError(f"Unknown template type: {template_type}")  # ✅ RAISE instead of RETURN
        
        # Simple template - no examples needed
        template = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{user_input}")
        ])
        
        return template
        