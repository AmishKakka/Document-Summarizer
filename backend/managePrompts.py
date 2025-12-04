'''
This module contains functions to create prompts for querying the language model.
'''
from langchain_core.prompts import ChatPromptTemplate

def creatingQuery(queryText: str, relevant_docs):
    contextText = [doc.page_content for doc in relevant_docs]
    contextText = "\n\n---\n\n".join(contextText)
    PROMPT_TEMPLATE = '''
    Answer the question - {question}
    ----
    Use Markdown for all formatting. For example, use bolding for key terms with **text**, and use bullet points for lists, but don't 
    mention it in your response. If you include code snippets, use triple backticks to format them properly.
    Now, your answer must be based on the following context - {context}
    Also, a final note - if you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer. 
    And the length of the response must be less than 500 words.
    '''

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=contextText, question=queryText)
    return prompt
