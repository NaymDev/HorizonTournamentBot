import requests

class ChallongeClient:
    BASE_URL = "https://api.challonge.com/v1"

    def __init__(self, api_key: str, user_agent: str = "HorizonChallongeClient/1.0"):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent
        })

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        response = self.session.get(f"{self.BASE_URL}{endpoint}.json", params=params)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(str(response.content))
            raise e
        return response.json()

    def _post(self, endpoint, data=None):
        if data is None:
            data = {}
        data["api_key"] = self.api_key
        response = self.session.post(f"{self.BASE_URL}{endpoint}.json", data=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(str(response.content))
            raise e
        return response.json()

    def _put(self, endpoint, data=None):
        if data is None:
            data = {}
        data["api_key"] = self.api_key
        response = self.session.put(f"{self.BASE_URL}{endpoint}.json", data=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(str(response.content))
            raise e
        return response.json()


    def create_tournament(self, name, url, signup_cap, tournament_type="single elimination"):
        data = {
            "tournament[name]": name,
            "tournament[url]": url,
            "tournament[tournament_type]": tournament_type,
            "tournament[open_signup]": False,
            "tournament[signup_cap]": signup_cap,
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
