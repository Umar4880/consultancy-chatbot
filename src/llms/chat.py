from chains.chain import ChainManagement
from .model import ModelManagement

class ChatManagement():
    def __init__(self, session_id: str = None, user_id:str = None):
        self.session_id = session_id
        self.user_id = user_id
        self.model = ModelManagement()


    def chat_with_consultant(self, message):
        manager = ChainManagement(mode='consultant', session_id=self.session_id, user_id=self.user_id, mode=self.model)

        return manager.invoke(message)

    def chat_with_docs_writer(self, message):
        manager = ChainManagement(mode='docs_writer', session_id=self.session_id, user_id=self.user_id, mode=self.model)

        return manager.invoke(message)