import requests
from typing import Optional, Dict, Any

class BuildingAPIClient:
    def __init__(self, base_url: str = "https://building-api.itc-hub.ru/api/v1"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        headers = {"Content-Type": "application/json"}
        data = {"email": email, "password": password}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if "access" in result:
                self.token = result["access"]
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_object_full(self, object_id: str) -> Dict[str, Any]:
        if not self.token:
            return {"error": "Authentication required"}
        
        url = f"{self.base_url}/objects/{object_id}/full"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
