import tkinter as tk
from tkinter import ttk

class RaceMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Race Menu")
        
        # Auto-instellingen
        self.auto_frame = tk.LabelFrame(root, text="Auto-instellingen")
        self.auto_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.auto_data = {
            "oranje": tk.StringVar(),
            "rood": tk.StringVar(),
            "groen": tk.StringVar(),
            "blauw": tk.StringVar(),
        }
        
        for i, (color, var) in enumerate(self.auto_data.items()):
            tk.Label(self.auto_frame, text=f"Auto {color.capitalize()}").grid(row=i, column=0, padx=5, pady=5)
            tk.Entry(self.auto_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=5)
        
        # Race-besturing
        self.control_frame = tk.LabelFrame(root, text="Race-besturing")
        self.control_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.start_button = tk.Button(self.control_frame, text="Start Race", command=self.start_race)
        self.start_button.pack(side="left", padx=5, pady=5)
        
        self.reset_button = tk.Button(self.control_frame, text="Reset Race", command=self.reset_race)
        self.reset_button.pack(side="left", padx=5, pady=5)
        
        # Eindklassement
        self.results_frame = tk.LabelFrame(root, text="Eindklassement")
        self.results_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.fastest_ever_label = tk.Label(self.results_frame, text="Snelste Tijd Ooit: 00:00.000")
        self.fastest_ever_label.pack(padx=5, pady=5)
        
        self.fastest_month_label = tk.Label(self.results_frame, text="Snelste Tijd van de Maand: 00:00.000")
        self.fastest_month_label.pack(padx=5, pady=5)
        
        self.edit_times_button = tk.Button(self.results_frame, text="Pas Snelste Tijden Aan", command=self.edit_times)
        self.edit_times_button.pack(padx=5, pady=5)
    
    def start_race(self):
        participating_cars = []
        for color, username in self.auto_data.items():
            if username.get().strip():  # Check if a username is provided
                participating_cars.append({"color": color, "username": username.get()})
        
        if participating_cars:
            print("Deelnemende auto's:", participating_cars)
            print("Race gestart!")
        else:
            print("Geen auto's geselecteerd. Vul gebruikersnamen in om te starten.")
    
    def reset_race(self):
        # Hier komt de logica om de race te resetten
        print("Race gereset!")
    
    def edit_times(self):
        # Hier komt de logica om snelste tijden handmatig aan te passen
        print("Snelste tijden aanpassen...")
        
# Main applicatie
if __name__ == "__main__":
    root = tk.Tk()
    app = RaceMenu(root)
    root.mainloop()