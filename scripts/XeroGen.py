import gradio as gr
import os
import csv
import requests
from datetime import datetime
from modules import script_callbacks
import modules.generation_parameters_copypaste as parameters_copypaste
from modules import extensions

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


def launch_chat_interface(models):
    API_KEY_TITLES = list(read_api_keys_from_csv().keys())
    iface_chat = gr.Interface(
        fn=chat_with_gpt,
        inputs=[
            gr.components.Textbox(label="New API Key Title (Optional)"),
            gr.components.Textbox(label="New API Key (Optional)", type="password"),
            gr.components.Dropdown(choices=API_KEY_TITLES, label="API Key Selection"),
            gr.components.Dropdown(choices=list(PROMPTS_DICT.keys()), label="Your Prompt"),
            gr.components.Textbox(label="Your Message"),
            gr.components.Dropdown(choices=models, label="Model Selection"),
            gr.components.Slider(minimum=1, maximum=10, step=1, label="Number of Prompts"),
            gr.components.Checkbox(label="Save Responses"),
            gr.components.Checkbox(label="Label"),
            gr.components.Checkbox(label="Style"),
            gr.components.Checkbox(label="Trend")
        ],
        outputs=gr.components.Textbox(label="ChatGPT Responses", type="text"),
        )
    iface_chat.launch(debug=False)
    return iface_chat

def create_chatbot_ui():
    # This function sets up the chatbot UI using Gradio
    first_api_key = next(iter(read_api_keys_from_csv().values()))
    models = fetch_models(first_api_key)
    launch_chat_interface(models)

def get_self_extension():
    # This function retrieves the current extension's object based on the file path
    if '__file__' in globals():
        filepath = __file__
    else:
        import inspect
        filepath = inspect.getfile(lambda: None)
    for ext in extensions.active():
        if ext.path in filepath:
            return ext
    return None
    
def on_ui_tabs():
    # This function sets up the Gradio UI with tabs
    ext = get_self_extension()
    if ext is None:
        return []

    # If you have additional JS or CSS files to include, you can adapt the following
    # js_ = [f'{x.path}?{os.path.getmtime(x.path)}' for x in ext.list_files('js', '.js')]
    # js_.insert(0, ext.path)

    with gr.Blocks(analytics_enabled=False) as blocks:
        with gr.Tab(label="XeroGen", elem_id="tab_XeroGen"):
            # Here you can set up your UI components, like create_chatbot_ui()
            create_chatbot_ui()

    return [(blocks, "XeroGen", "tab_XeroGen")]

script_callbacks.on_ui_tabs(on_ui_tabs)
