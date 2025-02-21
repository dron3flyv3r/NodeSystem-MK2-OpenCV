# Node System MK2

This project is a node-based editor built using Dear PyGui. It allows users to create, connect, and manage nodes that perform various operations. The system is designed to be extensible, allowing developers to create custom nodes with specific functionalities.

## Features

- Create and manage nodes
- Connect nodes to pass data between them
- Save and load workspace configurations
- Customizable node operations
- Copy/Past
- A preview window to visualize the output of a node (control + left click on a node)
- Type security for the nodes inputs and outputs
- undo/redo

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/dron3flyv3r/NodeSystem-MK2.git
    cd NodeSystem-MK2
    ```

2. Install the required dependencies:
    ```sh
    pip install dearpygui
    ```

## Usage

To start the node editor, run the following command:
```sh
python NodeEditor/NodeEditor.py
```

This will open the main viewport where you can add, connect, and manage nodes.

## Creating a New Node

To create a new node, follow these steps:

1. Create a new Python file in the `NodeEditor/Nodes` directory. For example, `MyNode.py`.

2. Define a new class that inherits from `Node`. Implement the required methods.

```python
# filepath: /NodeSystem-MK2/NodeEditor/Nodes/MyNode.py
import dearpygui.dearpygui as dpg
from NodeEditor.Core.Node import Node
from NodeEditor.Core.NodePackage import NodePackage

class MyNode(Node):
    def __init__(self):
        super().__init__("MyNode", "Category")
        self.input_idx = self.add_input("Input")
        self.add_output("Output")

    def compose(self):
        dpg.add_text("MyNode")

    def execute(self, inputs: list[NodePackage]) -> list[NodePackage]:
        input_package = inputs[self.input_idx]
        output_package = NodePackage()
        output_package.number = input_package.number * 2  # Example operation
        return [output_package]

    def view(self, output: NodePackage):
        dpg.add_text(f"Output: {output.number}")
```

3. The new node will be automatically loaded and available in the node editor.

## Creating a New Node Package

To create a custom node package, inherit from `NodePackage`:
```python
from NodeEditor.Core.NodePackage import NodePackage

class MyNodePackage(NodePackage):
    # Define any attributes or methods you need.
    pass
```

When working with a custom package, simply pass or return instances of it from node methods:
```python
def execute(self, inputs: list[MyNodePackage]) -> list[MyNodePackage]:
    return [MyNodePackage()]
```

## Node Class Overview

### Node

The base class for all nodes. It provides methods to add inputs, outputs, and define the node's behavior.

- `__init__(self, label: str, catagory: str, max_width: int = 100)`: Initializes the node with a label and category.
- `add_input(self, label: str = "") -> int`: Adds an input to the node.
- `add_output(self, label: str = "") -> int`: Adds an output to the node.
- `compose(self)`: Defines the node's UI components.
- `execute(self, inputs: list[NodePackage]) -> list[NodePackage]`: Defines the node's operation.
- `view(self, output: NodePackage)`: Updates the node's view with the output data. (Need either `view` or `viewer`)
- `viewer(self, outputs: list[NodePackage])`: Updates the node's view with the output data. (Need either `view` or `viewer`)

### NodePackage

A class to encapsulate data passed between nodes.

- `number: int`: An example attribute.
- `string: str`: An example attribute.
- `text(self) -> str`: Returns a string representation of the package.
- `copy(self) -> 'NodePackage'`: Returns a deep copy of the package.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.