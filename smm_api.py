import requests
from config import Config

class SMMClient:
    def __init__(self):
        self.url = Config.SMM_API_URL
        self.key = Config.SMM_API_KEY

    def create_order(self, service_id, link, quantity):
        if not self.key:
            # حالت شبیه‌سازی در صورتی که کلید هنوز وارد نشده باشد
            return {"order": "MOCK_SMM_12345"}
        payload = {
            'key': self.key,
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity
        }
        try:
            res = requests.post(self.url, data=payload, timeout=10)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def get_order_status(self, smm_order_id):
        if not self.key or "MOCK" in str(smm_order_id):
            return {"status": "In progress"}
        payload = {
            'key': self.key,
            'action': 'status',
            'order': smm_order_id
        }
        try:
            res = requests.post(self.url, data=payload, timeout=10)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def get_balance(self):
        if not self.key:
            return {"balance": "0.00", "currency": "USD"}
        payload = {'key': self.key, 'action': 'balance'}
        try:
            res = requests.post(self.url, data=payload, timeout=10)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

smm_client = SMMClient()

