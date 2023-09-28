import gradio as gr
import requests
import csv
import os
from datetime import datetime
import time

CSV_FILE = "chatgpt_responses.csv"
PROMPT_CSV = "prompts.csv"
API_KEYS_CSV = "api_keys.csv"
recent_outputs = {}
chat_sessions = {}  # Dictionary to store ongoing chat sessions by prompt title

def read_prompts_from_csv():
    prompts = {}
    with open(PROMPT_CSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            title, prompt = row
            prompts[title] = prompt
    return prompts

PROMPTS_DICT = read_prompts_from_csv()

def read_api_keys_from_csv():
    api_keys = {}
    with open(API_KEYS_CSV, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            title, key = row
            api_keys[title] = key
    return api_keys

def save_new_api_key_to_csv(title, api_key):
    with open(API_KEYS_CSV, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([title, api_key])
        
def fetch_models(api_key):
    response = requests.get(
        "https://api.openai.com/v1/engines",
        headers={
            "Authorization": f"Bearer {api_key}"
        }
    )
    data = response.json()
    if 'data' in data:
        models = [engine['id'] for engine in data['data']]
        if 'gpt-3.5-turbo' in models:
            models.remove('gpt-3.5-turbo')
            models.insert(0, 'gpt-3.5-turbo')
        return models
    else:
        print(f"Error fetching engines: {data.get('error', 'Unknown error')}")
        return []

def save_to_csv(user_message):
    global recent_outputs
    if recent_outputs:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mode = 'a' if os.path.exists(CSV_FILE) else 'w'
        
        with open(CSV_FILE, mode, newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if mode == 'w':
                writer.writerow(["Date Generated", "User Message", "Response"])
            for output in recent_outputs:
                writer.writerow([timestamp, user_message, output])
        recent_outputs.clear()

def chat_with_gpt(new_api_key_title, new_api_key, api_key_title, title, message, model=None, num_requests=1, save_responses=False, label=False, style=False, trend=False):
    global recent_outputs, chat_sessions

    # Check and save the new API key if provided
    if new_api_key_title and new_api_key:
        save_new_api_key_to_csv(new_api_key_title, new_api_key)
        api_key = new_api_key
    else:
        API_KEYS = read_api_keys_from_csv()
        api_key = API_KEYS[api_key_title]

    # Fetch user prompt from PROMPTS_DICT
    user_prompt = PROMPTS_DICT[title]  
    
    # Check model
    if model is None:
        model = "gpt-3.5-turbo"
    
    # Modify the message based on provided flags
    modified_message = message
    if style:
        modified_message = "$style, " + modified_message
    if num_requests > 1:
        modified_message = f"{num_requests} prompts, " + modified_message
    if label:
        modified_message = "$label, " + modified_message
    if trend:
        modified_message += ", $trend"
    
    # Prepare the history for the chat
    formatted_history = [{"role": "system", "content": user_prompt}]
    if title in chat_sessions:
        formatted_history.extend(chat_sessions[title])
    else:
        chat_sessions[title] = []
    # Replace or append the user's message
    if len(chat_sessions[title]) == 1:
        chat_sessions[title][0] = {"role": "user", "content": modified_message}
    else:
        chat_sessions[title].append({"role": "user", "content": modified_message})
    
    formatted_history.extend(chat_sessions[title])

    # Make the API request
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": formatted_history
        }
    )

    response_data = response.json()
    if 'choices' in response_data:
        all_responses = [response_data['choices'][0]['message']['content'].strip()]
    else:
        return f"Error: {response_data.get('error', 'Unknown error.')}"
    
    recent_outputs = all_responses.copy()  # Use .copy() to keep a separate list for saving
    if save_responses:
        save_to_csv(modified_message)
    return "\n---\n".join(all_responses)


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as ui_component:
        with gr.Row():
            new_api_key_title = gr.Textbox(label="New API Key Title (Optional)")
            new_api_key = gr.Textbox(label="New API Key (Optional)", type="password")
            api_key_title = gr.Dropdown(choices=list(read_api_keys_from_csv().keys()), label="API Key Selection")
            title = gr.Dropdown(choices=list(read_prompts_from_csv().keys()), label="Your Prompt")
            message = gr.Textbox(label="Your Message")
            model = gr.Dropdown(choices=fetch_models(next(iter(read_api_keys_from_csv().values()))), label="Model Selection")
            num_requests = gr.Slider(minimum=1, maximum=10, step=1, label="Number of Prompts")
            save_responses = gr.Checkbox(label="Save Responses")
            label = gr.Checkbox(label="Label")
            style = gr.Checkbox(label="Style")
            trend = gr.Checkbox(label="Trend")
            btn = gr.Button("Chat with GPT").style(full_width=False)
        with gr.Row():
            responses = gr.Textbox(label="ChatGPT Responses", type="text")

        btn.click(
            chat_with_gpt,
            inputs=[new_api_key_title, new_api_key, api_key_title, title, message, model, num_requests, save_responses, label, style, trend],
            outputs=[responses]
        )

        return [(ui_component, "ChatGPT Extension", "chatgpt_extension_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)