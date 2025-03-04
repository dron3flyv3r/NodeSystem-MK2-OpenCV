import threading
import time
from typing import Any, Callable, Literal, Optional
import dearpygui.dearpygui as dpg
import copy
import traceback
import concurrent.futures as future
from abc import ABC, abstractmethod

from NodeEditor.Core.NodePackage import NodePackage
from NodeEditor.Core.Themes import *


class NodeInput:
    def __init__(self, label: str, type: str = "any", default_data: Any = None):
        self.label = label
        self.type = type
        self.connected_node: Node | None = None
        self.latest_data: NodePackage | None = None
        self.id = dpg.generate_uuid()
        self.connected_output_idx: int | None = None


class NodeOutput:
    def __init__(self, label: str, type: str = "any"):
        self.label = label
        self.type = type
        self.connected_nodes: list[Node] = []
        self.id = dpg.generate_uuid()


class Node(ABC):
    def __init__(self, label: str, catagory: str, max_width: int = 100) -> None:
        self.label = label
        self.catagory = catagory
        self._max_width = max(max_width, 100)

        self.inputs: list[NodeInput] = []
        self.outputs: list[NodeOutput] = []

        self._node_id = dpg.generate_uuid()
        self._error_text_id = dpg.generate_uuid()
        self._time_text_id = dpg.generate_uuid()
        self._skip_execution: bool = False
        self._keep_error: bool = False
        self._node_preview_window_id = dpg.generate_uuid()
        self._node_editor_id: str | int | None = None

        self._custom_outputs: list[tuple[Callable[[Any], Any], str]] = []

        self._last_update_call = 0
        self._min_delay = 50  # ms
        self._update_call: bool = False

        self._node_delete_callback: Callable = lambda *args: None
        self._node_duplicate_callback: Callable = lambda *args: None

        threading.Thread(target=self._update_thread, daemon=True).start()

    def on_init(self):
        pass

    def on_load(self, data: dict):
        pass

    def on_save(self) -> dict:
        return {}

    def add_custom_output(self, call_back: Callable[[Any], Any], label: str = ""):
        self._custom_outputs.append((call_back, label))

    def add_input(self, label: str = "", type: str = "any", default_data: Optional[NodePackage] = None) -> int:
        node_input = NodeInput(label.capitalize() or f"Input {len(self.inputs)+1}", type.lower())
        node_input.latest_data = default_data
        idx = len(self.inputs)
        self.inputs.append(node_input)
        return idx

    def add_output(self, label: str = "", type: str = "any") -> int:
        node_output = NodeOutput(label.capitalize() or f"Output {len(self.outputs)+1}", type.lower())
        idx = len(self.outputs)
        self.outputs.append(node_output)
        return idx

    @abstractmethod
    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        return inputs

    def compose(self):
        pass

    def reset(self):
        pass

    def update(self):
        self._update_call = True
        self._last_update_call = time.time()

    def viewer(self, outputs: list[NodePackage]):
        for o in outputs:
            with dpg.group(horizontal=True):
                self.view(o)
                
    def view(self, output: NodePackage):
        raise NotImplementedError("View not implemented")

    def _close_preview(self, sender, app_data):
        if dpg.does_item_exist(self._node_preview_window_id):
            dpg.delete_item(self._node_preview_window_id)

    def _view(self, outputs: list[NodePackage] | None = None):

        if self._node_editor_id is None:
            return

        if len(self.outputs) == 0:
            return

        if outputs is None:
            inputs = []
            for node_input in self.inputs:
                if node_input.connected_node is None or node_input.latest_data is None:
                    self._on_warning()
                    return
                inputs.append(node_input.latest_data)

            if len(inputs) != len(self.inputs):
                return
            outputs = self.execute(copy.deepcopy(inputs))

        if len(outputs) != len(self.outputs):
            return

        if dpg.does_item_exist(self._node_preview_window_id):
            dpg.delete_item(self._node_preview_window_id, children_only=True)
        else:
            dpg.add_node(
                label=f"{self.label} Preview",
                parent=self._node_editor_id,
                tag=self._node_preview_window_id,
            )

        with dpg.node_attribute(
            attribute_type=dpg.mvNode_Attr_Static, parent=self._node_preview_window_id
        ):
            dpg.add_button(label="Close", callback=self._close_preview)

        # Rerender outputs
        try:
            for output in outputs:
                with dpg.node_attribute(
                    attribute_type=dpg.mvNode_Attr_Static,
                    parent=self._node_preview_window_id,
                ):
                    self.view(output)
        except NotImplementedError:
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Static,
                parent=self._node_preview_window_id,
            ):
                self.viewer(outputs)

    def _render_viewer(self):
        if not dpg.does_item_exist(self._node_preview_window_id):
            return

        # Do the the node is north of the current node make sure that the size of the view node is the don't overlap have a padding of 10
        node_pos = self._node_pos
        node_size = self._node_size
        view_pos = dpg.get_item_pos(self._node_preview_window_id)
        view_size = dpg.get_item_rect_size(self._node_preview_window_id)

        dpg.set_item_pos(
            self._node_preview_window_id,
            [node_pos[0], node_pos[1] - view_size[1] - 10],
        )


    def _update_thread(self):
        while True:
            self._update()
            time.sleep(0.01) if self._update_call else time.sleep(0.2)

    def _update(self):
        if (
            time.time() - self._last_update_call > self._min_delay * 0.001
            and self._update_call
        ):
            self._update_call = False
            self._call_output_nodes()

    def force_update(self):
        self._call_output_nodes()

    def _call_output_nodes(self):
        self._keep_error = False

        inputs = []
        for node_input in self.inputs:
            if node_input.latest_data is None:
                self._on_warning()
                return
            inputs.append(node_input.latest_data)

        try:
            try:
                dpg.bind_item_theme(self._node_id, executing_theme)
            except Exception as e:
                print("Error setting theme:", e)
            s_time = time.time()
            outputs = (
                self.execute(copy.deepcopy(inputs))
                if not self._skip_execution
                else inputs
            )
            self._on_success() if not self._keep_error else None
            dpg.set_value(
                self._time_text_id,
                f"{(time.time()-s_time)*1000:.2f}ms",
            )
        except Exception as e:
            traceback.print_exc()
            self.on_error(str(e))
            return

        if dpg.does_item_exist(self._node_preview_window_id):
            self._view(outputs)

        futures = []
        with future.ThreadPoolExecutor() as executor:
            for idx, output_data in enumerate(outputs):
                if idx < len(self.outputs):
                    node_output = self.outputs[idx]
                    for connected_node in node_output.connected_nodes:
                        connected_node._set_latest_input(output_data, self, idx)
                        futures.append(
                            executor.submit(connected_node._call_output_nodes)
                        )
        future.wait(futures, return_when=future.ALL_COMPLETED)

    def _set_latest_input(
        self, data: NodePackage, from_node: "Node", from_output_idx: int
    ):
        for node_input in self.inputs:
            if (
                node_input.connected_node == from_node
                and node_input.connected_output_idx == from_output_idx
            ):
                node_input.latest_data = data
                break

    def _compose(self, parent: int | str = 0, types: list[str] = []):
        shapes = [
            dpg.mvNode_PinShape_CircleFilled,
            dpg.mvNode_PinShape_Quad,
            dpg.mvNode_PinShape_Triangle,
            dpg.mvNode_PinShape_QuadFilled,
            dpg.mvNode_PinShape_Circle,
            dpg.mvNode_PinShape_TriangleFilled,
        ]
        
        self._node_editor_id = parent
        with dpg.node(label=self.label, tag=self._node_id, parent=parent):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                # add an "execute" button if there are no inputs
                if not self.inputs:
                    dpg.add_button(
                        label="Execute",
                        callback=self._call_output_nodes,
                        user_data=self._node_id,
                    )

                dpg.add_checkbox(
                    label="Skip Execution",
                    default_value=False,
                    callback=self._toggle_skip_execution,
                )
                dpg.add_text("", wrap=self._max_width, tag=self._error_text_id)

            # Compose input attributes
            for node_input in self.inputs:
                shape = 0
                if node_input.type in types:
                    shape = types.index(node_input.type) % len(shapes)
                    
                with dpg.node_attribute(
                    label=node_input.label,
                    attribute_type=dpg.mvNode_Attr_Input,
                    tag=node_input.id,
                    shape=shapes[shape],
                ):
                    dpg.add_text(node_input.label)

            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=10)
                self.compose()
                dpg.add_spacer(height=10)
                dpg.add_text("", wrap=self._max_width, tag=self._time_text_id)
                

            # Compose output attributes
            for node_output in self.outputs:
                shape = 0
                if node_output.type in types:
                    shape = types.index(node_output.type) % len(shapes)
                    
                with dpg.node_attribute(
                    label=node_output.label,
                    attribute_type=dpg.mvNode_Attr_Output,
                    tag=node_output.id,
                    shape=shapes[shape],
                ):
                    dpg.add_text(node_output.label, indent=self._max_width)

            with dpg.popup(self._node_id):
                dpg.add_menu_item(
                    label="Delete",
                    callback=self._node_delete_callback or (lambda *args: None),
                    user_data=self._node_id,
                )
                dpg.add_menu_item(
                    label="Duplicate",
                    callback=lambda: self._node_duplicate_callback(self),
                    user_data=self._node_id,
                )
                dpg.add_menu_item(label="Force Update", callback=self.force_update)
                dpg.add_menu_item(label="Reset", callback=self.reset)

    def on_error(self, error: str = ""):
        self._keep_error = True
        try:
            dpg.bind_item_theme(self._node_id, error_theme)
        except Exception as e:
            print("Error setting theme:", e)
        if error:
            dpg.set_value(self._error_text_id, error)

    def _on_warning(self):
        try:
            dpg.bind_item_theme(self._node_id, warning_theme)
        except Exception as e:
            print("Error setting theme:", e)
        dpg.set_value(self._error_text_id, "")

    def _on_success(self):
        try:
            dpg.bind_item_theme(self._node_id, success_theme)
        except Exception as e:
            print("Error setting theme:", e)
        dpg.set_value(self._error_text_id, "")

    def remove_output_node(self, output_idx: int, node: "Node"):
        if output_idx < len(self.outputs):
            if node in self.outputs[output_idx].connected_nodes:
                self.outputs[output_idx].connected_nodes.remove(node)
        else:
            print("Invalid output index")

    def remove_input_node(self, input_idx: int):
        if input_idx < len(self.inputs):
            self.inputs[input_idx].connected_node = None
            self.inputs[input_idx].latest_data = None
        else:
            print("Invalid input index")

    def _toggle_skip_execution(self):
        self._skip_execution = not self._skip_execution
        self.update()

    @property
    def _node_pos(self):
        return dpg.get_item_pos(self._node_id)

    @property
    def _node_size(self):
        return dpg.get_item_rect_size(self._node_id)

    def _set_node_pos(self, x: float, y: float):
        dpg.set_item_pos(self._node_id, [x, y])

    def to_dict(self):
        return {
            "label": self.label,
            "catagory": self.catagory,
            "max_width": self._max_width,
            "inputs": [input_.label for input_ in self.inputs],
            "outputs": [output.label for output in self.outputs],
            "position": self._node_pos,
            "state": self.on_save(),  # Custom state saved by subclass
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(
            data["label"], data["catagory"], max_width=data.get("max_width", 100)
        )
        for input_label in data.get("inputs", []):
            node.add_input(input_label)
        for output_label in data.get("outputs", []):
            node.add_output(output_label)
        if "position" in data:
            node._set_node_pos(*data["position"])
        node.on_load(data.get("state", {}))
        return node

    def __str__(self) -> str:
        return f"{self.label} ({self._node_id})"

    def __repr__(self) -> str:
        return self.__str__()
