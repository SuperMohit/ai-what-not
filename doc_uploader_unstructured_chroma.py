import os
import re
import streamlit as st
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table, Element
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

def extract_elements_with_by_title(pdf_path):
    # Use the by_title strategy to get structured chunks by headings/titles
    elements = partition_pdf(pdf_path, strategy="hi_res", by_title=True,  hi_res_model_name="yolox", infer_table_structure=True)
    print("Number of elements:", len(elements))
    # print each element
    for el in elements:
        print(el.text)
    return elements

def convert_elements_to_chunks(elements):
    # Convert each element into a chunk of text.
    # For Table elements, include a TABLE: ... END OF TABLE marker for clarity.
    chunks = []
    for el in elements:
        if isinstance(el, Table):
            print("TABLE:", el.text.strip())
            table_text = "TABLE:\n" + el.text.strip() + "\nEND OF TABLE"
            chunks.append(table_text)
        elif hasattr(el, 'text') and el.text:
            # Other text elements
            chunks.append(el.text.strip())
    return chunks

def clean_text(text):
    # Clean a text chunk by normalizing whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_vectorstore(chunks, embedding_model="text-embedding-3-large", persist_directory="./vectorstore"):
    embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=st.session_state.get("openai_api_key"))
    # Clean each chunk before embedding
    cleaned_chunks = [clean_text(c) for c in chunks if c.strip()]
    vectorstore = Chroma.from_texts(texts=cleaned_chunks, embedding=embeddings, persist_directory=persist_directory)
    vectorstore.persist()
    return vectorstore

def create_conversational_chain(vectorstore):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=st.session_state.get("openai_api_key"))
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever)
    return chain

# Streamlit UI
st.title("PDF Q&A with RAG (by_title Chunking)")

# Input for OpenAI API Key
api_key_input = st.text_input("Enter your OpenAI API Key:", type="password")
if api_key_input:
    st.session_state["openai_api_key"] = api_key_input

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file is not None and st.session_state.get("openai_api_key"):
    # Process PDF and create RAG pipeline if not done already
    if "vectorstore" not in st.session_state:
        with st.spinner("Processing PDF with 'by_title' strategy... This may take a moment."):
            # Save uploaded file temporarily
            pdf_path = "uploaded.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.read())

            # Extract elements using by_title strategy
            elements = extract_elements_with_by_title(pdf_path)
            chunks = convert_elements_to_chunks(elements)

            # Build vector store
            vectorstore = build_vectorstore(chunks)
            chain = create_conversational_chain(vectorstore)

            st.session_state["vectorstore"] = vectorstore
            st.session_state["chain"] = chain
            st.session_state["chat_history"] = []

    if "chain" in st.session_state:
        # Chat interface
        user_query = st.text_input("Ask a question about the PDF:")
        if user_query:
            chain = st.session_state["chain"]
            chat_history = st.session_state["chat_history"]
            with st.spinner("Thinking..."):
                result = chain({"question": user_query, "chat_history": chat_history})
                st.session_state["chat_history"].append((user_query, result["answer"]))

        # Display chat history
        if st.session_state.get("chat_history"):
            st.write("## Conversation History")
            for i, (q, a) in enumerate(st.session_state["chat_history"]):
                st.write(f"**User:** {q}")
                st.write(f"**Assistant:** {a}")
else:
    st.info("Please upload a PDF and enter your OpenAI API key to begin.")
