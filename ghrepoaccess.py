import requests
from crypt import base64_encode


def committer(name: str, email: str):
    return {"name": name, "email": email}


default_committer = lambda: committer('github-actions[bot]', 'github-actions[bot]@users.noreply.github.com')


class GHRepoAccess:
    auth_token: str
    committer: dict
    repo: str

    def __init__(self, auth_token: str, committer: dict, repo: str):
        self.auth_token = auth_token
        self.committer = committer
        #self.owner = owner
        self.repo = repo

    def check_existence(self, path: str) -> bool:
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        headers = {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.head(url, headers=headers)
        return response.status_code == 200

    def create_file(self, path: str, file_content: bytes) -> None | dict:
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        headers = {
            "Authorization": f"token {self.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 对文件内容进行base64编码
        encoded_content = base64_encode(file_content).decode('ascii')

        # 构造请求体
        payload = {
            "message": f"Create file {path}",
            "content": encoded_content
        }

        # 发送请求
        response = requests.put(url, json=payload, headers=headers)

        # 检查响应状态码
        if response.status_code == 201:
            return None  # 文件创建成功
        else:
            # 文件创建失败，返回错误信息
            return response.json()

