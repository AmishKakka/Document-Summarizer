from langchain.prompts import ChatPromptTemplate
import langchain_chroma as chromaDB
from google import genai
from pprint import pprint
import time

def generatingResponse(prompt):
    API_KEY = "your_api_key"
    client = genai.Client(api_key=API_KEY)
    
    chunk = client.models.generate_content(model='gemini-2.0-flash-001', 
                                           contents=prompt)
    print(chunk.candidates[0].content.parts[0].text)


def creatingQuery(queryText, base):
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Your answer must be based on the following context only - {context}
    '''
    
    from populateDatabase import GooglePalmEmbeddings
    db = chromaDB.Chroma(persist_directory=f'vectorData/{base}', embedding_function=GooglePalmEmbeddings())
    results = db.similarity_search_with_score(queryText, k=10)
    pprint(results)
    contextText = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_tempelate = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_tempelate.format(context=contextText, question=queryText)
    
    generatingResponse(prompt)


# ======================= Test ============================= #
# document = "name_of_the_document.pdf"
# from populateDatabase import ChromaDB, GooglePalmEmbeddings
# from processDocument import load_file_and_split, createChunkID

# # start = time.time()
# # # First load the document and split it into chunks
# splits = load_file_and_split(f"./assets/{document}")
# chunks = createChunkID(splits)

# # # Create and add the embeddings to the ChromaDB
# db = ChromaDB(document, GooglePalmEmbeddings())
# db.addEmbeddings_to_Chroma(chunks)
# db.observeDB()

# start = time.time()
# # Now create a query
# creatingQuery("Give a summary of the Deepmind project and list the resources relevant for it from github.")
# end = time.time()   
# print(f"Time taken: {(end-start):.4f} seconds")