from google import genai
import langchain_chroma as chromaDB

class GooglePalmEmbeddings:
    def __init__(self):
        API_KEY = "your_api_key"
        self.client = genai.Client(api_key=API_KEY)
        
    def embed_documents(self, documents):
        embeddings = (self.client.models.embed_content(
                model="models/text-embedding-004", 
                contents=documents))
        return [e.values for e in embeddings.embeddings]
        
    def embed_query(self, text):
        embeddings = self.client.models.embed_content(
            model="models/text-embedding-004", 
            contents=text)
        return embeddings.embeddings[0].values


class ChromaDB:
    def __init__(self, filename, embeddingFunction):
        self.filename = filename
        self.vector_db = chromaDB.Chroma(persist_directory=f'vectorData/{self.filename}', 
                                embedding_function=embeddingFunction)

    def addEmbeddings_to_Chroma(self, chunks):
        doc_name = chunks[0].metadata.get("source")
        print("Adding embeddings to ChromaDB collection for : ", doc_name)

        existing_items = self.vector_db.get(include=[])
        existing_ids = set(existing_items["ids"])
        print(f"Number of existing documents in DB: {len(existing_ids)}")
        
        new_chunks = []
        for chunk in chunks:
            if chunk.metadata["id"] not in existing_ids:
                new_chunks.append(chunk)
        if len(new_chunks) != 0:
            chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
            self.vector_db.add_documents(new_chunks, ids=chunk_ids)
            print(f"Added {len(new_chunks)} new documents to database {self.filename}.")
            print("Added embeddings to ChromaDB.")
        else:
            print("No new documents to add.")
            
    def observeDB(self):
        print(f"Number of embeddings for document '{self.filename}' --> {len(self.vector_db.get(include=[])["ids"])}")
        print("Document IDs of embeddings in database: ", self.vector_db.get(include=[])["ids"])
    
    
# ======================= Test ============================= #
# from processDocument import load_file_and_split, createChunkID

# # Loading the file and splitting it into chunks
# split_docs = load_file_and_split(r"./assets/name_of_the_document.pdf")
# chunks = createChunkID(split_docs)

# addEmbeddings_to_Chroma(chunks)

# observeDB("name_of_the_document")
# ========================================================= #