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

class Workspace(tk.Canvas):
    ON = '#0099ff'
    OFF = 'white'
    CIRCLERAD = 10

    def __init__(self, master, definition, project_frame, obj={}, **kwargs):
        super().__init__(master, background='white', **kwargs)
        self._project_frame = project_frame
        self._project = project_frame._project
        self._definition = definition
        self._title = self.create_text(0, 0, fill='grey', font=f'Courier 30', text=definition.name)

        self._components = {}
        for uid, gate in definition.gates.items():
            if uid in obj:
                x, y = obj[uid]
                self._components[uid] = self.create_component(x, y, gate)
            else:
                self._components[uid] = self.create_component(300, 300, gate)

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

        # Store tags when right clicking
        self._right_click_tags = None

        self._ws_popup = tk.Menu(self, tearoff=0)
        self._ws_popup.add_command(label='Reset all', command=self.reset_state)

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
        self.bind('<ButtonRelease-1>', self._on_left_release)
        self.bind('<Button-3>', self._on_right_click)
    
    def add_gate_type(self, name):
        try:
            if name == 'Reshaper':
                input_dims = simpledialog.askstring('Inputs', 'Enter dimensions of inputs as integers separated by commas')
                output_dims = simpledialog.askstring('Outputs', 'Enter dimensions of outputs as integers separated by commas')
                input_dims = [int(dim) for dim in input_dims.split(',')]
                output_dims = [int(dim) for dim in output_dims.split(',')]
                args = [input_dims, output_dims]
            else:
                args = []
            gate = self._project[name](*args)
            self._definition.add_gate(gate)
            self._components[gate.uid] = self.create_component(300, 300, gate)
        except ValueError as e:
            simpledialog.messagebox.showerror('Error', str(e))

    def _on_resize(self, e):
        self.coords(self._title, e.width / 2, e.height / 2)

    def _on_left_click(self, e):
        id = self.find_closest(e.x, e.y)

        # Make sure the item contains the point that was clicked
        if Bbox(self.bbox(id)).contains(e.x, e.y):
            tags = self.gettags(id)
        else:
            tags = []
        
        # Clear selected
        self._selected_gate = None
        self._selection_offset = None
        self._selected_input = None

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
                output_bbox = Bbox((e.x, e.y + input_bbox.hheight), input_bbox.width, input_bbox.height)
                connection_tag = f'virtualconnection:{self._selected_gate.uid}:{self._selected_input}'
                output = [0] * self._selected_gate.input_dims[self._selected_input]
                self._create_connection_lines(output_bbox, input_bbox, output, connection_tag)

            elif tags[2] == 'toggle':
                self._toggle(self._selected_gate, int(tags[3]), int(tags[4]))
            else:
                center = Bbox(self.bbox(tag)).center
                self._selection_offset = (center[0] - e.x, center[1] - e.y)
    
    def _get_state(self, gate, i, j):
        state = self._definition.get_gate_state(gate.uid)
        if gate.output_dims[i] == 1:
            return state[i]
        else:
            return state[i][j]

    def _set_state(self, gate, i, j, num, update_def=True):
        if gate.name == 'Source':
            s = 'toggle'
        else:
            s = 'display'
        tag = f'gate:{gate.uid}:{s}:{i}:{j}'

        # Get color
        if num == 1:
            color = Workspace.ON
        else:
            color = Workspace.OFF

        # Update color
        ids = self.find_withtag(tag)
        for id in ids:
            if self.type(id) != 'line' and self.itemconfigure(id)['fill'][4] != '':
                self.itemconfigure(id, fill=color)
        
        # Update gate state
        if update_def:
            state = self._definition.get_gate_state(gate.uid)
            if gate.dims[i] == 1:
                state[i] = num
            else:
                state[i][j] = num
            self._definition.set_gate_state(gate.uid, state)

    def _toggle(self, gate, i, j):
        num = self._get_state(gate, i, j)
        self._set_state(gate, i, j, abs(num - 1))

    def _on_left_move(self, e):
        if self._selected_gate is not None:
            # We are dragging a gate
            if self._selection_offset is not None:
                x_off, y_off = self._selection_offset
                self.move_component_to(self._selected_gate, e.x + x_off, e.y + y_off)
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
                    self.coords(line_id, e.x + x_off, e.y, x2, y2)
            # Check for state updates
            else:
                pass

    def _on_left_release(self, e):
        # Find closest item that is not a line
        ids = []
        for id in self.find_overlapping(e.x, e.y, e.x, e.y):
            if self.type(id) != 'line':
                ids.append(id)
        if len(ids) == 0:
            id = None
        else:
            id = ids[-1]

        # Make sure the item contains the point that was clicked
        if id is not None and Bbox(self.bbox(id)).contains(e.x, e.y):
            tags = self.gettags(id)
        else:
            tags = []
        
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
    
    def _on_right_click(self, e):
        # Find closest item that is not a line
        ids = []
        for id in self.find_overlapping(e.x, e.y, e.x, e.y):
            if self.type(id) != 'line':
                ids.append(id)
        if len(ids) == 0:
            id = None
        else:
            id = ids[-1]

        # Make sure the item contains the point that was clicked
        if id is not None and Bbox(self.bbox(id)).contains(e.x, e.y):
            tags = self.gettags(id)
        else:
            tags = []
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

    def reset_state(self):
        self._definition.reset_state()

        # Update all source components
        for uid in self._definition.gate_types['Source']:
            source = self._definition.gates[uid]
            state = self._definition.get_gate_state(uid)

            for i, output in enumerate(state):
                if type(output) == int:
                    output = [output]
                for j, num in enumerate(output):
                    self._set_state(source, i, j, num)

    def set_right_clicked_label(self):
        tags = self._right_click_tags
        label = simpledialog.askstring('Label', 'Enter label')
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

        r *= 0.8
        point_sets = [
            [x1+r, y1,
            x2-r, y1],
            [x2, y1+r,
            x2, y2-r],
            [x2-r, y2,
            x1+r, y2],
            [x1, y2-r,
            x1, y1+r]
        ]
        r /= 0.8
        corners = [(x2-r, y1+r), (x1+r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]
        bbox = Bbox(2*r, 2*r)

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
            for i, corner in enumerate(corners):
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
            for i, corner in enumerate(corners):
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

        text_id = self.create_text(
            0, 0,
            fill='black',
            font=f'Courier {name_size}',
            text=gate.name,
            tags=get_tags(f'{tag}:name')
        )

        # Create component interior bbox
        if gate.name != 'Source' and gate.name != 'Sink':
            center_bbox = Bbox(self.bbox(text_id)).pad(0, 3)
        else:
            text_bbox = Bbox(self.bbox(text_id)).pad(0, 3)
            if len(gate.dims) == 0:
                state_bbox = Bbox(0, 0)
            else:
                state_bbox = Bbox(circlerad * 2 * sum_dims(gate.dims), circlerad * 2).pad(0, 3)
            if gate.name == 'Source':
                state_bbox -= (0, text_bbox.hheight + state_bbox.hheight)
            else:
                state_bbox += (0, text_bbox.hheight + state_bbox.hheight)
            center_bbox = Bbox(
                (0, (text_bbox.yc + state_bbox.yc) / 2),
                max(text_bbox.width, state_bbox.width),
                text_bbox.height + state_bbox.height
            )

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
        rrec = self.create_round_rectangle(*gate_bbox, circlerad, fill='white', width=3, tags=get_tags(f'{tag}:body'))

        # Reorder text
        self.tag_lower(rrec, text_id)

        if gate.name == 'Source' or gate.name == 'Sink':
            if gate.name == 'Source':
                s = 'toggle'
            else:
                s = 'display'

            # Create boxes to hold the state
            dims = transform_dims(gate.dims)
            state = self._definition.get_gate_state(gate.uid)
            for i, (rdim, dim, acc_dim) in enumerate(zip(gate.dims, dims, accumulate(dims))):
                dbbox = Bbox(circlerad * 2, circlerad * 2).scalex(dim) +\
                        (state_bbox.x1 + 2 * circlerad * (acc_dim - dim) + circlerad * dim, state_bbox.yc)
                width = circlerad * 2 * dim / rdim

                for j in range(rdim):
                    bbox = Bbox(width, circlerad * 2)
                    center = (dbbox.x1 + bbox.width * j + bbox.hwidth, state_bbox.yc)

                    # Get input or output
                    if rdim == 1:
                        num = state[i]
                    else:
                        num = state[i][j]
                    
                    # Get color
                    if num == 1:
                        color = Workspace.ON
                    else:
                        color = Workspace.OFF

                    # Create toggle or display area
                    if width < 8:
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
                            fill=color
                        )

                # Create surrounding rectangle if necessary
                if width < 8:
                    self.create_round_rectangle(
                        *dbbox,
                        3,
                        tags=get_tags(f'{tag}:state')
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
                else:
                    num = max(curr_io)
                
                # Get color for input/output
                if num == 1:
                    color = Workspace.ON
                else:
                    color = 'black'

                # Draw input/output circle
                bbox = circle_bbox.scalex(dim)
                center = (base_bbox.x1 + 2 * circlerad * (acc_dim - dim) + circlerad * dim, base_bbox.yc)
                self.create_round_rectangle(
                    *(bbox + center),
                    circlerad,
                    fill='white',
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

        # Create lines
        connection_tag = f'connection:{from_gate.uid}:{to_gate.uid}:{output_idx}:{input_idx}'
        self._create_connection_lines(output_bbox, input_bbox, output, connection_tag)

        return connection_tag

    def _create_connection_lines(self, output_bbox, input_bbox, output, connection_tag):
        p1 = (output_bbox.x1, output_bbox.y1)
        p2 = (input_bbox.x1, input_bbox.y2 - 1)

        # Make output enumerable
        if type(output) == int:
            output = [output]

        # Create line for each output
        diff = 2 * Workspace.CIRCLERAD
        width = (output_bbox.width - diff) / len(output)
        for i, num in enumerate(output):
            if num == 1:
                color = Workspace.ON
            else:
                color = 'black'
            
            # Create line offset
            off = i * width + (width + diff) / 2

            # Create line
            self.create_line(
                p1[0] + off, p1[1], p2[0] + off, p2[1],
                fill=color,
                tags=get_tags(f'{connection_tag}:{i}')
            )
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
                        curr_io = [curr_io]
                    num = max(curr_io)
                    
                    # Get color for input/output
                    if num == 1:
                        color = Workspace.ON
                    else:
                        color = 'black'

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
                        for j, num in enumerate(nums):
                            self._set_state(gate, i, j, num, update_def=False)

        # Update all connection colors
        for (from_uid, to_uid), pairs in self._definition.connections.items():
            for output_idx, input_idx in pairs:
                output = outputs_dict[from_uid][output_idx]
                if type(output) == int:
                    output = [output]
                for j, num in enumerate(output):
                    # Get color for line
                    if num == 1:
                        color = Workspace.ON
                    else:
                        color = 'black'
                    line_ids = self.find_withtag(f'connection:{from_uid}:{to_uid}:{output_idx}:{input_idx}:{j}')
                    for line_id in line_ids:
                        self.itemconfigure(line_id, fill=color)

    def rename(self, new_name):
        self.itemconfigure(self._title, text=new_name)
    
    def update_gate_type(self, gate_type):
        for gate in self._definition.gates.values():
            if gate.name == gate_type:
                self.update_component(gate)

    def serialize(self):
        obj = {}
        for uid, tag in self._components.items():
            obj[uid] = Bbox(self.bbox(tag)).center
        return obj
    
    def deserialize(obj, master, definition, project_frame):
        return Workspace(master, definition, project_frame, obj=obj)