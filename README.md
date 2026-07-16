# EzPainter

EzPainter is a interactive Python drawing and data structures visualizer application built with **PySide6 (Qt for Python)**. It combines vector drawing shapes with dynamic, balanced binary trees and heap visualizations, backed by robust undo/redo capabilities and smooth viewport controls.

---

## Key Features

### Drawing & Painting

- **Select Tool (`V`)**: Move, resize, and inspect shapes, grids, and images.
- **Brush Tool (`B`)**: Custom freehand drawing with configurable brush width and color.
- **Table Tool (`T`)**: Insert custom tables/grid overlays on the canvas.
- **Shapes**: Draw scalable and resizable rectangles and ellipses that match your chosen color palette.
- **Merge Selected Objects (`M`)**: Flatten multiple selected canvas elements into a single transparent image layer, fully undoable/redoable and draggable across its entire bounds.
- **Clipboard Integration**: Paste images directly onto the canvas (`Ctrl+V` / `Cmd+V`).

### Data Structure Visualizers

- **Binary Tree**: Custom manual node creation, child attachment, and recursive subtree deletion.
- **Red-Black Tree**: Balanced binary tree supporting CLRS insertion and deletion algorithms with auto-balancing rotations and color properties.
- **Binary Search Tree (BST)**: Traditional binary search tree with standard insertion, lookup, successor min-finding, and deletion.
- **Min-Heap & Max-Heap**: Array-backed complete binary trees demonstrating bubble-up, bubble-down, extraction, and node deletions.
- **Smooth Layout Transitions**: Smooth sliding animations (`QTimeLine` based cubic ease-out) reposition nodes and connected edges dynamically during insertions, deletions, and structural balancing.
- **Complete Tree Layout**: A specialized level-order positioning layout keeping complete tree structures (Heaps) neat and compact.

### Viewport Navigation & Panel Controls

- **Smooth Zooming**: Zoom in/out of the canvas using `Ctrl + Mouse Wheel` (or `Cmd + Mouse Wheel` on macOS). Zooming naturally anchors directly under your mouse cursor and supports trackpad pinch gestures.
- **Interactive Zoom Input**: Enter specific zoom percentages directly into the toolbar text box.
- **Spacebar Panning**: Hold down the `Spacebar` key and click-drag the mouse to pan across the canvas.
- **Clean Suffix Labels**: Suffixes (`px` for brush size and `%` for zoom ratio) are separated into static, unmodifiable labels next to their respective inputs.
- **Active Tool Highlights**: Toggle buttons in the tool panel dynamically highlight the active tool.
- **Robust Clear Canvas**: Reset all visual elements and internal models cleanly, even when starting from an empty canvas.

### Command System

- Full application state commands integrated into a unified `QUndoStack` for unlimited Undo/Redo across drawing, modifications, and tree mutations.

---

## Keyboard Shortcuts

| Shortcut                           | Action                                         |
| ---------------------------------- | ---------------------------------------------- |
| **`V`**                            | Select Tool                                    |
| **`B`**                            | Brush Tool                                     |
| **`T`**                            | Table Tool                                     |
| **`M`**                            | Merge Selected Objects                         |
| **`Space` (Hold)**                 | Pan Canvas (Click-Drag)                        |
| **`Ctrl + Wheel` / `Cmd + Wheel`** | Zoom Canvas (Anchored under Mouse)             |
| **`Delete` / `Backspace`**         | Delete Selected Items / Nodes                  |
| **`Escape`**                       | Cancel Node Connections / Reset to Select Tool |
| **`Ctrl + Z` / `Cmd + Z`**         | Undo Action                                    |
| **`Ctrl + Y` / `Cmd + Y`**         | Redo Action                                    |
| **`Ctrl + V` / `Cmd + V`**         | Paste Image from Clipboard                     |

---

## Getting Started

### Prerequisites

- Python 3.10+
- PySide6

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Novax Labs, Ace
