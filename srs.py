import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import openai
from datetime import datetime
import os

OPENAI_API_KEY = st.secrets["openai_api_key"]
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def fetch_subreddit_comments(subreddit, since, until, size=1000):
    url = f"https://api.pullpush.io/reddit/submission/search"
    params = {
        "html_decode": "True",
        "subreddit": subreddit,
        "since": since,
        "until": until,
        "size": size
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        response.raise_for_status()

def save_comments_to_file(subreddit, comments):
    file_name = f"{subreddit}_comments_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with open(file_name, "w") as file:
        for comment in comments:
            file.write(comment + "\n")
    return file_name

def analyze_comments_with_gpt4o(file_path):
    with open(file_path, "r") as file:
        comments = file.read()
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an expert data analyst."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze the following comments for common themes, popularity, and provide the most liked and disliked comments:\n\n{comments}\n"
                    }
                ]
            }
        ],
        temperature=1,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content

def list_comment_files():
    return [file for file in os.listdir() if file.endswith("_comments.txt")]

st.sidebar.image("https://raw.githubusercontent.com/VantaLabs/subredditstats/main/SRS.png", width=100)

st.image("https://raw.githubusercontent.com/VantaLabs/subredditstats/main/SRS.png", width=400)
st.title("Subreddit Comments Analysis")

st.sidebar.title("Historical Analysis")

comment_files = list_comment_files()
num_files = len(comment_files)
st.sidebar.metric("Number of Historical Files", num_files)
selected_file = st.sidebar.selectbox("Select a comments file to review:", comment_files)

if selected_file:
    with open(selected_file, "r") as file:
        comments = file.read()
    st.sidebar.write(comments)

if st.sidebar.checkbox("Show raw data as dataframe"):
    if selected_file:
        data = []
        with open(selected_file, "r") as file:
            comments = file.readlines()
            for comment in comments:
                data.append(comment.strip())
        df = pd.DataFrame(data, columns=["Comments"])
        st.write("Raw Data")
        st.dataframe(df)

subreddit = st.text_input("Subreddit", "rabbitr1")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

if st.button("Fetch and Analyze Comments"):
    since_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    until_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp())
    
    with st.spinner("Fetching comments..."):
        comments_data = fetch_subreddit_comments(subreddit, since_timestamp, until_timestamp)
        comments_text = [comment["selftext"] for comment in comments_data if comment["selftext"]]
    
    if comments_text:
        file_path = save_comments_to_file(subreddit, comments_text)
        with st.spinner("Analyzing comments with GPT-4..."):
            analysis_result = analyze_comments_with_gpt4o(file_path)
        
        st.write("Analysis Results")
        st.write(analysis_result)
    else:
        st.write("No comments found for the specified period.")
