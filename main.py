import os
import streamlit as st
import tempfile
from transcriptor import transcribe
from yt_caption import get_caption_from_youtube
from embedding import create_embeddings, retrieve, reset_index
from openai import OpenAI

llm = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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
    input_type = st.radio('Select input type:', ('YouTube URL', 'File Upload'))

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

# Function to process file upload
def process_file_upload():
    if 'transcript' not in st.session_state or st.session_state.transcript is None:
        with col1:
            uploaded_file = st.file_uploader("Upload an audio or video file.", type=assemlyai_supported_file_ext)
            if uploaded_file is not None:
                st.write("Generating Video Transcript...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_file_path = tmp_file.name
                    transcript = transcribe(temp_file_path)
                    st.session_state.transcript = transcript  # Store the transcript in session state


# Display the appropriate widget based on the input type
if input_type == 'YouTube URL':
    process_text_input()
elif input_type == 'File Upload':
    process_file_upload()

def gpt(prompt):
    res = llm.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers question based on the given context. If the answer cannot be found, write \"I don't know.\""},
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
    with col1:
        st.write(st.session_state.transcript)

    # Create embeddings for the transcript
    if 'embeddings_created' not in st.session_state:
        with st.spinner("Creating Embeddings..."):
            create_embeddings(st.session_state.transcript)
            st.session_state.embeddings_created = True
    
    with col1:
        if st.button("Reset Index"):
            reset_index()

    with col2:
        if prompt := st.chat_input("Ask me anything based on the transcript:"):
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # generating response
            engineered_prompt = retrieve(prompt)
            if engineered_prompt:
                response = gpt(engineered_prompt)
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.markdown("Error occured, please try again.")
                st.session_state.messages.append({"role": "error", "content": "Error occured, please try again."})

# if 'messages' in st.session_state and st.session_state.messages:
#     # Display chat messages from history on app rerun
#     with col2:
#         for message in st.session_state.messages:
#             with st.chat_message(message["role"]):
#                 st.markdown(message["content"])