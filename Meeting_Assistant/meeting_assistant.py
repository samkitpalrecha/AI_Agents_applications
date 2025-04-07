# meeting_assistant.py
from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, Tool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain.tools import tool
from langchain.schema import AgentAction, AgentFinish
from langchain_core.messages import AIMessage

import pandas as pd
from trello import TrelloClient

import os
from dotenv import load_dotenv
load_dotenv()

# Initialize the LLaMA model
llama_model = ChatGroq(temperature=0.3)

# Configuration for Trello
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_SECRET = os.getenv("TRELLO_API_SECRET")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")

# Trello Client
trello_client = TrelloClient(
    api_key=TRELLO_API_KEY,
    api_secret=TRELLO_API_TOKEN
)

import tkinter as tk
from tkinter import filedialog

def get_file_path():
    # Open file dialog to select a file
    file_path = filedialog.askopenfilename(
        title="Open the Meeting Transcript (MP3)", 
        filetypes=[("MP3 files", "*.mp3")]
        )
    return file_path

# Create a Tkinter window
root = tk.Tk()
root.withdraw()  # Hide the root window

# Open file dialog and process the file
mp3_file_path = get_file_path()

from mp3_to_text import convert_mp3_to_text

# convert mp3 to text meeting notes
meeting_notes = convert_mp3_to_text(mp3_file_path)

# @tool("load_meeting_notes", return_direct=True)
# def load_meeting_notes(file_path: str) -> str:
#     """
#     Load meeting notes from a text file.
#     """
#     try:
#         with open(file_path, "r") as file:
#             notes = file.read()
#         return notes
#     except FileNotFoundError:
#         return "Meeting notes file not found."

# meeting_notes = load_meeting_notes.invoke(file_path)
# print(meeting_notes)  # Verify loaded notes

# Prompt template for extracting tasks
task_prompt = PromptTemplate(
    input_variables=["meeting_notes"],
    template="""You are an assistant tasked with extracting actionable tasks from meeting notes.
    You should categorize tasks into three groups:
    - **To-Do**: Tasks that need to be completed.
    - **Doing**: Tasks that are currently in progress.
    - **Done**: Tasks that have been completed.

    Please output the tasks in a **JSON-like format** for each category. Example:
    {{
        "To-Do": [
            "Set up Stripe to manage the subscription model with three tiers: Basic, Pro, and Enterprise.",
            "Define the exact breakdown for each subscription tier in terms of features and pricing."
        ],
        "Doing": [
            "Jordan is working on the frontend tasks, including the checkout process and user notifications.",
            "Taylor is focusing on the backend setup, integrating Stripe's API, and setting up webhook handlers."
        ],
        "Done": [
            "The meeting notes have been extracted to identify actionable tasks.",
            "The subscription tiers, features, and pricing have been defined."
        ]
    }}

    Meeting Notes:
    {meeting_notes}
    """
)

import re
import json

def parse_tasks(output: str):
    # Define regular expressions for each task category
    to_do_pattern = r'"To-Do":\s*\[(.*?)\],'
    doing_pattern = r'"Doing":\s*\[(.*?)\],'
    done_pattern = r'"Done":\s*\[(.*?)\]'

    # Use re.search() to extract the task lists as strings
    to_do_tasks = re.search(to_do_pattern, output, re.DOTALL)
    doing_tasks = re.search(doing_pattern, output, re.DOTALL)
    done_tasks = re.search(done_pattern, output, re.DOTALL)

    # Extract tasks from each category and clean up the results
    to_do_tasks = re.findall(r'"(.*?)"', to_do_tasks.group(1)) if to_do_tasks else []
    doing_tasks = re.findall(r'"(.*?)"', doing_tasks.group(1)) if doing_tasks else []
    done_tasks = re.findall(r'"(.*?)"', done_tasks.group(1)) if done_tasks else []

    # Return the tasks in a dictionary format
    return {
        "To-Do": to_do_tasks,
        "Doing": doing_tasks,
        "Done": done_tasks
    }

parser = StrOutputParser()

# LLM Chain for task generation
generate_tasks_chain = task_prompt | llama_model | parser

# Function to generate tasks
def generate_tasks(notes: str) -> list:
    response = generate_tasks_chain.invoke({"meeting_notes": notes})
    # print(response)
    return parse_tasks(response)
    # return response

tasks = generate_tasks(meeting_notes)
# print(tasks)  # Verify generated tasks

BOARD_ID = "675310b78bfa02bada2dce16"
TO_DO = "675310b73297b35ec2144e9f"
DOING = "675310b85b7ddad518384b7f"
DONE = "675310b8a29eea7c444568bb"

# Function to add tasks to Trello lists
def add_tasks_to_trello(tasks: dict):
    # Get the Trello board and lists
    board = trello_client.get_board(BOARD_ID)
    to_do_list = board.get_list(TO_DO)
    doing_list = board.get_list(DOING)
    done_list = board.get_list(DONE)

    # Add To-Do tasks to the corresponding Trello list
    for task in tasks.get("To-Do", []):
        to_do_list.add_card(name=task)

    # Add Doing tasks to the corresponding Trello list
    for task in tasks.get("Doing", []):
        doing_list.add_card(name=task)

    # Add Done tasks to the corresponding Trello list
    for task in tasks.get("Done", []):
        done_list.add_card(name=task)

    print("Tasks added to Trello successfully!")

# Call the function with the tasks parsed from meeting notes
add_tasks_to_trello(tasks)

import csv

def save_tasks_to_csv(tasks):
    # Define the CSV file name
    csv_file = 'new_tasks.csv'

    # Check if the file exists, if not create it and add headers
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write headers only if file is new
        if not file_exists:
            writer.writerow(['Task', 'Category'])

        # Write tasks to the CSV file
        for category, task_list in tasks.items():
            for task in task_list:
                writer.writerow([task, category])

    print(f"Tasks saved to {csv_file}")

import requests

def send_discord_notification(tasks):
    webhook_url = 'https://discord.com/api/webhooks/1314964938405445653/uY944iG1TFzELBgR5zGFvLvDZSu3n2AgcMPrSEmYbuK2MgXJYnrp1M5cj6S5lIhTlnRN'
    message = f"New Tasks Added to Trello:\n"

    # Format tasks to include in the notification
    for category, task_list in tasks.items():
        message += f"\n**{category}:**\n"
        for task in task_list:
            message += f"- {task}\n"

    # Send the notification
    payload = {'content': message}
    response = requests.post(webhook_url, json=payload)

    if response.status_code == 204:
        print("Discord notification sent successfully!")
    else:
        print(f"Failed to send notification. Status code: {response.status_code}")

# Save tasks to CSV
save_tasks_to_csv(tasks)

# Send Discord notification
send_discord_notification(tasks)     