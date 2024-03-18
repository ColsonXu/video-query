import os
import streamlit as st
import tempfile
import uuid
from transcriptor import transcribe
from yt_caption import get_caption_from_youtube
from embedding import create_embeddings, retrieve
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(layout="wide")
st.title("vQuery")

col1, col2 = st.columns(2)

assemlyai_supported_file_ext = [
    '.3ga', '.webm', '.8svx', '.mts', '.m2ts', '.ts', '.aac', '.mov', '.ac3', '.mp2',
    '.aif', '.mp4', '.m4p', '.m4v', '.aiff', '.mxf', '.alac', '.amr', '.ape', '.au',
    '.dss', '.flac', '.flv', '.m4a', '.m4b', '.m4p', '.m4r', '.mp3', '.mpga', '.ogg',
    '.oga', '.mogg', '.opus', '.qcp', '.tta', '.voc', '.wav', '.wma', '.wv'
]

# Radio button to select input type
with col1:
    input_type = st.radio('Select input type:', ('YouTube URL', 'Media Upload', 'Text File Upload'))

# Function to process text input
def process_text_input():
    if 'transcript' not in st.session_state or st.session_state.transcript is None:
        with col1:
            user_input = st.text_area("Enter YouTube URL here:")
            if st.button('Submit'):
                if user_input:
                    st.write("Video Transcript:")
                    try:
                        transcript = get_caption_from_youtube(user_input)
                        st.session_state.transcript = transcript  # Store the transcript in session state
                    except:
                        st.warning("Error occurred, please try again.")
                else:
                    st.warning("Please enter some text.")

# Function to process media file upload
def process_media_upload():
    if 'transcript' not in st.session_state or st.session_state.transcript is None:
        with col1:
            uploaded_file = st.file_uploader("Upload an audio or video file.", type=assemlyai_supported_file_ext, accept_multiple_files=False)
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_file_path = tmp_file.name
                    with st.status("Generating Video Transcript..."):
                        transcript = transcribe(temp_file_path)
                        st.session_state.transcript = transcript  # Store the transcript in session state

# Function to process text file upload
def process_text_upload():
    if 'transcript' not in st.session_state or st.session_state.transcript is None:
        with col1:
            uploaded_files = st.file_uploader("Upload text files.", type="txt", accept_multiple_files=True)
            if uploaded_files:
                texts = []
                for file in uploaded_files:
                    texts.append(file.getvalue().decode("utf-8"))
                combined_text = "\n\n".join(texts)
                print(combined_text)
                st.session_state.transcript = combined_text # Store the transcript in session state

# Display the appropriate widget based on the input type
if input_type == 'YouTube URL':
    process_text_input()
elif input_type == 'Media Upload':
    process_media_upload()
elif input_type == 'Text File Upload':
    process_text_upload()

def gpt(prompt):
    res = llm.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers question based on the given video transcript. If the answer cannot be found, write \"I don't know.\""},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return res.choices[0].message.content.strip()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if 'transcript' in st.session_state and st.session_state.transcript is not None:
    # with col1:
    #     st.write(st.session_state.transcript)

    # create a uuid for this upload used for embedding creation and retrieval
    if 'namespace' not in st.session_state or st.session_state.namespace is None:
        st.session_state.namespace = str(uuid.uuid4())
        print("create uuid:", st.session_state.namespace)

    # Create embeddings for the transcript
    if 'embeddings_created' not in st.session_state:
        with col2:
            with st.status("Creating Embeddings..."):
                print("create embeddings:", st.session_state.namespace)
                create_embeddings(st.session_state.transcript, st.session_state.namespace)
                st.session_state.embeddings_created = True

    with col2:
        if prompt := st.chat_input("Ask me anything based on the transcript:"):
            # with st.chat_message("user"):
            #     st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # generating response
            print("retieval: ", st.session_state.namespace)
            engineered_prompt = retrieve(prompt, st.session_state.namespace)
            if engineered_prompt:
                response = gpt(engineered_prompt)
                # with st.chat_message("assistant"):
                #     st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.markdown("I don't know.")
                st.session_state.messages.append({"role": "assistant", "content": "I don't know."})

if 'messages' in st.session_state and st.session_state.messages:
    # Display chat messages from history on app rerun
    with col2:
        for message in st.session_state.messages[::-1]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])