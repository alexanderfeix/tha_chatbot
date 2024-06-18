import os
from typing import List

import torch
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.embeddings.huggingface import HuggingFaceBgeEmbeddings
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

from scripts.information_retriever import WebsiteRetriever
from scripts.qa_retriever import get_data_in_html_format


class OllamaRAG:
    def __init__(self, embedding_db_path: str, data_path: str, text_gen_model: str, embedding_model: str,
                 reranking_model: str, alternative_data_path: str, alternative_embedding_db_path: str):
        """
        Initializes the RAG model with the given parameters.
        :param embedding_db_path: path to the main database
        :param data_path: path to the main dataset, either websites or QA set
        :param text_gen_model: either a model from Huggingface or Ollama
        :param embedding_model: name of the embedding model
        :param reranking_model: name of the reranking model
        :param alternative_data_path: path to the alternative dataset, either websites or QA set
        :param alternative_embedding_db_path: path to the alternative embedding database
        """
        self.embedding_llm, self.vector_index, self.vector_index_alternative = None, None, None
        self.retriever, self.retriever_alternative, self.llm, self.document_chain = None, None, None, None
        self.llm = Ollama(model=text_gen_model, temperature=0.1, base_url='http://ollama-container:11434')

        self.embed_model_name: str = embedding_model
        self.reranking_model: str = reranking_model

        self.docs = []
        self.setup(embedding_db_path, data_path, alternative_data_path, alternative_embedding_db_path)
        self.create_document_chain()

    def setup(self, embedding_db_path: str, data_path: str, alternative_data_path: str,
              alternative_embedding_db_path: str):
        """
        Main method to update the setup and configuration of the RAG model.
        :param embedding_db_path: path to the main database
        :param data_path: path to the dataset, retrieves data from website if the path contains "websites.json"
        :param alternative_data_path: path to the alternative dataset,
               retrieves data from website if the path contains "websites.json"
        :param alternative_embedding_db_path: path to the alternative embedding database
        :return:
        """
        model_name = self.embed_model_name
        encode_kwargs = {'normalize_embeddings': True}
        self.embedding_llm = HuggingFaceBgeEmbeddings(model_name=model_name, model_kwargs={
            "device": "cuda" if torch.cuda.is_available() else "cpu"}, encode_kwargs=encode_kwargs, )
        self.embedding_llm.query_instruction = "query: "  # used to embed queries
        self.embedding_llm.embed_instruction = "passage: "  # used to embed documents

        if os.path.isdir(embedding_db_path):
            self.vector_index = Chroma(persist_directory=embedding_db_path, embedding_function=self.embedding_llm)
        else:
            if "websites.json" in data_path:
                self.retrieve_data(data_path, True)
            else:  # QA set retrieval
                self.retrieve_data(data_path, False)
            self.build_vector_database(embedding_db_path, False)

        if os.path.isdir(alternative_embedding_db_path):
            self.vector_index_alternative = Chroma(persist_directory=alternative_embedding_db_path,
                                                   embedding_function=self.embedding_llm)
        else:
            self.retrieve_data(alternative_data_path, True)
            self.build_vector_database(alternative_embedding_db_path, True)

        self.retriever_alternative = self.vector_index_alternative.as_retriever(search_kwargs={"k": 5})
        self.retriever = self.vector_index.as_retriever(search_kwargs={"k": 5})
        self.create_document_chain()

    def retrieve_data(self, filepath: str, from_website: bool):
        """
        Method to retrieve the data from the given filepath.
        :param filepath: file path to the data
        :param from_website: whether the data is from a website or QA set
        :return: nothing, appends the documents to the docs list
        """
        self.docs = []

        if from_website:
            website_data = WebsiteRetriever(filepath)
            data = website_data.get_data(pdf_included=True)
        else:  # QA set
            data = get_data_in_html_format(filepath)

        for document in data:
            self.docs.append(
                Document(page_content=document["title"] + document["text"],
                         metadata={"url": document["url"], "title": document["title"]})
            )
        print(f"Loaded {len(self.docs)} documents.")

    def build_vector_database(self, embeddings_db_path: str, alternative: bool = False):
        """
        Method to build the vector database from the given documents.
        Chunks all documents according to the amount of chars.
        :param embeddings_db_path: path to the main or alternative database
        :param alternative: Whether to build the alternative database
        """
        chunk_size = 1850
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=70,
                                                       separators=["\n", ".", "-"])
        chunked = text_splitter.split_documents(self.docs)
        print(f"Chunked {len(chunked)} documents.")

        if alternative:
            self.vector_index_alternative = Chroma.from_documents(chunked, self.embedding_llm,
                                                                  persist_directory=embeddings_db_path)
            self.vector_index_alternative.persist()
        else:
            self.vector_index = Chroma.from_documents(chunked, self.embedding_llm, persist_directory=embeddings_db_path)
            self.vector_index.persist()

    def create_document_chain(self):
        """
        Method to set up the document chain for the LLM model.
        Called on initialization and in the setup method.
        """
        prompt = PromptTemplate(
            template="""You are a chatbot that should answer questions about the Technical University of Applied Sciences Augsburg (THA). Questions can appear in German or English. You should provide the most relevant information based on the given context and answer either in English or German depending on the user question. Answer without introduction of yourself and provide only relevant information.  Only answer questions that are related to the THA. Use the following pieces of context to answer the user question at the end. 
CONTEXT: {context} 
If the answer is not contained in the context, just say that you don't know, don't try to make up an answer. Answer in German, if the user question appeared in German or answer in English if the user question appeared in English!
{chat_history} USER: {question} ASSISTANT:""",
            input_variables=["context", "chat_history", "question"]
        )
        self.document_chain = create_stuff_documents_chain(llm=self.llm, prompt=prompt)

    def retrieve_documents(self, query: str, alternative_search: bool = False):
        """
        First method in the pipeline to retrieve relevant documents based on the given query.
        :param query: user question
        :param alternative_search: whether to retrieve from the alternative database
        :return: a list of documents. A document contains the page_content and metadata
        """
        if alternative_search:
            return self.retriever_alternative.get_relevant_documents(query)
        else:
            return self.retriever.get_relevant_documents(query)

    def rerank_search_results(self, query: str, docs: list[Document]):
        """
        Reranks the search results based on the given query.
        :param query: user question
        :param docs: retrieved documents
        :return: reranked documents and their scores
        """
        unique_docs, pairs = [], []
        for doc in docs:
            if doc not in unique_docs:
                unique_docs.append(doc)
        cross_encoder = CrossEncoder(self.reranking_model, max_length=512)
        for doc in unique_docs:
            pairs.append([query, doc.page_content])

        scores = cross_encoder.predict(pairs)

        sorted_docs = list(zip(scores, unique_docs))
        sorted_docs.sort(key=lambda i: i[0], reverse=True)
        # Use a maximum of eight documents for reranking
        reranked_docs = [doc for _, doc in sorted_docs][0:8]
        scores = [score for score, _ in sorted_docs][0:8]
        return reranked_docs, scores

    def generate_response(self, query: str, docs: list[Document], chat_history):
        """
        Generates a response based on the given query and documents.
        Also includes the chat history and skips long answers within the history.
        :param chat_history: last conversation messages as string
        :param query: user input
        :param docs: reranked docs
        :return: dict containing the answer and context
        """
        history_str = ""
        question = ""
        
        for message in chat_history:
            text = message.message.replace("\n", " ")
            if len(text.split(" ")) > 350:
                continue
            
            if message.origin == "human":
                question = f"USER: {text}"
            elif message.origin == "ai":
                if question != "":
                    history_str += f"{question} ASSISTANT: {text}\n"
                    question = ""
        
        context = docs[0:3]
        return self.document_chain.invoke({"context": context, "chat_history": history_str, "question": query})

    def get_response(self, query: str, chat_history,
                     rag_threshold: float = 5.0, rag_alternative_threshold: float = -2.0):
        """
        Main method to generate the response from the user question.
        :param query: user question
        :param chat_history: simple list of past conversation
        :param rag_threshold: threshold value for the confidence score,
               at which score the alternative database should be invoked
        :param rag_alternative_threshold: threshold value for the confidence score,
               at which score the chatbot should answer with no context.
               This is implemented to avoid hallucinated answers.
        :return: the answer, context and the reranked documents
        """

        relevant_docs: List[Document] = self.retrieve_documents(query)
        reranked_docs, scores = self.rerank_search_results(query, relevant_docs)
        
        if scores[0] < rag_threshold:
            relevant_docs: List[Document] = self.retrieve_documents(query, alternative_search=True)
            reranked_docs, scores_alternative = self.rerank_search_results(query, relevant_docs)
            similarity_score = scores_alternative[0]
            if scores_alternative[0] < rag_alternative_threshold:
                reranked_docs[0].page_content = ""
                reranked_docs[0].metadata = {"url": "https://tha.de/", "title": "THA Website"}
                response = self.generate_response(query, [reranked_docs[0]], [])
                return response, ["none"], [reranked_docs[0]], f"Out of scope: {similarity_score}"
            else:
                response = self.generate_response(query, reranked_docs, chat_history)
        else:
            similarity_score = scores[0]
            response = self.generate_response(query, reranked_docs, chat_history)
        return response, relevant_docs, reranked_docs, f"Similarity score: {similarity_score}"
