import json
import time
from typing import Any
import dearpygui.dearpygui as dpg
import os
import importlib

from NodeEditor.Core.Node import Node

class NodeEditor:

    def __init__(self, nodes_dir: str = "NodeEditor/Nodes") -> None:
        
        self.nodes_dir = nodes_dir
        
        self.available_nodes: list = []
        self.nodes: list[Node] = []
        self._menu_node_setup: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self.node_links: list[tuple[int | str, int, int]] = []  # (link_id, start_attr, end_attr)
        self.node_editor = dpg.generate_uuid()
        self.right_click_menu = dpg.generate_uuid()
        self._copied_nodes_data = None
        self._node_types: list[str] = ["any"]
        self._undo_stack: list = []
        self._redo_stack: list = []
        
        self._auto_load_available_nodes()
        
    def save_workspace(self, file_path: str = "workspace.json"):
        workspace_data = {
            "nodes": [],
            "links": [],
        }
        # Build a mapping from attribute IDs to node indices and input/output indices
        attr_id_to_node = {}
        for node_index, node in enumerate(self.nodes):
            node_data = {
                "node_class": node.__class__.__name__,
                "label": node.label,
                "position": node._node_pos,
                "state": node.on_save(),
            }
            workspace_data["nodes"].append(node_data)
            # Map outputs
            for output_idx, output in enumerate(node.outputs):
                attr_id_to_node[output.id] = {
                    "node_index": node_index,
                    "output_idx": output_idx
                }
            # Map inputs
            for input_idx, input_ in enumerate(node.inputs):
                attr_id_to_node[input_.id] = {
                    "node_index": node_index,
                    "input_idx": input_idx
                }
        # Save links using node indices and input/output indices
        for link_id, start_attr, end_attr in self.node_links:
            start_info = attr_id_to_node.get(start_attr)
            end_info = attr_id_to_node.get(end_attr)
            if start_info and end_info:
                link_data = {
                    "start_node_index": start_info["node_index"],
                    "start_output_idx": start_info["output_idx"],
                    "end_node_index": end_info["node_index"],
                    "end_input_idx": end_info["input_idx"],
                }
                workspace_data["links"].append(link_data)
        # Save to file
        with open(file_path, 'w') as f:
            json.dump(workspace_data, f)

    def load_workspace(self, file_path: str = "workspace.json"):
        self.clear_workspace()
        with open(file_path, 'r') as f:
            workspace_data = json.load(f)

        # Load nodes
        for node_data in workspace_data["nodes"]:
            node_class_name = node_data["node_class"]
            node_class = next(
                (cls for cls in self.available_nodes if cls.__name__ == node_class_name), None
            )
            if node_class:
                node = node_class()
                self._add_node(node)
                node.on_load(node_data.get("state", {}))
                # Set node position
                if "position" in node_data:
                    node._set_node_pos(*node_data["position"])
            else:
                print(f"Error: Node class '{node_class_name}' not found.")

        # Load links
        for link_data in workspace_data["links"]:
            start_node_index = link_data["start_node_index"]
            start_output_idx = link_data["start_output_idx"]
            end_node_index = link_data["end_node_index"]
            end_input_idx = link_data["end_input_idx"]

            if (start_node_index < len(self.nodes)) and (end_node_index < len(self.nodes)):
                start_node = self.nodes[start_node_index]
                end_node = self.nodes[end_node_index]

                # Get attribute IDs
                start_attr = start_node.outputs[start_output_idx].id
                end_attr = end_node.inputs[end_input_idx].id

                # Create link
                link_id = dpg.add_node_link(start_attr, end_attr, parent=self.node_editor)
                self.node_links.append((link_id, start_attr, end_attr))

                # Update node connections
                start_node.outputs[start_output_idx].connected_nodes.append(end_node)
                end_node.inputs[end_input_idx].connected_node = start_node
                end_node.inputs[end_input_idx].connected_output_idx = start_output_idx
            else:
                print("Error: Invalid node indices in link data.")
                
        # Trigger updates after all connections are established
        # Process source nodes (nodes with no inputs or unconnected inputs) first
        source_nodes = []
        for node in self.nodes:
            has_all_inputs_connected = all(input_.connected_node is not None for input_ in node.inputs)
            if not node.inputs or not has_all_inputs_connected:
                source_nodes.append(node)
        
        # Update the source nodes first to start the data flow
        for node in source_nodes:
            node.force_update()
        
    def clear_workspace(self):
        # Delete all the links
        for link_id, _, _ in self.node_links:
            dpg.delete_item(link_id)
            
        # Delete all the nodes
        for node in self.nodes:
            dpg.delete_item(node._node_id)
            
        self.nodes = []
        self.node_links = []
        
    def _auto_load_available_nodes(self):
        
        file_path = self.nodes_dir
        import_path = file_path.replace("/", ".")
        files = os.listdir(file_path)
        
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                file = file.replace(".py", "")
                module = importlib.import_module(f"{import_path}.{file}")
                class_name = file
                class_ = getattr(module, class_name)
                self.available_nodes.append(class_)
        
    def _setup_menu(self):
        for node_class in self.available_nodes:
            temp_node: Node = node_class()
            category = temp_node.catagory
            main_category, _, sub_category = category.partition("/")

            if main_category not in self._menu_node_setup:
                self._menu_node_setup[main_category] = {}

            if sub_category not in self._menu_node_setup[main_category]:
                self._menu_node_setup[main_category][sub_category] = []

            node_info = {
                "name": temp_node.label,
                "user_data": node_class,
            }

            self._menu_node_setup[main_category][sub_category].append(node_info)
        
    def _link_nodes_callback(self, sender, app_data):
        self.push_undo_state()
        # app_data contains [start_attr, end_attr]
        start_attr, end_attr = app_data
        link_id = dpg.generate_uuid()

        # Set up the connections between nodes
        start_node, start_output_idx = self._find_node_output_by_id(start_attr)
        end_node, end_input_idx = self._find_node_input_by_id(end_attr)
        
        if start_output_idx is None or end_input_idx is None:
            return

        if start_node and end_node:
            output_type = start_node.outputs[start_output_idx].type
            input_type = end_node.inputs[end_input_idx].type
            if (output_type != "any"
                and input_type != "any"
                and output_type != input_type):
                print(f"Error: Type mismatch ({output_type} -> {input_type}). Link aborted.")
                return

        dpg.add_node_link(start_attr, end_attr, parent=sender, tag=link_id)
        self.node_links.append((link_id, start_attr, end_attr))
        
        if start_node and end_node and start_output_idx is not None and end_input_idx is not None:
            start_node.outputs[start_output_idx].connected_nodes.append(end_node)
            end_node.inputs[end_input_idx].connected_node = start_node
            end_node.inputs[end_input_idx].connected_output_idx = start_output_idx
            
            # Immediately trigger an update for better responsiveness
            start_node.force_update()
        else:
            print("Error: Nodes not found for linking.")
        
    def _delink_nodes_callback(self, sender, app_data):
        self.push_undo_state()
        # app_data contains link_id
        link_id = app_data
        for idx, (l_id, start_attr, end_attr) in enumerate(self.node_links):
            if l_id == link_id:
                dpg.delete_item(link_id)
                start_node, start_output_idx = self._find_node_output_by_id(start_attr)
                end_node, end_input_idx = self._find_node_input_by_id(end_attr)
                if start_node and end_node and start_output_idx is not None and end_input_idx is not None:
                    if end_node in start_node.outputs[start_output_idx].connected_nodes:
                        start_node.outputs[start_output_idx].connected_nodes.remove(end_node)
                    if end_node.inputs[end_input_idx].connected_node == start_node:
                        end_node.inputs[end_input_idx].connected_node = None
                        end_node.inputs[end_input_idx].latest_data = None
                        end_node.inputs[end_input_idx].connected_output_idx = None
                self.node_links.pop(idx)
                
                # Update the end node to show warning if needed
                if end_node:
                    end_node._on_warning()
                break
        
    def compose(self, parent: str | int = ""):
        with dpg.node_editor(callback=self._link_nodes_callback, delink_callback=self._delink_nodes_callback, tag=self.node_editor, parent=parent):                            
            for node in self.nodes:
                for output in node.outputs:
                    if output.type not in self._node_types:
                        self._node_types.append(output.type)
                for input_ in node.inputs:
                    if input_.type not in self._node_types:
                        self._node_types.append(input_.type)
                node._compose(types=self._node_types)
                
    def _add_node(self, node: Node):
        self.push_undo_state()
        node._node_delete_callback = self._node_delete_callback
        node._node_duplicate_callback = self._node_duplicate_callback
        node.on_init()
        self.nodes.append(node)
        for output in node.outputs:
            if output.type not in self._node_types:
                self._node_types.append(output.type)
        for input_ in node.inputs:
            if input_.type not in self._node_types:
                self._node_types.append(input_.type)
        node._compose(parent=self.node_editor, types=self._node_types)
        
    def _delete_selected_node(self):
        self.push_undo_state()
        selected = dpg.get_selected_nodes(self.node_editor)
        for node_id in selected:
            self._node_delete_callback(None, None, node_id)

    def _node_duplicate_callback(self, node):
        self.push_undo_state()
        # Duplicate the node
        node_object = node
        
        for n in self.available_nodes:
            if n.__name__ == node_object.__class__.__name__:
                new_node = n()
                break
        else:
            print("Error: Node class not found.")
            return
        try:
            new_node.on_load(node_object.on_save())
        except Exception as e:
            pass
        
        self._add_node(new_node)
        pos = node_object._node_pos
        pos = (pos[0] + 20, pos[1] + 20)
        new_node._set_node_pos(*pos)
        
    def _node_delete_callback(self, sender, app_data, user_data):
        self.push_undo_state()
        node_id = user_data
        node = self._find_node_by_id(node_id)
        if node:
            # Remove links associated with this node
            links_to_remove = []
            for link_id, start_attr, end_attr in self.node_links:
                if dpg.get_item_parent(start_attr) == node_id or dpg.get_item_parent(end_attr) == node_id:
                    links_to_remove.append(link_id)
            for link_id in links_to_remove:
                self._delink_nodes_callback(None, link_id)
            # Delete the node
            node._close_preview(None, None)
            dpg.delete_item(node_id)
            self.nodes.remove(node)
        
    def _find_node_by_id(self, node_id):
        for node in self.nodes:
            if node._node_id == node_id:
                return node
        return None

    def _find_node_output_by_id(self, attribute_id):
        for node in self.nodes:
            for idx, output in enumerate(node.outputs):
                if output.id == attribute_id:
                    return node, idx
        return None, None

    def _find_node_input_by_id(self, attribute_id):
        for node in self.nodes:
            for idx, input_ in enumerate(node.inputs):
                if input_.id == attribute_id:
                    return node, idx
        return None, None        
        
    def _menu_callback(self, sender, user_data, app_data):
        node_class = app_data
        node = node_class()
        self._add_node(node)
        
    def _menu_callback_right_click(self, sender, user_data, app_data):
        node: Node = app_data()
        self._add_node(node)
        dpg.configure_item(self.right_click_menu, show=False)
        mouse_position = dpg.get_mouse_pos(local=False)
        node._set_node_pos(mouse_position[0] - 25, mouse_position[1] - 50)
        
    def right_click_cb(self, sender, app_data):
        # Check if the right click is in a node
        for node in self.nodes:
            node_pos = node._node_pos
            node_size = node._node_size
            mouse_pos = dpg.get_mouse_pos(local=False)
            
            if node_pos[0] < mouse_pos[0] < node_pos[0] + node_size[0] and node_pos[1] < mouse_pos[1] < node_pos[1] + node_size[1]:
                return
        
        mice_pos = dpg.get_mouse_pos(local=False)
        
        # Adjust mouse position by the node editor's position
        node_editor_pos = dpg.get_item_pos(self.node_editor)
        adjusted_mouse_pos = [mice_pos[0] - node_editor_pos[0], mice_pos[1] - node_editor_pos[1]]
        adjusted_mouse_pos = [float(i) for i in adjusted_mouse_pos]
        
        dpg.configure_item(self.right_click_menu, show=True)
        dpg.set_item_pos(self.right_click_menu, adjusted_mouse_pos)
        
    def left_click_cb(self, sender, app_data):
        if not dpg.get_item_state(self.right_click_menu).get("visible", False):
            return
        window_pos = dpg.get_item_pos(self.right_click_menu)
        window_size = dpg.get_item_rect_size(self.right_click_menu)
        mouse_pos = dpg.get_mouse_pos(local=False)
        
        if window_pos[0] + window_size[0] < mouse_pos[0]:
            return
        
        # Check if the left click is in the window
        if window_pos[0] < mouse_pos[0] < window_pos[0] + window_size[0] and window_pos[1] < mouse_pos[1] < window_pos[1] + window_size[1]:
            return
        
        dpg.configure_item(self.right_click_menu, show=False)
        
    def control_click_cb(self, sender, app_data):
        if not dpg.is_key_down(dpg.mvKey_LControl):
            return
        # get the node that was clicked on
        # Iterate in reverse order to prioritize nodes drawn on top
        for node in reversed(self.nodes):
            node_pos = node._node_pos
            node_size = node._node_size
            mouse_pos = dpg.get_mouse_pos(local=False)
            
            if node_pos[0] < mouse_pos[0] < node_pos[0] + node_size[0] and node_pos[1] < mouse_pos[1] < node_pos[1] + node_size[1]:
                node._view()
                return
        
    def copy_selected_nodes(self):
        selected = dpg.get_selected_nodes(self.node_editor)
        node_indices = []
        for idx, node in enumerate(self.nodes):
            if node._node_id in selected:
                node_indices.append(idx)
        # Gather node/link data
        workspace_data = {"nodes": [], "links": []}
        attr_id_to_node_idx = {}
        for idx in node_indices:
            node = self.nodes[idx]
            node_data = {
                "class": node.__class__.__name__,
                "state": node.on_save(),
                "position": node._node_pos
            }
            workspace_data["nodes"].append(node_data)
            for o_idx, o in enumerate(node.outputs):
                attr_id_to_node_idx[o.id] = (idx, "out", o_idx)
            for i_idx, i_ in enumerate(node.inputs):
                attr_id_to_node_idx[i_.id] = (idx, "in", i_idx)
        for link_id, start_attr, end_attr in self.node_links:
            s_info = attr_id_to_node_idx.get(start_attr)
            e_info = attr_id_to_node_idx.get(end_attr)
            if s_info and e_info:
                workspace_data["links"].append({
                    "start_node_idx": node_indices.index(s_info[0]),
                    "start_output_idx": s_info[2],
                    "end_node_idx": node_indices.index(e_info[0]),
                    "end_input_idx": e_info[2]
                })
        self._copied_nodes_data = workspace_data

    def paste_copied_nodes(self):
        if not self._copied_nodes_data:
            return
        
        mouse_x, mouse_y = dpg.get_mouse_pos(local=False)
        
        # Find bounding box of copied nodes
        min_x = float('inf')
        min_y = float('inf')
        for node_info in self._copied_nodes_data["nodes"]:
            x, y = node_info["position"]
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y

        # Offset to place them around the mouse position
        offset_x = mouse_x - min_x
        offset_y = mouse_y - min_y
        
        # Clear current selection
        dpg.clear_selected_nodes(self.node_editor)
        
        new_nodes = []
        for node_info in self._copied_nodes_data["nodes"]:
            node_class = next(
                (cls for cls in self.available_nodes if cls.__name__ == node_info["class"]), 
                None
            )
            if node_class:
                node = node_class()
                node.on_load(node_info["state"])
                old_pos = node_info["position"]
                new_pos = (old_pos[0] + offset_x, old_pos[1] + offset_y)
                self._add_node(node)
                node._set_node_pos(*new_pos)
                
                new_nodes.append(node)

        for link_info in self._copied_nodes_data["links"]:
            start_node = new_nodes[link_info["start_node_idx"]]
            end_node = new_nodes[link_info["end_node_idx"]]
            start_attr = start_node.outputs[link_info["start_output_idx"]].id
            end_attr = end_node.inputs[link_info["end_input_idx"]].id
            link_id = dpg.add_node_link(start_attr, end_attr, parent=self.node_editor)
            self.node_links.append((link_id, start_attr, end_attr))

        # Optionally clear buffer after paste
        # self._copied_nodes_data = None

    def copy_cb(self, sender, app_data):
        if dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_down(dpg.mvKey_C):
            self.copy_selected_nodes()
        elif dpg.is_key_down(dpg.mvKey_LControl) and dpg.is_key_down(dpg.mvKey_V):
            self.paste_copied_nodes()

    def push_undo_state(self):
        # Store the current workspace in undo stack
        workspace_data = self._serialize_workspace()
        self._undo_stack.append(workspace_data)
        # Clear redo stack because new action breaks redo chain
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack:
            return
        # Save current state to redo
        current_state = self._serialize_workspace()
        self._redo_stack.append(current_state)
        # Load previous state
        prev_state = self._undo_stack.pop()
        self._deserialize_workspace(prev_state)

    def redo(self):
        if not self._redo_stack:
            return
        # Save current state to undo
        current_state = self._serialize_workspace()
        self._undo_stack.append(current_state)
        # Load redo state
        next_state = self._redo_stack.pop()
        self._deserialize_workspace(next_state)

    def _serialize_workspace(self):
        # Use existing save logic to get a workspace dict
        workspace_data = {
            "nodes": [],
            "links": []
        }
        # Build a mapping from attribute IDs to node indices and input/output indices
        attr_id_to_node = {}
        for node_index, node in enumerate(self.nodes):
            node_data = {
                "node_class": node.__class__.__name__,
                "label": node.label,
                "position": node._node_pos,
                "state": node.on_save(),
            }
            workspace_data["nodes"].append(node_data)
            # Map outputs
            for output_idx, output in enumerate(node.outputs):
                attr_id_to_node[output.id] = {
                    "node_index": node_index,
                    "output_idx": output_idx
                }
            # Map inputs
            for input_idx, input_ in enumerate(node.inputs):
                attr_id_to_node[input_.id] = {
                    "node_index": node_index,
                    "input_idx": input_idx
                }
        # Save links using node indices and input/output indices
        for link_id, start_attr, end_attr in self.node_links:
            start_info = attr_id_to_node.get(start_attr)
            end_info = attr_id_to_node.get(end_attr)
            if start_info and end_info:
                link_data = {
                    "start_node_index": start_info["node_index"],
                    "start_output_idx": start_info["output_idx"],
                    "end_node_index": end_info["node_index"],
                    "end_input_idx": end_info["input_idx"],
                }
                workspace_data["links"].append(link_data)
        return workspace_data

    def _deserialize_workspace(self, workspace_data):
        self.clear_workspace()
        # Load nodes
        for node_data in workspace_data["nodes"]:
            node_class_name = node_data["node_class"]
            node_class = next(
                (cls for cls in self.available_nodes if cls.__name__ == node_class_name), None
            )
            if node_class:
                node = node_class()
                node.on_load(node_data.get("state", {}))
                self._add_node(node)
                # Set node position
                if "position" in node_data:
                    node._set_node_pos(*node_data["position"])
            else:
                print(f"Error: Node class '{node_class_name}' not found.")

        # Load links
        for link_data in workspace_data["links"]:
            start_node_index = link_data["start_node_index"]
            start_output_idx = link_data["start_output_idx"]
            end_node_index = link_data["end_node_index"]
            end_input_idx = link_data["end_input_idx"]

            if (start_node_index < len(self.nodes)) and (end_node_index < len(self.nodes)):
                start_node = self.nodes[start_node_index]
                end_node = self.nodes[end_node_index]

                # Get attribute IDs
                start_attr = start_node.outputs[start_output_idx].id
                end_attr = end_node.inputs[end_input_idx].id

                # Create link
                link_id = dpg.add_node_link(start_attr, end_attr, parent=self.node_editor)
                self.node_links.append((link_id, start_attr, end_attr))

                # Update node connections
                start_node.outputs[start_output_idx].connected_nodes.append(end_node)
                end_node.inputs[end_input_idx].connected_node = start_node
            else:
                print("Error: Invalid node indices in link data.")
                
        # Trigger updates after all connections are established
        # Process source nodes (nodes with no inputs or unconnected inputs) first
        source_nodes = []
        for node in self.nodes:
            has_all_inputs_connected = all(input_.connected_node is not None for input_ in node.inputs)
            if not node.inputs or not has_all_inputs_connected:
                source_nodes.append(node)
        
        # Update the source nodes first to start the data flow
        for node in source_nodes:
            node.force_update()

    def start(self):
        self._setup_menu()
        
        with dpg.handler_registry():
            dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=self._delete_selected_node)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, callback=self.right_click_cb)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=self.left_click_cb)
            dpg.add_key_press_handler(dpg.mvKey_LControl)
            dpg.add_key_press_handler(dpg.mvKey_C, callback=self.copy_cb)
            dpg.add_key_press_handler(dpg.mvKey_V, callback=self.copy_cb)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=self.control_click_cb)
            dpg.add_key_press_handler(
                key=dpg.mvKey_Z, 
                callback=lambda: self.undo() if dpg.is_key_down(dpg.mvKey_LControl) else None
            )
            dpg.add_key_press_handler(
                key=dpg.mvKey_Y, 
                callback=lambda: self.redo() if dpg.is_key_down(dpg.mvKey_LControl) else None
            )
            
            
        with dpg.window(label="Right click window", modal=False, show=False, tag=self.right_click_menu, no_title_bar=True):
            # Add the nodes to the right click menu
            for catagory, nodes in self._menu_node_setup.items():
                    with dpg.menu(label=catagory):
                        
                        for sub_catagory, nodes in nodes.items():
                            if sub_catagory == "":
                                for node in nodes:
                                    dpg.add_menu_item(label=node["name"], callback=self._menu_callback_right_click, user_data=(node["user_data"]))
                            else:
                                with dpg.menu(label=sub_catagory):
                                    for node in nodes:
                                        dpg.add_menu_item(label=node["name"], callback=self._menu_callback_right_click, user_data=(node["user_data"]))
                
        with dpg.window(label="Node Editor") as main_window:
            # dpg.bind_theme(create_star_trek_theme())
            
            with dpg.menu_bar():
                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(label="Clear Nodes", callback=self.clear_workspace)
                    dpg.add_menu_item(label="Save Workspace", callback=lambda: self.save_workspace())
                    dpg.add_menu_item(label="Load Workspace", callback=lambda: self.load_workspace())
                    
                for category, sub_categories in self._menu_node_setup.items():
                    with dpg.menu(label=category):
                        for sub_category, nodes in sub_categories.items():
                            if sub_category:
                                with dpg.menu(label=sub_category):
                                    for node in nodes:
                                        dpg.add_menu_item(
                                            label=node["name"],
                                            callback=self._menu_callback,
                                            user_data=node["user_data"],
                                        )
                            else:
                                for node in nodes:
                                    dpg.add_menu_item(
                                        label=node["name"],
                                        callback=self._menu_callback,
                                        user_data=node["user_data"],
                                    )
                
            self.compose()
            
        dpg.create_viewport(title="Main Viewport")
        dpg.set_primary_window(main_window, True)
        dpg.setup_dearpygui()
        
        
        # dpg.show_style_editor()
        
        dpg.show_viewport()
        # dpg.start_dearpygui()
        while dpg.is_dearpygui_running():
            for n in self.nodes:
                n._render_viewer()
            dpg.render_dearpygui_frame()
            
        dpg.destroy_context()