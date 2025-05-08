import tkinter as tk

root = tk.Tk()
root.title("Testvenster")
root.geometry("200x100")
label = tk.Label(root, text="Dit is een testvenster.")
label.pack()
root.mainloop()