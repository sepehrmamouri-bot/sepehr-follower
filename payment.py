import requests
from config import Config

class ZarinPalGateway:
    def __init__(self):
        self.merchant = Config.ZARINPAL_MERCHANT
        self.sandbox = Config.ZARINPAL_SANDBOX
        if self.sandbox:
            self.req_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.start_url = "https://sandbox.zarinpal.com/pg/StartPay/"
            self.ver_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
        else:
            self.req_url = "https://www.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
            self.start_url = "https://www.zarinpal.com/pg/StartPay/"
            self.ver_url = "https://www.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"

    def request_payment(self, amount_toman, description, phone, callback_url):
        amount_rial = int(amount_toman) * 10
        data = {
            "MerchantID": self.merchant,
            "Amount": amount_rial,
            "Description": description,
            "Mobile": phone,
            "CallbackURL": callback_url
        }
        try:
            res = requests.post(self.req_url, json=data, timeout=10)
            result = res.json()
            if result.get("Status") == 100:
                authority = result["Authority"]
                return {
                    "success": True,
                    "authority": authority,
                    "url": f"{self.start_url}{authority}"
                }
            return {"success": False, "error": f"Status: {result.get('Status')}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_payment(self, authority, amount_toman):
        amount_rial = int(amount_toman) * 10
        data = {
            "MerchantID": self.merchant,
            "Authority": authority,
            "Amount": amount_rial
        }
        try:
            res = requests.post(self.ver_url, json=data, timeout=10)
            result = res.json()
            if result.get("Status") in [100, 101]:
                return {"success": True, "ref_id": result.get("RefID")}
            return {"success": False, "status": result.get("Status")}
        except Exception as e:
            return {"success": False, "error": str(e)}

gateway = ZarinPalGateway()

