from google import genai
from google.genai import types
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
import os

class GooglePalmEmbeddings:
    def __init__(self):
        # Replace with your actual API key from Google Cloud Credentials
        self.client = genai.Client(api_key="your-google-api-key") 
        
    def embed_documents(self, documents):
        embeddings = (self.client.models.embed_content(
                model="models/text-embedding-004",  # or "models/text-embedding-003"
                contents=documents,
                config=types.EmbedContentConfig(task_type='retrieval_document')))
        return [e.values for e in embeddings.embeddings]
        
    def embed_query(self, text):
        embeddings = self.client.models.embed_content(
            model="models/text-embedding-004", 
            contents=text,
            config=types.EmbedContentConfig(task_type='retrieval_query'))
        return embeddings.embeddings[0].values


class VectorDB:
    def __init__(self, embeddingFunction):
        self.vector_db = PineconeVectorStore(index_name="document-summarizer", 
                                             embedding=embeddingFunction,
                                             pinecone_api_key="your-pinecone-api-key"
                                             )
        # print(self.vector_db)

    def addEmbeddings(self, docs: list[Document], uid: str, file_id: str):
        for doc in docs:
            doc.metadata = {
                "user_id": uid,
                "file_id": file_id}        
        self.vector_db.add_documents(docs)
        print(f"Added {len(docs)} embeddings for file_id: {file_id}")
               
    def deleteEmbeddings(self, uid: str, file_id: str):
        self.vector_db.index.delete(
            filter={
                "user_id": uid,
                "file_id": file_id
            }
        )
        print(f"Deleted embeddings for file_id: {file_id}")
    
    def query(self, question: str, uid: str) -> list[Document]:
        relevant_docs = self.vector_db.similarity_search(
            query=question,
            k=7,
            filter={"user_id": uid}
        )
        print(f"Found {len(relevant_docs)} relevant documents.")
        return relevant_docs
    
    
# ======================= Test ============================= #
# from processDocument import load_file_and_split, createChunkID
# Loading the file and splitting it into chunks
# split_docs = load_file_and_split(r"./assets/AttentionPaper.pdf")
# chunks1 = createChunkID(split_docs)

# split_docs = load_file_and_split(r"./assets/document.pdf")
# chunks2 = createChunkID(split_docs)

# chunks = chunks2
# print("Number of chunks: \t", len(chunks))
# print(chunks[0])

# Creating the embeddings and adding them to the vector db
# db = VectorDB(GooglePalmEmbeddings())

# db.addEmbeddings(chunks, uid="user1", file_id="document.pdf")

# db.deleteEmbeddings(uid="user1", file_id="document.pdf")

# results = db.query("What is the purpose of this document?", user_id="user1")
# print("Number of relevant documents: \t", len(results))
# for doc in results:
#     print(doc.metadata['user_id'], ":\t", doc.page_content)
# ========================================================== #
