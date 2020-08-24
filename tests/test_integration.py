import glob
import os
import requests
import subprocess
import time
import pytest


@pytest.fixture(scope="module")
def set_env():
    with open(".env", "r") as f:
        for k, v in [line.strip().split("=", 1) for line in f.readlines()]:
            os.environ[k] = v


@pytest.fixture(scope="function")
def clean_up():
    """Removes files and state left over from previous runs
    """
    required_directories = [
        "OPENSAFELY_HIGH_PRIVACY_STORAGE_BASE",
        "OPENSAFELY_MEDIUM_PRIVACY_STORAGE_BASE",
    ]
    with open(".env", "r") as f:
        for k, v in [line.strip().split("=", 1) for line in f.readlines()]:
            if k in required_directories:
                for f in glob.glob(os.path.join(v, "*/*")):
                    print(f"deleting {f}")
                    # We use docker to remove files to work around
                    # permissions issues (files created in the docker
                    # container will be owned by root)
                    subprocess.check_call(
                        [
                            "docker-compose",
                            "run",
                            "--rm",
                            "--entrypoint=",  # unset it
                            "job-runner",
                            "rm",
                            "-rf",
                            f,
                        ]
                    )
    response = requests.get("http://localhost:8000/jobs/", json={"page_size": 100})
    response.raise_for_status()
    for job in response.json()["results"]:
        response = requests.delete(
            job["url"],
            auth=(
                os.environ["OPENSAFELY_QUEUE_USER"],
                os.environ["OPENSAFELY_QUEUE_PASS"],
            ),
        )
        response.raise_for_status()


@pytest.fixture(scope="module")
def make_workspace():
    kw = {
        "name": "my workspace",
        "branch": "master",
        "owner": "me",
        "db": "dummy",
        "repo": "https://github.com/opensafely/job-integration-tests",
    }

    response = requests.post(
        "http://localhost:8000/workspaces/",
        json=kw,
        auth=(os.environ["OPENSAFELY_QUEUE_USER"], os.environ["OPENSAFELY_QUEUE_PASS"]),
    )
    response.raise_for_status()
    return response.json()["id"]


def push_job(operation=None, status=None, workspace_id=None):
    completed_at = started_at = None
    started = False
    if status is not None:
        completed_at = "2020-07-30T12:52:09.670448+00:00"
        started_at = "2020-07-30T12:52:09.670448+00:00"
        started = True
    response = requests.post(
        "http://localhost:8000/jobs/",
        json={
            "backend": "expectations",
            "db": "dummy",
            "workspace_id": workspace_id,
            "status_code": status,
            "operation": operation,
            "started": started,
            "completed_at": completed_at,
            "started_at": started_at,
        },
        auth=(os.environ["OPENSAFELY_QUEUE_USER"], os.environ["OPENSAFELY_QUEUE_PASS"]),
    )
    try:
        response.raise_for_status()
    except Exception as error:
        print(error.response.text)
        raise
    url = response.json()["url"]
    return url


def test_job_with_dependencies(clean_up, set_env, make_workspace):
    url = push_job(operation="do_thing", workspace_id=make_workspace)
    elapsed_seconds = 0
    while True:
        if elapsed_seconds > 40:
            raise RuntimeError("Test timed out")
        response = requests.get(url).json()
        if response["status_code"] == 0:
            with open(response["outputs"][0]["location"], "r") as f:
                output = f.read()
                assert "(16 vars, 1,000 obs)" in output
                break
        time.sleep(1)
        elapsed_seconds += 1


def test_job_with_failed_dependencies(clean_up, set_env, make_workspace):
    url = push_job(operation="generate_cohort", status=1, workspace_id=make_workspace)
    url = push_job(operation="do_thing", workspace_id=make_workspace)
    elapsed_seconds = 0
    while True:
        if elapsed_seconds > 30:
            raise RuntimeError("Test timed out")
        response = requests.get(url).json()
        status_code = response["status_code"]
        if status_code is not None:
            assert status_code != 0, response
            break
        time.sleep(1)
        elapsed_seconds += 1
