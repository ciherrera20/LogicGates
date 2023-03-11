import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog
from bbox import Bbox
import math
import random
from functools import reduce
from itertools import accumulate

def get_tags(composite_tag):
    return tuple(accumulate(composite_tag.split(':'), func=lambda fields, field: f'{fields}:{field}'))

def transform_dims(dims):
    return [math.log(dim, 2) + 1 for dim in dims]

def sum_dims(dims):
    return reduce(lambda acc, x: acc + x, transform_dims(dims), 0)

class ReshaperDialog(simpledialog.Dialog):
    def __init__(self, parent, *args, **kwargs):
        self.input_dims = None
        self.output_dims = None
        super().__init__(parent, 'New Reshaper', *args, **kwargs)

    def body(self, master):
        tk.Label(master, text="Input dimensions:").grid(row=0)
        tk.Label(master, text="Output dimensions:").grid(row=1)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        self.input_dims = self.e1.get()
        self.output_dims = self.e2.get()
        self.destroy()

class Workspace(tk.Canvas):
    # VSCode theme
    # # Colors for connection lines and io circle outlines
    # ON = '#0099ff'
    # OFF = 'white'
    # ERROR = 'red'

    # # Color for io circle fill
    # IO_FILL = '#111111'
    # IO_OUTLINE_OFF = 'white'

    # # Colors for states
    # STATE_OUTLINE = 'white'
    # STATE_FILL_OFF = '#111111'

    # # Colors for gate body
    # BODY_OUTLINE = '#ffc813'
    # BODY_FILL = '#333333'

    # # Gate name color
    # TEXT_COLOR = 'white'

    # # Workspace colors
    # BACKGROUND = '#1e1e1e'
    # TITLE = '#4ec9b0'

    # Colors for connection lines and io circle outlines
    ON = '#0099ff'
    OFF = 'black'
    ERROR = 'red'

    # Color for io circle fill
    IO_FILL = 'white'

    # Colors for states
    STATE_OUTLINE = 'black'
    STATE_FILL_OFF = 'white'

    # Colors for gate body
    BODY_OUTLINE = 'black'
    BODY_FILL = 'white'

    # Gate name color
    TEXT_COLOR = 'black'

    # Workspace colors
    BACKGROUND = 'white'
    TITLE = 'grey'

    CIRCLERAD = 10

    def __init__(self, master, definition, project_frame, obj={}, **kwargs):
        super().__init__(master, background=Workspace.BACKGROUND, **kwargs)
        self._project_frame = project_frame
        self._project = project_frame._project
        self._definition = definition
        self._title = self.create_text(0, 0, fill=Workspace.TITLE, font=f'Courier 30', text=definition.name)

        self._components = {}
        for uid, gate in definition.gates.items():
            if uid in obj:
                x, y = obj[uid]
                self._components[uid] = self.create_component(x, y, gate)
            else:
                self._components[uid] = self.place_gate(gate)

        for (from_uid, to_uid), pairs in definition.connections.items():
            from_gate = definition.gates[from_uid]
            to_gate = definition.gates[to_uid]
            for (output_idx, input_idx) in pairs:
                self.create_connection((from_gate, output_idx), (input_idx, to_gate))

        # Store the selected gate object
        self._selected_gate = None
        self._selection_offset = None

        # Store the index of the selected input
        self._selected_input = None
        self._toggled_to = None

        # Store tags when right clicking
        self._right_click_tags = None

        self._ws_popup = tk.Menu(self, tearoff=0)
        self._ws_popup.add_command(label='Organize', command=self.organize_gates)
        # self._ws_popup.add_command(label='Repair self', command=self._definition.repair_state)
        self._ws_popup.add_command(label='Reset self', command=self.reset_state)
        self._ws_popup.add_command(label='Repair instances', command=self._definition.repair_instances)

        self._component_popup = tk.Menu(self, tearoff=0)
        self._component_popup.add_command(label='Duplicate', command=self.duplicate_right_clicked_gate)
        self._component_popup.add_command(label='Reset', command=self.reset_right_clicked_gate)
        self._component_popup.add_command(label='Delete', command=self.delete_right_clicked_gate)

        self._def_source_popup = tk.Menu(self, tearoff=0)
        self._def_source_popup.add_command(label='Add input(s)', command=self.add_right_clicked_io)
        self._def_source_popup.add_command(label='Reset', command=self.reset_right_clicked_gate)

        self._def_source_output_popup = tk.Menu(self, tearoff=0)
        self._def_source_output_popup.add_command(label='Set label', command=self.set_right_clicked_label)
        self._def_source_output_popup.add_command(label='Delete input', command=self.delete_right_clicked_io)
        self._def_source_output_popup.add_command(label='Insert input(s)', command=self.insert_right_clicked_io)

        self._def_sink_popup = tk.Menu(self, tearoff=0)
        self._def_sink_popup.add_command(label='Add output(s)', command=self.add_right_clicked_io)
        self._def_sink_popup.add_command(label='Reset', command=self.reset_right_clicked_gate)

        self._def_sink_input_popup = tk.Menu(self, tearoff=0)
        self._def_sink_input_popup.add_command(label='Set label', command=self.set_right_clicked_label)
        self._def_sink_input_popup.add_command(label='Delete output', command=self.delete_right_clicked_io)
        self._def_sink_input_popup.add_command(label='Insert output(s)', command=self.insert_right_clicked_io)

        # Set event listeners
        self.bind('<Configure>', self._on_resize)
        self.bind('<Button-1>', self._on_left_click)
        self.bind('<B1-Motion>', self._on_left_move)
        self.bind('<Button-2>', self._on_middle_click)
        self.bind('<B2-Motion>', self._on_middle_move)
        self.bind('<ButtonRelease-1>', self._on_left_release)
        self.bind('<Button-3>', self._on_right_click)
    
    def add_gate_type(self, name):
        try:
            if name == 'Reshaper':
                rdialog = ReshaperDialog(self)
                input_dims, output_dims = rdialog.input_dims, rdialog.output_dims

                # Handle cancel
                if input_dims is None or output_dims is None:
                    return

                # Convert to lists of dimensions
                if input_dims == '':
                    input_dims = []
                else:
                    input_dims = [int(dim) for dim in input_dims.split(',')]
                if output_dims == '':
                    output_dims = []
                else:
                    output_dims = [int(dim) for dim in output_dims.split(',')]
                args = [input_dims, output_dims]
            elif name == 'Source' or name == 'Sink':
                dim_str = simpledialog.askstring(f'New {name}', 'Enter dimensions')
                if dim_str is None:
                    return
                if dim_str == '':
                    dims = []
                else:
                    dims = [int(dim) for dim in dim_str.split(',')]
                args = [dims]
            elif name == 'Constant':
                dim_str = simpledialog.askstring(f'New Constant', 'Enter dimension')
                if dim_str is None or dim_str == '':
                    return
                dim = int(dim_str)
                args = [dim]
            else:
                args = []
            gate = self._project[name](*args)
            self._definition.add_gate(gate)
            self._components[gate.uid] = self.place_gate(gate, force=False)
        except ValueError as e:
            simpledialog.messagebox.showerror('Error', str(e))

    def _on_resize(self, e):
        self.coords(self._title, e.width / 2, e.height / 2)

    def _on_left_click(self, e):
        x, y = self.canvasx(e.x), self.canvasy(e.y)
        id = self.find_closest(x, y)

        # Make sure the item contains the point that was clicked
        if Bbox(self.bbox(id)).contains(x, y):
            tags = self.gettags(id)
        else:
            tags = []
        
        # Clear selected
        self._selected_gate = None
        self._selection_offset = None
        self._selected_input = None
        self._toggled_to = None

        # Clicking on a gate
        if len(tags) != 0 and tags[0] == 'gate':
            if tags[-1] == 'current':
                tags = tags[-2].split(':')
            else:
                tags = tags[-1].split(':')
            
            # Record the gate that was clicked and where it was clicked relative to its center
            self._selected_gate = self._definition.gates[int(tags[1])]
            tag = self._components[self._selected_gate.uid]

            if tags[2] == 'input':
                # Record which input was clicked on
                self._selected_input = int(tags[3])
                to_pair = (self._selected_input, self._selected_gate)
                from_pair = self._definition.get_from_pair(to_pair)

                # Remove current connection
                if from_pair is not None:
                    from_gate, output_idx = from_pair
                    self._definition.remove_connection(from_pair, to_pair)
                    tag = f'connection:{from_gate.uid}:{self._selected_gate.uid}:{output_idx}:{self._selected_input}'
                    self.delete(tag)
                
                # Create virtual connection
                to_tag = self._components[self._selected_gate.uid]
                input_tag = f'{to_tag}:input:{self._selected_input}'
                input_bbox = Bbox(self.bbox(input_tag))
                output_bbox = Bbox((x, y + input_bbox.hheight), input_bbox.width, input_bbox.height)
                connection_tag = f'virtualconnection:{self._selected_gate.uid}:{self._selected_input}'
                output = [0] * self._selected_gate.input_dims[self._selected_input]
                self._create_connection_lines(output_bbox, input_bbox, output, len(output), connection_tag)
            elif tags[2] == 'toggle':
                self._toggled_to = self._toggle(self._selected_gate, int(tags[3]), int(tags[4]))
            else:
                center = Bbox(self.bbox(tag)).center
                self._selection_offset = (center[0] - x, center[1] - y)
    
    def _on_middle_click(self, e):
        self.scan_mark(e.x, e.y)
    
    def _get_state(self, gate, i, j):
        if gate.name == 'Constant':
            state = gate.get_state()
        else:
            state = self._definition.get_gate_state(gate.uid)
        if gate.output_dims[i] == 1:
            return state[i]
        else:
            return state[i][j]

    def _set_state(self, gate, i, j, num, update_def=True):
        if gate.name == 'Source' or gate.name == 'Constant':
            s = 'toggle'
        else:
            s = 'display'
        tag = f'gate:{gate.uid}:{s}:{i}:{j}'

        # Get color
        if num is None:
            color = Workspace.ERROR
        elif num == 1:
            color = Workspace.ON
        else:
            color = Workspace.STATE_FILL_OFF

        # Update color
        ids = self.find_withtag(tag)
        for id in ids:
            if self.type(id) != 'line' and self.itemconfigure(id)['fill'][4] != '':
                self.itemconfigure(id, fill=color)
        
        # Update gate state
        if update_def:
            # Retrieve the state
            if gate.name == 'Constant':
                state = gate.get_state()
            else:
                state = self._definition.get_gate_state(gate.uid)

            # Update the state
            if gate.dims[i] == 1:
                state[i] = num
            else:
                state[i][j] = num
            
            # Set the new state
            if gate.name == 'Constant':
                gate.set_state(state)
            else:
                self._definition.set_gate_state(gate.uid, state)

    def _toggle(self, gate, i, j):
        num = self._get_state(gate, i, j)
        self._set_state(gate, i, j, abs(num - 1))
        return abs(num - 1)

    def _on_left_move(self, e):
        if self._selected_gate is not None:
            x, y = self.canvasx(e.x), self.canvasy(e.y)
            # We are dragging a gate
            if self._selection_offset is not None:
                x_off, y_off = self._selection_offset
                self.move_component_to(self._selected_gate, x + x_off, y + y_off, force=True)
            # We are making a connection
            elif self._selected_input is not None:
                to_tag = self._components[self._selected_gate.uid]
                input_tag = f'{to_tag}:input:{self._selected_input}'
                input_bbox = Bbox(self.bbox(input_tag))

                # Move input connections
                line_ids = self.find_withtag('virtualconnection')
                for line_id in line_ids:
                    _, _, x2, y2 = self.coords(line_id)
                    x_off = x2 - input_bbox.xc
                    self.coords(line_id, x + x_off, y, x2, y2)
            # Check for state updates
            elif self._toggled_to is not None:
                # Find closest item that is not a line
                tags = self._get_closest_tags(x, y)
                if len(tags) != 0 and tags[0] == 'gate':
                    if tags[-1] == 'current':
                        tags = tags[-2].split(':')
                    else:
                        tags = tags[-1].split(':')

                    # We are over the selected gate
                    if int(tags[1]) == self._selected_gate.uid and tags[2] == 'toggle':
                        self._set_state(self._selected_gate, int(tags[3]), int(tags[4]), self._toggled_to)
    
    def _on_middle_move(self, e):
        self.scan_dragto(e.x, e.y, gain=1)

        # Keep title in the middle
        w, h = self.winfo_width(), self.winfo_height()
        self.coords(self._title, self.canvasx(w / 2), self.canvasy(h / 2))

    def _on_left_release(self, e):
        # Find closest item that is not a line
        x, y = self.canvasx(e.x), self.canvasy(e.y)
        tags = self._get_closest_tags(x, y)
        
        # Clicking on a gate
        if len(tags) != 0 and tags[0] == 'gate':
            if tags[-1] == 'current':
                tags = tags[-2].split(':')
            else:
                tags = tags[-1].split(':')
            
            # Record the gate that was clicked and where it was clicked relative to its center
            gate = self._definition.gates[int(tags[1])]

            # Make new connection
            if self._selected_gate is not None and self._selected_input is not None:
                if tags[2] == 'output':
                    # Record which input was clicked on
                    output_idx = int(tags[3])
                    try:
                        self._definition.add_connection((gate, output_idx), (self._selected_input, self._selected_gate))
                        self.create_connection((gate, output_idx), (self._selected_input, self._selected_gate))
                    except ValueError:
                        pass
            
        # Delete virtual connections
        self.delete('virtualconnection')

        # Clear selected
        self._selected_gate = None
        self._selection_offset = None
        self._selected_input = None
        self._toggled_to = None
    
    def _get_closest_tags(self, x, y):
        # Find closest item that is not a line
        ids = []
        for id in self.find_overlapping(x, y, x, y):
            if self.type(id) != 'line':
                ids.append(id)
        if len(ids) == 0:
            id = None
        else:
            id = ids[-1]

        # Make sure the item contains the point that was clicked
        if id is not None and Bbox(self.bbox(id)).contains(x, y):
            tags = self.gettags(id)
        else:
            tags = []
        return tags

    def _on_right_click(self, e):
        # Find closest item that is not a line
        x, y = self.canvasx(e.x), self.canvasy(e.y)
        tags = self._get_closest_tags(x, y)
        self._right_click_tags = None
        
        # Clicking on a gate
        if len(tags) != 0 and tags[0] == 'gate':
            if tags[-1] == 'current':
                tags = tags[-2].split(':')
            else:
                tags = tags[-1].split(':')
            self._right_click_tags = tags

            # Show the appropriate popup menu
            uid = int(tags[1])
            if uid == self._definition.source.uid:
                if 'output' in tags:
                    popup = self._def_source_output_popup
                else:
                    popup = self._def_source_popup
            elif uid == self._definition.sink.uid:
                if 'input' in tags:
                    popup = self._def_sink_input_popup
                else:
                    popup = self._def_sink_popup
            else:
                popup = self._component_popup
            try:
                popup.tk_popup(e.x_root, e.y_root, 0)
            finally:
                popup.grab_release()
        else:
            try:
                self._ws_popup.tk_popup(e.x_root, e.y_root, 0)
            finally:
                self._ws_popup.grab_release()

    def organize_gates(self):
        padding = 10
        rank = self._definition.graph.get_layers(self._definition.source.uid)
        layers = {}
        ranks = sorted(set(rank.values()))
        max_rank = ranks[-1]
        for layer in ranks:
            uids = [uid for uid in rank if rank[uid] == layer]
            layers[max_rank - layer] = uids
        
        old_bbox = Bbox(self.bbox('gate'))

        bboxes = {}
        for layer, uids in layers.items():
            for uid in uids:
                bboxes[uid] = Bbox(self.bbox(self._components[uid])).pad(padding, padding)

        layer_bboxes = [None] * len(layers)
        for layer, uids in layers.items():
            layer_bbox = Bbox(
                sum([bboxes[uid].width for uid in uids]),
                max([bboxes[uid].height for uid in uids])
            )
            layer_bboxes[layer] = layer_bbox
        
        theight = sum([layer_bbox.height for layer_bbox in layer_bboxes])
        # y = old_bbox.y1 + layer_bboxes[0].hheight - padding
        y = old_bbox.yc - (theight / 2) + layer_bboxes[0].hheight
        for layer, layer_bbox in enumerate(layer_bboxes):
            for uid in layers[layer]:
                bbox = bboxes[uid]
                bboxes[uid] = Bbox((bbox.xc, y), bbox.width, bbox.height)
            y += layer_bbox.height
        
        for _, uids in layers.items():
            for uid in uids:
                bbox = bboxes[uid]
                gate = self._definition.gates[uid]
                self.move_component_to(gate, bbox.xc, bbox.yc, force=True)

    def reset_state(self):
        self._definition.reset_state()

        # Update all source components
        for uid in self._definition.gate_types['Source']:
            source = self._definition.gates[uid]
            state = self._definition.get_gate_state(uid)

            for i, output in enumerate(state):
                if output is None or type(output) == int:
                    output = [output]
                for j, num in enumerate(output):
                    self._set_state(source, i, j, num)

    def place_gate(self, gate, force=True):
        new_tag = self.create_component(self.canvasx(0), self.canvasy(0), gate)
        new_bbox = Bbox(self.bbox(new_tag))
        new_bbox += (new_bbox.hwidth, new_bbox.hheight)
        bboxes = []
        for tag in self._components.values():
            bboxes.append(Bbox(self.bbox(tag)))
        bboxes = sorted(bboxes, key=lambda bbox: (bbox.yc, bbox.xc))
        for bbox in bboxes:
            Bbox.resolve_collision(bbox, new_bbox)
        self.move_component_to(gate, new_bbox.xc, new_bbox.yc, force=force)
        return new_tag

    def set_right_clicked_label(self):
        tags = self._right_click_tags
        label = simpledialog.askstring('Label', 'Enter label')
        if label is not None:
            if int(tags[1]) == self._definition.source.uid:
                self._definition.rename_input(int(tags[3]), label)
                self.update_component(self._definition.source)
            else:
                self._definition.rename_output(int(tags[3]), label)
                self.update_component(self._definition.sink)
            self._project_frame.update_gate_type(self._definition.name)

    def duplicate_right_clicked_gate(self):
        tags = self._right_click_tags
        gate = self._definition.gates[int(tags[1])]
        duplicate = self._definition.duplicate_gate(gate)
        self._components[duplicate.uid] = self.create_component(300, 300, duplicate)

    def reset_right_clicked_gate(self):
        tags = self._right_click_tags
        gate = self._definition.gates[int(tags[1])]
        self._definition.reset_gate_state(gate)
    
    def delete_right_clicked_gate(self):
        tags = self._right_click_tags
        gate = self._definition.gates[int(tags[1])]
        self.delete_component(gate)
        self._definition.remove_gate(gate)

    def add_right_clicked_io(self):
        tags = self._right_click_tags
        try:
            if int(tags[1]) == self._definition.source.uid:
                s = 'input'
            else:
                s = 'output'
            dim_str = simpledialog.askstring(f'New {s}(s)', 'Enter dimension(s)')
            if dim_str is not None and dim_str != '':
                dims = [int(dim) for dim in dim_str.split(',')]
                for dim in dims:
                    if int(tags[1]) == self._definition.source.uid:
                        self._definition.append_input(dim)
                        self.update_component(self._definition.source)
                    else:
                        self._definition.append_output(dim)
                        self.update_component(self._definition.sink)
                self._project_frame.update_gate_type(self._definition.name)
        except ValueError or TypeError as e:
            simpledialog.messagebox.showerror('Error', str(e))
    
    def delete_right_clicked_io(self):
        tags = self._right_click_tags
        if int(tags[1]) == self._definition.source.uid:
            self._definition.remove_input(int(tags[3]))
            self.update_component(self._definition.source)
        else:
            self._definition.remove_output(int(tags[3]))
            self.update_component(self._definition.sink)
        self._project_frame.update_gate_type(self._definition.name)
    
    def insert_right_clicked_io(self):
        tags = self._right_click_tags
        try:
            if int(tags[1]) == self._definition.source.uid:
                s = 'input'
            else:
                s = 'output'
            dim_str = simpledialog.askstring(f'New {s}(s)', 'Enter dimension(s)')
            if dim_str is not None and dim_str != '':
                dims = [int(dim) for dim in dim_str.split(',')]
                for dim in dims:
                    if int(tags[1]) == self._definition.source.uid:
                        self._definition.insert_input(int(tags[3]), dim)
                        self.update_component(self._definition.source)
                    else:
                        self._definition.insert_output(int(tags[3]), dim)
                        self.update_component(self._definition.sink)
                self._project_frame.update_gate_type(self._definition.name)
        except ValueError or TypeError as e:
            simpledialog.messagebox.showerror('Error', str(e))

    def create_round_rectangle(self, x1, y1, x2, y2, r=25, **kwargs):
        fill = kwargs.get('fill', '')
        outline = kwargs.get('outline', 'black')
        width = kwargs.get('width', 1)
        tags = kwargs.get('tags', ())

        if type(r) != list:
            r = [r] * 4

        r0, r1, r2, r3 = r
        point_sets = [
            [x1 + 0.8 * r0, y1,
            x2 - 0.8 * r1, y1],
            [x2, y1 + 0.8 * r1,
            x2, y2 - 0.8 * r2],
            [x2 - 0.8 * r2, y2,
            x1 + 0.8 * r3, y2],
            [x1, y2 - 0.8 * r3,
            x1, y1 + 0.8 * r0]
        ]
        corners = [(x2-r1, y1+r1), (x1+r0, y1+r0), (x1+r3, y2-r3), (x2-r2, y2-r2)]

        # Draw interior
        interior = None
        if fill != '':
            interior = self.create_polygon(
                *reduce(lambda x, y: x + y, point_sets),
                fill=fill,
                outline='',
                width=0,
                tags=tags
            )
            for i, (ri, corner) in enumerate(zip([r1, r0, r3, r2], corners)):
                bbox = Bbox(2*ri, 2*ri)
                id = self.create_arc(
                    *(bbox + corner),
                    start=90*i,
                    extent=91,
                    fill=fill,
                    outline='',
                    style=tk.CHORD,
                    width=0,
                    tags=tags
                )

        # Draw outline
        if outline != '':
            for i, (ri, corner) in enumerate(zip([r1, r0, r3, r2], corners)):
                bbox = Bbox(2*ri, 2*ri)
                self.create_arc(
                    *(bbox + corner),
                    start=90*i,
                    extent=91,
                    style=tk.ARC,
                    outline=outline,
                    width=width,
                    tags=tags
                )
            for points in point_sets:
                self.create_line(
                    *points,
                    fill=outline,
                    width=width,
                    tags=tags
                )
        return interior

    def create_component(self, x, y, gate):
        name_size = 10  # Fontsize for component name
        label_size = 7  # Fontsize for input and output labels
        circlerad = Workspace.CIRCLERAD
        tag = f'gate:{gate.uid}'

        # Create component name
        if gate.name == 'Constant':
            text_bbox = Bbox(0, 0)
        else:
            if gate == self._definition.source or gate == self._definition.sink:
                text = f'{self._definition.name}'
            else:
                text = gate.name
            text_id = self.create_text(
                0, 0,
                fill=Workspace.TEXT_COLOR,
                font=f'Courier {name_size}',
                text=text,
                tags=get_tags(f'{tag}:name')
            )
            text_bbox = Bbox(self.bbox(text_id)).pad(0, 3)

        # Create component interior bbox
        if gate.name == 'Source' or gate.name == 'Sink' or gate.name == 'Constant':
            # Create bbox for the state
            if len(gate.dims) == 0:
                state_bbox = Bbox(0, 0)
            else:
                state_bbox = Bbox(circlerad * 2 * sum_dims(gate.dims), circlerad * 2).pad(0, 3)

            # Move the state depending on the text
            if gate.name == 'Source':
                state_bbox -= (0, text_bbox.hheight + state_bbox.hheight)
            elif gate.name == 'Sink':
                state_bbox += (0, text_bbox.hheight + state_bbox.hheight)
            
            # Create center bbox
            center_bbox = Bbox(
                (0, (text_bbox.yc + state_bbox.yc) / 2),
                max(text_bbox.width, state_bbox.width),
                text_bbox.height + state_bbox.height
            )
        else:
            center_bbox = Bbox(self.bbox(text_id)).pad(0, 3)

        # Calculate input and output bounding boxes
        inputs_bbox = Bbox(circlerad * 2 * sum_dims(gate.input_dims), circlerad * 2)
        inputs_bbox += center_bbox.center
        inputs_bbox += (0, center_bbox.hheight + inputs_bbox.hheight)
        outputs_bbox = Bbox(circlerad * 2 * sum_dims(gate.output_dims), circlerad * 2)
        outputs_bbox += center_bbox.center
        outputs_bbox -= (0, center_bbox.hheight + outputs_bbox.hheight)

        # Create gate body
        gate_bbox = Bbox(
            center_bbox.center,
            max(center_bbox.width, inputs_bbox.width, outputs_bbox.width),
            center_bbox.height
        ).pad(circlerad, circlerad)
        rrec = self.create_round_rectangle(*gate_bbox, circlerad, fill=Workspace.BODY_FILL, outline=Workspace.BODY_OUTLINE, width=3, tags=get_tags(f'{tag}:body'))

        # Reorder text
        if gate.name != 'Constant':
            self.tag_lower(rrec, text_id)

        if gate.name == 'Source' or gate.name == 'Sink' or gate.name == 'Constant':
            if gate.name == 'Source' or gate.name == 'Constant':
                s = 'toggle'
            else:
                s = 'display'

            # Create boxes to hold the state
            dims = transform_dims(gate.dims)
            if gate.name == 'Constant':
                state = gate.get_state()
            else:
                state = self._definition.get_gate_state(gate.uid)
            for i, (rdim, dim, acc_dim) in enumerate(zip(gate.dims, dims, accumulate(dims))):
                dbbox = Bbox(circlerad * 2, circlerad * 2).scalex(dim) +\
                        (state_bbox.x1 + 2 * circlerad * (acc_dim - dim) + circlerad * dim, state_bbox.yc)
                width = circlerad * 2 * dim / rdim

                for j in range(rdim):
                    bbox = Bbox(width, circlerad * 2)
                    center = (dbbox.x1 + bbox.width * j + bbox.hwidth, state_bbox.yc)

                    # Get input or output
                    if state[i] is None:
                        num = None
                    elif rdim == 1:
                        num = state[i]
                    else:
                        num = state[i][j]
                    
                    # Get color
                    if num is None:
                        color = Workspace.ERROR
                    elif num == 1:
                        color = Workspace.ON
                    else:
                        color = Workspace.STATE_FILL_OFF

                    # Create toggle or display area
                    if width < 8:
                        # Add cap rectangles
                        if j == 0 or j == rdim - 1:
                            if j == 0:
                                rads = [3, 0, 0, 3]
                            else:
                                rads = [0, 3, 3, 0]
                            self.create_round_rectangle(
                                *(bbox + center),
                                rads,
                                tags=get_tags(f'{tag}:{s}:{i}:{j}'),
                                fill=color,
                                outline='',
                                width=0
                            )
                        else:
                            self.create_rectangle(
                                *(bbox + center),
                                tags=get_tags(f'{tag}:{s}:{i}:{j}'),
                                fill=color,
                                outline='',
                                width=0
                            )
                    else:
                        self.create_round_rectangle(
                            *(bbox + center),
                            3,
                            tags=get_tags(f'{tag}:{s}:{i}:{j}'),
                            fill=color,
                            outline=Workspace.STATE_OUTLINE
                        )

                # Create surrounding rectangle if necessary
                if width < 8:
                    self.create_round_rectangle(
                        *dbbox,
                        3,
                        tags=get_tags(f'{tag}:state'),
                        outline=Workspace.STATE_OUTLINE
                    )

        # Create input and output circles
        circle_bbox = Bbox(circlerad * 2, circlerad * 2)
        it = zip(
            ['input', 'output'],
            [gate.input_dims, gate.output_dims],
            [gate.input_labels, gate.output_labels],
            [inputs_bbox, outputs_bbox],
            [self._definition.get_gate_inputs(gate.uid), self._definition.get_gate_outputs(gate.uid)]
        )

        max_char = 3.99  # Maximum number of characters per circlerad * 2
        for s, dims, labels, base_bbox, io in it:
            dims = transform_dims(dims)
            for i, (dim, acc_dim, curr_io) in enumerate(zip(dims, accumulate(dims), io)):
                # Get current value of input/output
                if type(curr_io) == int:
                    num = curr_io
                elif curr_io is None:
                    num = None
                else:
                    if None in curr_io:
                        num = None
                    else:
                        num = max(curr_io)
                
                # Get color for input/output
                if num is None:
                    color = Workspace.ERROR
                elif num == 1:
                    color = Workspace.ON
                else:
                    color = Workspace.OFF

                # Draw input/output circle
                bbox = circle_bbox.scalex(dim)
                center = (base_bbox.x1 + 2 * circlerad * (acc_dim - dim) + circlerad * dim, base_bbox.yc)
                self.create_round_rectangle(
                    *(bbox + center),
                    circlerad,
                    fill=Workspace.IO_FILL,
                    outline=color,
                    tags=get_tags(f'{tag}:{s}:{i}')
                )

                # Truncate label
                label = labels[i]
                if len(label) > int(max_char * dim):
                    label = label[:int(max_char * dim)]

                # Add label
                self.create_text(
                    *center,
                    font=f'Courier {label_size}',
                    text=f'{label}',
                    tags=get_tags(f'{tag}:{s}:{i}:label')
                )

        self.move_component_to(gate, x, y, force=True)
        return tag

    def delete_component(self, gate):
        self.delete(f'gate:{gate.uid}')

        # Delete input connections
        for predecessor_uid in self._definition.get_gate_predecessors(gate.uid):
            self.delete(f'connection:{predecessor_uid}:{gate.uid}')
        
        # Delete output connections
        self.delete(f'connection:{gate.uid}')
        del self._components[gate.uid]
    
    def update_component(self, gate):
        x, y = Bbox(self.bbox(f'gate:{gate.uid}')).center
        self.delete_component(gate)
        self._components[gate.uid] = self.create_component(x, y, gate)

        # Create input connections
        for predecessor_uid in self._definition.get_gate_predecessors(gate.uid):
            from_gate = self._definition.gates[predecessor_uid]
            for output_idx, input_idx in self._definition.connections[from_gate.uid, gate.uid]:
                self.create_connection((from_gate, output_idx), (input_idx, gate))

        # Create output connections
        for successor_uid in self._definition.get_gate_successors(gate.uid):
            to_gate = self._definition.gates[successor_uid]
            for output_idx, input_idx in self._definition.connections[gate.uid, to_gate.uid]:
                self.create_connection((gate, output_idx), (input_idx, to_gate))

    def create_connection(self, from_pair, to_pair):
        (from_gate, output_idx), (input_idx, to_gate) = from_pair, to_pair
        from_tag = self._components[from_gate.uid]
        to_tag = self._components[to_gate.uid]
        output_tag = f'{from_tag}:output:{output_idx}'
        input_tag = f'{to_tag}:input:{input_idx}'
        input_bbox = Bbox(self.bbox(input_tag))
        output_bbox = Bbox(self.bbox(output_tag))

        # Get output
        outputs = self._definition.get_gate_outputs(from_gate.uid)
        output = outputs[output_idx]
        dim = from_gate.output_dims[output_idx]

        # Create lines
        connection_tag = f'connection:{from_gate.uid}:{to_gate.uid}:{output_idx}:{input_idx}'
        self._create_connection_lines(output_bbox, input_bbox, output, dim, connection_tag)

        return connection_tag

    def _create_connection_lines(self, output_bbox, input_bbox, output, dim, connection_tag):
        p1 = (output_bbox.x1, output_bbox.y1 + 1)
        p2 = (input_bbox.x1, input_bbox.y2 - 1)

        # Make output enumerable
        if type(output) == int:
            output = [output]

        # Create line for each output
        diff = 2 * Workspace.CIRCLERAD
        width = (output_bbox.width - diff) / dim
        # print(dim, output)
        for i in range(dim):
            if output is None:
                num = None
            else:
                num = output[i]
            
            if num is None:
                color = Workspace.ERROR
            elif num == 1:
                color = Workspace.ON
            else:
                color = Workspace.OFF
            
            # Create line offset
            off = i * width + (width + diff) / 2

            # Create line
            line_id = self.create_line(
                p1[0] + off, p1[1], p2[0] + off, p2[1],
                fill=color,
                tags=get_tags(f'{connection_tag}:{i}')
            )
            self.tag_raise(line_id, self._title)
        return connection_tag

    def move_component_to(self, gate, x, y, force=False):
        tag = f'gate:{gate.uid}'
        bbox = Bbox(self.bbox(tag))
        w, h = self.winfo_width(), self.winfo_height()
        if not force:
            x = max(x, bbox.hwidth)
            x = min(x, w - bbox.hwidth)
            y = max(y, bbox.hheight)
            y = min(y, h - bbox.hheight)
        x_off = x - bbox.center[0]
        y_off = y - bbox.center[1]
        self.move(tag, x_off, y_off)

        # Move input connections
        for predecessor_uid in self._definition.get_gate_predecessors(gate.uid):
            line_ids = self.find_withtag(f'connection:{predecessor_uid}:{gate.uid}')
            for line_id in line_ids:
                x1, y1, x2, y2 = self.coords(line_id)
                self.coords(line_id, x1, y1, x2 + x_off, y2 + y_off)
        
        # Move output connections
        for successor_uid in self._definition.get_gate_successors(gate.uid):
            line_ids = self.find_withtag(f'connection:{gate.uid}:{successor_uid}')
            for line_id in line_ids:
                x1, y1, x2, y2 = self.coords(line_id)
                self.coords(line_id, x1 + x_off, y1 + y_off, x2, y2)
    
    def tick(self):
        self._definition.tick()

        # Update gate input/output colors
        outputs_dict = {}
        for uid, tag in self._components.items():
            gate = self._definition.gates[uid]
            inputs = self._definition.get_gate_inputs(uid)
            outputs = self._definition.get_gate_outputs(uid)
            outputs_dict[uid] = outputs
            for s, io in zip(['input', 'output'], [inputs, outputs]):
                for idx, curr_io in enumerate(io):
                    ids = self.find_withtag(f'{tag}:{s}:{idx}')

                    # Get current value of input/output
                    if type(curr_io) == int:
                        num = curr_io
                    elif curr_io is None:
                        num = None
                    else:
                        if None in curr_io:
                            num = None
                        else:
                            num = max(curr_io)
                    
                    # Get color for input/output
                    if num is None:
                        color = Workspace.ERROR
                    elif num == 1:
                        color = Workspace.ON
                    else:
                        color = Workspace.OFF

                    # Update colors
                    for id in ids:
                        if self.type(id) == 'line' or self.type(id) == 'text':
                            self.itemconfigure(id, fill=color)
                        elif self.itemconfigure(id)['outline'][4] != '':
                            self.itemconfigure(id, outline=color)
        
            # Update sink state colors
            if gate.name == 'Sink':
                state = self._definition.get_gate_state(gate.uid)
                for i, nums in enumerate(state):
                    if gate.dims[i] == 1:
                        self._set_state(gate, i, 0, nums, update_def=False)
                    else:
                        for j in range(gate.dims[i]):
                            if nums is None:
                                num = None
                            else:
                                num = nums[j]
                            self._set_state(gate, i, j, num, update_def=False)

        # Update all connection colors
        for (from_uid, to_uid), pairs in self._definition.connections.items():
            for output_idx, input_idx in pairs:
                output = outputs_dict[from_uid][output_idx]
                if type(output) == int:
                    output = [output]
                for j in range(self._definition.gates[from_uid].output_dims[output_idx]):
                    if output is None:
                        num = None
                    else:
                        num = output[j]

                    # Get color for line
                    if num is None:
                        color = Workspace.ERROR
                    elif num == 1:
                        color = Workspace.ON
                    else:
                        color = Workspace.OFF
                    line_ids = self.find_withtag(f'connection:{from_uid}:{to_uid}:{output_idx}:{input_idx}:{j}')
                    for line_id in line_ids:
                        self.itemconfigure(line_id, fill=color)

    def rename(self, new_name):
        self.itemconfigure(self._title, text=new_name)
        self.update_component(self._definition.source)
        self.update_component(self._definition.sink)
    
    def update_gate_type(self, gate_type):
        for gate in self._definition.gates.values():
            if gate.name == gate_type:
                self.update_component(gate)

    def remove_decoupled_components(self):
        removed = set()
        for uid, tag in self._components.items():
            if uid not in self._definition.gates:
                self.delete(tag)
                self.delete(f'connection:{uid}')
                self.delete(f'virtualconnection:{uid}')

                # Remove input connections
                line_ids = self.find_withtag('connection')
                for line_id in line_ids:
                    tags = self.gettags(line_id)
                    if tags[-1] == 'current':
                        tags = tags[-2].split(':')
                    else:
                        tags = tags[-1].split(':')
                    if int(tags[2]) == uid:
                        self.delete(line_id)

                removed.add(uid)
        for uid in removed:
            del self._components[uid]

    @property
    def name(self):
        return self._definition.name

    def serialize(self):
        obj = {}
        xc, yc = self.canvasx(0), self.canvasy(0)
        for uid, tag in self._components.items():
            x, y = Bbox(self.bbox(tag)).center
            obj[uid] = (x - xc, y - yc)  # Save screen coordinates as canvas coordinates
        return obj
    
    def deserialize(obj, master, definition, project_frame):
        return Workspace(master, definition, project_frame, obj=obj)