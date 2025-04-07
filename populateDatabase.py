from google import genai
from google.genai import types
import langchain_chroma as chromaDB
from pprint import pprint

class GooglePalmEmbeddings:
    def __init__(self):
        API_KEY = "your_api_key"
        self.client = genai.Client(api_key=API_KEY)
        
    def embed_documents(self, documents):
        embeddings = (self.client.models.embed_content(
                model="models/text-embedding-004", 
                contents=documents,
                config=types.EmbedContentConfig(task_type='retrieval_document')))
        return [e.values for e in embeddings.embeddings]
        
    def embed_query(self, text):
        embeddings = self.client.models.embed_content(
            model="models/text-embedding-004", 
            contents=text,
            config=types.EmbedContentConfig(task_type='retrieval_query'))
        return embeddings.embeddings[0].values


class ChromaDB:
    def __init__(self, embeddingFunction):
        self.vector_db = chromaDB.Chroma(persist_directory=f'vectorData/', 
                                embedding_function=embeddingFunction)

    def addEmbeddings_to_Chroma(self, chunks):
        doc_name = chunks[0].metadata.get("source")
        existing_items = self.vector_db.get(include=[])
        existing_ids = set(existing_items["ids"])
        print(f"Number of existing documents in DB: {len(existing_ids)}")
        print("Adding embeddings to ChromaDB collection for : ", doc_name)
        
        new_chunks = []
        for chunk in chunks:
            if chunk.metadata["id"] not in existing_ids:
                new_chunks.append(chunk)
        if len(new_chunks) != 0:
            chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
            self.vector_db.add_documents(new_chunks, ids=chunk_ids)
            print(f"Added {len(new_chunks)} new documents.")
            print("Added embeddings to ChromaDB.")
        else:
            print("No new documents to add.")
            
    def observeDB(self):
        print("Document IDs of embeddings in database: ", self.vector_db.get(include=[])["ids"])
    
    
# ======================= Test ============================= #
# from processDocument import load_file_and_split, createChunkID

# # Loading the file and splitting it into chunks
# split_docs = load_file_and_split(r"./assets/AttentionPaper.pdf")
# chunks1 = createChunkID(split_docs)

# split_docs = load_file_and_split(r"./assets/other_document.pdf")
# chunks2 = createChunkID(split_docs)

# chunks = chunks1 + chunks2
# print("Number of chunks: \n", len(chunks))

# # Creating the embeddings and adding them to the ChromaDB
# db = ChromaDB(GooglePalmEmbeddings())

# for i in range(0, len(chunks), 100):
#     # print(f"Adding chunks {i} to {i+99}")
#     db.addEmbeddings_to_Chroma(chunks[i:i+100])

# db.observeDB()
# ========================================================= #
