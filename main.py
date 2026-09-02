import math

def main():
    print("=== Kanban Task Manager CLI ===")
    
    # Structural Tuples & Sets
    COLUMNS = ("To Do", "In Progress", "Done")
    tags = {"python", "cli"}
    
    # Task Storage (List of Dictionaries)
    tasks = []
    
    running = True
    while running:
        print("\n1. Add Task\n2. View Tasks\n3. Exit")
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            title = input("Enter task title: ").strip()
            # Type Casting & String Slicing
            short_title = title[:20] if len(title) > 20 else title
            est_hours = float(input("Estimated hours: ") or 1.0)
            
            # Math module
            points = math.ceil(est_hours * 2)
            
            task = {
                "id": len(tasks) + 1,
                "title": short_title,
                "status": COLUMNS[0],
                "points": points
            }
            tasks.append(task)
            print(f"Task '{short_title}' added with priority weight {points}.")
            
        elif choice == "2":
            print("\n--- Current Tasks ---")
            for t in tasks:
                print(f"[{t['id']}] {t['title']} | Status: {t['status']} | Points: {t['points']}")
                
        elif choice == "3":
            running = False
            
if __name__ == "__main__":
    main()