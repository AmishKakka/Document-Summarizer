from langchain.prompts import ChatPromptTemplate
import langchain_chroma as chromaDB
import time
from backend.populateDatabase import GooglePalmEmbeddings

def creatingQuery(queryText):
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Use Markdown for all formatting. For example, use bolding for key terms with **text**, and use bullet points for lists, but don't 
    mention it in your response. If you include code snippets, use triple backticks to format them properly.
    Now, your answer must be based on the following context - {context}
    Also, a final note - if you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer. 
    And the length of the response must be less than 700 words.
    '''
    db = chromaDB.Chroma(persist_directory=f'./vectorData', 
                         embedding_function=GooglePalmEmbeddings())
    try:        
        results = db.similarity_search_with_score(queryText, k=5)
        print(results)
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
# document = "Amish Kakka Resume.pdf"
# from processDocument import load_file_and_split, createChunkID
# from backend.configs import API_KEY
# import google.genai as genai
# from fastapi.responses import HTMLResponse
# from markdown_it import MarkdownIt

# md = MarkdownIt()
# start = time.time()
# # First load the document and split it into chunks
# splits = load_file_and_split(f"./assets/{document}")
# chunks = createChunkID(splits)

# # Create and add the embeddings to the ChromaDB
# db = ChromaDB(GooglePalmEmbeddings())
# db.addEmbeddings_to_Chroma(chunks)
# db.observeDB()

# start = time.time()
# # Now create a query
# prompt = creatingQuery("Give a summary of the document.")
# print("Response:", prompt)
# model_output = ""
# client = genai.Client(api_key=API_KEY)

# for next_text in client.models.generate_content_stream(model='gemini-2.0-flash-001', 
#                                                             contents=prompt):
#     model_output += next_text.text

# html_content = md.render(model_output)
# print(HTMLResponse(content=html_content, media_type = 'text/html').body.decode('utf-8'))
# end = time.time()   
# print(f"Time taken: {(end-start):.4f} seconds")
