import json

class HTMLExporter:
    def __init__(self):
        self.template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
        }}
        #mindmap {{
            display: block;
            width: 100vw;
            height: 100vh;
        }}
    </style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/markmap-toolbar@0.17.3-alpha.8/dist/style.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.15/dist/katex.min.css">
</head>
<body>
    <svg id="mindmap"></svg>
    <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.17.3-alpha.8/dist/browser/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-toolbar@0.17.3-alpha.8/dist/index.js"></script>
    <script>
        ((getMarkmap, options, data, root) => {{
            const mm = getMarkmap().Markmap.create(
                'svg#mindmap',
                (options || getMarkmap().deriveOptions)(root),
                data
            );
            window.mm = mm;
            window.mm.fit();
        }})(() => window.markmap, null, 
            {{
                "content": "{title}",
                "children": {content}
            }}, 
            {{
                "colorFreezeLevel": 2,
                "initialExpandLevel": 2,

                "maxWidth": 300,
            }}
        );
    </script>
    <script>
        (() => {{
            setTimeout(() => {{
                const {{ markmap, mm }} = window;
                const toolbar = new markmap.Toolbar();
                toolbar.attach(mm);
                const el = toolbar.render();
                el.setAttribute('style', 'position:absolute;bottom:20px;right:20px');
                document.body.append(el);
            }});
        }})();
    </script>
    <script>
        (e => {{
            window.WebFontConfig = {{
                custom: {{
                    families: [
                        "KaTeX_AMS",
                        "KaTeX_Caligraphic:n4,n7",
                        "KaTeX_Fraktur:n4,n7",
                        "KaTeX_Main:n4,n7,i4,i7",
                        "KaTeX_Math:i4,i7",
                        "KaTeX_Script",
                        "KaTeX_SansSerif:n4,n7,i4",
                        "KaTeX_Size1",
                        "KaTeX_Size2",
                        "KaTeX_Size3",
                        "KaTeX_Size4",
                        "KaTeX_Typewriter"
                    ]
                }},
                active: () => {{
                    e().refreshHook.call();
                }}
            }};
        }})(() => window.markmap);
    </script>
    <script src="https://cdn.jsdelivr.net/npm/webfontloader@1.6.28/webfontloader.js" defer></script>
</body>
</html>
"""

    def parse_markdown_to_json(self, content: str) -> list:
        """Преобразует markdown в структуру данных для markmap"""
        lines = content.split('\n')
        result = []
        stack = [(0, result)]  # (indent_level, children_list)
        
        for line in lines:
            if not line.strip():
                continue
            
            # Определяем уровень и содержимое строки
            if line.startswith('#'):
                # Заголовок
                level = len(line.split()[0])
                content = line.lstrip('#').strip()
                indent = level
            elif line.strip().startswith(('-', '*', '+')):
                # Маркированный список
                indent = len(line) - len(line.lstrip())
                content = line.strip().lstrip('-').lstrip('*').lstrip('+').strip()
                level = (indent // 2) + 1
            else:
                continue
            
            # Создаем новый узел
            new_node = {
                "content": content,
                "children": []
            }
            
            # Находим правильного родителя
            while stack and stack[-1][0] >= level:
                stack.pop()
            
            if not stack:
                stack.append((0, result))
            
            # Добавляем узел к родителю
            stack[-1][1].append(new_node)
            stack.append((level, new_node["children"]))
        
        return result

    def markdown_to_html(self, title: str, content: str) -> str:
        """Преобразует markdown в автономный HTML файл с встроенной визуализацией markmap"""
        try:
            # Преобразуем markdown в JSON структуру
            content_json = self.parse_markdown_to_json(content)
            
            # Форматируем HTML с данными
            html = self.template.format(
                title=title,
                content=json.dumps(content_json)
            )
            
            return html
            
        except Exception as e:
            print(f"Error generating HTML: {str(e)}")
            raise