import logging
import json
from utils import ApiConfig, HevyClient, IntervalsIcuClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _initialize_clients():
    config = ApiConfig()
    hevy_client = HevyClient(api_key=config.HEVY_API_KEY)
    icu_client = IntervalsIcuClient(
        athlete_id=config.ICU_ATHLETE_ID,
        api_key=config.ICU_API_KEY
    )
    return hevy_client, icu_client


def sync_activity(activity_id, hevy_client: HevyClient, icu_client: IntervalsIcuClient):
    """
    Fetches a single activity from Hevy and uploads it to Intervals.icu.
    """
    workout = hevy_client.fetch_activity(activity_id)
    icu_client.post_activity(workout=workout)

    return {
        "statusCode": 200,
        "body": f"Activity {activity_id} successfully synchronized to Intervals.icu"
    }


def hevy_webhook_handler(event, _):
    """
    Handles incoming webhooks from Hevy, validates the request, and triggers sync.
    """

    hevy_client, icu_client = _initialize_clients()
    hevy_webhook_key = hevy_client.api_key

    headers_norm = {str(k).lower(): v for k, v in event.get('headers', {}).items()}
    hevy_token = headers_norm.get('authorization', '').strip()

    if hevy_token != hevy_webhook_key:
        logger.warning('Unauthorized webhook request received.')
        return {
            "statusCode": 401,
            "body": "UNAUTHORIZED"
        }

    body = json.loads(event.get('body', '{}'))
    payload = body.get('payload', {})
    activity_id = payload.get('workoutId')

    if not activity_id:
        return {
            "statusCode": 400,
            "body": "Missing workoutId in payload. Expected: { 'id': 'uuid', 'payload': { 'workoutId': 'wid' } }"
        }
    return sync_activity(activity_id, hevy_client, icu_client)
