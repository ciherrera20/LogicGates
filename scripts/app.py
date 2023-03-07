import tkinter as tk
import tkinter.ttk as ttk
from gates.utils import ProgramEncoder
import json
from project_frame import ProjectFrame
# import ctypes
# ctypes.windll.shcore.SetProcessDpiAwareness(1)

# class Component(ttk.Frame):
#     def __init__(self, master, name, **kwargs):
#         super().__init__(master, **kwargs)
#         self._name = name

if __name__ == '__main__':
    # project = Project.load('../saves/project.json')

    window = tk.Tk()
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()
    window.title('Logic Gates')
    window.iconbitmap('../assets/comp.ico')
    window.state('zoomed')
    window.minsize(int(screenwidth * 0.5), int(screenheight * 0.5))

    # Create the project menu
    project_menu = tk.Menu(window, tearoff=0)
    window.config(menu=project_menu)

    # Function to save file
    def save_project():
        with open('../saves/frame.json', 'w') as f:
            json.dump(project_frame.serialize(), f, cls=ProgramEncoder, indent=4)

    file_menu = tk.Menu(project_menu)
    project_menu.add_cascade(label='File', menu=file_menu)
    file_menu.add_command(label='Save', command=save_project)

    # Open project from the save file
    with open('../saves/frame.json', 'r') as f:
        project_frame = ProjectFrame.deserialize(json.load(f), window)
    project_frame.pack(fill=tk.BOTH, expand=True)

    project_frame.loop()
    window.mainloop()