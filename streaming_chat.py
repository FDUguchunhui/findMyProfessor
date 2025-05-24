from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.current_response = ""
        
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.current_response += token
        print(token, end="", flush=True)

def setup_chat():
    # Initialize vectorstore
    vectorstore = Chroma(
        persist_directory="faculties_vectorstore",
        embedding_function=OpenAIEmbeddings()
    )

    # Create retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Initialize LLM with streaming enabled
    llm = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4",
        streaming=True
    )

    # Set up memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Create conversation chain with streaming
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        callbacks=[StreamingCallbackHandler()]
    )

    return conversation_chain

def chat(query, history=None):
    """
    Chat with the faculty database using RAG with streaming
    """
    conversation_chain = setup_chat()
    result = conversation_chain.invoke({"question": query})
    return result["answer"]

if __name__ == "__main__":
    # Example usage
    while True:
        user_input = input("\nEnter your question (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        print("\nResponse: ", end="")
        chat(user_input) 