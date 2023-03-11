import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog
from tkinter import filedialog
from gates.utils import ProgramEncoder
from gates import Project
import json
from project_frame import ProjectFrame
from tempfile import NamedTemporaryFile
import shutil
# import ctypes
# ctypes.windll.shcore.SetProcessDpiAwareness(1)

# TODOs:
# TODO keep track of which gates in a definition are connected to the output and save only those states
# TODO when modifying a gate definition, change the saved gate states to reflect it

# Known bugs:
# If a definition changes its number of inputs or outputs, particularly by inserting one, and another definition had a connection to the old input or output, the connection does not update leading to possible mismatched dimensions

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        self.title('Logic Gates')
        self.iconbitmap('../assets/comp.ico')
        self.state('zoomed')
        self.minsize(int(screenwidth * 0.5), int(screenheight * 0.5))

        # Create the project menu
        self._menu = tk.Menu(self)
        self.config(menu=self._menu)

        self._file_menu = tk.Menu(self._menu, tearoff=0)
        self._file_menu.add_command(label='Save', command=self._save_project)
        self._file_menu.add_command(label='Save as', command=self._save_project_as)
        self._file_menu.add_command(label='Open project', command=self._open_project)
        self._file_menu.add_command(label='New project', command=self._new_project)
        self._file_menu.add_command(label='Close project', command=self._close_project)
        self._file_menu.entryconfig(0, state='disabled')
        self._file_menu.entryconfig(1, state='disabled')
        self._file_menu.entryconfig(4, state='disabled')
        self._menu.add_cascade(label='File', menu=self._file_menu)

        self._file_edit_menu = tk.Menu(self._menu, tearoff=0)
        self._file_edit_menu.add_command(label='Rename', command=self._rename_project)
        self._file_edit_menu.entryconfig(0, state='disabled')
        self._menu.add_cascade(label='Edit', menu=self._file_edit_menu)

        self._project_frame = None
        self._filename = None

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _save_project(self):
        if self._filename is not None:
            with NamedTemporaryFile('w', dir='.', delete=False) as temp:
                json.dump(self._project_frame.serialize(), temp, cls=ProgramEncoder, indent=4)
            shutil.move(temp.name, self._filename)
        else:
            raise ValueError('Save destination not specified')

    def _save_project_as(self):
        with filedialog.asksaveasfile() as f:
            self._filename = f.name
        self._save_project()
        self._file_menu.entryconfig(0, state='active')

    def _open_project(self):
        self._filename = filedialog.askopenfilename()
        if self._filename is not None and self._filename != '':
            self._close_project()
            try:
                with open(self._filename, 'r') as f:
                    self._project_frame = ProjectFrame.deserialize(json.load(f), self)
                self._project_frame.pack(fill=tk.BOTH, expand=True)
                self._project_frame.startloop()
                self._file_menu.entryconfig(0, state='active')
                self._file_menu.entryconfig(1, state='active')
                self._file_menu.entryconfig(4, state='active')
                self._file_edit_menu.entryconfig(0, state='active')
            except Exception as e:
                print(f'Could not open project: {str(e)}')

    def _new_project(self):
        project_name = simpledialog.askstring('New project', 'Enter project name', initialvalue='New project')
        if project_name is not None and project_name != '':
            self._close_project()
            self._project_frame = ProjectFrame(self, Project(project_name))
            self._project_frame.pack(fill=tk.BOTH, expand=True)
            self._project_frame.startloop()
            self._file_menu.entryconfig(1, state='active')
            self._file_menu.entryconfig(4, state='active')
            self._file_edit_menu.entryconfig(0, state='active')

    def _close_project(self):
        if self._project_frame is not None:
            self._prompt_save()
            self._project_frame.forget()
            self._project_frame = None
            self._file_menu.entryconfig(0, state='disabled')
            self._file_menu.entryconfig(1, state='disabled')
            self._file_menu.entryconfig(4, state='disabled')
            self._file_edit_menu.entryconfig(0, state='disabled')

    def _rename_project(self):
        if self._project_frame is not None:
            new_name = simpledialog.askstring('Rename project', 'Enter a new name', initialvalue=self._project_frame.name)
            if new_name is not None and new_name != '':
                self._project_frame._rename(new_name)

    def _on_closing(self):
        if self._project_frame is not None:
            self._prompt_save()
        self.destroy()

    def _prompt_save(self):
        save = simpledialog.messagebox.askokcancel('Save', 'Would you like to save before closing this project?')
        if save:
            if self._filename is not None:
                self._save_project()
            else:
                self._save_project_as()

    def mainloop(self, *args, **kwargs):
        super().mainloop(*args, **kwargs)

if __name__ == '__main__':
    app = App()
    app.mainloop()