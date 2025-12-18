import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import time  # For simulating progress

class Student:
    def __init__(self, id, name, age, grade):
        self.id = id
        self.name = name
        self.age = age
        self.grade = grade

    def to_dict(self):
        return {"id": self.id, "name": self.name, "age": self.age, "grade": self.grade}

class StudentManagementSystem:
    def __init__(self, filename="students.json"):
        self.filename = filename
        self.students = []
        self.load_students()

    def load_students(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.students = [Student(**s) for s in data]
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Corrupted data file. Starting fresh.")
                self.students = []

    def save_students(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump([s.to_dict() for s in self.students], f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")

    def add_student(self, id, name, age, grade):
        if not id or not name or not grade:
            messagebox.showerror("Error", "ID, Name, and Grade are required!")
            return False
        if any(s.id == id for s in self.students):
            messagebox.showerror("Error", "Student ID already exists!")
            return False
        try:
            age = int(age)
            if age <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Age must be a positive integer!")
            return False
        self.students.append(Student(id, name, age, grade))
        self.save_students()
        return True

    def view_students(self, sort_by=None):
        if sort_by:
            if sort_by == "id":
                self.students.sort(key=lambda s: s.id)
            elif sort_by == "name":
                self.students.sort(key=lambda s: s.name.lower())
            elif sort_by == "age":
                self.students.sort(key=lambda s: s.age)
            elif sort_by == "grade":
                self.students.sort(key=lambda s: s.grade.lower())
        return self.students

    def search_students(self, query):
        query = query.lower()
        return [s for s in self.students if query in s.id.lower() or query in s.name.lower()]

    def update_student(self, id, name=None, age=None, grade=None):
        for s in self.students:
            if s.id == id:
                if name: s.name = name
                if age:
                    try:
                        age = int(age)
                        if age <= 0: raise ValueError
                        s.age = age
                    except ValueError:
                        messagebox.showerror("Error", "Age must be a positive integer!")
                        return False
                if grade: s.grade = grade
                self.save_students()
                return True
        messagebox.showerror("Error", "Student not found!")
        return False

    def delete_student(self, id):
        for s in self.students:
            if s.id == id:
                self.students.remove(s)
                self.save_students()
                return True
        messagebox.showerror("Error", "Student not found!")
        return False

    def clear_all_students(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all students?"):
            self.students = []
            self.save_students()
            return True
        return False

    def export_to_csv(self, progress_callback):
        if not self.students:
            messagebox.showerror("Error", "No students to export!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Name", "Age", "Grade"])
                    for i, s in enumerate(self.students):
                        writer.writerow([s.id, s.name, s.age, s.grade])
                        progress_callback((i + 1) / len(self.students) * 100)
                        time.sleep(0.01)  # Simulate delay for progress demo
                messagebox.showinfo("Success", "Data exported to CSV!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

class StudentManagementGUI:
    def __init__(self, root):
        self.sms = StudentManagementSystem()
        self.root = root
        self.root.title("Interactive Student Management System")
        self.root.geometry("900x600")
        self.root.configure(bg="#2e2e2e")  # Dark background

        # Custom ttk styles for dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff", font=("Arial", 10))
        style.configure("TButton", background="#4a90e2", foreground="#ffffff", font=("Arial", 10, "bold"), padding=5, relief="flat")
        style.map("TButton", background=[("active", "#357abd")])  # Hover effect
        style.configure("TEntry", fieldbackground="#404040", foreground="#ffffff", insertcolor="#ffffff", font=("Arial", 10))
        style.configure("TCombobox", fieldbackground="#404040", foreground="#ffffff", font=("Arial", 10))
        style.configure("TProgressbar", background="#4a90e2", troughcolor="#404040")

        # Tooltips
        self.tooltips = {}

        # Main layout: Left for list/search, Right for sidebar inputs
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        # Left frame: List and controls
        left_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Search and sort
        top_frame = ttk.Frame(left_frame)
        top_frame.pack(fill="x", pady=5)
        ttk.Label(top_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.live_search)
        self.create_tooltip(self.search_entry, "Type to search by ID or Name in real-time")

        ttk.Label(top_frame, text="Sort by:").grid(row=0, column=2, padx=5)
        self.sort_var = tk.StringVar(value="id")
        sort_combo = ttk.Combobox(top_frame, textvariable=self.sort_var, values=["id", "name", "age", "grade"], state="readonly")
        sort_combo.grid(row=0, column=3, padx=5)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_list())

        # Listbox with dark styling
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(list_frame, width=60, height=15, font=("Arial", 10), selectmode=tk.SINGLE, bg="#404040", fg="#ffffff", selectbackground="#4a90e2")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select_student)

        # Buttons below list
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)
        self.delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self.delete_student, state="disabled")
        self.delete_btn.grid(row=0, column=0, padx=5)
        self.create_tooltip(self.delete_btn, "Delete the selected student (Ctrl+D)")
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_csv).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Exit", command=root.quit).grid(row=0, column=3, padx=5)

        # Right frame: Sidebar for inputs
        right_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        ttk.Label(right_frame, text="Student Details", font=("Arial", 12, "bold")).pack(pady=10)

        # Input fields
        ttk.Label(right_frame, text="ID:").pack(anchor="w", padx=10)
        self.id_var = tk.StringVar()
        self.id_entry = ttk.Entry(right_frame, textvariable=self.id_var)
        self.id_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(right_frame, text="Name:").pack(anchor="w", padx=10)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(right_frame, textvariable=self.name_var)
        self.name_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(right_frame, text="Age:").pack(anchor="w", padx=10)
        self.age_var = tk.StringVar()
        self.age_entry = ttk.Entry(right_frame, textvariable=self.age_var)
        self.age_entry.pack(fill="x", padx=10, pady=5)

        ttk.Label(right_frame, text="Grade:").pack(anchor="w", padx=10)
        self.grade_var = tk.StringVar()
        self.grade_entry = ttk.Entry(right_frame, textvariable=self.grade_var)
        self.grade_entry.pack(fill="x", padx=10, pady=5)

        # Action buttons
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Add Student", command=self.add_student).grid(row=0, column=0, padx=5)
        self.update_btn = ttk.Button(action_frame, text="Update Selected", command=self.update_student, state="disabled")
        self.update_btn.grid(row=0, column=1, padx=5)

        # Progress bar and status
        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)
        self.status_var = tk.StringVar(value="Ready - Start typing in the ID field!")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w", background="#404040", foreground="#ffffff")
        status_bar.pack(fill="x", side="bottom")

        # Keyboard shortcuts
        root.bind("<Control-d>", lambda e: self.delete_student())

        self.refresh_list()
        self.id_entry.focus()  # Auto-focus on ID field

    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            self.tooltips[widget] = tooltip
            widget.bind("<Leave>", lambda e: tooltip.destroy())

        widget.bind("<Enter>", show_tooltip)

    def live_search(self, event):
        query = self.search_var.get()
        if query:
            results = self.sms.search_students(query)
        else:
            results = self.sms.view_students()
        self.update_listbox(results)

    def refresh_list(self):
        students = self.sms.view_students(self.sort_var.get())
        self.update_listbox(students)
        self.update_buttons()

    def update_listbox(self, students):
        self.listbox.delete(0, tk.END)
        for s in students:
            color = "#00ff00" if s.grade.upper() in ["A", "B"] else "#ff4444"  # Brighter colors for dark theme
            self.listbox.insert(tk.END, f"ID: {s.id} | Name: {s.name} | Age: {s.age} | Grade: {s.grade}")
            self.listbox.itemconfig(tk.END, {'fg': color})

    def update_buttons(self):
        selected = self.listbox.curselection()
        state = "normal" if selected else "disabled"
        self.delete_btn.config(state=state)
        self.update_btn.config(state=state)

    def on_select_student(self, event):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            student_text = self.listbox.get(index)
            parts = student_text.split(" | ")
            self.id_var.set(parts[0].split(": ")[1])
            self.name_var.set(parts[1].split(": ")[1])
            self.age_var.set(parts[2].split(": ")[1])
            self.grade_var.set(parts[3].split(": ")[1])
            self.update_buttons()

    def add_student(self):
        id = self.id_var.get()
        name = self.name_var.get()
        age = self.age_var.get()
        grade = self.grade_var.get()
        if self.sms.add_student(id, name, age, grade):
            self.refresh_list()
            self.clear_fields()
            self.status_var.set("Student added successfully!")
            self.id_entry.focus()

    def update_student(self):
        selected = self.listbox.curselection()
        if not selected: return
        id = self.id_var.get()
        name = self.name_var.get()
        age = self.age_var.get()
        grade = self.grade_var.get()
        if messagebox.askyesno("Confirm", "Update this student?"):
            if self.sms.update_student(id, name, age, grade):
                self.refresh_list()
                self.clear_fields()
                self.status_var.set("Student updated!")
                self.id_entry.focus()

    def delete_student(self):
        selected = self.listbox.curselection()
        if not selected: return
        index = selected[0]
        student_text = self.listbox.get(index)
        id = student_text.split(" | ")[0].split(": ")[1]
        if messagebox.askyesno("Confirm", "Delete this student?"):
            if self.sms.delete_student(id):
                self.refresh_list()
                self.clear_fields()
                self.status_var.set("Student deleted!")

    def clear_fields(self):
        self.id_var.set("")
        self.name_var.set("")
        self.age_var.set("")
        self.grade_var.set("")

    def clear_all(self):
        if self.sms.clear_all_students():
            self.refresh_list()
            self.clear_fields()
            self.status_var.set("All students cleared!")

    def export_csv(self):
        def progress_callback(value):
            self.progress['value'] = value
            self.root.update_idletasks()
        self.progress['value'] = 0
        self.sms.export_to_csv(progress_callback)
        self.progress['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentManagementGUI(root)
    root.mainloop()
