"""
This file es responsible for the ingestion of the data (langchain documentation).
It embedds the data into vectors, and stores it in the pinecone vectorstore.
"""
from langchain.document_loaders import ReadTheDocsLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

import os
import pinecone
from consts import INDEX_NAME

# initialize pinecone client
pinecone.init(api_key=os.environ["PINECONE_API_KEY"],
              environment=os.environ["PINECONE_ENVIRONMENT"])

# The ingestion process is divided into 3 steps:
# 1. Load the documents from the source (ReadTheDocsLoader)
# 2. Split the documents into chunks (RecursiveCharacterTextSplitter)
# 3. Embed the chunks into vectors and store them in the vectorstore (Pinecone.from_documents)


def ingest_docs() -> None:
    # The ReadTheDocsLoader is a class that is in charge of taking the dump of some scrapped data-fetching
    #  process and loading it into the vectorstore.
    loader = ReadTheDocsLoader(
        "langchain-docs/langchain.readthedocs.io/en/latest/"
    )

    # loader.load() -> [documents] (documents are just dictionaries)
    raw_documents = loader.load()

    print(f"Loaded {len(raw_documents)} documents")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""])

    # Execute splitter, to allow parallelization of the embedding process.
    documents = text_splitter.split_documents(documents=raw_documents)

    print(f"Split {len(documents)} documents into chunks")

    # Simple dictionary manipulation to change the source path of the documents, to a valid langchain docs page.
    # This will enable us later to have easy access to the "relevant" context. (proximity search)
    for doc in documents:
        old_path = doc.metadata["source"]
        new_url = old_path.replace(
            "langchain-docs/", "https:/")
        doc.metadata.update({"source": new_url})

    print(f"Uploading {len(documents)} documents to vectorstore (pinecone)")
    # The embeddings object is in charge of embedding the documents into vectors.
    embeddings = OpenAIEmbeddings()

    # Take the chunks, imbed them into vectors and store them in the Pinecone vector database.
    Pinecone.from_documents(documents,
                            embeddings, index_name=INDEX_NAME)
    print("*********Added documents to Pinecone*********")


if __name__ == '__main__':
    ingest_docs()
