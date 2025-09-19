from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pprint import pprint

def load_file_and_split(file_name):
    loader = PyPDFLoader(f"{file_name}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False
        )
    return loader.load_and_split(text_splitter)
    

def createChunkID(chunks):
    current_chunk_idx = 0
    last_page_id = None
    
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"
        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_idx += 1
        else:
            current_chunk_idx = 0
            
        chunk_id = f"{current_page_id}:{current_chunk_idx}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id
    return chunks


# ======================= Test ============================= #
# split_docs = load_file_and_split(r"./assets/document.pdf")
# content = [doc.page_content for doc in split_docs]

# chunks = createChunkID(split_docs)
# pprint([chunk.metadata['id'] for chunk in chunks])
# print([chunk.page_content for chunk in chunks])
# ========================================================== #