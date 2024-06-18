import os
import pathlib
import uuid

import requests

from backend.rag.ollama_rag import OllamaRAG


class ChatBot:
    """
    Main class to set up and run the chatbot.
    """

    def __init__(self):
        self.conversation_id = uuid.uuid4()
        self.base_dir = pathlib.Path(os.path.abspath(os.path.dirname(__file__))).resolve().parents[0]
        self.model, self.dataset_path, self.embedding_db_path, = None, None, None
        self.embedding_db_path_alternative, self.alternative_dataset = None, None

    def _set_embedding(self, embedding_db: str, embedding_db_alternative: str):
        """
        Sets the embedding database paths.
        :param embedding_db: name of the embedding database
        :param embedding_db_alternative: name of the alternative embedding database
        """
        self.embedding_db_path = os.path.join(self.base_dir, f"backend/rag/{embedding_db}")
        self.embedding_db_path_alternative = os.path.join(self.base_dir, f"backend/rag/{embedding_db_alternative}")

    def _set_dataset(self):
        """
        Sets the dataset paths.
        """
        self.dataset_path = os.path.join(self.base_dir, "data/")
        self.alternative_dataset = os.path.join(self.base_dir, "data/")

    def setup(self, embedding_db: str, text_gen_model: str, embedding_model: str,
              reranking_model: str, embedding_database_alternative: str):
        """
        Main Method to set up the chatbot with the given parameters.
        """
        self._set_embedding(embedding_db, embedding_database_alternative)
        self._set_dataset()
        self.model = OllamaRAG(self.embedding_db_path, self.dataset_path, text_gen_model.lower(), embedding_model,
                               reranking_model, self.alternative_dataset, self.embedding_db_path_alternative)

    def run(self, query, chat_history):
        """
        Main method to run the chatbot with the given query.
        This method decides whether to use Rasa or RAG to answer the query.
        :param chat_history: recent conversation as string
        :param query: user question
        :return: response from the chatbot as tuple: (answer, relevant_docs, reranked_docs, similarity_score)
        """
        response = requests.post("http://rasa:5005/model/parse", json={"text": query, "message_id": query.strip()})

        if (response.json()["intent"]["name"] == "out_of_scope" or
                response.json()["intent"]["name"] == "nlu_fallback"):
            return self.model.get_response(query, chat_history, 5.0, -2.0)
        else:
            real_response = requests.post("http://rasa:5005/conversations/test_id/trigger_intent", json={
                                              "name": response.json()["intent"]["name"],
                                              "entities": response.json()["entities"]
                                          })
            return (real_response.json()['messages'][0]['text'], [], [],
                    f"RASA confidence: {response.json()['intent']['confidence']}")
