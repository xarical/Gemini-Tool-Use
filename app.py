import json
import os
from threading import Thread

import google.generativeai as genai
import gradio as gr
import requests

import tool_server

# config the model
genai.configure(api_key=os.environ['API_KEY'])
generation_config = {
  "max_output_tokens": 512,
  "temperature": 0.9
}
model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config)

system_prompt = """
**Prompt:**
You are a helpful assistant chatbot. You are talking to the user through a chat interface.
Use the tools detailed in the Tool Specifications section below to augment your built-in ability to perform tasks. Use different tools together to answer questions. If the tool call returns unhelpful results or an error or if an applicable tool is not listed, answer the user's question to the best of your knowledge. Separate lists of more than 2 tools into separate messages and send those messages one at a time.
Your response must be a valid JSON object similar to the 'assistant' messages in the following example conversation:
**Example:**
{
  "role": "user",
  "content": "Hi!"
}
{
  "role": "assistant",
  "type": "answer"
  "content": "Hello! 👋 How can I assist you today?"
}
{
  "role": "user",
  "content": "What is the time in India?"
}
{
  "role": "assistant",
  "type": "tool",
  "content": [
    {"name": "datetime", "data": {}}, 
    {"name": "websearch", "data": {"query": "Time difference between India and UTC"}}
  ]
}
{
  "role": "system", 
  "content": {"date": "2024-08-13", "time": "9:47:13"}
}
{
  "role": "system", 
  "content": "Time Difference between UTC and IST Indian. Indian Standard Time is 5 hours 30 minutes ahead from the UTC universal time. UTC to IST Indian Time Conversion"
}
{
  "role": "assistant",
  "type": "tool",
  "content": [
    {"name": "calculator", "data": {"operator": "add", "num1": 9, "num2": 5}},
    {"name": "calculator", "data": {"operator": "add", "num1": 47, "num2": 30}}
  ]
}
{
  "role": "system",
  "content": "14"
}
{
  "role": "system",
  "content": "77"
}
{
  "role": "assistant",
  "type": "answer",
  "content": "It’s currently 15:17 in IST (Indian Standard Time). This is equivalent to 3:17 PM in IST. Is there anything else I can assist you with? 😊"
}
**Tool Specifications:**
{
  "name": "datetime"
  "description": "A tool to get the current date and time in form YYYY-MM-DD and HH:MM:SS, in UTC with a 24-hour clock. It accepts nothing as the data."
  "data": {}
}
{
  "name": "calculator"
  "description": "A simple calculator tool that can do the four arithmetic operations. It accepts an operator and two integers."
  "data": {"operator": "string, add/subtract/multiply/divide", "num1": any int, "num2": any int}
}
{
  "name": "websearch"
  "description": "A search tool that can do a limited search of the web for answers. Results are not guaranteed to be accurate. IT DOES NOT WORK TO SEARCH ANYTHING TIME-SENSITIVE. It accepts a search query."
  "data": {"query": "any string"}
}
"""

url = "http://127.0.0.1:3000"

# handle the chatbot's messages
def chatbot_response(user_input, history):
  messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_input}]
  while True:
    chat_completion = model.generate_content(str(messages))
    chat_completion = chat_completion.text.replace('```json', '').replace('```', '').strip()
    print(chat_completion)
    messages.append(chat_completion)
    try:
      response = json.loads(chat_completion)
    except json.decoder.JSONDecodeError as e:
      print(e)
      r = '{"error": "Your previous message was invalid JSON and caused an error during parsing. (Hint: you may have hit the token limit, try separating your messages into multiple messages)}'
      print(r)
      messages.append({"role": "system", "content": r})
      continue
    if response["type"] == "tool":
      handle_tools(response["content"], messages)
    elif response["type"] == "answer":
      return response["content"]

# make the tool calls
def handle_tools(tools, messages):
  for tool in tools:
    try:
      if tool["name"] == "datetime":
        r = requests.get(url+"/datetime")
        r = r.json()
      elif tool["name"] == "calculator":
        r = requests.post(url+"/calculator", json=tool["data"])
        r = r.json()
      elif tool["name"] == "websearch":
        r = requests.post(url+"/websearch", json=tool["data"])
        r = r.json()
        tool_server.kill_vnc()
      else:
        r = f'{{"error": "Tool {tool["name"]} is an invalid tool"}}'
    except Exception as e:
      print(e)
      r = f'{{"error": "An error with making the API call to the tool {tool["name"]} has occurred, please inform the user of this"}}'
    print(r)
    messages.append({"role": "system", "content": r})

# start the tool_server
t = Thread(target=tool_server.run)
t.start()

# start the gradio interface
demo = gr.ChatInterface(fn=chatbot_response,
                       title="✨ Gemini Tool Use 🔨",
                       description="A Gemini 1.5 Flash chatbot, with Tool Use using a demo API implemented in Flask. It can use a calculator to perform basic arithmetic, get the current date and time, and search the web.")
demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)