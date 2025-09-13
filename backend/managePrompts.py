from langchain.prompts import ChatPromptTemplate
# import langchain_chroma as chromaDB
from backend.populateDatabase import ChromaDB, GooglePalmEmbeddings

def creatingQuery(queryText):
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Use Markdown for all formatting. For example, use bolding for key terms with **text**, and use bullet points for lists, but don't 
    mention it in your response. If you include code snippets, use triple backticks to format them properly.
    Now, your answer must be based on the following context and also gather information from the internet, to find supporting facts 
    related to - {context}
    '''
    db = ChromaDB(GooglePalmEmbeddings())

    try:
        results = db.vector_db.similarity_search_with_score(queryText, k=5)
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
# db = ChromaDB(GooglePalmEmbeddings())
# db.addEmbeddings_to_Chroma(chunks)
# db.observeDB()

# start = time.time()
# # Now create a query
# prompt = creatingQuery("Give a summary of the document.", document)
# print("Response:", prompt)
# end = time.time()   
# print(f"Time taken: {(end-start):.4f} seconds")
