import threading
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from loguru import logger
from auto_reviewer.utils import ReviewerConfig, MergeRequest, MergeRequestConfig
from auto_reviewer.llm import review_with_llm, ChatClient
from pydantic import BaseModel
from pathlib import Path
import re
from typing import Optional
from threading import Lock

PROJECT_ROOT_PATH = Path(__file__).resolve().parent

app = FastAPI()

reviewer_config = ReviewerConfig.from_config(PROJECT_ROOT_PATH / 'reviewer-config.yaml')

CLIENTS = dict()
CLIENTS_LOCK = Lock()


def start_review(mr: MergeRequest, client: ChatClient):
    logger.info("Starting review process for merge request")

    try:
        comments, success = review_with_llm(mr, client)
        if success:
            mr.submit_comment(comments)
            logger.info("Comments successfully submitted.")
            return Response(status_code=200)
        else:
            return Response(status_code=500)
    except Exception as e:
        logger.error(f"Review failed: {e}")


class GitlabEvent(BaseModel):
    event_type: str
    project: dict
    object_attributes: dict
    merge_request: Optional[dict] = None


@app.get("/healthz")
async def healthz() -> Response:
    return Response(status_code=200)


@app.post("/auto-reviewer")
async def gitlab_webhook(event: GitlabEvent) -> Response:
    project_name = event.project['name']
    project_id = event.project['id']
    prompt = event.object_attributes['description']

    if not prompt.startswith("@reviewer-bot"):
        return Response(status_code=200)

    pattern = r'@reviewer-bot:(\w+)'
    match = re.search(pattern, prompt)
    model_provider = match.group(1) if match else 'oai'

    # Handle the 'merge_requests' and 'note' events
    if event.event_type == 'merge_requests' and event.object_attributes.get('action') == 'open':
        merge_id = event.object_attributes['iid']
    elif event.event_type == 'note' and event.merge_request:
        merge_id = event.merge_request['iid']
    else:
        raise HTTPException(status_code=400, detail="Invalid GitLab event or missing merge request.")

    logger.info(
        f"Processing merge request - project: {project_name}, merge id: {merge_id}, model provider: {model_provider}")

    mr = MergeRequest.from_config(
        MergeRequestConfig(project_name=project_name, project_id=project_id, merge_id=merge_id),
        config=reviewer_config
    )

    with CLIENTS_LOCK:
        if model_provider not in CLIENTS:
            chat_config = getattr(reviewer_config.llm_config, model_provider)
            client = ChatClient.from_config(chat_config)
            CLIENTS[model_provider] = client
        else:
            client = CLIENTS[model_provider]

    try:
        thread = threading.Thread(target=start_review, args=(mr, client))
        thread.start()
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail="Error starting review thread.")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5100)
