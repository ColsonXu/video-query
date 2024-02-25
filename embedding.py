import re
import os
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm
from time import sleep
import uuid  # To generate unique IDs for each chunk

llm = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

EMBED_MODEL = "text-embedding-3-small"

SENTENCE_WINDOW = 20  # Number of sentences per chunk
SENTENCE_STRIDE = 4   # Overlap in sentences
WORDS_WINDOW = 400    # Number of words per chunk
WORDS_STRIDE = 80     # Overlap in words

###################### setup ######################
# Test embedding to find dimension
test_embedding = llm.embeddings.create(
    input=[
        "Sample document text goes here",
        "there will be several phrases in each batch"
    ],
    model=EMBED_MODEL
)

index_name = "vquery"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=len(test_embedding.data[0].embedding),
        metric='cosine',
        spec=ServerlessSpec(
            cloud="aws",
            region="us-west-2"
        )
    )

index = pc.Index(index_name)

def _create_sentence_chunks_re(text, window, stride):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    i = 0
    while i < len(sentences):
        chunk = ' '.join(sentences[i:i+window])
        chunks.append({
            'id': str(uuid.uuid4()),  # Assign a unique ID to each chunk
            'text': chunk
        })
        i += stride

    return chunks

def _create_sentence_chunks_fixed(text, window, stride):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        # Create the chunk of text
        chunk_text = ' '.join(words[i:i + window])
        # Append a dictionary with an ID and the chunk text
        chunks.append({
            'id': str(uuid.uuid4()),  # Assign a unique ID to each chunk
            'text': chunk_text
        })
        i += stride  # Move forward by stride for overlap

        # Ensure we capture the content at the end of the text if it does not align perfectly with the window
        if i + window > len(words) and i < len(words):
            # Ensure this last chunk is unique and not a repeat of the previous chunk
            if i != len(words) - window:  # Check to avoid duplicating the last chunk
                last_chunk_text = ' '.join(words[-window:])
                chunks.append({
                    'id': str(uuid.uuid4()),  # Assign a unique ID to the last chunk
                    'text': last_chunk_text
                })
            break

    return chunks

def _upsert(index, namespace, data):
    batch_size = 100
    for i in tqdm(range(0, len(data), batch_size)):
        i_end = min(len(data), i+batch_size)
        meta_batch = data[i:i_end]
        
        ids_batch = [x['id'] for x in meta_batch]
        texts = [x['text'] for x in meta_batch]

        try:
            print("creating embedding")
            res = llm.embeddings.create(input=texts, model=EMBED_MODEL)
        except:
            print("exception")
            done = False
            while not done:
                sleep(5)
                try:
                    res = llm.embeddings.create(input=texts, model=EMBED_MODEL)
                    done = True
                except:
                    pass

        embeds = [record.embedding for record in res.data]
        
        # Prepare data for upserting to Pinecone
        to_upsert = list(zip(ids_batch, embeds, meta_batch))
        
        # Upsert to Pinecone
        index.upsert(vectors=to_upsert, namespace=namespace)


def create_embeddings(transcript, namespace):
    chunks = _create_sentence_chunks_re(transcript, SENTENCE_WINDOW, SENTENCE_STRIDE)
    if len(chunks) == 1 and len(transcript) > 10000:
        chunks = _create_sentence_chunks_fixed(transcript, WORDS_WINDOW, WORDS_STRIDE)
    print(chunks)
    _upsert(index, namespace, chunks)


limit = 3750
def retrieve(query, namespace):
    res = llm.embeddings.create(
        input=[query],
        model=EMBED_MODEL
    )

    xq = res.data[0].embedding
    res = index.query(vector=xq, top_k=3, include_metadata=True, namespace=namespace)

    contexts = [
        x.metadata['text'] for x in res.matches
    ]

    if len(contexts) == 0:
        print(res)
        return None

    prompt_start = (
        "Answer the question based on the context below.\n\n" +
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {query}\nAnswer:"
    )

    # append contexts until hitting limit
    for i in range(len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) +
                prompt_end
            )
    return prompt
