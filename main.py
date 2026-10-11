import os
import uuid
import requests
import httpx
import urllib3
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

load_dotenv()
base_dir = Path(__file__).resolve().parent

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

if not GIGACHAT_AUTH_KEY:
    raise ValueError("Не найден GIGACHAT_AUTH_KEY в .env")

prompt_path = base_dir / "prompt.txt"
system_prompt = prompt_path.read_text(encoding="utf-8").strip()


def get_access_token() -> str:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
    }

    data = {
        "scope": GIGACHAT_SCOPE
    }

    response = requests.post(
        url,
        headers=headers,
        data=data,
        timeout=30,
        verify=False  
    )

    response.raise_for_status()
    return response.json()["access_token"]

def log_print(text):
    print(text)
    with (base_dir / "chat.log").open("a", encoding="utf-8") as log:
        log.write(text + "\n")

def get_gift_ideas(user_description: str) -> str:
    access_token = get_access_token()

    client = OpenAI(
        api_key=access_token,
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        http_client=httpx.Client(verify=False)  
    )

    completion = client.chat.completions.create(
        model="GigaChat",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Подбери подарки для такого человека: {user_description}"
            }
        ],
        temperature=0.8,
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    person_description = "Девушка, 27 лет, любит йогу, кофе, уютные вещи для дома и путешествия"
    print(get_gift_ideas(person_description))