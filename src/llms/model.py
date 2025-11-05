from langchain_google_genai import ChatGoogleGenerativeAI
from src.llms.utils.config import config
from langchain_core.language_models import BaseChatModel

from pydantic import PrivateAttr

class ModelManagement(BaseChatModel):
    _model_name: str = PrivateAttr()
    _api_key: str = PrivateAttr()
    _temperature: float = PrivateAttr()
    _max_tokens: int = PrivateAttr()
    _chat_model: object = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._model_name = config.model
        self._api_key = config.api_key
        self._temperature = config.temperature
        self._max_tokens = config.max_tokens
        
        # Debug prints
        print(f"DEBUG: API Key loaded: {self._api_key[:10]}..." if self._api_key else "DEBUG: No API key loaded!")
        print(f"DEBUG: Model name: {self._model_name}")
        
        self._chat_model = self._create_chat_model()
    # ...rest of your code, use self._model_name, etc.

    def _create_chat_model(self):
        return ChatGoogleGenerativeAI(
            model=self._model_name,
            api_key=self._api_key,
            temperature=self._temperature,
            max_tokens=self._max_tokens
        )

    def _generate(self, messages, stop=None, **kwargs):
        # Delegate to the underlying model's _generate if available
        return self._chat_model._generate(messages, stop=stop, **kwargs)

    def invoke(self, input_data, **kwargs):
        """
        Main method called by the chain to get model response
        """
        return self._chat_model.invoke(input_data, **kwargs)

    @property
    def _llm_type(self):
        return "custom"

    def validate_api_key(self):
        try:
            self._chat_model._generate('test')
            return True
        except Exception as e:
            raise ValueError("Invalid api key: ", e)