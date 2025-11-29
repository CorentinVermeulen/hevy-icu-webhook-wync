import requests
import base64
import os
from datetime import datetime


class ApiConfig:

    def __init__(self):
        self.HEVY_API_KEY = os.getenv("HEVY_API_KEY")
        self.ICU_ATHLETE_ID = os.getenv("ICU_ATHLETE_ID")
        self.ICU_API_KEY = os.getenv("ICU_API_KEY")

        if not self.HEVY_API_KEY:
            raise ValueError("HEVY_API_KEY environment variable not set.")
        if not self.ICU_ATHLETE_ID:
            raise ValueError("ICU_ATHLETE_ID environment variable not set.")
        if not self.ICU_API_KEY:
            raise ValueError("ICU_API_KEY environment variable not set.")


class IntervalsIcuClient:
    """Client for interacting with the Intervals.icu API."""

    BASE_URL = "https://intervals.icu/api/v1/athlete/{athlete_id}"

    def __init__(self, athlete_id, api_key):
        self.athlete_id = athlete_id
        # Intervals.icu uses Basic Auth with 'API_KEY:<key>' as the username/password
        token = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
        self.base_url = self.BASE_URL.format(athlete_id=athlete_id)

    def _post(self, endpoint, payload):
        """Internal helper for POST requests."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response

    def post_events(self, workouts):
        """Posts multiple workouts as bulk events.
        Update events with matching external_id if it already exists.
        """

        endpoint = "events/bulk?upsert=true"
        payload = [
            {
                "category": "WORKOUT",
                "type": "WeightTraining",
                "color": "sweetSpot",
                "external_id": workout.get('id'),
                "name": workout.get('title', 'Hevy Workout'),
                "start_date_local": _convert_start_time(workout.get('start_time')),
                "description": _parse_exercises_to_desc(workout.get('exercises')),
                "moving_time": _get_moving_time(workout.get('start_time'), workout.get('end_time'))
            } for workout in workouts
        ]

        if not payload:
            # Return a response object similar to success if nothing to sync
            return requests.Response()

        return self._post(endpoint, payload)

    def post_activity(self, workout):
        """Posts a single workout as a manual activity."""
        endpoint = "activities/manual"
        payload = {
            "category": "WORKOUT",
            "type": "WeightTraining",
            "source": "UPLOAD",
            "entered": True,
            "color": "sweetSpot",
            "external_id": workout.get('id'),
            "name": "Hevy - " + workout.get('title', 'Workout'),
            "start_date_local": _convert_start_time(workout.get('start_time')),
            "description": _parse_exercises_to_desc(workout.get('exercises')),
            "moving_time": _get_moving_time(workout.get('start_time'), workout.get('end_time'))
        }

        return self._post(endpoint, payload)


class HevyClient:
    """Client for interacting with the Hevy API."""

    BASE_URL = "https://api.hevyapp.com/v1"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "accept": "application/json",
            "api-key": api_key
        }

    def fetch_activity(self, activity_id):
        url = f"{self.BASE_URL}/workouts/{activity_id}"
        response = requests.get(url, headers=self.headers)
        if not response.ok:
            raise "Failed to fetch activity.\nCode: %s\nBody: %s" % (response.status_code, response.text)
        return response.json()

    def fetch_workouts_page(self, page=1, page_size=10):
        page_size = min(page_size, 10)
        url = f"{self.BASE_URL}/workouts?page={page}&pageSize={page_size}"
        response = requests.get(url, headers=self.headers)
        if not response.ok:
            raise "Failed to fetch workout page %s/%s.\nCode: %s\nBody: %s" % (page, page_size, response.status_code,
                                                                               response.text)
        return response.json()


def _get_moving_time(start_str=None, end_str=None):
    """Calculates the moving time in seconds."""
    if not start_str or not end_str:
        return 60 * 60
    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
        return int((end_dt - start_dt).total_seconds())  # Use total_seconds() for precision
    except ValueError:
        return 60 * 60


def _convert_start_time(start_str):
    """Converts ISO format time string to Intervals.icu preferred format."""
    return datetime.fromisoformat(start_str).strftime("%Y-%m-%dT%H:%M:%S")


def _parse_exercises_to_desc(exercises):
    """Converts a list of exercises into a formatted description string."""
    out = []
    for ex in exercises:
        title = ex.get('title', 'Untitled Exercise')
        lines = [
            "-" * (len(title) * 2),
            title.upper(),
            "-" * (len(title) * 2)
        ]
        if ex.get('notes'):
            lines.append(f"({ex['notes']})")

        for s in ex.get('sets', []):
            line = ""
            if s.get('weight_kg') and s.get('reps'):
                line = f"\t-{s['reps']} x {s['weight_kg']}kg."
            elif s.get('duration_seconds'):
                line = f"\t-{s['duration_seconds']}s"
            elif s.get('distance_meters'):
                line = f"\t-{s['distance_meters']}m"

            if line:
                lines.append(line)

        out.append("\n".join(lines))

    return "\n\n".join(out)


### Synchronize All previous activities (not webhook-related) ###

def local_sync_all(max_page=1, page_size=10):
    """
    Synchronizes Hevy workouts to Intervals.icu activities.
    """

    config = ApiConfig()
    hevy_client = HevyClient(api_key=config.HEVY_API_KEY)
    icu_client = IntervalsIcuClient(
        athlete_id=config.ICU_ATHLETE_ID,
        api_key=config.ICU_API_KEY
    )

    curr_page = 1
    page_count = 1
    activity_count = 0

    while curr_page <= page_count and curr_page <= max_page:
        res = hevy_client.fetch_workouts_page(page=curr_page, page_size=page_size)
        page_count = res.get('page_count', 1)

        for workout in res.get('workouts', []):
            icu_client.post_activity(workout)
            activity_count += 1
            print(f"\rActivity {activity_count} synced. (page {curr_page}/{page_count})", end="")

        curr_page += 1
