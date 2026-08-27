import os
import shutil
import re
from pathlib import Path

# Paths
SRC_DIR = Path(r"C:\Users\DELL\work\rfq\backend\app")
DEST_DIR = Path(r"C:\Users\DELL\work\bigzbyagent\voicelatex-agents\apps\procurement-service\src")

# 1. Clean Slate: Delete specific folders
folders_to_delete = ["agents", "core", "db", "models", "modules", "routers", "services", "schemas"]
for folder in folders_to_delete:
    target_path = DEST_DIR / folder
    if target_path.exists() and target_path.is_dir():
        shutil.rmtree(target_path)
        print(f"Deleted {target_path}")

# 2. Copy Code
mapping = {
    "api/v1": "routers",
    "agents": "agents",
    "core": "core",
    "db": "db",
    "models": "models",
    "schemas": "schemas",
    "services": "services",
}

for src_folder, dest_folder in mapping.items():
    src_path = SRC_DIR / src_folder
    dest_path = DEST_DIR / dest_folder
    if src_path.exists():
        shutil.copytree(src_path, dest_path)
        print(f"Copied {src_path} to {dest_path}")

# Copy dependencies.py
if (SRC_DIR / "dependencies.py").exists():
    shutil.copy2(SRC_DIR / "dependencies.py", DEST_DIR / "dependencies.py")
    print(f"Copied dependencies.py")

# 3. Import Refactoring
def refactor_imports(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace absolute imports
                # from app. -> from src.
                # import app. -> import src.
                new_content = re.sub(r'from\s+app\.', 'from src.', content)
                new_content = re.sub(r'import\s+app\.', 'import src.', new_content)
                
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Refactored imports in {filepath}")

refactor_imports(DEST_DIR)

print("Migration script completed.")
