from langchain.prompts import ChatPromptTemplate
import langchain_chroma as chromaDB
import backend.config as config

def creatingQuery(queryText):
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Now, your answer must be based on the following context and also gather information from the internet related to - {context}
    '''
    
    if config.ChromaDB is None:
        print("Error: ChromaDB not initialized. Please set API key and upload documents.")
        return f"Please answer this question: {queryText}. (Note: Document context is unavailable as the database is not ready)."

    try:
        results = config.ChromaDB.vector_db.similarity_search_with_score(queryText, k=5)
        contextText = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        if not contextText:
            print("Warning: No relevant context found in documents for the query.")
            contextText = "No specific context found in the provided documents."

    except Exception as e:
        print(f"Error during similarity search: {e}")
        contextText = f"Error retrieving context: {e}"

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=contextText, question=queryText)
    
    return prompt


# ======================= Test ============================= #
# document = "your_document.pdf"
# from populateDatabase import ChromaDB, GooglePalmEmbeddings
# from processDocument import load_file_and_split, createChunkID

# start = time.time()
# First load the document and split it into chunks
# splits = load_file_and_split(f"./assets/{document}")
# chunks = createChunkID(splits)

# # Create and add the embeddings to the ChromaDB
# db = ChromaDB(document, GooglePalmEmbeddings())
# db.addEmbeddings_to_Chroma(chunks)
# db.observeDB()

# start = time.time()
# # Now create a query
# prompt = creatingQuery("Give a summary of the document.", document)
# print("Response:", prompt)
# end = time.time()   
# print(f"Time taken: {(end-start):.4f} seconds")
