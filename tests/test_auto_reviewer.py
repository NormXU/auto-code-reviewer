import pytest
from fastapi.testclient import TestClient
from unittest import mock
from main import app  # Import your FastAPI app
from auto_reviewer.llm import ChatClient


@pytest.fixture
def mock_chat_client():
    # Mock the ChatClient class to avoid actual API calls
    mock_client = mock.MagicMock(spec=ChatClient)
    mock_client.chat.return_value = "Mocked Review Comment"
    return mock_client


@pytest.fixture
def mock_gitlab():
    # Mock the response for Gitlab projects and merge requests
    mock_gitlab_instance = mock.MagicMock()
    mock_project = mock.MagicMock()
    mock_mr = mock.MagicMock(title='test-project', description="@reviewer-bot:oai")

    mock_project.mergerequests.get.return_value = mock_mr

    mock_mr.changes.return_value = {"changes": [
        {
            "new_file": True,
            "deleted_file": False,
            "renamed_file": False,
            "modified_file": False,
            "new_path": "src/new_file.py",
            "diff": "+ diff content for new file..."
        },
        {
            "new_file": False,
            "deleted_file": True,
            "renamed_file": False,
            "modified_file": False,
            "old_path": "src/old_file.py",
            "diff": "- diff content for deleted file..."
        },
        {
            "new_file": False,
            "deleted_file": False,
            "renamed_file": True,
            "modified_file": False,
            "old_path": "src/old_name.py",
            "new_path": "src/new_name.py",
            "diff": "+ diff content for renamed file..."
        },
        {
            "new_file": False,
            "deleted_file": False,
            "renamed_file": False,
            "modified_file": True,
            "new_path": "src/modified_file.py",
            "diff": "+ diff content for modified file..."
        }
    ]}

    mock_gitlab_instance.projects.get.return_value = mock_project

    return mock_gitlab_instance


@pytest.fixture
def client():
    # Create the TestClient instance
    return TestClient(app)


def test_auto_reviewer_valid_request(client, mock_chat_client, mock_gitlab):
    mock_event = {
        "event_type": "merge_requests",
        "project": {"name": "test-project", "id": 1},
        "object_attributes": {
            "description": "@reviewer-bot:oai",
            "action": "open",
            "iid": 123
        },
        "merge_request": None
    }

    with mock.patch("main.ChatClient.from_config", return_value=mock_chat_client):
        with mock.patch("auto_reviewer.utils.Gitlab", return_value=mock_gitlab):
            # Act
            response = client.post("/auto-reviewer", json=mock_event)
            print("debug")

    # Assert
    assert response.status_code == 200
