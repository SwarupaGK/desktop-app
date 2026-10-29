import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SchoolApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.geometry("1200x700")
        self.app.title("🏫 StudentHub - School Management")

        self.students = []

        self.show_login()

    def show_login(self):
        self.clear_screen()

        frame = ctk.CTkFrame(self.app)
        frame.pack(expand=True, fill="both", padx=50, pady=50)

        ctk.CTkLabel(frame, text="🔐 Login",
                     font=ctk.CTkFont(size=30, weight="bold")).pack(pady=30)

        self.username_entry = ctk.CTkEntry(frame)
        self.username_entry.pack(pady=10)
        self.username_entry.insert(0, "admin")

        self.password_entry = ctk.CTkEntry(frame, show="*")
        self.password_entry.pack(pady=10)
        self.password_entry.insert(0, "admin")

        ctk.CTkButton(frame, text="Login", command=self.handle_login).pack(pady=20)

    def handle_login(self):
        if self.username_entry.get() == "admin" and self.password_entry.get() == "admin":
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid Login")

    def show_dashboard(self):
        self.clear_screen()

        self.sidebar = ctk.CTkFrame(self.app, width=250)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="🏫 StudentHub",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20)

        buttons = [
            ("➕ Add Student", self.show_add_student),
            ("📋 View Students", self.show_view_students),
            ("🔐 Logout", self.show_login)
        ]

        for text, cmd in buttons:
            ctk.CTkButton(
                self.sidebar,
                text=text,
                command=cmd,
                height=45,
                fg_color="#2b5aa5",
                hover_color="#1f538d",
                text_color="white",
                anchor="w"
            ).pack(fill="x", padx=10, pady=5)

        self.main = ctk.CTkFrame(self.app)
        self.main.pack(side="right", fill="both", expand=True)

    def clear_screen(self):
        for w in self.app.winfo_children():
            w.destroy()

    def clear_main(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ------------------ ADD STUDENT (bilingual ready) ------------------
    def show_add_student(self):
        self.clear_main()

        frame = ctk.CTkScrollableFrame(self.main)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="➕ विद्यार्थी जोडा / Add Student",
                     font=ctk.CTkFont(size=25, weight="bold")).pack(pady=20)

        # Full list of fields (English labels, but Marathi can be typed inside)
        self.entries = {}
        fields = [
            "Name / नाव",
            "Roll No / रोल नंबर",
            "URN",
            "Mothers Name / आईचे नाव",
            "Fathers Name / वडिलांचे नाव",
            "Class / वर्ग",
            "Division / विभाग",
            "Cast",
            "Aadhar No",
            "Birth Date (DD/MM/YYYY)",
            "Birth Place",
            "Date of Leaving LC (DD/MM/YYYY)"
        ]

        for field in fields:
            ctk.CTkLabel(frame, text=field).pack(anchor="w", padx=20)
            entry = ctk.CTkEntry(frame, width=400)
            entry.pack(padx=20, pady=5)
            self.entries[field] = entry

        ctk.CTkButton(frame, text="💾 Save",
                      command=self.save_student,
                      fg_color="#27ae60").pack(pady=20)

    def save_student(self):
        # Extract all fields into a dict
        data = {k: v.get() for k, v in self.entries.items()}

        required = ["Name / नाव"]
        for k in required:
            if data[k].strip() == "":
                messagebox.showerror("Error", f"{k} required")
                return

        self.students.append(data)
        messagebox.showinfo("Success", "Student Saved")

        # Clear all entry fields after save
        for e in self.entries.values():
            e.delete(0, "end")

    # ------------------ VIEW STUDENTS (with LC/Bonafide) ------------------
    def show_view_students(self):
        self.clear_main()

        frame = ctk.CTkFrame(self.main)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        cols = ("Name", "Roll", "URN", "Parents", "Class", "Division")

        self.tree = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)

        self.tree.pack(fill="both", expand=True)

        # Insert all students into the table
        for student in self.students:
            name = student["Name / नाव"]
            roll = student["Roll No / रोल नंबर"]
            urn = student["URN"]
            parents = f"{student['Mothers Name / आईचे नाव']} & {student['Fathers Name / वडिलांचे नाव']}"
            cls = student["Class / वर्ग"]
            div = student["Division / विभाग"]

            self.tree.insert("", "end", values=(name, roll, urn, parents, cls, div))

        # Buttons
        btn_frame = ctk.CTkFrame(self.main)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_frame, text="📄 Generate Certificate",
                      command=self.ask_certificate_type,
                      fg_color="#e67e22").pack(side="left", padx=10)

    # Popup: ask LC or Bonafide
    def ask_certificate_type(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showerror("Error", "प्रथम एक विद्यार्थी निवडा / Select a student first")
            return

        data = self.tree.item(selected, "values")
        student_index = self.tree.index(selected)
        student = self.students[student_index]

        # New Toplevel window to choose certificate type
        choice_win = ctk.CTkToplevel(self.app)
        choice_win.title("Certificate Type")
        choice_win.geometry("300x150")
        choice_win.resizable(False, False)

        ctk.CTkLabel(choice_win, text="Choose Certificate Type",
                     font=ctk.CTkFont(size=16)).pack(pady=20)

        btn_frame = ctk.CTkFrame(choice_win)
        btn_frame.pack(fill="x", padx=20)

        ctk.CTkButton(btn_frame, text="LC Certificate",
                      command=lambda: (choice_win.destroy(), self.generate_lc_certificate(student)),
                      fg_color="#2980b9").pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="Bonafide Certificate",
                      command=lambda: (choice_win.destroy(), self.generate_bonafide_certificate(student)),
                      fg_color="#27ae60").pack(side="left", padx=10)

    # ------------------ LC CERTIFICATE ------------------
    def generate_lc_certificate(self, student):
        name = student["Name / नाव"]
        roll = student["Roll No / रोल नंबर"]
        urn = student["URN"]
        cls = student["Class / वर्ग"]
        div = student["Division / विभाग"]
        aadhar = student["Aadhar No"]
        birth_date = student["Birth Date (DD/MM/YYYY)"]
        birth_place = student["Birth Place"]
        leaving_date = student["Date of Leaving LC (DD/MM/YYYY)"]

        cert_window = ctk.CTkToplevel(self.app)
        cert_window.title("LC Certificate")
        cert_window.geometry("650x450")

        text = f"""
        📜 LEAVING CERTIFICATE (LC)

        This is to certify that

        Name: {name}
        Roll No: {roll}
        URN: {urn}
        Aadhar No: {aadhar}
        Date of Birth: {birth_date}
        Birth Place: {birth_place}
        Class: {cls}-{div}

        has left this school on {leaving_date}.

        Date: __________

        Signature
        (Principal)
        """

        ctk.CTkLabel(cert_window, text=text,
                     font=ctk.CTkFont(size=14), justify="left").pack(padx=20, pady=20)

    # ------------------ BONAFIDE CERTIFICATE ------------------
    def generate_bonafide_certificate(self, student):
        name = student["Name / नाव"]
        roll = student["Roll No / रोल नंबर"]
        urn = student["URN"]
        cls = student["Class / वर्ग"]
        div = student["Division / विभाग"]

        cert_window = ctk.CTkToplevel(self.app)
        cert_window.title("Bonafide Certificate")
        cert_window.geometry("600x400")

        text = f"""
        📜 BONAFIDE CERTIFICATE

        This is to certify that

        Name: {name}
        Roll No: {roll}
        URN: {urn}

        is a bonafide student of Class {cls}-{div}
        in our school.

        Date: __________

        Signature
        (Principal)
        """

        ctk.CTkLabel(cert_window, text=text,
                     font=ctk.CTkFont(size=14), justify="left").pack(padx=20, pady=20)

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    app = SchoolApp()
    app.run()
