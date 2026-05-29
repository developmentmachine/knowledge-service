#!/usr/bin/env python3
import os
import requests
import argparse
from pathlib import Path
from loguru import logger

API_URL = "http://localhost:8001/api/v1/ingest"
ALLOWED_EXTENSIONS = {'.md', '.txt', '.py', '.java', '.go', '.sh'}
IGNORE_DIRS = {'.git', 'node_modules', '.venv', 'venv', 'build', 'dist', '__pycache__', '.idea', 'target', 'docs_build'}

def ingest_file(project_id: str, file_path: Path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.warning(f"Skipping binary or non-utf8 file: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return False

    if not content.strip():
        return False

    payload = {
        "project_id": project_id,
        "file_path": str(file_path),
        "content": content,
        "metadata": {
            "extension": file_path.suffix
        }
    }

    response = None
    try:
        response = requests.post(API_URL, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        logger.info(f"✅ Ingested [{project_id}] {file_path.name} -> {data.get('chunks_ingested', 0)} chunks")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API Error for {file_path}: {e}")
        if response is not None:
             logger.error(f"Response: {response.text}")
        return False

def scan_and_ingest(workspace_dir: str, target_projects: list[str] = None):
    workspace_path = Path(workspace_dir).resolve()
    
    if not workspace_path.exists() or not workspace_path.is_dir():
        logger.error(f"Workspace directory not found: {workspace_path}")
        return

    logger.info(f"Scanning workspace: {workspace_path}")
    
    for project_dir in workspace_path.iterdir():
        if not project_dir.is_dir() or project_dir.name in IGNORE_DIRS:
            continue
            
        project_id = project_dir.name
        
        # Filter projects if specified
        if target_projects and project_id not in target_projects:
            continue

        logger.info(f"Processing project: {project_id}")
        
        for root, dirs, files in os.walk(project_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in ALLOWED_EXTENSIONS and not file.startswith('.'):
                    ingest_file(project_id, file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest workspace documents into Knowledge-Service")
    parser.add_argument("--workspace", type=str, required=True, help="Root workspace directory containing project subfolders")
    parser.add_argument("--projects", nargs="+", help="Specific projects to ingest (e.g. agent-platform AlphaGPT)")
    args = parser.parse_args()

    scan_and_ingest(args.workspace, args.projects)
