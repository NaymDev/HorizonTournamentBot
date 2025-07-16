import requests

class ChallongeClient:
    BASE_URL = "https://api.challonge.com/v1"

    def __init__(self, api_key: str, username: str):
        self.api_key = api_key
        self.username = username
        self.auth = (self.username, self.api_key)

    def _get(self, endpoint, params=None):
        response = requests.get(f"{self.BASE_URL}{endpoint}.json", auth=self.auth, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint, data=None):
        response = requests.post(f"{self.BASE_URL}{endpoint}.json", auth=self.auth, data=data)
        response.raise_for_status()
        return response.json()

    def _put(self, endpoint, data=None):
        response = requests.put(f"{self.BASE_URL}{endpoint}.json", auth=self.auth, data=data)
        response.raise_for_status()
        return response.json()

    def create_tournament(self, name, url, tournament_type="single elimination"):
        data = {
            "tournament[name]": name,
            "tournament[url]": url,
            "tournament[tournament_type]": tournament_type,
            "tournament[open_signup]": False
        }
        return self._post("/tournaments", data)

    def get_tournament(self, tournament_id):
        return self._get(f"/tournaments/{tournament_id}")

    def add_participant(self, tournament_id, name, misc=""):
        data = {
            "participant[name]": name,
            "participant[misc]": misc
        }
        return self._post(f"/tournaments/{tournament_id}/participants", data)
    
    def check_in_participant(self, tournament_id, participant_id):
        return self._post(f"/tournaments/{tournament_id}/participants/{participant_id}/check_in")
    
    def check_out_participant(self, tournament_id, participant_id):
        return self._post(f"/tournaments/{tournament_id}/participants/{participant_id}/undo_check_in")

    def list_participants(self, tournament_id):
        return self._get(f"/tournaments/{tournament_id}/participants")

    def start_tournament(self, tournament_id):
        return self._post(f"/tournaments/{tournament_id}/start")

    def get_matches(self, tournament_id):
        return self._get(f"/tournaments/{tournament_id}/matches")

    def get_participant_seed(self, tournament_id, participant_id):
        participant = self._get(f"/tournaments/{tournament_id}/participants/{participant_id}")
        return participant['participant']['seed']
