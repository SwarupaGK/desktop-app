import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MarathiSchoolApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("एकलव्य गुरुकुल - विद्यार्थी व्यवस्थापन")
        self.root.geometry("1400x900")
        self.collapsed = False
        self.create_navigation()
        self.show_login()
    
    def create_navigation(self):
        # Main container
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        # SIDEBAR (Fixed colors)
        self.sidebar = ctk.CTkFrame(self.main_container, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        
        # Header
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="#1f538d")
        header_frame.pack(fill="x", pady=(20,10), padx=20)
        ctk.CTkLabel(header_frame, text="🏫 एकलव्य", font=ctk.CTkFont(size=24, weight="bold"), 
                    text_color="white").pack(pady=10)
        
        # Navigation buttons
        nav_items = [
            ("🏠", "मुख्य पटल", self.show_main),
            ("➕", "विद्यार्थी जोडा", self.show_add),
            ("📋", "विद्यार्थी पहा", self.show_view),
            ("💾", "बॅकअप", self.show_backup)
        ]
        
        self.nav_buttons = {}
        for icon, text, command in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, 
                text=f"{icon} {text}", 
                font=ctk.CTkFont(size=16), 
                height=50,
                command=command,
                fg_color="transparent",
                hover_color="#2b5aa5",
                anchor="w"
            )
            btn.pack(fill="x", padx=20, pady=8)
            self.nav_buttons[text] = btn
        
        # COLLAPSE BUTTON (Fixed)
        self.toggle_btn = ctk.CTkButton(
            self.sidebar, 
            text="◀", 
            width=40, 
            height=40,
            fg_color="#1f538d",
            hover_color="#2b5aa5",
            text_color="white",
            command=self.toggle_sidebar,
            font=ctk.CTkFont(size=18)
        )
        self.toggle_btn.pack(side="bottom", pady=20, padx=20)
        
        # Content area
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nswe")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
    
    def toggle_sidebar(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.sidebar.configure(width=70)
            self.toggle_btn.configure(text="▶")
            for text, btn in self.nav_buttons.items():
                btn.configure(text=text.split()[0])  # Show only icon
        else:
            self.sidebar.configure(width=280)
            self.toggle_btn.configure(text="◀")
            for text_full, btn in self.nav_buttons.items():
                btn.configure(text=text_full)
    
    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def show_login(self):
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        
        title = ctk.CTkLabel(frame, text="🔐 प्रवेश", font=ctk.CTkFont(size=36, weight="bold"))
        title.pack(pady=80)
        
        login_frame = ctk.CTkFrame(frame, width=400, height=300)
        login_frame.pack(pady=20)
        
        ctk.CTkLabel(login_frame, text="नाव:", font=ctk.CTkFont(size=20)).pack(pady=(40,10))
        self.uname = ctk.CTkEntry(login_frame, width=350, height=50, font=ctk.CTkFont(size=16))
        self.uname.pack(pady=5)
        self.uname.insert(0, "admin")
        
        ctk.CTkLabel(login_frame, text="परवलीचा शब्द:", font=ctk.CTkFont(size=20)).pack(pady=(30,10))
        self.passw = ctk.CTkEntry(login_frame, width=350, height=50, show="*", font=ctk.CTkFont(size=16))
        self.passw.pack(pady=5)
        self.passw.insert(0, "admin123")
        
        login_btn = ctk.CTkButton(login_frame, text="प्रवेश करा", width=350, height=55,
                                 font=ctk.CTkFont(size=20, weight="bold"), fg_color="#1f538d",
                                 command=self.handle_login)
        login_btn.pack(pady=40)
        
        frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    def handle_login(self):
        if self.uname.get() == "admin" and self.passw.get() == "admin123":
            self.show_main()
        else:
            messagebox.showerror("चूक", "चुकीचे प्रमाणपत्र!")
    
    def show_main(self):
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        
        title = ctk.CTkLabel(frame, text="🏫 एकलव्य गुरुकुल शाळा", font=ctk.CTkFont(size=40, weight="bold"))
        title.pack(pady=80)
        
        subtitle = ctk.CTkLabel(frame, text="विद्यार्थी व्यवस्थापन प्रणाली v2.0\nस्वागत आहे!", 
                              font=ctk.CTkFont(size=24), text_color="gray")
        subtitle.pack(pady=20)
        
        frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    def show_add(self):
        self.clear_content()
        frame = ctk.CTkScrollableFrame(self.content_area)
        
        title = ctk.CTkLabel(frame, text="➕ नवीन विद्यार्थी जोडा", font=ctk.CTkFont(size=32, weight="bold"))
        title.pack(pady=30)
        
        # Form fields
        fields = [("पूर्ण नाव", "name"), ("आईचे नाव", "mother"), ("जात", "caste"), 
                 ("जन्मतारीख (YYYY-MM-DD)", "dob"), ("पत्ता", "address"), ("जन्मठिकाण", "birth_place"),
                 ("प्रवेश तारीख", "admission"), ("वर्ग/विभाग", "class"), ("सोड तारीख", "leave_date")]
        
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(frame, text=f"{label}:", font=ctk.CTkFont(size=16)).pack(anchor="w", padx=50, pady=(25,5))
            entry = ctk.CTkEntry(frame, width=700, height=45, font=ctk.CTkFont(size=16))
            entry.pack(fill="x", padx=50, pady=(0,20))
            self.entries[key] = entry
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=40)
        ctk.CTkButton(btn_frame, text="✅ जोडा", width=200, height=50, fg_color="#28a745",
                     font=ctk.CTkFont(size=18, weight="bold"), command=self.save_student).pack(side="left", padx=20)
        ctk.CTkButton(btn_frame, text="🏠 मुख्य", width=200, height=50, fg_color="#6c757d",
                     font=ctk.CTkFont(size=18), command=self.show_main).pack(side="left", padx=20)
        
        frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    def save_student(self):
        messagebox.showinfo("यश!", "विद्यार्थी यशस्वीरीत्या जोडला!")
    
    def show_view(self):
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        ctk.CTkLabel(frame, text="📋 विद्यार्थी यादी (लवकरच)", font=ctk.CTkFont(size=36)).pack(pady=200)
        frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    def show_backup(self):
        self.clear_content()
        frame = ctk.CTkFrame(self.content_area)
        ctk.CTkLabel(frame, text="💾 बॅकअप (लवकरच)", font=ctk.CTkFont(size=36)).pack(pady=200)
        frame.pack(fill="both", expand=True, padx=40, pady=40)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MarathiSchoolApp()
    app.run()
