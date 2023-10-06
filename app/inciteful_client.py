import requests
from requests.exceptions import HTTPError, RequestException


class IncitefulClient:
    BASE_URL = "https://api.inciteful.xyz"

    def handle_response(self, req):
        try:
            req.raise_for_status()  # Raise HTTPError for bad responses

            # Check if the response contains JSON
            content_type = req.headers.get("Content-Type")
            if content_type is not None and "application/json" in content_type:
                return req.json()
            elif content_type is not None and "text" in content_type:
                return req.text
            else:
                raise ValueError("Unsupported response content type.")
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return {"error": f"HTTP error occurred: {http_err}"}
        except RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            return {"error": f"Request error occurred: {req_err}"}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {"error": f"An error occurred: {e}"}

    def get_papers(self, paper_ids):
        url = f"{self.BASE_URL}/paper"
        params = {"ids[]": paper_ids, "condensed": False}
        req = requests.get(url, params=params)
        return self.handle_response(req)

    def get_similar_papers(self, paper_id, num_results=10):
        url = f"{self.BASE_URL}/paper/similar/{paper_id}"
        params = {"n": num_results}
        req = requests.get(url, params=params)
        return self.handle_response(req)

    def query_single_paper(self, paper_id, sql_query):
        url = f"{self.BASE_URL}/query/{paper_id}"
        req = requests.post(url, data=sql_query)
        return self.handle_response(req)

    def query_multi_paper(self, paper_ids, sql_query):
        if paper_ids == []:
            return {"error": "No papers selected."}
        elif sql_query == None:
            return {"error": "No query provided."}

        if len(paper_ids) == 1:
            sql_query = sql_query.replace("{{filters}}", f"1=1")
        else:
            sql_query = sql_query.replace("{{filters}}", f"distance >= 2")

        url = f"{self.BASE_URL}/query"
        params = {"ids[]": paper_ids, "prune": 10000}
        req = requests.post(url, params=params, data=sql_query)
        return self.handle_response(req)
