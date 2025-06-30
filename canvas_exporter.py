import json
import uuid
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class CanvasNode:
    id: str
    text: str
    x: int
    y: int
    width: int = 250
    height: int = 60
    type: str = "text"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }

@dataclass
class CanvasEdge:
    id: str
    fromNode: str
    toNode: str
    fromSide: str = "right"
    toSide: str = "left"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fromNode": self.fromNode,
            "toNode": self.toNode,
            "fromSide": self.fromSide,
            "toSide": self.toSide
        }

class CanvasExporter:
    def __init__(self):
        self.LEVEL_SPACING = 400    # Горизонтальное расстояние между уровнями
        self.NODE_SPACING = 200     # Вертикальное расстояние между узлами
        self.NODE_WIDTH = 250
        self.NODE_HEIGHT = 60

    def create_node(self, text: str, x: int, y: int) -> CanvasNode:
        """Создает узел с указанным текстом и позицией"""
        return CanvasNode(
            id=str(uuid.uuid4()),
            text=text,
            x=x,
            y=y,
            width=self.NODE_WIDTH,
            height=self.NODE_HEIGHT
        )

    def create_edge(self, from_node: CanvasNode, to_node: CanvasNode) -> CanvasEdge:
        """Создает связь между двумя узлами"""
        return CanvasEdge(
            id=str(uuid.uuid4()),
            fromNode=from_node.id,
            toNode=to_node.id
        )

    def markdown_to_canvas(self, markdown_content: str) -> str:
        """Преобразует markdown в формат Obsidian Canvas"""
        # Подготовка структуры
        nodes: List[CanvasNode] = []
        edges: List[CanvasEdge] = []
        level_nodes: Dict[int, List[CanvasNode]] = {}

        # Получаем только строки с заголовками
        lines = [line for line in markdown_content.splitlines() 
                if line.strip() and line.startswith('#')]

        # Находим корневой узел
        root_node = None
        for line in lines:
            level = len(line) - len(line.lstrip('#'))
            title = line.strip('# ').strip()
            
            if level == 1:  # Корневой узел
                root_node = self.create_node(title, 0, 0)
                nodes.append(root_node)
                level_nodes[1] = [root_node]
                break

        if not root_node:
            return json.dumps({"nodes": [], "edges": [], "version": "3.1.1"}, 
                            ensure_ascii=False, indent=2)

        # Обработка остальных узлов
        current_parent = root_node
        prev_level = 1
        level_counters = {1: 0}

        for line in lines[1:]:  # Пропускаем корневой узел
            level = len(line) - len(line.lstrip('#'))
            title = line.strip('# ').strip()

            # Инициализируем счетчик для нового уровня
            if level not in level_counters:
                level_counters[level] = 0

            # Вычисляем позицию для нового узла
            x = self.LEVEL_SPACING * level
            total_height = level_counters[level] * self.NODE_SPACING
            y = total_height - (total_height / 2 if level_counters[level] > 0 else 0)

            # Создаем новый узел
            new_node = self.create_node(title, x, y)
            nodes.append(new_node)
            
            # Обновляем счетчик узлов на текущем уровне
            level_counters[level] += 1

            # Определяем родительский узел
            if level > prev_level:
                current_parent = nodes[-2]
            elif level < prev_level:
                # Находим ближайший родительский узел подходящего уровня
                for node in reversed(nodes[:-1]):
                    if node.x < new_node.x:
                        current_parent = node
                        break

            # Создаем связь с родительским узлом
            if current_parent and current_parent != new_node:
                edge = self.create_edge(current_parent, new_node)
                edges.append(edge)

            prev_level = level

        # Оптимизация расположения узлов
        for level in range(2, max(level_counters.keys()) + 1):
            if level in level_counters and level_counters[level] > 1:
                level_nodes = [node for node in nodes if node.x == self.LEVEL_SPACING * level]
                total_nodes = len(level_nodes)
                
                # Распределяем узлы равномерно
                for i, node in enumerate(level_nodes):
                    node.y = (i - (total_nodes - 1) / 2) * self.NODE_SPACING

        # Формируем финальную структуру
        canvas_structure = {
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "version": "3.1.1"
        }

        return json.dumps(canvas_structure, ensure_ascii=False, indent=2)