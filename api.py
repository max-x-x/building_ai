import requests
from utils import extract_object_info

def get_object_info(token, object_id):
    """
    Получает информацию об объекте по ID и токену
    """
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"https://building-api.itc-hub.ru/api/v1/objects/{object_id}/full"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        object_data = response.json()
        
        result = extract_object_info(object_data)
        return result
        
    except Exception as e:
        if "Что вы не относитесь к этому объекту" in str(e):
            return {"error": "У вас нет доступа к этому объекту"}
        else:
            return {"error": str(e)}
