from django.conf.global_settings import SECRET_KEY
from google import genai
from django.conf import settings
from typing import Dict, Optional
import os
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')
client = genai.Client(api_key=API_KEY)


response= client.models.generate_content(
    model='gemini-2.5-pro',
    contents='Tengo un habito en mi calentario de habitos que es hacer presbanca en mi gimancio cada 3 dia a la semana'
             'mido 1.80metros y peso 71kg'
)
