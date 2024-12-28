import json

import munch
import yaml
from gitlab import Gitlab
from pydantic import BaseModel


def open_json(filepath: str):
    with open(filepath) as f:
        requests = json.load(f)
    return requests


def load_yaml(path):
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


class MergeRequestConfig(BaseModel):
    project_name: str
    project_id: int
    merge_id: int


class ReviewerConfig:

    def __init__(self, llm_config, project_configs):
        self.llm_config = llm_config
        self.project_configs = project_configs

    @classmethod
    def from_config(cls, path):
        reviewer_cfg = load_yaml(path)
        return cls(
            llm_config=munch.munchify(reviewer_cfg['llm']),
            project_configs=munch.munchify(reviewer_cfg['projects']),
        )


class MergeRequest:

    def __init__(
        self,
        gl: Gitlab,
        project_id: int,
        merge_id: int,
    ):
        self.gl = gl
        self.project = self.gl.projects.get(project_id)
        self.mr = self.project.mergerequests.get(merge_id)

        self.title = self.mr.title
        self.description = self.mr.description

    @classmethod
    def from_config(cls, mr_config: MergeRequestConfig, config):
        project_configs = config.project_configs
        if mr_config.project_name not in project_configs:
            raise ValueError(
                f'project_name {mr_config.project_name} not found in the {project_configs}'
            )

        project_config = project_configs[mr_config.project_name]

        gl = Gitlab(
            url=project_config.url,
            private_token=project_config.private_token,
        )

        return cls(
            gl=gl,
            project_id=mr_config.project_id,
            merge_id=mr_config.merge_id,
        )

    def get_changes(self) -> list[dict]:
        changes = self.mr.changes()
        return changes['changes']

    def submit_comment(self, comment: str):
        self.mr.notes.create({'body': comment})

    def get_file_content(self, file_name: str) -> str:
        # https://python-gitlab.readthedocs.io/en/stable/gl_objects/projects.html#project-files
        return self.project.files.get(file_path=file_name,
                                      ref=self.mr.sha).decode().decode('utf-8')
