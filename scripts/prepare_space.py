"""Prepare a clean Hugging Face Docker SDK upload directory without credentials."""

from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    output = artifacts / "huggingface-space"
    if output.is_symlink() or output.resolve().parent != artifacts.resolve():
        raise ValueError("Upload output must stay inside the artifacts directory.")
    ignore = shutil.ignore_patterns(
        "node_modules", "static", "__pycache__", "*.tsbuildinfo", ".env", ".env.*", "*.log", ".pytest_cache"
    )
    with tempfile.TemporaryDirectory(prefix="space-", dir=artifacts) as staging:
        staged = Path(staging)
        for directory in ["backend", "frontend", "samples", "deploy"]:
            shutil.copytree(root / directory, staged / directory, ignore=ignore)
        for name in ["Dockerfile", "README.md"]:
            shutil.copyfile(root / "deploy/huggingface" / name, staged / name)
        shutil.copyfile(root / ".dockerignore", staged / ".dockerignore")
        attributes = root / ".gitattributes"
        if attributes.exists():
            shutil.copyfile(attributes, staged / attributes.name)
        for script in staged.rglob("*.sh"):
            script.write_bytes(script.read_bytes().replace(b"\r\n", b"\n"))
        notices = root / "THIRD_PARTY_NOTICES.md"
        if notices.exists():
            shutil.copyfile(notices, staged / notices.name)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(staged, output)
    return output


if __name__ == "__main__":
    print(prepare())
