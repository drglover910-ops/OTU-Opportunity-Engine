"""Upload only public-safe application files; never upload storage or career records."""
import os
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd
SPACE = 'Dezz-9-10/OTU-Opportunity-Engine'
FILES = ('app.py', 'Dockerfile', 'README.md', 'VERSION', 'CHANGELOG.md')
def main():
    token = os.environ.get('HF_TOKEN')
    if not token:
        raise SystemExit('Add HF_TOKEN under GitHub repository Settings > Secrets and variables > Actions. Never put tokens in source code.')
    root = Path(__file__).resolve().parents[1]
    api = HfApi(token=token)
    try:
        api.whoami()
        info = api.space_info(SPACE)
        if not info.private:
            raise SystemExit('Make the Space private before deploying this personal opportunity app.')
        version = (root / 'VERSION').read_text().strip()
        result = api.create_commit(repo_id=SPACE, repo_type='space',
            operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=str(root / name)) for name in FILES],
            commit_message=f'Deploy OTU Opportunity Engine v{version}')
        print(f'Uploaded v{version} to {SPACE}. Commit: {result.oid}. Hugging Face build/runtime must be checked separately.')
    except SystemExit:
        raise
    except Exception as exc:
        # Do not log client request details or authentication values.
        raise SystemExit(f'Deployment failed ({type(exc).__name__}). Check token validity, Space permissions, privacy and Hugging Face build logs.') from None
if __name__ == '__main__':
    main()
