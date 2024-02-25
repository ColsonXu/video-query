# video-query

DEMO (might not work right now, but the app works locally): https://vquery.streamlit.app/

## Inspiration
As a student and avid self-learner, I often watch a lot of videos to gain new knowledge. Video is a great medium for knowledge because humans are visual learners. However, it is a tedious job when I want to review those concepts or find some specific detail in a 2-hour long lecture recording. Before vQuery, there is no way to interactively search a video file using natural language.

## What it does
For those who dream of a personal assistant who watches lecture recordings for you, vQuery is a chatbot that answers any question you have about the knowledge presented in the videos you upload. vQuery leverages industry-leading Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to provide intelligent natural language understanding and accurate responses. 

## How I built it
The general flow of vQuery is the user input either a video file or a YouTube link. If the user uploads a video, a transcript of that video is generated using the Assembly AI API. If a YouTube link is given, the caption can be downloaded directly from YouTube and turned into a transcript because YouTube automatically generates captions for all videos. This optimization saves a lot of time, as generating the transcript is the most time-consuming step.

With a transcript of the video, vector embeddings are generated using OpenAI’s embedding API. Those embeddings are then stored in a Pinecone vector database. This is essentially the knowledge base of our chatbot.

The way vector embeddings work is that they turn non-numerical data (text, images, audio) into a vector of numbers. By using a vector database, we can then perform similarity searches among those embeddings. Thus, when the user asks a question, that question is also turned into an embedding, and Pinecone will return a couple of embeddings it thinks are the most relevant to our search query.

 The returned embeddings are turned back into texts and compiled into an engineered prompt for our LLM (GPT-3.5). Using this engineered prompt, the LLM can access specific details of our input data (video) even though the video is not part of its training data. This is called RAG, and being able to create RAG-enabled custom LLMs is a very in-demand skill right now.

## Challenges I ran into
I initially wanted to use Cloudflare’s AI Workers, but I am not familiar with its workflow. I followed the documentation of LangChain, which is a popular framework that allows developers to create LLM pipelines, and it supports Cloudflare’s AI Workers. However, since this technology is still in its very early stage, breaking changes are pushed out frequently. I had a lot of trouble getting the pipeline to run using TypeScript because of package export errors. After I realized that it was not a problem I could fix without help from package maintainers, I switched to using individual APIs and built the project in Python, which I am more familiar with.

I also faced the same challenge building the project in Python - the codebase is rapidly changing, and oftentimes, even the documentation is not up-to-date. This means even when I am following the documentation word-by-word, I could still run into errors not documented anywhere.

I stayed up all night for this project. When it was almost finished, I copied the code into a GitHub repo because I was developing locally without version control. Maybe I was too tired, but one thing led to another; when I finally ran a `git reset --hard` to fix an error, I realized that the code base was gone in both directories before I had the chance to push it to GitHub. I panicked for a little while. Fortunately, even without committing locally, staged files can be found in `.git/lost-found/`.

## Accomplishments that I’m proud of
I am very proud of the fact that I built this project completely from scratch. I finally got out of the “tutorial hell.” I am also proud of the fact that I made so many different APIs work together. As I mentioned before, the libraries for LLM and RAG are rapidly evolving. This made troubleshooting much more challenging. Thus, I am proud of the fact I am able to fix all of the bugs I encountered.

## What I learned
**How Vector Databases and Retrieval-Augmented Generation works.**

Vector Database is a very hot topic right now. It enables developers to create custom chatbots on their own dataset without the need to fine-tune the LLM. It also solves the hallucination problem faced by LLMs, making the result much more accurate and reliable.

**Set up version control before starting a project.**

After almost losing a whole day and a whole night’s work, I learned a painful lesson to back up my code. Sometimes, I will start a scratch folder just to try out things, but sometimes, one of those playgrounds slowly shapes into the final project. This is why sometimes I develop without version control. This is a very bad practice for obvious reasons. Things happen, and you can lose all your progress in an instant. Version control also makes trying out and reverting from new features much easier.

## What's next for vQuery
Since I have to learn the entire tech stack from scratch, I have limited time to make the app perfect. The most important next step is to perform integration testing to ensure app stability. There are already some edge cases I can think of where the app could fail.

When uploading long videos, processing can take a long time. I want to implement sessions where each chat session is saved. The user can upload a video in different sessions, go to whichever one finishes first, and start asking questions. The user would be able to come back to a previous session to continue asking questions on a video instead of having to re-upload it again.
