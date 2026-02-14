"""
File management utilities for JSON storage
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from app.config import settings


class FileManager:
    """Handles JSON file storage and retrieval"""

    @staticmethod
    def save_json(file_path: str, data: Dict[str, Any]) -> bool:
        """
        Save data to JSON file

        Args:
            file_path: Path to save file (relative to project root)
            data: Dictionary to save

        Returns:
            bool: True if successful
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving JSON to {file_path}: {e}")
            return False

    @staticmethod
    def load_json(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load data from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            Dictionary if successful, None otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {file_path}: {e}")
            return None

    @staticmethod
    def get_team_dir(team_id: str) -> Path:
        """Get team's results directory"""
        team_dir = settings.RESULTS_DIR / team_id
        team_dir.mkdir(parents=True, exist_ok=True)
        return team_dir

    @staticmethod
    def save_analysis(team_id: str, agent_name: str, data: Dict[str, Any]) -> str:
        """
        Save agent analysis for a team

        Args:
            team_id: Team identifier
            agent_name: Agent name (github, ppt, voice)
            data: Analysis data

        Returns:
            str: Path to saved file
        """
        # Add metadata
        data['agent'] = agent_name
        data['analyzed_at'] = datetime.utcnow().isoformat()

        # Save to team directory
        team_dir = FileManager.get_team_dir(team_id)
        file_path = team_dir / f"{agent_name}.json"

        FileManager.save_json(str(file_path), data)
        return str(file_path)

    @staticmethod
    def load_analysis(team_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Load agent analysis for a team

        Args:
            team_id: Team identifier
            agent_name: Agent name (github, ppt, voice)

        Returns:
            Analysis data if exists
        """
        team_dir = settings.RESULTS_DIR / team_id
        file_path = team_dir / f"{agent_name}.json"
        return FileManager.load_json(str(file_path))

    @staticmethod
    def get_all_analyses(team_id: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get all analyses for a team

        Args:
            team_id: Team identifier

        Returns:
            Dictionary with github, ppt, voice analyses
        """
        return {
            'github': FileManager.load_analysis(team_id, 'github'),
            'ppt': FileManager.load_analysis(team_id, 'ppt'),
            'voice': FileManager.load_analysis(team_id, 'voice')
        }

    @staticmethod
    def check_analyses_complete(team_id: str) -> tuple[bool, list[str]]:
        """
        Check which analyses are complete for a team

        Args:
            team_id: Team identifier

        Returns:
            (all_complete, list_of_available_analyses)
        """
        analyses = FileManager.get_all_analyses(team_id)
        available = [name for name, data in analyses.items() if data is not None]
        all_complete = len(available) == 3
        return all_complete, available


# Convenience functions
def save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """Save JSON file"""
    return FileManager.save_json(file_path, data)


def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file"""
    return FileManager.load_json(file_path)


def save_analysis(team_id: str, agent_name: str, data: Dict[str, Any]) -> str:
    """Save agent analysis"""
    return FileManager.save_analysis(team_id, agent_name, data)


def load_analysis(team_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
    """Load agent analysis"""
    return FileManager.load_analysis(team_id, agent_name)


def get_all_analyses(team_id: str) -> Dict[str, Optional[Dict[str, Any]]]:
    """Get all analyses for team"""
    return FileManager.get_all_analyses(team_id)


def check_analyses_complete(team_id: str) -> tuple[bool, list[str]]:
    """Check if all analyses complete"""
    return FileManager.check_analyses_complete(team_id)
