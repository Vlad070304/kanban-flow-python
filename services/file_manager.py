import json
import os

#File I/O, File Detection, Reading/Writing Files
class FileManager:
    @staticmethod
    def save_tasks_json(filepath: str, tasks_data: list):
        try:
            with open(filepath, 'w') as f:
                json.dump(tasks_data, f, indent=4)
            print(f"Data saved successfully to {filepath}")
        except IOError as e:
            print(f"Failed to write file: {e}")
        finally:
            print("File write operation concluded.")

    @staticmethod
    def load_tasks_json(filepath: str) -> list:
        if not os.path.exists(filepath):
            print("No previous save file found. Initializing empty dataset.")
            return []
            
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading file {filepath}: {e}")
            return []