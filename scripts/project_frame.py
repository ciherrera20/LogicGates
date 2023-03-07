import tkinter as tk
import tkinter.ttk as ttk
from directory import Directory
from gates import Project
from workspace import Workspace

class ProjectFrame(tk.Frame):
    def __init__(self, master, project, dir_obj=None, ws_obj=None, **kwargs):
        super().__init__(master, **kwargs)

        # Store project
        self._project = project

        # Create topbar that holds the project's name
        self._topbar = tk.Frame(self, background='orange')
        self._topbar.pack(side=tk.TOP, fill=tk.BOTH)
        self._project_label = ttk.Label(self._topbar, text=project.name)
        self._project_label.pack(padx=5, side=tk.LEFT)

        # Create the TPS controls
        self._tps_var = tk.IntVar()
        self._increment_tps_button = tk.Button(self._topbar, text=">", command=self._increment_tps)
        self._increment_tps_button.pack(side=tk.RIGHT)
        self._tps_scale = tk.Scale(self._topbar, from_=0, to=100, var=self._tps_var, showvalue=0, orient=tk.HORIZONTAL, command=self._tps_change)
        self._tps_scale.pack(side=tk.RIGHT)
        self._decrement_tps_button = tk.Button(self._topbar, text="<", command=self._decrement_tps)
        self._decrement_tps_button.pack(side=tk.RIGHT)
        self._tps_label = tk.Label(self._topbar, text='TPS: 0')
        self._tps_label.pack(side=tk.RIGHT)
        self._tps_step = tk.Button(self._topbar, text="Step", command=self.tick)
        self._tps_step.pack(side=tk.RIGHT)

        # Create sidebar that holds the project directory and buttons to manipulate it
        self._sidebar = tk.Frame(self, background='red')
        self._sidebar.pack(side=tk.LEFT, fill=tk.BOTH)

        # Create the directory widget
        if dir_obj is None:
            self._tree = Directory(self._sidebar, project)
        else:
            self._tree = Directory.deserialize(dir_obj, self._sidebar, self)
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
        self._add_instance = ttk.Button(self._sidebar, text="Add instance", command=self.add_selected_gate)
        self._add_instance.pack(padx=5, pady=5, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame to hold workspaces widget
        self._workspaces_frame = tk.Canvas(self, background='blue')
        self._workspaces_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a workspace for every custom gate definition
        self._workspaces = {}
        for name in self._project.get_gate_names():
            if name not in Project.BUILTIN_GATES:
                if ws_obj is not None and name in ws_obj:
                    self._workspaces[name] = Workspace.deserialize(ws_obj[name], self._workspaces_frame, project[name], self)
                else:
                    self._workspaces[name] = Workspace(self._workspaces_frame, project[name], self)

        self._current_workspace = None

        self._tree.bind('<Double-Button-1>', self._on_double_click)
    
    def _on_double_click(self, e):
        iid = self._tree.identify_row(e.y)
        if not self._tree.is_folder(iid):
            self.hide_workspace()

        if self._tree.is_component(iid):
            name = self._tree.get_name(iid)
            if name not in Project.BUILTIN_GATES:
                self.show_workspace(name)

    def hide_workspace(self):
        if self._current_workspace is not None:
            self._current_workspace.forget()
            self._current_workspace = None

    def show_workspace(self, name):
        self.hide_workspace()
        if name is not None and name != '':
            self._current_workspace = self._workspaces[name]
            self._current_workspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def add_workspace(self, name):
        self._workspaces[name] = Workspace(self._workspaces_frame, self._project[name], self)
        self.show_workspace(name)

    def delete_workspace(self, name):
        if self._current_workspace == self._workspaces[name]:
            self.hide_workspace()
        del self._workspaces[name]
    
    def rename_workspace(self, name, new_name):
        ws = self._workspaces[name]
        del self._workspaces[name]
        ws.rename(new_name)
        self._workspaces[new_name] = ws
        self.update_gate_type(new_name)
    
    def update_gate_type(self, gate_name):
        for ws in self._workspaces.values():
            ws.update_gate_type(gate_name)

    def add_selected_gate(self):
        row_id = self._tree.focus()
        if self._tree.is_component(row_id) and self._current_workspace is not None:
            self._current_workspace.add_gate_type(self._tree.get_name(row_id))

    def serialize(self):
        workspaces = {name: ws.serialize() for name, ws in self._workspaces.items()}
        return {
            'project': self._project.serialize(),
            'directory': self._tree.serialize(),
            'workspaces': workspaces,
            'tps': self._tps_var.get()
        }

    def deserialize(obj, master):
        gates = {}
        project = Project.deserialize(obj['project'], gates)

        # Remap gates in workspace obj
        old_ws_obj = obj['workspaces']
        ws_obj = {}
        for name, old_ws in old_ws_obj.items():
            ws = {}
            for old_uid, (x, y) in old_ws.items():
                if int(old_uid) in gates:
                    uid = gates[int(old_uid)].uid
                    ws[uid] = (x, y)
            ws_obj[name] = ws

        pframe = ProjectFrame(
            master,
            project,
            dir_obj = obj['directory'],
            ws_obj = ws_obj
        )
        pframe._tps_var.set(obj.get('tps', 20))
        pframe._tps_change()
        return pframe

    def tick(self):
        if self._current_workspace is not None:
            self._current_workspace.tick()
    
    def _tps_change(self, e=None):
        self._tps_label.config(text=f'TPS: {self._tps_var.get()}')
    
    def _increment_tps(self):
        self._tps_var.set(self._tps_var.get() + 1)
        self._tps_change()
    
    def _decrement_tps(self):
        self._tps_var.set(self._tps_var.get() - 1)
        self._tps_change()

    def loop(self):
        tps = self._tps_var.get()
        if tps > 0:
            self.tick()
            self.after(int(1000 / tps), self.loop)
        else:
            # Check if tps is nonzero every 100 milliseconds
            self.after(100, self.loop)