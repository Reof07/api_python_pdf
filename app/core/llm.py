import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

# Llamar al modelo Cohere
model = init_chat_model("command-r-plus", model_provider="cohere") 