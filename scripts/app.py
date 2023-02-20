import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog
from PIL import Image, ImageTk
from gates import Project
import json

class ProjectFrame(tk.Frame):
    def __init__(self, master, project, dir_obj=None, **kwargs):
        super().__init__(master, **kwargs)

        # Create topbar that holds the project's name
        self._topbar = tk.Frame(self, background='orange')
        self._topbar.pack(side=tk.TOP, fill=tk.BOTH)
        ttk.Label(self._topbar, text=project.name).pack(padx=5, pady=5, side=tk.LEFT)

        # Create sidebar that holds the project directory and buttons to manipulate it
        self._sidebar = tk.Frame(self, background='red')
        self._sidebar.pack(side=tk.LEFT, fill=tk.BOTH)

        # Create the directory widget
        if dir_obj is None:
            self._tree = Directory(self._sidebar, project)
        else:
            self._tree = Directory.deserialize(dir_obj, self._sidebar, project)
        self._tree.heading('#0', text='Components')
        self._tree.pack(padx=5, pady=5, side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Button to create a new component
        self._new_component = ttk.Button(self._sidebar, text="New component", command=self._tree.new_component)
        self._new_component.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button to create a new folder
        self._new_folder = ttk.Button(self._sidebar, text="New folder", command=self._tree.new_folder)
        self._new_folder.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button to delete a component or folder
        self._delete = ttk.Button(self._sidebar, text="Delete", command=self._tree.delete_selected)
        self._delete.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button to add an instance of the selected component to the current workspace
        self._add_instance = ttk.Button(self._sidebar, text="Add instance")
        self._add_instance.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Widget to hold the workspaces
        self._workspaces = tk.Frame(self, background='blue')
        self._workspaces.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

class Directory(ttk.Treeview):
    def __init__(self, master, project, populate=True):
        super().__init__(master)
        self._project = project

        self._component_popup = tk.Menu(self, tearoff=0)
        self._component_popup.add_command(label='Add instance')
        self._component_popup.add_command(label='Rename', command=self.rename_selected)
        self._component_popup.add_command(label='Delete', command=self.delete_selected)

        self._folder_popup = tk.Menu(self, tearoff=0)
        self._folder_popup.add_command(label='New component', command=self.new_component)
        self._folder_popup.add_command(label='New folder', command=self.new_folder)
        self._folder_popup.add_command(label='Rename', command=self.rename_selected)
        self._folder_popup.add_command(label='Delete', command=self.delete_selected)

        self._other_popup = tk.Menu(self, tearoff=0)
        self._other_popup.add_command(label='New component', command=self.new_component)
        self._other_popup.add_command(label='New folder', command=self.new_folder)

        # Get icons
        folder_icon_dir = '../assets/folder.png'
        component_icon_dir = '../assets/comp.png'
        self._folder_icon = ImageTk.PhotoImage(Image.open(folder_icon_dir).resize((15, 15)))
        self._component_icon = ImageTk.PhotoImage(Image.open(component_icon_dir).resize((15, 15)))

        # Keep track of which entries are folders vs components
        self._folders = {}
        self._folder_rows = {}
        self._components = {}
        self._component_rows = {}
        self._attributes = {}

        # The row currently being dragged
        self._dragged_row = ''

        # Add gates
        if populate:
            builtins_folder = self._add_folder('', 'builtins')
            for name in project.get_gate_names():
                if name in Project.BUILTIN_GATES:
                    self._add_component(builtins_folder, name, deleteable=False, renameable=False)
                else:
                    self._add_component('', name)

        # Event listeners
        self.bind('<Button-1>', self._on_left_click)
        self.bind('<B1-Motion>', self._on_left_move)
        self.bind('<ButtonRelease-1>', self._on_left_release)
        self.bind('<Button-3>', self._on_right_click)

    def is_folder(self, iid):
        return iid in self._folder_rows
    
    def is_component(self, iid):
        return iid in self._component_rows
    
    def get_name(self, iid):
        if self.is_folder(iid):
            return self._folder_rows[iid]
        elif self.is_component(iid):
            return self._component_rows[iid]
    
    def is_deleteable(self, iid):
        return self._attributes[iid]['deleteable']
    
    def is_renameable(self, iid):
        return self._attributes[iid]['renameable']

    def _add_folder(self, parent, name, deleteable=True, renameable=True):
        if self.is_component(parent):
            raise ValueError('Cannot nest component in another component')
        if name not in self._folders:
            if self._folder_icon is not None:
                iid = self.insert(parent, tk.END, text=name, image=self._folder_icon)
            else:
                iid = self.insert(parent, tk.END, text=name)
            self._folders[name] = iid
            self._folder_rows[iid] = name
            self._attributes[iid] = {'deleteable': deleteable, 'renameable': renameable}
            return iid
        else:
            raise ValueError('{} already exists'.format(name))
    
    def _add_component(self, parent, name, deleteable=True, renameable=True):
        if self.is_component(parent):
            raise ValueError('Cannot nest component in another component')
        if name not in self._components:
            if self._component_icon is not None:
                iid = self.insert(parent, tk.END, text=name, image=self._component_icon)
            else:
                iid = self.insert(parent, tk.END, text=name)
            self._components[name] = iid
            self._component_rows[iid] = name
            self._attributes[iid] = {'deleteable': deleteable, 'renameable': renameable}
            return iid
        else:
            raise ValueError('{} already exists'.format(name))
    
    def new_folder(self):
        row_id = self.focus()
        if self.is_component(row_id):
            row_id = self.parent(row_id)

        name = simpledialog.askstring('Input', 'Enter folder name')
        if name and name != '':
            try:
                self._add_folder(row_id, name)
            except ValueError as e:
                simpledialog.messagebox.showerror('Error', str(e))
    
    def new_component(self):
        row_id = self.focus()
        if self.is_component(row_id):
            row_id = self.parent(row_id)

        name = simpledialog.askstring('Input', 'Enter component name')
        if name and name != '':
            try:
                self._add_component(row_id, name)
            except ValueError as e:
                simpledialog.messagebox.showerror('Error', str(e))

    def delete(self, iid, force=False):
        if not self.is_deleteable(iid):
            raise ValueError('Cannot delete')
        if self.is_folder(iid):
            # Remove folder
            name = self._folder_rows[iid]
            children = self.get_children(iid)
            if len(children) > 0 and not force:
                raise Warning('{} is not empty'.format(name, len(children)))
            
            # Recursively remove nested folders and components
            for child in children:
                self.delete(child, force=True)

            # Delete this folder
            del self._folders[name]
            del self._folder_rows[iid]
            del self._attributes[iid]
            super().delete(iid)
        else:
            # Remove component
            name = self._component_rows[iid]
            self._project.delete_definition(name, force=force)
            del self._components[name]
            del self._component_rows[iid]
            del self._attributes[iid]
            super().delete(iid)

    def delete_selected(self):
        row_id = self.focus()
        if row_id != '':
            try:
                try:
                    self.delete(row_id, force=False)
                except Warning as w:
                    proceed = simpledialog.messagebox.askokcancel('Warning', '{}. Continue?'.format(str(w)))
                    if proceed:
                        self.delete(row_id, force=True)
            except ValueError as e:
                simpledialog.messagebox.showerror('Error', str(e))

    def rename(self, iid, new_name):
        if not self.is_renameable(iid):
            raise ValueError('Cannot rename')
        if self.is_folder(iid):
            name = self._folder_rows[iid]
            if new_name in self._folders:
                raise ValueError('{} already exists'.format(new_name))
            self.item(iid, text=new_name)
            self._folder_rows[iid] = new_name
            del self._folders[name]
            self._folders[new_name] = iid
        else:
            name = self._component_rows[iid]
            if new_name in self._components:
                raise ValueError('{} already exists'.format(new_name))
            self._project.rename_definition(name, new_name)
            self.item(iid, text=new_name)
            self._component_rows[iid] = new_name
            del self._components[name]
            self._components[new_name] = iid
        
    def rename_selected(self):
        row_id = self.focus()
        if row_id != '':
            new_name = simpledialog.askstring('Input', 'Enter component name', initialvalue=self.get_name(row_id))
            if new_name and new_name != '':
                try:
                    self.rename(row_id, new_name)
                except ValueError as e:
                    simpledialog.messagebox.showerror('Error', str(e))
    
    def serialize(self):
        def helper(iid):
            structure = {}
            children = self.get_children(iid)
            for child in children:
                name = self.get_name(child)
                if self.is_folder(child):
                    structure[name] = helper(child)
                else:
                    structure[name] = None
            return structure
        structure = helper('')

        folders = {name: self._attributes[iid] for name, iid in self._folders.items()}
        components = {name: self._attributes[iid] for name, iid in self._components.items()}

        return {
            'folders': folders,
            'components': components,
            'structure': structure
        }

    def deserialize(obj, master, project):
        tree = Directory(master, project, populate=False)
        
        def helper(parent, structure):
            for name, children in structure.items():
                if children is None:
                    tree._add_component(parent, name, **obj['components'][name])
                else:
                    iid = tree._add_folder(parent, name, **obj['folders'][name])
                    helper(iid, children)
        helper('', obj['structure'])

        return tree

    def _on_left_click(self, e):
        region = self.identify_region(e.x, e.y)
        if region == 'nothing' or region == 'heading':
            self.focus('')
            self.selection_set()
        self._dragged_row = self.identify_row(e.y)

    def _on_left_move(self, e):
        destination = self.identify_row(e.y)
        if self._dragged_row != '' and destination != self._dragged_row:
            parent = self.parent(destination)
            try:
                if self.is_component(destination):
                    self.move(self._dragged_row, parent, self.index(destination))
                elif self.is_folder(destination) or self.identify_region(e.x, e.y) == 'heading':
                    self.move(self._dragged_row, destination, 0)
                else:
                    self.move(self._dragged_row, '', tk.END)
            except tk.TclError:
                pass
    
    def _on_left_release(self, _):
        self._dragged_row == ''

    def _on_right_click(self, e):
        # Focus on clicked row
        region = self.identify_region(e.x, e.y)
        if region == 'tree':
            row = self.identify_row(e.y)
            self.focus(row)
            self.selection_set(row)
        else:
            row = ''
            self.focus('')
            self.selection_set()

        # Show the appropriate popup menu
        if self.is_component(row):
            try:
                self._component_popup.tk_popup(e.x_root, e.y_root, 0)
            finally:
                self._component_popup.grab_release()
        elif self.is_folder(row):
            try:
                self._folder_popup.tk_popup(e.x_root, e.y_root, 0)
            finally:
                self._folder_popup.grab_release()
        else:
            try:
                self._other_popup.tk_popup(e.x_root, e.y_root, 0)
            finally:
                self._other_popup.grab_release()

if __name__ == '__main__':
    project = Project.load('../saves/project.json')

    window = tk.Tk()
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()
    window.title('Logic Gates')
    window.state('zoomed')
    window.minsize(int(screenwidth * 0.5), int(screenheight * 0.5))

    with open('../saves/directory.json', 'r') as f:
        project_frame = ProjectFrame(window, project, dir_obj = json.load(f))
    project_frame.pack(fill=tk.BOTH, expand=True)

    def save_dir():
        with open('../saves/directory.json', 'w') as f:
            json.dump(project_frame._tree.serialize(), f, indent=4)

    save = ttk.Button(window, text='save', command=save_dir)
    save.pack(padx=5, pady=5, side=tk.BOTTOM)

    window.mainloop()