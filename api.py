import requests

def get_total_value(address: str):
    address = address.strip()
    if not address.startswith("0x") or len(address) != 42:
        print("Неверный формат адреса:", address)
        return None

    url = f"https://data-api.polymarket.com/value?user={address}"
    try:
        r = requests.get(url)
        print("Status code:", r.status_code)
        print("Response:", r.text)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        print("Error in get_total_value:", e)
        return None

def get_positions(address: str, limit: int = 50):
    """
    Получаем текущие позиции пользователя через /positions
    """
    address = address.strip()
    if not address.startswith("0x") or len(address) != 42:
        print("Неверный формат адреса:", address)
        return None

    url = f"https://data-api.polymarket.com/positions?user={address}&limit={limit}"
    try:
        r = requests.get(url)
        print("Status code:", r.status_code)
        print("Response:", r.text)
        if r.status_code != 200:
            return None
        return r.json()  # вернёт список позиций
    except Exception as e:
        print("Error in get_positions:", e)
        return None
