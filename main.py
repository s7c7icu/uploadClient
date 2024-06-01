import crypt
from ghrepoaccess import GHRepoAccess, default_committer
import passphrases
import json
from os import path
import argparse


_log = print


class Config:
    auth_token: str
    meta_repo: str
    data_repo: str
    meta_url: str
    data_url: str
    download_url: str

    committer: str  # 默认值：default_committer()
    encrypt_algorithms: str # 默认值："deflate+aes+base64"
    # password_len: int   # 默认值 16
    meta_slug_len: int  # 默认值 6

    def __init__(self,
                 auth_token: str,
                 meta_repo: str, data_repo: str,
                 meta_url: str, data_url: str, download_url: str,
                 committer: str = default_committer(),
                 encrypt_algorithms: str = "deflate+aes+base64",
                 meta_slug_len: int = 6):
        self.auth_token = auth_token
        self.meta_repo = meta_repo
        self.data_repo = data_repo
        self.meta_url = meta_url
        self.data_url = data_url
        self.download_url = download_url
        self.committer = committer
        self.encrypt_algorithms = encrypt_algorithms
        # self.password_len = password_len
        self.meta_slug_len = meta_slug_len

    def to_dict(self) -> dict:
        # 将Config对象转换为字典
        return {
            "auth_token": self.auth_token,
            "meta_repo": self.meta_repo,
            "data_repo": self.data_repo,
            "meta_url": self.meta_url,
            "data_url": self.data_url,
            "download_url": self.download_url,
            "committer": self.committer,
            "encrypt_algorithms": self.encrypt_algorithms,
            # "password_len": self.password_len,
            "meta_slug_len": self.meta_slug_len
        }

    def from_dict(self, data: dict):
        # 从字典创建Config对象
        self.auth_token = data.get("auth_token", self.auth_token)
        self.meta_repo = data.get("meta_repo", self.meta_repo)
        self.data_repo = data.get("data_repo", self.data_repo)
        self.meta_url = data.get("meta_url", self.meta_url)
        self.data_url = data.get("data_url", self.data_url)
        self.download_url = data.get("download_url", self.download_url)
        self.committer = data.get("committer", self.committer)
        self.encrypt_algorithms = data.get("encrypt_algorithms", self.encrypt_algorithms)
        # self.password_len = data.get("password_len", self.password_len)
        self.meta_slug_len = data.get("meta_slug_len", self.meta_slug_len)

    def is_uninitialized(self):
        return not (
            self.auth_token and self.meta_repo and self.data_repo and
            self.meta_url and self.data_url and self.download_url
        )



default_config = lambda: Config(None, None, None, None, None, None)



def main0(filename: str, file_content: bytes,
         config: Config):
    password: str = crypt.urlsafe_base64_encode(passphrases.gen_cipher(24 + 32)).decode('ascii')
    encrypted_content: bytes = crypt.encrypt_file(file_content, password, config.encrypt_algorithms)   # 原始数据大小

    size = len(file_content)
    meta = {
        'schema': 1,
        'alg': config.encrypt_algorithms,
        'size': size,
        'filename': crypt.base64_encode_str(filename),
        'hash': {                   # 原始数据哈希
            'sha256': crypt.sha256_hash(file_content),
            'sha512': crypt.sha512_hash(file_content)
        }
    }
    _log('Generated meta')

    if size <= 4096:
        meta['data'] = {'raw': encrypted_content.decode('ascii')} if encrypted_content.isascii() else {'base64': crypt.base64_encode(encrypted_content).decode('ascii')}
    else:
        data_slug = crypt.sha512_hash(encrypted_content)
        uri = data_slug[:2] + "/" + data_slug[2:10] + "/" + data_slug[10:] + ".bin"

        data_repo_access = GHRepoAccess(config.auth_token, config.committer, config.data_repo)
        if data_repo_access.check_existence(uri):
            _log(f'File {uri} in repo {config.data_repo} exists')
        else:
            _log(f'Putting {uri} onto repo {config.data_repo}')
            data_repo_access.create_file(uri, encrypted_content)
        meta['data'] = {'fetch': f'{config.data_url}/{uri}'}

    # Gen meta and its slug
    meta_repo_access = GHRepoAccess(config.auth_token, config.committer, config.meta_repo)
    meta_dump = json.dumps(meta)

    while True:
        meta_slug = passphrases.gen_meta_slug(config.meta_slug_len)
        uri = f'{meta_slug[0]}/{meta_slug}.json'
        if meta_repo_access.check_existence(uri):
            continue
        break
    response = meta_repo_access.create_file(uri, meta_dump.encode('utf8'))
    if not response:
        _log(f'Successfully created {config.meta_url}/{uri}. The file will be available in a few minutes.')
        _log(f'Visit this address to download: {config.download_url}/{meta_slug}#{password}')
        _log(f'Do not leak the link to strangers!')
    else:
        _log('Error while uploading meta:', json.dumps(response))


def main(path_to_file: str, path_to_config: str, filename: str):
    config = default_config()
    try:
        with open(path_to_config) as f:
            config.from_dict(json.load(f))
    except FileNotFoundError:
        pass
    if config.is_uninitialized():
        _log(f'Config file {path_to_config} is uninitialized')
        with open(path_to_config, 'w') as f:
            json.dump(config.to_dict(), f, indent=4)
        _log('Please complete the config')
        return
    with open(path_to_file, 'rb') as f:
        content = f.read()
    main0(filename, content, config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="s7c7icu uploadClient")
    parser.add_argument('path_to_file', type=str, help="路径必须提供。")
    parser.add_argument('-c', '--config', type=str, help="配置文件路径，默认为 './config'")
    parser.add_argument('-n', '--filename', type=str, help="文件名重写，默认为与路径最后一个 '/' 后的子串一致。")
    args = parser.parse_args()

    main(args.path_to_file, args.config or './config.json', args.filename or args.path_to_file[args.path_to_file.rfind('/') + 1:])
