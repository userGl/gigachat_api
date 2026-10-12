import os
import time
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
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")
GIGACHAT_TEMPERATURE = float(os.getenv("GIGACHAT_TEMPERATURE", 0.8))

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

def get_api_response(description: str, access_token: str, model_name: str, temperature: float):
    client = OpenAI(
        api_key=access_token,
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        http_client=httpx.Client(verify=False)  
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Предложи варианты как провести вечер: {description}"}
        ],
        temperature=temperature,
    )
    return completion

if __name__ == "__main__":
    log_print(f"\n--- Запуск: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    access_token = get_access_token()
    log_print(f"Промпт: {system_prompt}")
    while True:
        description = input("\nВедите описание пользователя (0 — выход): ").strip()
        if description == "0":
            log_print("Выход из программы.")
            break
        started = time.perf_counter()
        response = get_api_response(description, access_token, GIGACHAT_MODEL, GIGACHAT_TEMPERATURE)
        time_elapsed = time.perf_counter() - started
        # Получаем полный объект ответа
        full_response = response
        # Диагностический вывод, включать при необходимости
        # log_print(f"Full response: {full_response.model_dump_json(indent=2)}")        
        finish_reason = full_response.choices[0].finish_reason
        usage = full_response.usage
        text_response = full_response.choices[0].message.content
        log_print(f"Описание пользователя:\n{description}")
        log_print(f"Ответ:\n{text_response}")
        log_print(f"Модель: {full_response.model}")
        log_print(f"Температура: {GIGACHAT_TEMPERATURE}")   
        log_print(f"Время выполнения: {time_elapsed:.2f} секунд")
        log_print( f"Метаданные: Finish Reason='{finish_reason}', " f"Токены (Всего/Промпт/Ответ/Кэшированные промпт): {usage.total_tokens}/{usage.prompt_tokens}/{usage.completion_tokens}/{usage.precached_prompt_tokens}" )
