import requests

def get_total_value(address: str):
    """
    Get the total balance for the user by their address
    """
    if not is_valid_address(address):
        print(f"Invalid address format: {address}")
        return None

    url = f"https://data-api.polymarket.com/value?user={address}"
    return make_request(url)

def get_positions(address: str, limit: int = 50):
    """
    Get the current positions for the user
    """
    if not is_valid_address(address):
        print(f"Invalid address format: {address}")
        return None

    url = f"https://data-api.polymarket.com/positions?user={address}&limit={limit}"
    return make_request(url)

def is_valid_address(address: str) -> bool:
    """
    Check if the address has the correct format
    """
    return address.strip().startswith("0x") and len(address.strip()) == 42

def make_request(url: str):
    """
    Make an HTTP request and handle the response
    """
    try:
        r = requests.get(url)
        print("Status code:", r.status_code)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Request error: {r.status_code}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None
    

