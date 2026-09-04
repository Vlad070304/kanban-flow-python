from functools import reduce

class AnalyticsEngine:
    @staticmethod
    def filter_by_status(tasks: list, status: str) -> list:
        return list(filter(lambda t: t.get("status") == status, tasks))

    @staticmethod
    def get_task_titles(tasks: list) -> list:
        return list(map(lambda t: t.get("title", "").upper(), tasks))

    @staticmethod
    def calculate_total_points(tasks: list) -> int:
        if not tasks:
            return 0
        return reduce(lambda acc, t: acc + t.get("points", 0), tasks, 0)

    @staticmethod
    def generate_status_counts(tasks: list) -> dict:
        statuses = ["To Do", "In Progress", "Done"]
        # Dictionary Comprehension
        return {s: len([t for t in tasks if t.get("status") == s]) for s in statuses}

    @staticmethod
    def process_tags_interactive():
        tags = []
        # Walrus Operator
        while (tag := input("Enter tag (or press Enter to finish): ").strip()):
            tags.append(tag)
        return tags