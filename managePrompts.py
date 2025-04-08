from langchain.prompts import ChatPromptTemplate
import langchain_chroma as chromaDB
from google import genai
from pprint import pprint
import time


def creatingQuery(queryText):
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Now, if there is not document attached, forget about the context and answer the question based on your knowledge.
    If there is a document attached then your answer must be based on the following context - {context}
    '''
    
    from populateDatabase import GooglePalmEmbeddings
    db = chromaDB.Chroma(persist_directory=f'vectorData/', embedding_function=GooglePalmEmbeddings())
    results = db.similarity_search_with_score(queryText, k=10)
    # pprint(results)
    contextText = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_tempelate = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_tempelate.format(context=contextText, question=queryText)
    
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
