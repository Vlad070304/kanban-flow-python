import math
from models.base_task import TimedTask, RecurringTask

def main():
    t1 = TimedTask("Write Code", "Implement OOP models", 45)
    t2 = RecurringTask("Code Review", "Review PRs", "Daily")
    
    t1.set_status("In Progress")
    
    for task in [t1, t2]:
        print(task.get_summary())

if __name__ == "__main__":
    main()

