import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
import re
import os
from genson import SchemaBuilder
from jsonschema import validate, ValidationError
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import copy

class JSONSchemaValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("Валидатор JSON-схем")
        self.root.geometry("900x900")  # Увеличенный размер окна
        
        self.current_schema = None
        self.merged_json = None
        
        # Создание основного фрейма
        self.main_frame = ttk.Frame(root, padding="15")  # Увеличенный отступ
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка сетки для расширения с окном
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        for i in range(11):  # Увеличено для новых строк
            self.main_frame.rowconfigure(i, weight=1)
        
        # Создание фрейма для кнопок с прокруткой - увеличиваем ширину
        buttons_frame = ttk.LabelFrame(self.main_frame, text="Действия", padding="15")  # Увеличиваем padding с 10 до 15
        buttons_frame.grid(row=0, column=0, pady=10, sticky=tk.W+tk.E)  # Увеличиваем pady с 5 до 10
        
        # Расположим кнопки в две колонки для экономии места по вертикали
        # Обеспечиваем равное распределение веса для колонок
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)  # Добавляем третью колонку
        
        # Создание и настройка кнопок - переорганизуем расположение
        self.extract_schema_btn = ttk.Button(
            buttons_frame, 
            text="Извлечь схему из JSON",
            command=self.extract_schema,
            width=20  # Уменьшаем ширину для лучшего размещения
        )
        self.extract_schema_btn.grid(row=0, column=0, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        self.save_schema_btn = ttk.Button(
            buttons_frame,
            text="Сохранить схему в файл",
            command=self.save_schema,
            width=20
        )
        self.save_schema_btn.grid(row=0, column=1, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        self.load_schema_btn = ttk.Button(
            buttons_frame,
            text="Загрузить схему из файла",
            command=self.load_schema,
            width=20
        )
        self.load_schema_btn.grid(row=0, column=2, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        self.validate_json_btn = ttk.Button(
            buttons_frame, 
            text="Проверить JSON-файл",
            command=self.validate_json_file,
            width=20
        )
        self.validate_json_btn.grid(row=1, column=0, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        # Кнопка для объединения JSON файлов
        self.merge_json_btn = ttk.Button(
            buttons_frame,
            text="Объединить JSON-файлы",
            command=self.merge_json_files,
            width=20
        )
        self.merge_json_btn.grid(row=1, column=1, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        # Кнопка для извлечения списка фамилий
        self.extract_names_btn = ttk.Button(
            buttons_frame,
            text="Показать список фамилий",
            command=self.show_surnames_list,
            width=20
        )
        self.extract_names_btn.grid(row=1, column=2, pady=8, padx=8, sticky=tk.W+tk.E)  # Увеличиваем pady и padx с 5 до 8
        
        # Добавляем новую кнопку для удаления docagent
        self.delete_docagent_btn = ttk.Button(
            buttons_frame,
            text="Удалить docagent по cln",
            command=self.delete_docagent_by_cln,
            width=20
        )
        self.delete_docagent_btn.grid(row=2, column=0, pady=8, padx=8, sticky=tk.W+tk.E)
        
        # Добавляем кнопку сохранения отчета об ошибках
        self.save_errors_btn = ttk.Button(
            buttons_frame,
            text="Сохранить отчет об ошибках",
            command=self.save_errors_to_file,
            width=20
        )
        self.save_errors_btn.grid(row=2, column=1, pady=8, padx=8, sticky=tk.W+tk.E)
        
        # Добавляем кнопку автоудаления docagent по cln из файла ошибок
        self.auto_delete_btn = ttk.Button(
            buttons_frame,
            text="Удалить docagent из файла",
            command=self.delete_docagents_from_error_file,
            width=20
        )
        self.auto_delete_btn.grid(row=2, column=2, pady=8, padx=8, sticky=tk.W+tk.E)
        
        # Добавляем кнопку для синхронизации tar14 с tar4
        self.sync_tar_btn = ttk.Button(
            buttons_frame,
            text="Синхронизировать tar14/tar4",
            command=self.sync_tar14_with_tar4,
            width=20
        )
        self.sync_tar_btn.grid(row=3, column=0, pady=8, padx=8, sticky=tk.W+tk.E)
        
        # Добавляем кнопку для создания выборки docagent
        self.extract_docagents_btn = ttk.Button(
            buttons_frame,
            text="Выборка docagent по cln",
            command=self.extract_docagents_by_cln_list,
            width=20
        )
        self.extract_docagents_btn.grid(row=3, column=1, pady=8, padx=8, sticky=tk.W+tk.E)
        
        # Создание текстовой области для отображения схемы - увеличиваем отступ
        self.schema_label = ttk.Label(self.main_frame, text="Текущая схема:")
        self.schema_label.grid(row=1, column=0, pady=(20,5), sticky=tk.W)
        
        # Использование PanedWindow для создания изменяемых панелей
        self.paned = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.paned.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Панель области текста схемы
        schema_frame = ttk.Frame(self.paned)
        self.schema_text = scrolledtext.ScrolledText(schema_frame, height=15, width=100, wrap=tk.WORD)
        self.schema_text.pack(fill=tk.BOTH, expand=True)
        self.paned.add(schema_frame, weight=1)
        
        # Область результатов валидации
        results_frame = ttk.Frame(self.paned)
        
        self.results_label = ttk.Label(results_frame, text="Результаты проверки:")
        self.results_label.pack(anchor=tk.W, pady=(5,0))
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=100, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.paned.add(results_frame, weight=1)
        
        # Метка статуса - добавляем отступ снизу
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, pady=5)
        
        # Добавляем прогресс-бар и скрываем его изначально
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Обработка: ")
        self.progress_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            orient=tk.HORIZONTAL, 
            length=500, 
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Скрываем прогресс-бар до его использования
        self.progress_frame.grid_remove()
        
        # Словарь для перевода сообщений об ошибках валидации
        self.error_translations = {
            r"'([^']+)' is a required property": r"Отсутствует обязательное свойство '\1'",
            r"Additional properties are not allowed \('([^']+)' was unexpected\)": r"Дополнительные свойства не разрешены (обнаружено неожиданное свойство '\1')",
            r"'([^']+)' is not of type '([^']+)'": r"'\1' не соответствует типу '\2'",
            r"'([^']+)' does not match '([^']+)'": r"'\1' не соответствует формату '\2'",
            r"'([^']+)' is not one of (.+)": r"'\1' не соответствует ни одному из допустимых значений \2",
            r"'([^']+)' is too short": r"'\1' слишком короткий",
            r"'([^']+)' is too long": r"'\1' слишком длинный",
            r"'([^']+)' is less than the minimum of ([0-9]+)": r"'\1' меньше минимально допустимого значения \2",
            r"'([^']+)' is greater than the maximum of ([0-9]+)": r"'\1' больше максимально допустимого значения \2",
            r"'([^']+)' is not a multiple of ([0-9.]+)": r"'\1' не кратно \2",
            r"([0-9.]+) is not a multiple of ([0-9.]+)": r"\1 не кратно \2",
            r"\[\] should be non-empty": r"Массив не должен быть пустым",
            r"None is not of type 'object'": r"Обнаружено значение None, ожидается объект",
            r"None is not of type 'array'": r"Обнаружено значение None, ожидается массив",
            r"None is not of type 'string'": r"Обнаружено значение None, ожидается строка",
            r"None is not of type 'number'": r"Обнаружено значение None, ожидается число",
            r"None is not of type 'integer'": r"Обнаружено значение None, ожидается целое число",
            r"None is not of type 'boolean'": r"Обнаружено значение None, ожидается логическое значение",
            r"Failed validating (.+) in schema": r"Ошибка валидации \1 в схеме",
            r"Expecting value: line ([0-9]+) column ([0-9]+)": r"Ожидается значение: строка \1, столбец \2",
            r"'' is too short": r"Пустая строка слишком короткая",
            r"'' does not match '(.+)'": r"Пустая строка не соответствует требуемому формату",
            r"'' is not valid under any of the given schemas": r"Пустая строка не соответствует ни одной из доступных схем",
            r"does not match any pattern": r"Не соответствует ни одному из допустимых шаблонов",
            r"\" does not match": r"Значение не соответствует требуемому формату"
        }
        
        # Автоматическая загрузка схемы при запуске
        self.load_default_schema()

    def show_surnames_list(self):
        """Извлечение и отображение списка фамилий из поля 'vfam' в JSON-файле"""
        try:
            # Запрос JSON файла
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл для извлечения фамилий",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
                
            # Загрузка данных из файла
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                
            # Поиск и извлечение фамилий и информации из cln
            data_entries = self.extract_data(json_data)
            
            if not data_entries:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "В JSON-файле не найдены фамилии в поле 'vfam'", "info")
                self.results_text.tag_configure("info", foreground="blue")
                
                self.status_label.config(
                    text="Данные не найдены",
                    foreground="orange"
                )
                return
            
            # Отображение списка фамилий и cln
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Список фамилий и информации из 'cln':\n\n", "title")
            self.results_text.tag_configure("title", font=("Arial", 10, "bold"))
            
            # Сортировка и отображение данных с порядковым номером
            sorted_data = sorted(data_entries, key=lambda x: x.get('vfam', ''))
            for i, entry in enumerate(sorted_data, 1):
                surname = entry.get('vfam', 'Нет фамилии')
                cln_value = entry.get('cln', 'Нет информации')
                self.results_text.insert(tk.END, f"{i}. Фамилия: ", "label")
                self.results_text.insert(tk.END, f"{surname}", "surname")
                self.results_text.insert(tk.END, f", cln: ", "label")
                self.results_text.insert(tk.END, f"{cln_value}\n", "cln_value")
            
            self.results_text.tag_configure("label", font=("Arial", 9, "bold"))
            self.results_text.tag_configure("surname", font=("Arial", 9))
            self.results_text.tag_configure("cln_value", font=("Arial", 9), foreground="blue")
            
            self.status_label.config(
                text=f"Найдено {len(data_entries)} записей",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении данных: {str(e)}")
            self.status_label.config(
                text="Ошибка при извлечении данных",
                foreground="red"
            )

    def extract_data(self, json_data):
        """Рекурсивное извлечение данных из полей 'vfam' и 'cln' из JSON структуры"""
        data_entries = []
        processed_entries = set()  # Для отслеживания уникальных комбинаций vfam+cln
        
        def extract_from_node(node, current_path=None):
            if current_path is None:
                current_path = []
                
            if isinstance(node, dict):
                # Проверяем наличие полей vfam и cln в текущем словаре
                vfam_value = None
                cln_value = None
                
                if 'vfam' in node:
                    if isinstance(node['vfam'], str) and node['vfam'].strip():
                        vfam_value = node['vfam'].strip()
                    elif isinstance(node['vfam'], list) and node['vfam']:
                        # Если vfam - список, берём первый непустой элемент
                        for item in node['vfam']:
                            if isinstance(item, str) and item.strip():
                                vfam_value = item.strip()
                                break
                
                if 'cln' in node:
                    if isinstance(node['cln'], (str, int, float)) and str(node['cln']).strip():
                        cln_value = str(node['cln']).strip()
                    elif isinstance(node['cln'], list) and node['cln']:
                        # Если cln - список, берём первый непустой элемент
                        for item in node['cln']:
                            if isinstance(item, (str, int, float)) and str(item).strip():
                                cln_value = str(item).strip()
                                break
                
                # Если нашли vfam или cln, добавляем в результат
                if vfam_value or cln_value:
                    entry = {}
                    if vfam_value:
                        entry['vfam'] = vfam_value
                    if cln_value:
                        entry['cln'] = cln_value
                    
                    # Проверяем, что такой комбинации ещё нет
                    entry_key = f"{vfam_value}:{cln_value}"
                    if entry and entry_key not in processed_entries:
                        data_entries.append(entry)
                        processed_entries.add(entry_key)
                        
                # Даже если нашли vfam/cln на текущем уровне, продолжаем поиск глубже
                for key, value in node.items():
                    extract_from_node(value, current_path + [key])
                    
            elif isinstance(node, list):
                # Рекурсивно обрабатываем все элементы списка
                for i, item in enumerate(node):
                    extract_from_node(item, current_path + [i])
        
        # Начинаем рекурсивный поиск с корня JSON
        extract_from_node(json_data)
        
        return data_entries

    def load_default_schema(self):
        """Загрузка схемы из файла Scheme.json при запуске программы"""
        default_schema_file = "Scheme.json"
        if os.path.exists(default_schema_file):
            try:
                self.load_schema_from_file(default_schema_file)
                self.status_label.config(
                    text=f"Схема из файла {default_schema_file} загружена автоматически!",
                    foreground="green"
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Не удалось загрузить схему из {default_schema_file}: {str(e)}",
                    foreground="orange"
                )

    def extract_schema(self):
        """Извлечение JSON схемы из выбранного файла"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
            
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            builder = SchemaBuilder()
            builder.add_object(json_data)
            self.current_schema = builder.to_schema()
            
            # Отображение схемы
            self.schema_text.delete(1.0, tk.END)
            self.schema_text.insert(1.0, json.dumps(self.current_schema, indent=2, ensure_ascii=False))
            
            # Очистка результатов валидации
            self.results_text.delete(1.0, tk.END)
            
            self.status_label.config(
                text="Схема успешно извлечена!",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка извлечения схемы: {str(e)}")
            self.status_label.config(
                text="Ошибка извлечения схемы",
                foreground="red"
            )

    def save_schema(self):
        """Сохранение текущей схемы в файл"""
        if not self.current_schema:
            messagebox.showwarning(
                "Предупреждение",
                "Нет схемы для сохранения. Пожалуйста, сначала извлеките или загрузите схему!"
            )
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile="schema.json"
            )
            if not file_path:
                return
                
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.current_schema, file, indent=2, ensure_ascii=False)
                
            self.status_label.config(
                text="Схема успешно сохранена!",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения схемы: {str(e)}")
            self.status_label.config(
                text="Ошибка сохранения схемы",
                foreground="red"
            )

    def load_schema(self):
        """Загрузка схемы из выбранного пользователем файла"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
            
            self.load_schema_from_file(file_path)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки схемы: {str(e)}")
            self.status_label.config(
                text="Ошибка загрузки схемы",
                foreground="red"
            )

    def load_schema_from_file(self, file_path):
        """Загрузка схемы из указанного файла"""
        with open(file_path, 'r', encoding='utf-8') as file:
            self.current_schema = json.load(file)
            
        # Отображение схемы
        self.schema_text.delete(1.0, tk.END)
        self.schema_text.insert(1.0, json.dumps(self.current_schema, indent=2, ensure_ascii=False))
        
        # Очистка результатов валидации
        self.results_text.delete(1.0, tk.END)
        
        self.status_label.config(
            text="Схема успешно загружена!",
            foreground="green"
        )

    def find_line_from_path(self, json_str, path_elements):
        """Поиск номера строки в JSON строке на основе пути элемента, вызвавшего ошибку валидации"""
        if not path_elements:
            return 1
        
        try:
            # Разбиваем JSON на строки для поиска
            lines = json_str.split('\n')
            line_count = len(lines)
            
            # Построение полного пути для последовательного поиска
            full_path = []
            for element in path_elements:
                if isinstance(element, int):
                    full_path.append(f"[{element}]")
                else:
                    full_path.append(f'"{element}"')
            
            # Прямое сканирование файла для поиска каждого элемента пути
            current_depth = 0  # Глубина вложенности JSON
            in_string = False  # Находимся ли мы в строке
            escape_next = False  # Следующий символ экранирован
            
            # Токены для поиска
            found_tokens = 0
            current_path_index = 0
            current_token = full_path[current_path_index] if full_path else None
            
            # Счетчики для массивов
            array_stack = []  # Стек для отслеживания индексов внутри массивов
            current_array_index = 0
            last_token_line = 1
            
            # Просматриваем каждую строку и символ
            for line_num, line in enumerate(lines, 1):
                for char_pos, char in enumerate(line):
                    # Обработка экранирования
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    # Обработка строк в кавычках
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    
                    # Пропускаем символы внутри строк
                    if in_string:
                        continue
                    
                    # Обработка структурных элементов JSON
                    if char == '{':
                        current_depth += 1
                    elif char == '}':
                        current_depth -= 1
                    elif char == '[':
                        array_stack.append(0)  # Начинаем новый массив с индекса 0
                    elif char == ']':
                        if array_stack:
                            array_stack.pop()  # Завершили обработку массива
                    elif char == ',' and array_stack:
                        # Увеличиваем индекс текущего массива при переходе к следующему элементу
                        array_stack[-1] += 1
                        
                    # Поиск ключей и элементов, соответствующих нашему пути
                    if current_token and current_path_index < len(full_path):
                        token = full_path[current_path_index]
                        
                        # Ищем ключ в текущей строке
                        if '"' in token and char == ':' and token in line[:char_pos]:
                            key_pos = line[:char_pos].rfind(token)
                            if key_pos >= 0:
                                # Нашли ключ
                                found_tokens += 1
                                current_path_index += 1
                                last_token_line = line_num
                                
                                if current_path_index < len(full_path):
                                    current_token = full_path[current_path_index]
                                else:
                                    # Нашли последний элемент пути
                                    return line_num
                                    
                        # Ищем индекс массива
                        elif '[' in token and ']' in token and array_stack:
                            index_str = token.strip('[]')
                            if index_str.isdigit() and array_stack and array_stack[-1] == int(index_str):
                                # Нашли соответствующий индекс массива
                                found_tokens += 1
                                current_path_index += 1
                                last_token_line = line_num
                                
                                if current_path_index < len(full_path):
                                    current_token = full_path[current_path_index]
                                else:
                                    # Нашли последний элемент пути
                                    return line_num
            
            # Если мы прошли весь файл, но не нашли полного пути,
            # возвращаем строку последнего найденного элемента или поиск напрямую
            if found_tokens > 0:
                return last_token_line
            
            # Если ничего не нашли методом прохода, попробуем найти по ключевым паттернам
            for path_index, element in enumerate(path_elements):
                # Ищем паттерны в зависимости от типа элемента
                if isinstance(element, str):
                    # Для ключей словаря - ищем "ключ":
                    pattern = f'"{re.escape(element)}"\\s*:'
                    
                    # Если это последний элемент, можно искать и без двоеточия
                    if path_index == len(path_elements) - 1:
                        pattern = f'"{re.escape(element)}"'
                        
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            return i
                            
                elif isinstance(element, int):
                    # Для индексов массива - ищем [индекс]
                    pattern = f'\\[\\s*{element}\\s*\\]'
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            return i
            
            # Если всё еще не нашли, возвращаем предполагаемую строку на основе структуры
            if path_elements and isinstance(path_elements[-1], int):
                # Для числовых индексов, пробуем найти элемент по индексу
                index_value = path_elements[-1]
                # Предполагаем, что индекс примерно соответствует строке в документе
                # (с некоторым смещением для учёта структуры)
                estimated_line = min(line_count // 2 + index_value, line_count)
                return max(1, estimated_line)
            
            # В самом крайнем случае возвращаем приблизительное место
            return max(1, min(line_count // 2, line_count))
            
        except Exception as e:
            # В случае любой ошибки, выводим отладочную информацию
            print(f"Ошибка при поиске строки: {str(e)}")
            
            # Возвращаем более осмысленное значение вместо случайного
            try:
                # В качестве эвристики возвращаем строку, где встречается последний элемент пути
                if path_elements:
                    last_element = path_elements[-1]
                    search_term = f'"{last_element}"' if isinstance(last_element, str) else f"[{last_element}]"
                    
                    for i, line in enumerate(json_str.split('\n'), 1):
                        if search_term in line:
                            return i
            except:
                pass
            
            # Если даже это не сработало, возвращаем середину файла
            return max(1, len(json_str.split('\n')) // 2)

    def translate_error_message(self, message):
        """Перевод сообщения об ошибке с английского на русский"""
        translated_message = message
        
        for pattern, replacement in self.error_translations.items():
            translated_message = re.sub(pattern, replacement, translated_message)
            
        return translated_message

    def merge_json_files(self):
        """Объединение двух JSON файлов"""
        try:
            # Запрос первого JSON файла
            file_path1 = filedialog.askopenfilename(
                title="Выберите первый JSON файл",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path1:
                return
                
            # Запрос второго JSON файла
            file_path2 = filedialog.askopenfilename(
                title="Выберите второй JSON файл",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path2:
                return
                
            # Загрузка данных из обоих файлов
            with open(file_path1, 'r', encoding='utf-8') as file1:
                json_data1 = json.load(file1)
                
            with open(file_path2, 'r', encoding='utf-8') as file2:
                json_data2 = json.load(file2)
                
            # Запрос типа объединения
            merge_type = messagebox.askyesno(
                "Способ объединения", 
                "Хотите выполнить рекурсивное объединение (да) или простое объединение (нет)?\n\n"
                "Рекурсивное: объединяет вложенные структуры.\n"
                "Простое: объединяет только верхний уровень."
            )
            
            # Объединение JSON данных
            if merge_type:
                # Рекурсивное объединение
                self.merged_json = self.deep_merge(json_data1, json_data2)
            else:
                # Простое объединение
                self.merged_json = self.simple_merge(json_data1, json_data2)
            
            # Отображение результата в текстовом поле
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, json.dumps(self.merged_json, indent=2, ensure_ascii=False))
            
            # Запрос на сохранение объединенного файла
            if messagebox.askyesno("Сохранение", "Хотите сохранить объединенный JSON в файл?"):
                self.save_merged_json()
                
            self.status_label.config(
                text="JSON файлы успешно объединены!",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при объединении JSON файлов: {str(e)}")
            self.status_label.config(
                text="Ошибка при объединении JSON файлов",
                foreground="red"
            )

    def deep_merge(self, json1, json2):
        """Рекурсивное объединение JSON структур"""
        # Если оба элемента - словари, объединяем их рекурсивно
        if isinstance(json1, dict) and isinstance(json2, dict):
            result = json1.copy()
            for key, value in json2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self.deep_merge(result[key], value)
                elif key in result and isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + [item for item in value if item not in result[key]]
                else:
                    result[key] = value
            return result
            
        # Если оба элемента - списки, объединяем их с удалением дубликатов
        elif isinstance(json1, list) and isinstance(json2, list):
            # Попытка объединить списки объектов с учетом содержимого
            if all(isinstance(item, dict) for item in json1 + json2):
                result = json1.copy()
                for item in json2:
                    if item not in result:
                        result.append(item)
                return result
            else:
                # Для списков примитивов просто объединяем
                return json1 + [item for item in json2 if item not in json1]
                
        # Если типы не совпадают или это не контейнеры, возвращаем json2
        else:
            return json2

    def simple_merge(self, json1, json2):
        """Простое объединение JSON структур (только верхний уровень)"""
        # Если оба элемента - словари, объединяем их
        if isinstance(json1, dict) and isinstance(json2, dict):
            result = json1.copy()
            result.update(json2)
            return result
            
        # Если оба элемента - списки, объединяем их
        elif isinstance(json1, list) and isinstance(json2, list):
            return json1 + json2
            
        # Если типы не совпадают или это не контейнеры, возвращаем json2
        else:
            return json2

    def save_merged_json(self):
        """Сохранение объединенного JSON в файл"""
        if not self.merged_json:
            messagebox.showwarning(
                "Предупреждение",
                "Нет объединенных данных для сохранения."
            )
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile="merged.json"
            )
            if not file_path:
                return
                
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.merged_json, file, indent=2, ensure_ascii=False)
                
            self.status_label.config(
                text="Объединенный JSON успешно сохранен!",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения объединенного JSON: {str(e)}")
            self.status_label.config(
                text="Ошибка сохранения объединенного JSON",
                foreground="red"
            )

    def validate_json_file(self):
        """Валидация выбранного JSON файла по текущей схеме"""
        # Проверка наличия текущей схемы
        if not self.current_schema:
            messagebox.showwarning(
                "Предупреждение",
                "Пожалуйста, сначала извлеките или загрузите схему!"
            )
            return
        
        # Запрос на игнорирование ошибок кратности
        ignore_multiple_errors = messagebox.askyesno(
            "Игнорировать ошибки кратности",
            "Хотите игнорировать ошибки кратности при валидации?"
        )
        
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
            
            # Показываем прогресс-бар для процесса загрузки
            self.show_progress("Загрузка JSON файла...")
            
            # Чтение содержимого файла как строки для сохранения информации о строках
            with open(file_path, 'r', encoding='utf-8') as file:
                json_str = file.read()
            
            self.update_progress(10, "Парсинг JSON...")
            
            # Парсинг JSON
            json_data = json.loads(json_str)
            
            self.update_progress(20, "Предварительная обработка данных...")
            
            # Предварительная обработка JSON перед валидацией
            json_data = self.round_monetary_values(json_data)  # Обработка чисел с плавающей точкой
            
            # Очистка предыдущих результатов валидации
            self.results_text.delete(1.0, tk.END)
            
            self.update_progress(30, "Проверка уникальности cln...")
            
            # Проверка на уникальность cln
            duplicate_clns = self.check_cln_uniqueness(json_data)
            
            # Полная валидация с собиранием всех ошибок
            # Передаем функцию обновления прогресса
            errors = self.collect_validation_errors(
                json_data, 
                json_str, 
                ignore_multiple_errors, 
                update_progress=self.update_progress
            )
            
            self.update_progress(70, "Обработка результатов валидации...")
            
            # Если найдены дубликаты cln, добавляем ошибки в общий список
            if duplicate_clns:
                for cln, positions in duplicate_clns.items():
                    for idx, position in enumerate(positions[1:], 1):  # Пропускаем первое вхождение
                        error_message = f"Повторяющееся значение cln: {cln} (уже встречается в docagent с индексом {positions[0]['index']})"
                        path = position['path']
                        line = self.find_line_from_path(json_str, path)
                        instance_value = cln
                        schema_info = "Значения cln должны быть уникальными в пределах файла"
                        docagent_info = self.get_docagent_info(json_data, path)
                        errors.append((error_message, path, line, instance_value, schema_info, docagent_info))
            
            self.update_progress(80, "Формирование отчета...")
            
            # Если есть ошибки кратности и их нужно игнорировать
            if ignore_multiple_errors:
                # Показываем сообщение, что ошибки кратности игнорируются
                self.results_text.insert(tk.END, "✓ Ошибки кратности игнорируются.\n", "info")
                self.results_text.tag_configure("info", foreground="blue")
                
                # Удаляем ошибки кратности из списка
                errors = [err for err in errors if "не кратно" not in err[0]]
            
            # Если список ошибок пуст (все ошибки игнорируются или их нет)
            if not errors:
                self.results_text.insert(tk.END, "✓ JSON файл соответствует схеме!\n", "success")
                self.results_text.tag_configure("success", foreground="green")
                
                self.update_progress(100, "Валидация завершена успешно!")
                
                messagebox.showinfo(
                    "Успех",
                    "JSON файл соответствует схеме! (с учетом игнорирования ошибок кратности)" if ignore_multiple_errors else "JSON файл соответствует схеме!"
                )
                self.status_label.config(
                    text="Валидация успешна!",
                    foreground="green"
                )
            else:
                # Выводим заголовок для ошибок
                self.results_text.insert(tk.END, f"✗ Найдено {len(errors)} ошибок валидации:\n\n", "error_title")
                self.results_text.tag_configure("error_title", foreground="red", font=("Arial", 10, "bold"))
                
                # Словарь для отслеживания ошибок по docagent
                docagent_errors = {}
                
                # Обновляем прогресс-бар для отображения процесса вывода ошибок
                total_errors = len(errors)
                self.update_progress(85, f"Обработка {total_errors} ошибок...")
                
                # Выводим найденные ошибки
                for i, (error_msg, path, line, instance_value, schema_info, docagent_info) in enumerate(errors, 1):
                    # Периодически обновляем прогресс-бар
                    if i % max(1, total_errors // 10) == 0 or i == total_errors:
                        progress_value = 85 + int((i / total_errors) * 10)  # От 85% до 95%
                        self.update_progress(progress_value, f"Обработка ошибок {i}/{total_errors}...")
                    
                    self.results_text.insert(tk.END, f"Ошибка #{i}:\n", "error_num")
                    self.results_text.tag_configure("error_num", foreground="red", font=("Arial", 9, "bold"))
                    
                    self.results_text.insert(tk.END, f"Описание: {error_msg}\n", "error_msg")
                    self.results_text.tag_configure("error_msg", foreground="red")
                    
                    self.results_text.insert(tk.END, f"Путь к элементу: {path}\n", "path")
                    self.results_text.tag_configure("path", foreground="blue")
                    
                    self.results_text.insert(tk.END, f"Строка в файле: {line}\n", "line_num")
                    self.results_text.tag_configure("line_num", foreground="purple")
                    
                    # Выводим значение, вызвавшее ошибку
                    self.results_text.insert(tk.END, "Значение: ", "value_label")
                    self.results_text.tag_configure("value_label", font=("Arial", 9, "bold"))
                    
                    # Форматируем вывод значения в зависимости от типа
                    if isinstance(instance_value, dict):
                        self.results_text.insert(tk.END, f"{json.dumps(instance_value, ensure_ascii=False)[:100]}...\n", "value")
                    elif isinstance(instance_value, list):
                        self.results_text.insert(tk.END, f"{json.dumps(instance_value, ensure_ascii=False)[:100]}...\n", "value")
                    else:
                        self.results_text.insert(tk.END, f"{instance_value}\n", "value")
                    self.results_text.tag_configure("value", foreground="brown")
                    
                    # Информация о схеме
                    if schema_info:
                        self.results_text.insert(tk.END, "Требования схемы: ", "schema_label")
                        self.results_text.tag_configure("schema_label", font=("Arial", 9, "bold"))
                        self.results_text.insert(tk.END, f"{schema_info}\n", "schema")
                        self.results_text.tag_configure("schema", foreground="green")
                    
                    # Если есть информация о docagent, выводим её и учитываем для статистики
                    if docagent_info:
                        self.results_text.insert(tk.END, "Информация о docagent: ", "docagent_label")
                        self.results_text.tag_configure("docagent_label", font=("Arial", 9, "bold"))
                        
                        for key, value in docagent_info.items():
                            self.results_text.insert(tk.END, f"{key}: {value}, ", "docagent")
                        self.results_text.insert(tk.END, "\n", "docagent")
                        self.results_text.tag_configure("docagent", foreground="blue")
                        
                        # Собираем статистику по ошибкам docagent
                        docagent_id = self.get_docagent_identifier(docagent_info)
                        if docagent_id:
                            if docagent_id in docagent_errors:
                                docagent_errors[docagent_id]["count"] += 1
                                docagent_errors[docagent_id]["errors"].append(error_msg)
                            else:
                                docagent_errors[docagent_id] = {
                                    "info": docagent_info,
                                    "count": 1,
                                    "errors": [error_msg]
                                }
                    
                    # Пустая строка между ошибками
                    self.results_text.insert(tk.END, "\n", "normal")
                
                self.update_progress(95, "Формирование сводки ошибок...")
                
                # Добавляем сводку по ошибкам в конце отчета
                self.results_text.insert(tk.END, "\n" + "="*80 + "\n", "separator")
                self.results_text.tag_configure("separator", foreground="gray")
                
                self.results_text.insert(tk.END, "СВОДКА ПО ОШИБКАМ В DOCAGENT:\n\n", "summary_title")
                self.results_text.tag_configure("summary_title", foreground="dark blue", font=("Arial", 10, "bold"))
                
                # Если есть ошибки, связанные с docagent
                if docagent_errors:
                    # Сортируем docagent по количеству ошибок (по убыванию)
                    sorted_docagents = sorted(docagent_errors.items(), key=lambda x: x[1]["count"], reverse=True)
                    total_docagents = len(sorted_docagents)
                    
                    for j, (docagent_id, data) in enumerate(sorted_docagents, 1):
                        # Периодически обновляем прогресс-бар
                        if j % max(1, total_docagents // 5) == 0 or j == total_docagents:
                            progress_value = 95 + int((j / total_docagents) * 5)  # От 95% до 100%
                            self.update_progress(progress_value, f"Обработка сводки {j}/{total_docagents}...")
                        
                        docagent_info = data["info"]
                        error_count = data["count"]
                        
                        # Формируем идентификатор для отображения
                        display_name = f"DocAgent #{docagent_id}"
                        if "Фамилия (vfam)" in docagent_info:
                            display_name = f"{docagent_info['Фамилия (vfam)']}"
                            if "Имя (vname)" in docagent_info:
                                display_name += f" {docagent_info['Имя (vname)']}"
                                if "Отчество (votch)" in docagent_info:
                                    display_name += f" {docagent_info['Отчество (votch)']}"
                        
                        # Выводим информацию о docagent и количестве ошибок
                        self.results_text.insert(tk.END, f"{display_name} - ", "docagent_name")
                        self.results_text.tag_configure("docagent_name", foreground="black", font=("Arial", 9, "bold"))
                        
                        self.results_text.insert(tk.END, f"Ошибок: {error_count}\n", "error_count")
                        self.results_text.tag_configure("error_count", foreground="red")
                        
                        # Выводим дополнительную информацию о docagent
                        if "cln" in docagent_info:
                            cln_value = docagent_info["cln"]
                            cln_display = cln_value if cln_value else "(пусто)"
                            self.results_text.insert(tk.END, f"   cln: {cln_display}\n", "cln")
                            self.results_text.tag_configure("cln", foreground="blue")
                        
                        if "Индекс в массиве docagent" in docagent_info:
                            self.results_text.insert(tk.END, f"   Индекс: {docagent_info['Индекс в массиве docagent']}\n", "index")
                            self.results_text.tag_configure("index", foreground="gray")
                        
                        # Выводим типы ошибок (уникальные)
                        unique_errors = set(data["errors"])
                        self.results_text.insert(tk.END, "   Типы ошибок:\n", "error_types_label")
                        self.results_text.tag_configure("error_types_label", foreground="dark red")
                        
                        for k, error in enumerate(unique_errors, 1):
                            self.results_text.insert(tk.END, f"     {k}. {error}\n", "error_type")
                            self.results_text.tag_configure("error_type", foreground="brown")
                        
                        self.results_text.insert(tk.END, "\n", "normal")
                else:
                    # Если не найдено docagent_errors, создаем сводку на основе всех ошибок
                    # Группируем ошибки по типам
                    error_types = {}
                    for error_msg, path, line, instance_value, schema_info, docagent_info in errors:
                        if error_msg in error_types:
                            error_types[error_msg] += 1
                        else:
                            error_types[error_msg] = 1
                    
                    self.results_text.insert(tk.END, "В документе нет явно связанных docagent с ошибками, но найдены следующие типы ошибок:\n\n", "no_docagent")
                    self.results_text.tag_configure("no_docagent", foreground="dark orange")
                    
                    # Выводим типы ошибок и их количество
                    sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
                    for error_type, count in sorted_errors:
                        self.results_text.insert(tk.END, f"{error_type} - ", "error_type_name")
                        self.results_text.tag_configure("error_type_name", foreground="black", font=("Arial", 9, "bold"))
                        
                        self.results_text.insert(tk.END, f"Найдено: {count}\n", "error_type_count")
                        self.results_text.tag_configure("error_type_count", foreground="red")
                
                self.update_progress(100, "Валидация завершена!")
                
                self.status_label.config(
                    text=f"Найдено {len(errors)} ошибок валидации в {len(docagent_errors)} docagent" if docagent_errors else f"Найдено {len(errors)} ошибок валидации",
                    foreground="red"
                )
            
            # Скрываем прогресс-бар после завершения
            self.hide_progress()
            
        except Exception as e:
            # Обработка других исключений
            self.hide_progress()
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✗ Ошибка: {str(e)}\n", "general_error")
            self.results_text.tag_configure("general_error", foreground="red")
            
            messagebox.showerror(
                "Ошибка",
                f"Ошибка при валидации: {str(e)}"
            )
            self.status_label.config(
                text="Ошибка при валидации",
                foreground="red"
            )

    def check_cln_uniqueness(self, json_data):
        """
        Проверяет уникальность значений cln в пределах JSON-файла
        
        Аргументы:
            json_data -- данные JSON для проверки
            
        Возвращает:
            Словарь с повторяющимися cln и их позициями: {cln_value: [{'path': [...], 'index': n}, ...]}
        """
        all_clns = {}  # {cln_value: [{'path': [...], 'index': n}, ...]}
        
        def scan_for_cln(node, path=None):
            if path is None:
                path = []
                
            if isinstance(node, dict):
                # Проверяем, является ли текущий узел docagentinfo с полем cln
                if "docagentinfo" in node and isinstance(node["docagentinfo"], dict):
                    docagentinfo = node["docagentinfo"]
                    
                    if "cln" in docagentinfo:
                        cln_value = str(docagentinfo["cln"]).strip()
                        
                        # Пропускаем пустые значения cln
                        if cln_value:
                            # Получаем индекс docagent в массиве
                            docagent_index = None
                            for i, p in enumerate(path):
                                if p == "docagent" and i+1 < len(path) and isinstance(path[i+1], int):
                                    docagent_index = path[i+1]
                                    break
                            
                            # Сохраняем путь и индекс
                            cln_info = {
                                'path': path + ["docagentinfo", "cln"],
                                'index': docagent_index
                            }
                            
                            if cln_value in all_clns:
                                all_clns[cln_value].append(cln_info)
                            else:
                                all_clns[cln_value] = [cln_info]
                
                # Рекурсивно обрабатываем все значения словаря
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        scan_for_cln(value, path + [key])
                        
            elif isinstance(node, list):
                # Рекурсивно обрабатываем все элементы списка
                for i, item in enumerate(node):
                    if isinstance(item, (dict, list)):
                        scan_for_cln(item, path + [i])
        
        # Начинаем рекурсивный поиск
        scan_for_cln(json_data)
        
        # Фильтруем только дубликаты (больше одного вхождения)
        duplicates = {cln: positions for cln, positions in all_clns.items() if len(positions) > 1}
        
        return duplicates

    def collect_validation_errors(self, json_data, json_str, ignore_multiples=False, update_progress=None):
        """Собирает все ошибки валидации в список с подробной информацией
        
        Аргументы:
            json_data -- данные JSON для валидации
            json_str -- строковое представление JSON
            ignore_multiples -- игнорировать ли ошибки кратности
            update_progress -- функция для обновления прогресс-бара
            
        Возвращает:
            Список кортежей (сообщение_об_ошибке, путь, номер_строки, значение, схема, docagent_info)
        """
        from jsonschema.validators import validator_for
        
        # Сначала подсчитаем количество блоков docagent в JSON для прогресс-бара
        if update_progress:
            docagent_count = self.count_docagent_blocks(json_data)
            if docagent_count > 0:
                update_progress(40, f"Подготовка к валидации {docagent_count} блоков docagent...")
        
        errors = []
        validator_class = validator_for(self.current_schema)
        validator = validator_class(self.current_schema)
        
        # Счетчик обработанных блоков docagent для прогресс-бара
        processed_blocks = 0
        docagent_paths = {}  # Для отслеживания путей до docagent
        
        for error in validator.iter_errors(json_data):
            error_message = error.message
            translated_message = self.translate_error_message(error_message)
            error_path = list(error.path)
            line_number = self.find_line_from_path(json_str, error_path)
            
            # Если это ошибка кратности и мы их игнорируем, пропускаем
            if ignore_multiples and "not a multiple of" in error_message:
                continue
            
            # Получаем значение, вызвавшее ошибку
            instance_value = error.instance
            
            # Получаем информацию о схеме для данного пути
            schema_info = self.get_schema_info_for_error(error)
            
            # Получаем информацию о docagent, если она есть
            docagent_info = self.get_docagent_info(json_data, error_path)
            
            # Обновляем прогресс-бар, если найден новый блок docagent
            if update_progress and docagent_info:
                # Создаем уникальный идентификатор для этого docagent
                docagent_id = None
                if "Индекс в массиве docagent" in docagent_info:
                    docagent_id = docagent_info["Индекс в массиве docagent"]
                    
                # Если это новый блок docagent, увеличиваем счетчик
                if docagent_id is not None and docagent_id not in docagent_paths:
                    docagent_paths[docagent_id] = True
                    processed_blocks += 1
                    
                    # Обновляем прогресс-бар примерно каждые 5% или на каждом 10-м блоке
                    if docagent_count > 0 and (processed_blocks % max(1, docagent_count // 20) == 0 or processed_blocks == docagent_count):
                        progress = 40 + int((processed_blocks / docagent_count) * 30)  # От 40% до 70%
                        update_progress(progress, f"Валидация docagent {processed_blocks}/{docagent_count}...")
            
            errors.append((translated_message, error_path, line_number, instance_value, schema_info, docagent_info))
        
        return errors
    
    def count_docagent_blocks(self, json_data):
        """Подсчитывает количество блоков docagent в JSON структуре
        
        Аргументы:
            json_data -- данные JSON для анализа
            
        Возвращает:
            Количество найденных блоков docagent
        """
        count = 0
        
        def traverse(node, path=None):
            nonlocal count
            if path is None:
                path = []
                
            if isinstance(node, dict):
                # Проверяем, является ли текущий узел docagent с docagentinfo
                if "docagentinfo" in node and isinstance(node["docagentinfo"], dict):
                    count += 1
                
                # Рекурсивная обработка вложенных словарей
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse(value, path + [key])
                        
            elif isinstance(node, list):
                # Рекурсивная обработка элементов списка
                for i, item in enumerate(node):
                    if isinstance(item, (dict, list)):
                        traverse(item, path + [i])
        
        # Начинаем обход структуры JSON
        traverse(json_data)
        return count

    def get_schema_info_for_error(self, error):
        """Получает информацию о схеме для конкретной ошибки"""
        schema_info = ""
        
        # Извлекаем информацию из схемы на основе типа ошибки
        if hasattr(error, 'validator'):
            validator_type = error.validator
            
            if validator_type == 'type':
                schema_info = f"Ожидаемый тип: {error.validator_value}"
            elif validator_type == 'enum':
                schema_info = f"Допустимые значения: {error.validator_value}"
            elif validator_type == 'pattern':
                schema_info = f"Должно соответствовать шаблону: {error.validator_value}"
            elif validator_type == 'format':
                schema_info = f"Должно соответствовать формату: {error.validator_value}"
            elif validator_type == 'required':
                schema_info = f"Обязательные поля: {error.validator_value}"
            elif validator_type == 'maxLength':
                schema_info = f"Максимальная длина: {error.validator_value}"
            elif validator_type == 'minLength':
                schema_info = f"Минимальная длина: {error.validator_value}"
            elif validator_type == 'maximum':
                schema_info = f"Максимальное значение: {error.validator_value}"
            elif validator_type == 'minimum':
                schema_info = f"Минимальное значение: {error.validator_value}"
            elif validator_type == 'multipleOf':
                schema_info = f"Должно быть кратно: {error.validator_value}"
            elif validator_type == 'additionalProperties':
                schema_info = "Дополнительные свойства не разрешены"
            else:
                schema_info = f"Валидатор: {validator_type}, значение: {error.validator_value}"
        
        return schema_info

    def get_docagent_info(self, json_data, error_path):
        """Извлекает информацию о блоке docagent по пути ошибки"""
        try:
            # Найдем индекс блока docagent в пути ошибки
            docagent_index = -1
            docagent_array_index = -1
            
            # Просматриваем путь для поиска docagent или его части
            for i, path_element in enumerate(error_path):
                if path_element == "docagent" and i + 1 < len(error_path) and isinstance(error_path[i + 1], int):
                    docagent_index = i
                    docagent_array_index = error_path[i + 1]
                    break
            
            # Если docagent не найден, проверяем, возможно мы уже внутри docagent
            if docagent_index == -1:
                # Ищем "docagentinfo" в пути - это указывает, что мы внутри блока docagent
                for i, path_element in enumerate(error_path):
                    if path_element == "docagentinfo":
                        # Ищем индекс docagent, просматривая путь в обратном порядке
                        for j in range(i-1, -1, -1):
                            if j >= 0 and isinstance(error_path[j], int) and j > 0 and error_path[j-1] == "docagent":
                                docagent_index = j-1  # Индекс "docagent" в пути
                                docagent_array_index = error_path[j]  # Индекс в массиве docagent
                                break
                        break
            
            # Если docagent все еще не найден, возвращаем None
            if docagent_index == -1:
                return None
                
            # Построим путь к блоку docagent
            path_to_docagent = error_path[:docagent_index + 2]  # Включаем "docagent" и индекс в массиве
            
            # Извлекаем данные по пути
            docagent_block = json_data
            for path_element in path_to_docagent:
                if isinstance(docagent_block, dict) and path_element in docagent_block:
                    docagent_block = docagent_block[path_element]
                elif isinstance(docagent_block, list) and isinstance(path_element, int) and path_element < len(docagent_block):
                    docagent_block = docagent_block[path_element]
                else:
                    return None  # Путь не существует
            
            # Проверяем, что блок содержит docagentinfo
            if not isinstance(docagent_block, dict):
                return None
            
            result = {}
            
            # Добавляем индекс в массиве для точной идентификации
            result["Индекс в массиве docagent"] = docagent_array_index
            
            # Проверяем, есть ли docagentinfo в блоке
            if "docagentinfo" in docagent_block and isinstance(docagent_block["docagentinfo"], dict):
                docagentinfo = docagent_block["docagentinfo"]
                
                # Извлекаем нужные поля с проверкой их существования
                if "vfam" in docagentinfo:
                    result["Фамилия (vfam)"] = docagentinfo["vfam"]
                    
                if "vname" in docagentinfo:
                    result["Имя (vname)"] = docagentinfo["vname"]
                    
                if "votch" in docagentinfo:
                    result["Отчество (votch)"] = docagentinfo["votch"]
                    
                # Добавляем cln, даже если он пустой
                if "cln" in docagentinfo:
                    result["cln"] = docagentinfo["cln"]
            
            return result
                
        except Exception as e:
            # При любых ошибках просто возвращаем None
            print(f"Ошибка при извлечении информации о docagent: {str(e)}")
            return None

    def get_docagent_identifier(self, docagent_info):
        """Создает уникальный идентификатор для docagent на основе его информации"""
        if not docagent_info:
            return None
        
        # Формируем фамилию и инициалы, если они доступны
        name_parts = []
        if "Фамилия (vfam)" in docagent_info and docagent_info["Фамилия (vfam)"]:
            name_parts.append(docagent_info["Фамилия (vfam)"])
            
            if "Имя (vname)" in docagent_info and docagent_info["Имя (vname)"]:
                name_parts.append(docagent_info["Имя (vname)"][0] + ".")
                
            if "Отчество (votch)" in docagent_info and docagent_info["Отчество (votch)"]:
                name_parts.append(docagent_info["Отчество (votch)"][0] + ".")
        
        full_name = " ".join(name_parts) if name_parts else None
        
        # Пробуем использовать cln как основной идентификатор, если он не пустой
        if "cln" in docagent_info and docagent_info["cln"]:
            cln_str = str(docagent_info["cln"]).strip()
            # Если cln не пустой, используем его
            if cln_str:
                # Добавляем имя к cln для лучшей идентификации
                if full_name:
                    return f"{full_name} (cln: {cln_str})"
                else:
                    return f"cln: {cln_str}"
        
        # Если cln пустой или не существует, используем фамилию и индекс
        if full_name and "Индекс в массиве docagent" in docagent_info:
            return f"{full_name} (индекс: {docagent_info['Индекс в массиве docagent']})"
        
        # Если нет имени, используем только индекс
        if "Индекс в массиве docagent" in docagent_info:
            return f"Индекс docagent: {docagent_info['Индекс в массиве docagent']}"
        
        # Если даже индекса нет, возвращаем неизвестный идентификатор
        import random
        return f"Неизвестный docagent #{random.randint(1000, 9999)}"

    def round_monetary_values(self, json_obj):
        """Обработка чисел с плавающей точкой с помощью Decimal для точного представления"""
        if isinstance(json_obj, dict):
            for key, value in list(json_obj.items()):
                if isinstance(value, float):
                    # Используем Decimal для точного представления
                    decimal_value = Decimal(str(value))
                    
                    # Проверяем, делится ли значение точно на 0.01
                    if decimal_value % Decimal('0.01') != 0:
                        # Корректируем до ближайшего кратного 0.01
                        decimal_value = (decimal_value // Decimal('0.01')) * Decimal('0.01')
                    
                    # Преобразуем обратно в float для совместимости
                    json_obj[key] = float(decimal_value)
                    
                elif isinstance(value, (dict, list)):
                    self.round_monetary_values(value)
                    
        elif isinstance(json_obj, list):
            for i, item in enumerate(json_obj):
                if isinstance(item, float):
                    # Тот же метод округления для элементов списка
                    decimal_value = Decimal(str(item))
                    
                    # Проверяем и корректируем
                    if decimal_value % Decimal('0.01') != 0:
                        decimal_value = (decimal_value // Decimal('0.01')) * Decimal('0.01')

                    json_obj[i] = float(decimal_value)
                    
                elif isinstance(item, (dict, list)):
                    self.round_monetary_values(item)
                    
        return json_obj

    def delete_docagent_by_cln(self):
        """Удаляет блок docagent из JSON файла по указанному cln"""
        try:
            # Запрос JSON файла
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл для удаления docagent",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
            
            # Запрос cln для поиска и удаления docagent
            cln_to_delete = simpledialog.askstring("Ввод cln", "Введите cln docagent для удаления:")
            if not cln_to_delete:
                return
            
            # Показываем прогресс-бар
            self.show_progress("Загрузка JSON файла...")
            
            # Загрузка данных из файла
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            self.update_progress(40, "Поиск и удаление docagent...")
            
            # Поиск и удаление всех docagent с указанным cln
            deleted_count = self.remove_docagent_by_cln(json_data, cln_to_delete)
            
            self.update_progress(70, "Проверка результатов удаления...")
            
            if deleted_count == 0:
                self.hide_progress()
                messagebox.showinfo(
                    "Информация", 
                    f"Docagent с cln={cln_to_delete} не найден в файле."
                )
                self.status_label.config(
                    text=f"Docagent с cln={cln_to_delete} не найден",
                    foreground="orange"
                )
                return
            
            self.update_progress(80, "Подготовка к сохранению...")
            
            # Запрос имени файла для сохранения результата
            save_path = filedialog.asksaveasfilename(
                title="Сохранить файл без удаленных docagent",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile=f"modified_{os.path.basename(file_path)}"
            )
            if not save_path:
                self.hide_progress()
                return
            
            self.update_progress(90, "Сохранение модифицированного файла...")
            
            # Сохранение модифицированного JSON в новый файл
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            self.update_progress(95, "Формирование отчета...")
            
            # Вывод информации об успешном удалении
            messagebox.showinfo(
                "Успех", 
                f"Удалено {deleted_count} блоков docagent с cln={cln_to_delete}. "
                f"Результат сохранен в {save_path}"
            )
            self.status_label.config(
                text=f"Удалено {deleted_count} блоков docagent с cln={cln_to_delete}",
                foreground="green"
            )
            
            # Отображаем модифицированный JSON в области результатов
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Удалено {deleted_count} блоков docagent с cln={cln_to_delete}.\n\n", "success")
            self.results_text.tag_configure("success", foreground="green")
            
            # Отображаем первые 1000 символов модифицированного JSON
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            preview = json_str[:1000] + "..." if len(json_str) > 1000 else json_str
            self.results_text.insert(tk.END, "Предпросмотр JSON:\n\n", "title")
            self.results_text.tag_configure("title", font=("Arial", 10, "bold"))
            self.results_text.insert(tk.END, preview, "json")
            self.results_text.tag_configure("json", font=("Courier New", 9))
            
            self.update_progress(100, "Операция успешно завершена!")
            
            # Скрываем прогресс-бар после завершения
            self.hide_progress()
            
        except Exception as e:
            # Скрываем прогресс-бар в случае ошибки
            self.hide_progress()
            
            messagebox.showerror("Ошибка", f"Ошибка при удалении docagent: {str(e)}")
            self.status_label.config(
                text=f"Ошибка при удалении docagent: {str(e)}",
                foreground="red"
            )

    def extract_cln_from_error_file(self, content):
        """
        Извлекает CLN из файла с отчетом об ошибках
        
        Аргументы:
            content -- содержимое файла с отчетом
            
        Возвращает:
            Список уникальных CLN
        """
        # Ищем все CLN в формате "CLN: XXXXXX" из текста
        cln_matches = re.findall(r'CLN:\s*([0-9A-Z]+)', content)
        
        # Собираем их в множество для уникальности
        cln_set = set(cln_matches)
        
        return list(cln_set)

    def show_progress(self, text="Обработка файла..."):
        """Показывает прогресс-бар с указанным текстом"""
        self.progress_label.config(text=text)
        self.progress_bar["value"] = 0
        self.progress_frame.grid()
        self.root.update_idletasks()
        
    def update_progress(self, value, text=None):
        """Обновляет значение прогресс-бара и опционально текст"""
        if 0 <= value <= 100:
            self.progress_bar["value"] = value
            if text:
                self.progress_label.config(text=text)
            self.root.update_idletasks()
    
    def hide_progress(self):
        """Скрывает прогресс-бар"""
        self.progress_frame.grid_remove()
        self.root.update_idletasks()

    def save_errors_to_file(self):
        """Сохраняет только сводную часть отчета об ошибках валидации в файл errors.txt"""
        try:
            # Показываем прогресс-бар
            self.show_progress("Подготовка данных для сохранения...")
            
            # Получаем содержимое текстового поля с результатами
            error_report = self.results_text.get(1.0, tk.END)
            
            self.update_progress(20, "Проверка отчета...")
            
            # Проверяем, есть ли данные для сохранения
            if not error_report.strip():
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "Нет данных для сохранения. Сначала выполните валидацию JSON-файла."
                )
                return
                
            # Проверяем наличие сводной части в отчете
            if "СВОДКА ПО ОШИБКАМ В DOCAGENT" not in error_report:
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "В отчете не найдена сводная информация о docagent с ошибками."
                )
                return
            
            self.update_progress(40, "Подготовка диалога сохранения...")
            
            # Запрашиваем имя файла для сохранения (предлагаем errors.txt по умолчанию)
            file_path = filedialog.asksaveasfilename(
                title="Сохранить сводку об ошибках",
                defaultextension=".txt",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
                initialfile="errors_summary.txt"
            )
            
            if not file_path:
                self.hide_progress()
                return  # Пользователь отменил сохранение
            
            self.update_progress(60, "Извлечение сводной части отчета...")
                
            # Извлекаем только сводную часть отчета (после маркера СВОДКА ПО ОШИБКАМ В DOCAGENT)
            summary_start_idx = error_report.find("СВОДКА ПО ОШИБКАМ В DOCAGENT")
            if summary_start_idx >= 0:
                summary_only = error_report[summary_start_idx:]
            else:
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "Не удалось найти сводную часть отчета."
                )
                return
            
            self.update_progress(80, "Форматирование отчета...")
                
            # Создаем более структурированный отчет для сохранения в файл
            # Удаляем теги форматирования и добавляем заголовок
            current_time = self.get_current_time()
            formatted_report = f"СВОДКА ПО ОШИБКАМ ВАЛИДАЦИИ JSON\n"
            formatted_report += f"Дата и время: {current_time}\n"
            formatted_report += "=" * 80 + "\n\n"
            
            # Добавляем только сводную часть отчета
            formatted_report += self.clean_text_tags(summary_only)
            
            self.update_progress(90, "Сохранение файла...")
            
            # Сохраняем в файл
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(formatted_report)
            
            self.update_progress(100, "Файл успешно сохранен!")
                
            # Выводим сообщение об успешном сохранении
            messagebox.showinfo(
                "Информация",
                f"Сводка по ошибкам успешно сохранена в файл:\n{file_path}"
            )
            
            self.status_label.config(
                text=f"Сводка сохранена в {file_path}",
                foreground="green"
            )
            
            # Скрываем прогресс-бар
            self.hide_progress()
            
        except Exception as e:
            # Скрываем прогресс-бар в случае ошибки
            self.hide_progress()
            
            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить сводку об ошибках: {str(e)}"
            )
            self.status_label.config(
                text=f"Ошибка при сохранении сводки: {str(e)}",
                foreground="red"
            )

    def clean_text_tags(self, text):
        """Удаляет теги форматирования tkinter из текста и добавляет простое форматирование"""
        # Заменяем символы Unicode на обычные символы для лучшей совместимости
        clean_text = text.replace("✓", "+").replace("✗", "X")
        
        # Добавляем подчеркивания для заголовков
        lines = clean_text.split('\n')
        
        # Обрабатываем особые строки
        for i, line in enumerate(lines):
            # Форматируем заголовок сводки
            if "СВОДКА ПО ОШИБКАМ В DOCAGENT" in line:
                lines[i] = line
                if i+1 < len(lines):
                    lines[i+1] = "-" * len(line)
            
            # Выделяем имена docagent
            if " - Ошибок: " in line:
                # Это строка с именем docagent и количеством ошибок
                parts = line.split(" - Ошибок: ")
                if len(parts) == 2:
                    lines[i] = f"* {parts[0].strip()} - Ошибок: {parts[1].strip()}"
        
        return '\n'.join(lines)
    
    def get_current_time(self):
        """Возвращает текущую дату и время в отформатированном виде"""
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    def delete_docagents_from_error_file(self):
        """Удаляет блоки docagent из JSON-файла по cln, полученным из файла ошибок"""
        try:
            # Запрос файла со сводкой ошибок
            error_file_path = filedialog.askopenfilename(
                title="Выберите файл сводки ошибок",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
                initialfile="errors_summary.txt"
            )
            if not error_file_path:
                return
                
            # Запрос JSON-файла для очистки
            json_file_path = filedialog.askopenfilename(
                title="Выберите JSON-файл для очистки",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not json_file_path:
                return
            
            # Показываем прогресс-бар
            self.show_progress("Чтение файла ошибок...")
                
            # Чтение файла ошибок
            with open(error_file_path, 'r', encoding='utf-8') as file:
                error_content = file.read()
            
            self.update_progress(20, "Извлечение cln из файла ошибок...")
                
            # Извлечение cln из файла ошибок
            cln_values = self.extract_cln_from_error_file(error_content)
            
            if not cln_values:
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "В файле сводки ошибок не найдены значения cln."
                )
                return
                
            # Вывод информации о найденных cln для отладки
            self.status_label.config(
                text=f"Найдено {len(cln_values)} уникальных значений cln",
                foreground="blue"
            )
            
            self.update_progress(40, "Загрузка JSON файла...")
                
            # Загрузка JSON-файла
            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            self.update_progress(50, f"Поиск и удаление docagent с {len(cln_values)} cln...")
                
            # Удаление docagent по найденным cln
            total_deleted = 0
            deleted_clns = []
            
            # Обновляем прогресс-бар по мере обработки cln
            for i, cln in enumerate(cln_values):
                # Обновляем прогресс-бар каждые несколько cln или на последнем
                if i % 5 == 0 or i == len(cln_values) - 1:
                    progress = 50 + int((i / len(cln_values)) * 20)  # От 50% до 70%
                    self.update_progress(progress, f"Обработка cln {i+1}/{len(cln_values)}...")
                
                deleted_count = self.remove_docagent_by_cln(json_data, cln)
                if deleted_count > 0:
                    total_deleted += deleted_count
                    deleted_clns.append(cln)
            
            self.update_progress(70, "Проверка результатов удаления...")
                    
            if total_deleted == 0:
                self.hide_progress()
                messagebox.showinfo(
                    "Информация",
                    "Не найдено docagent с указанными cln для удаления."
                )
                return
            
            self.update_progress(80, "Подготовка к сохранению файла...")
                
            # Запрос места для сохранения очищенного JSON-файла
            save_path = filedialog.asksaveasfilename(
                title="Сохранить очищенный JSON-файл",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile=f"cleaned_{os.path.basename(json_file_path)}"
            )
            if not save_path:
                self.hide_progress()
                return
            
            self.update_progress(90, "Сохранение очищенного JSON файла...")
                
            # Сохранение очищенного JSON-файла
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            self.update_progress(95, "Формирование отчета...")
                
            # Вывод результатов
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Удалено {total_deleted} блоков docagent с {len(deleted_clns)} различными cln.\n\n", "success")
            self.results_text.tag_configure("success", foreground="green")
            
            self.results_text.insert(tk.END, "Удалены следующие cln:\n", "title")
            self.results_text.tag_configure("title", font=("Arial", 10, "bold"))
            
            for i, cln in enumerate(deleted_clns, 1):
                self.results_text.insert(tk.END, f"{i}. cln: {cln}\n", "cln")
            self.results_text.tag_configure("cln", foreground="blue")
            
            # Отображение предпросмотра очищенного JSON
            self.results_text.insert(tk.END, "\nПредпросмотр очищенного JSON:\n", "preview_title")
            self.results_text.tag_configure("preview_title", font=("Arial", 10, "bold"))
            
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            preview = json_str[:1000] + "..." if len(json_str) > 1000 else json_str
            self.results_text.insert(tk.END, preview, "json")
            self.results_text.tag_configure("json", font=("Courier New", 9))
            
            self.update_progress(100, "Операция успешно завершена!")
            
            messagebox.showinfo(
                "Успех",
                f"Удалено {total_deleted} блоков docagent. Результат сохранен в {save_path}"
            )
            
            self.status_label.config(
                text=f"Удалено {total_deleted} блоков docagent с {len(deleted_clns)} cln",
                foreground="green"
            )
            
            # Скрываем прогресс-бар после завершения
            self.hide_progress()
            
        except Exception as e:
            # Скрываем прогресс-бар в случае ошибки
            self.hide_progress()
            
            messagebox.showerror(
                "Ошибка",
                f"Ошибка при удалении docagent: {str(e)}"
            )
            self.status_label.config(
                text=f"Ошибка при массовом удалении docagent: {str(e)}",
                foreground="red"
            )

    def sync_tar14_with_tar4(self):
        """Синхронизирует записи в блоке tar14 с соответствующими записями в блоке tar4 по nmonth"""
        try:
            # Запрос JSON файла
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл для синхронизации tar14/tar4",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not file_path:
                return
            
            # Показываем прогресс-бар
            self.show_progress("Загрузка JSON файла...")
            
            # Чтение содержимого файла
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            
            self.update_progress(20, "Анализ структуры JSON...")
            
            # Вызываем функцию для поиска и синхронизации tar14 с tar4
            total_docagents, modified_docagents, total_added_records = self.process_tar_blocks(json_data)
            
            if modified_docagents == 0:
                self.update_progress(100, "Синхронизация завершена")
                self.hide_progress()
                messagebox.showinfo(
                    "Информация",
                    "Все блоки tar14 уже синхронизированы с tar4 или блоки не найдены."
                )
                self.status_label.config(
                    text="Изменений не требуется",
                    foreground="blue"
                )
                return
            
            self.update_progress(80, "Подготовка к сохранению результатов...")
            
            # Запрос пути для сохранения модифицированного файла
            save_path = filedialog.asksaveasfilename(
                title="Сохранить синхронизированный JSON-файл",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile=f"synced_{os.path.basename(file_path)}"
            )
            if not save_path:
                self.hide_progress()
                return
            
            self.update_progress(90, "Сохранение синхронизированного JSON...")
            
            # Сохранение модифицированного JSON в новый файл
            with open(save_path, 'w', encoding='utf-8') as file:
                json.dump(json_data, file, indent=2, ensure_ascii=False)
            
            self.update_progress(95, "Формирование отчета...")
            
            # Отображаем результаты в области вывода
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Синхронизация tar14 с tar4 завершена успешно!\n\n", "success")
            self.results_text.tag_configure("success", foreground="green")
            
            self.results_text.insert(tk.END, f"Обработано docagent: {total_docagents}\n", "info")
            self.results_text.insert(tk.END, f"Модифицировано docagent: {modified_docagents}\n", "info")
            self.results_text.insert(tk.END, f"Добавлено записей в tar14: {total_added_records}\n\n", "info")
            self.results_text.tag_configure("info", foreground="blue")
            
            # Отображаем превью модифицированного JSON
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            preview = json_str[:1000] + "..." if len(json_str) > 1000 else json_str
            self.results_text.insert(tk.END, "Предпросмотр JSON:\n\n", "title")
            self.results_text.tag_configure("title", font=("Arial", 10, "bold"))
            self.results_text.insert(tk.END, preview, "json")
            self.results_text.tag_configure("json", font=("Courier New", 9))
            
            self.update_progress(100, "Синхронизация успешно завершена!")
            
            messagebox.showinfo(
                "Успех",
                f"Синхронизировано {modified_docagents} блоков docagent, добавлено {total_added_records} записей. "
                f"Результат сохранен в {save_path}"
            )
            
            self.status_label.config(
                text=f"Синхронизировано {modified_docagents} блоков docagent, добавлено {total_added_records} записей",
                foreground="green"
            )
            
            # Скрываем прогресс-бар после завершения
            self.hide_progress()
            
        except Exception as e:
            # Скрываем прогресс-бар в случае ошибки
            self.hide_progress()
            
            messagebox.showerror("Ошибка", f"Ошибка при синхронизации tar14/tar4: {str(e)}")
            self.status_label.config(
                text=f"Ошибка при синхронизации: {str(e)}",
                foreground="red"
            )

    def process_tar_blocks(self, json_data):
        """
        Рекурсивно обходит JSON структуру, находит блоки docagent и сравнивает tar14 с tar4
        
        Аргументы:
            json_data -- данные JSON для обработки
            
        Возвращает:
            (total_docagents, modified_docagents, total_added_records) - количество обработанных/измененных блоков и добавленных записей
        """
        total_docagents = 0
        modified_docagents = 0
        total_added_records = 0
        
        def process_node(node, path=None):
            nonlocal total_docagents, modified_docagents, total_added_records
            
            if path is None:
                path = []
                
            if isinstance(node, dict):
                # Проверяем, является ли текущий узел docagent
                if "docagentinfo" in node and isinstance(node["docagentinfo"], dict):
                    total_docagents += 1
                    
                    # Обновляем прогресс-бар
                    self.update_progress(
                        20 + int((total_docagents % 100) / 100 * 60),
                        f"Обработка docagent #{total_docagents}..."
                    )
                    
                    # Проверяем наличие блоков tar4 и tar14
                    if "tar4" in node and "tar14" in node:
                        if isinstance(node["tar4"], list) and isinstance(node["tar14"], list):
                            was_modified, added_records = self.sync_tar_blocks(node["tar4"], node["tar14"])
                            
                            if was_modified:
                                modified_docagents += 1
                                total_added_records += added_records
                
                # Рекурсивно обрабатываем все значения словаря
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        process_node(value, path + [key])
                        
            elif isinstance(node, list):
                # Рекурсивно обрабатываем все элементы списка
                for i, item in enumerate(node):
                    if isinstance(item, (dict, list)):
                        process_node(item, path + [i])
        
        # Начинаем рекурсивный поиск с корня JSON
        process_node(json_data)
        
        return total_docagents, modified_docagents, total_added_records

    def sync_tar_blocks(self, tar4_list, tar14_list):
        """
        Синхронизирует записи в tar14 с tar4 по полю nmonth
        
        Аргументы:
            tar4_list -- список записей из блока tar4
            tar14_list -- список записей из блока tar14
            
        Возвращает:
            (was_modified, added_records) - был ли блок изменен и количество добавленных записей
        """
        if not tar4_list:  # Если tar4 пуст, нечего синхронизировать
            return False, 0
        
        was_modified = False
        added_records = 0
        
        # Создаем словарь существующих записей в tar14 для быстрого поиска по nmonth
        tar14_dict = {}
        for item in tar14_list:
            if "nmonth" in item and isinstance(item["nmonth"], (int, float)):
                tar14_dict[item["nmonth"]] = True
        
        # Проверяем каждую запись в tar4
        for tar4_item in tar4_list:
            if "nmonth" in tar4_item and isinstance(tar4_item["nmonth"], (int, float)):
                nmonth_value = tar4_item["nmonth"]
                
                # Если такой nmonth отсутствует в tar14, добавляем его
                if nmonth_value not in tar14_dict:
                    new_tar14_item = {
                        "nmonth": nmonth_value,
                        "nsumt": 0,
                        "nsumdiv": 0
                    }
                    tar14_list.append(new_tar14_item)
                    tar14_dict[nmonth_value] = True
                    was_modified = True
                    added_records += 1
        
        return was_modified, added_records

    def remove_docagent_by_cln(self, json_data, cln):
        """Рекурсивно ищет и удаляет блоки docagent с заданным cln"""
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, dict) and "docagentinfo" in value:
                    if value["docagentinfo"].get("cln") == cln:
                        del json_data[key]
                    else:
                        self.remove_docagent_by_cln(value, cln)
                elif isinstance(value, list):
                    for item in value:
                        self.remove_docagent_by_cln(item, cln)
        elif isinstance(json_data, list):
            for item in json_data:
                self.remove_docagent_by_cln(item, cln)

    def extract_docagents_by_cln_list(self):
        """Создает выборку docagent по списку CLN из текстового файла"""
        try:
            # Запрос файла со списком CLN
            cln_file_path = filedialog.askopenfilename(
                title="Выберите файл со списком CLN",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if not cln_file_path:
                return
                
            # Запрос исходного JSON файла
            json_file_path = filedialog.askopenfilename(
                title="Выберите исходный JSON файл",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            if not json_file_path:
                return
                
            # Показываем прогресс-бар
            self.show_progress("Чтение списка CLN...")
            
            # Читаем список CLN из файла
            with open(cln_file_path, 'r', encoding='utf-8') as f:
                cln_content = f.read()
                
            # Извлекаем CLN из содержимого файла
            cln_list = self.extract_cln_from_file(cln_content)
            
            # Преобразуем все CLN в верхний регистр для единообразия
            cln_list = [cln.upper() for cln in cln_list]
            
            if not cln_list:
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "В указанном файле не найдены значения CLN."
                )
                return
                
            self.update_progress(20, f"Найдено {len(cln_list)} CLN в файле...")
            
            # Читаем исходный JSON файл
            self.update_progress(30, "Загрузка JSON файла...")
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            # Создаем копию структуры без блоков docagent
            self.update_progress(40, "Создание базовой структуры...")
            base_structure = self.create_base_structure(json_data)
            
            # Извлекаем нужные блоки docagent
            self.update_progress(50, "Поиск и извлечение блоков docagent...")
            extracted_docagents = []
            total_found = self.extract_docagents(json_data, cln_list, extracted_docagents)
            
            # Если не найдено ни одного блока docagent
            if total_found == 0:
                self.hide_progress()
                messagebox.showinfo(
                    "Информация",
                    f"Не найдено блоков docagent с указанными CLN ({len(cln_list)} CLN)."
                )
                self.status_label.config(
                    text="Блоки docagent не найдены",
                    foreground="blue"
                )
                return
            
            # Добавляем извлеченные блоки в базовую структуру
            self.update_progress(80, "Формирование итогового JSON...")
            result_json = self.merge_docagents_to_structure(base_structure, extracted_docagents)
            
            # Проверяем, есть ли docagent в результате (теперь в pckagent)
            if "pckagent" not in result_json or "docagent" not in result_json["pckagent"] or not result_json["pckagent"]["docagent"]:
                self.hide_progress()
                messagebox.showwarning(
                    "Предупреждение",
                    "Ошибка при добавлении docagent в результирующий файл."
                )
                self.status_label.config(
                    text="Ошибка при создании выборки",
                    foreground="red"
                )
                return
                
            # Запрос пути для сохранения результата
            self.update_progress(90, "Подготовка к сохранению результатов...")
            save_path = filedialog.asksaveasfilename(
                title="Сохранить выборку docagent",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfile=f"docagents_extract_{os.path.basename(json_file_path)}"
            )
            if not save_path:
                self.hide_progress()
                return
            
            # Сохраняем результат
            self.update_progress(95, "Сохранение результатов...")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, indent=2, ensure_ascii=False)
            
            # Выводим отчет
            self.update_progress(100, "Завершение работы...")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"✓ Выборка docagent успешно создана!\n\n", "success")
            self.results_text.tag_configure("success", foreground="green")
            
            self.results_text.insert(tk.END, f"Всего CLN в списке: {len(cln_list)}\n", "info")
            self.results_text.insert(tk.END, f"Найдено и извлечено docagent: {total_found}\n", "info")
            self.results_text.insert(tk.END, f"Сохранено в файл: {save_path}\n\n", "info")
            self.results_text.tag_configure("info", foreground="blue")
            
            # Список найденных CLN
            self.results_text.insert(tk.END, "Найдены следующие CLN:\n", "title")
            self.results_text.tag_configure("title", font=("Arial", 10, "bold"))
            
            for found_cln in sorted([str(docagent.get("cln", "Нет CLN")) for docagent in extracted_docagents]):
                self.results_text.insert(tk.END, f"- {found_cln}\n", "found_cln")
            self.results_text.tag_configure("found_cln", foreground="green")
            
            # Список не найденных CLN
            found_cln_set = set([str(docagent.get("cln", "")).upper() for docagent in extracted_docagents])
            not_found_cln = [cln for cln in cln_list if cln.upper() not in found_cln_set]
            
            if not_found_cln:
                self.results_text.insert(tk.END, "\nНе найдены следующие CLN:\n", "title_not_found")
                self.results_text.tag_configure("title_not_found", font=("Arial", 10, "bold"))
                
                for not_found in sorted(not_found_cln):
                    self.results_text.insert(tk.END, f"- {not_found}\n", "not_found_cln")
                self.results_text.tag_configure("not_found_cln", foreground="red")
            
            # Вывод превью JSON
            self.results_text.insert(tk.END, "\nПредпросмотр JSON:\n", "preview_title")
            self.results_text.tag_configure("preview_title", font=("Arial", 10, "bold"))
            
            json_str = json.dumps(result_json, indent=2, ensure_ascii=False)
            preview = json_str[:1000] + "..." if len(json_str) > 1000 else json_str
            self.results_text.insert(tk.END, preview, "json")
            self.results_text.tag_configure("json", font=("Courier New", 9))
            
            # Успешное выполнение
            messagebox.showinfo(
                "Успех",
                f"Найдено и извлечено {total_found} блоков docagent. Результат сохранен в файл {save_path}"
            )
            
            self.status_label.config(
                text=f"Извлечено {total_found} блоков docagent из {len(cln_list)} в списке",
                foreground="green"
            )
            
            self.hide_progress()
            
        except Exception as e:
            self.hide_progress()
            messagebox.showerror("Ошибка", f"Ошибка при создании выборки docagent: {str(e)}")
            self.status_label.config(
                text=f"Ошибка при создании выборки: {str(e)}",
                foreground="red"
            )

    def extract_cln_from_file(self, content):
        """
        Извлекает список CLN из содержимого текстового файла.
        Каждая строка файла содержит отдельный CLN.
        CLN - это набор цифр и заглавных букв латинского алфавита (например, 4090773C014PB3).
        Пустые строки игнорируются.
        
        Аргументы:
            content -- содержимое файла со списком CLN
            
        Возвращает:
            Список уникальных CLN
        """
        cln_list = []
        
        # Разбиваем содержимое на строки
        lines = content.splitlines()
        print(f"Прочитано {len(lines)} строк из файла CLN")
        
        for i, line in enumerate(lines):
            # Очищаем строку от лишних пробелов
            line = line.strip()
            
            # Пропускаем пустые строки
            if not line:
                continue
            
            # Для отладки
            print(f"Обработка строки #{i+1}: '{line}'")
                
            # Если строка содержит только цифры и буквы A-Z, используем её как есть
            if re.match(r'^[0-9A-Z]+$', line):
                cln = line
                cln_list.append(cln)
                print(f"  Найден CLN (прямое совпадение): {cln}")
            else:
                # Иначе пытаемся извлечь CLN из строки с помощью регулярного выражения
                match = re.search(r'[0-9A-Z]+', line)
                if match:
                    cln = match.group(0)
                    cln_list.append(cln)
                    print(f"  Найден CLN (через regex): {cln}")
                else:
                    print(f"  CLN не найден в строке")
        
        # Убираем дубликаты, преобразуя список в множество и обратно
        unique_cln = list(set(cln_list))
        print(f"Всего найдено уникальных CLN: {len(unique_cln)}")
        for cln in unique_cln:
            print(f"  - {cln}")
            
        return unique_cln

    def create_base_structure(self, json_data):
        """
        Создает копию структуры JSON без блоков docagent,
        но сохраняет структуру pckagent
        
        Аргументы:
            json_data -- исходные данные JSON
            
        Возвращает:
            Копию структуры без блоков docagent, но с сохранением pckagent
        """
        if isinstance(json_data, dict):
            # Если это словарь, создаем новый словарь
            result = {}
            for key, value in json_data.items():
                # Если это pckagent, сохраняем его структуру, но удаляем docagent
                if key == "pckagent":
                    result[key] = {}
                    # Копируем все из pckagent, кроме docagent
                    for subkey, subvalue in value.items():
                        if subkey != "docagent":
                            result[key][subkey] = self.create_base_structure(subvalue)
                # Для остальных ключей рекурсивно обрабатываем значения
                else:
                    result[key] = self.create_base_structure(value)
            return result
        elif isinstance(json_data, list):
            # Если это список, обрабатываем каждый элемент
            result = []
            for item in json_data:
                # Проверяем, является ли элемент списка блоком docagent
                if isinstance(item, dict) and "docagentinfo" in item:
                    continue  # Пропускаем блоки docagent в списках
                else:
                    result.append(self.create_base_structure(item))
            return result
        else:
            # Для простых типов просто возвращаем значение
            return json_data

    def extract_docagents(self, json_data, cln_list, extracted_docagents, path=None):
        """
        Рекурсивно ищет блоки docagent с указанными CLN
        
        Аргументы:
            json_data -- исходные данные JSON
            cln_list -- список CLN для поиска
            extracted_docagents -- список для сохранения найденных блоков docagent
            path -- текущий путь в JSON-структуре
            
        Возвращает:
            Количество найденных блоков docagent
        """
        if path is None:
            path = []
            print(f"Начало поиска блоков docagent. Список CLN: {cln_list}")
            
        found_count = 0
        
        if isinstance(json_data, dict):
            # Проверяем, является ли текущий узел docagent
            if "docagentinfo" in json_data and isinstance(json_data["docagentinfo"], dict):
                # Получаем CLN из docagentinfo
                cln_value = json_data["docagentinfo"].get("cln")
                
                # Преобразуем CLN в строку верхнего регистра для сравнения
                cln_str = str(cln_value).upper() if cln_value is not None else ""
                
                # Отладка: выводим информацию о найденном docagent
                print(f"Найден docagent с CLN: {cln_str}, путь: {path}")
                
                # Сравниваем CLN со списком (все в верхнем регистре)
                cln_found = False
                for search_cln in cln_list:
                    if search_cln.upper() == cln_str:
                        cln_found = True
                        print(f"CLN {cln_str} совпадает с {search_cln} в списке, добавляем в результат")
                        break
                
                # Если CLN найден в списке, добавляем в результат
                if cln_found:
                    # Сохраняем информацию о docagent для отчета и весь блок целиком
                    docagent_info = {
                        "cln": cln_value,
                        "path": path,
                        "full_data": json_data  # Сохраняем полный блок docagent
                    }
                    
                    # Добавляем ФИО, если есть
                    if "vfam" in json_data["docagentinfo"]:
                        docagent_info["vfam"] = json_data["docagentinfo"]["vfam"]
                    if "vname" in json_data["docagentinfo"]:
                        docagent_info["vname"] = json_data["docagentinfo"]["vname"]
                    if "votch" in json_data["docagentinfo"]:
                        docagent_info["votch"] = json_data["docagentinfo"]["votch"]
                    
                    # Добавляем блок docagent в список и увеличиваем счетчик
                    extracted_docagents.append(docagent_info)
                    found_count += 1
                    
                    # Обновляем прогресс-бар
                    self.update_progress(
                        50 + min(30, found_count * 2),
                        f"Найдено {found_count} блоков docagent..."
                    )
                else:
                    print(f"CLN {cln_str} не найден в списке, пропускаем")
            
            # Рекурсивно обрабатываем все значения словаря
            for key, value in json_data.items():
                if isinstance(value, (dict, list)):
                    found_count += self.extract_docagents(value, cln_list, extracted_docagents, path + [key])
        
        elif isinstance(json_data, list):
            # Рекурсивно обрабатываем все элементы списка
            for i, item in enumerate(json_data):
                if isinstance(item, (dict, list)):
                    found_count += self.extract_docagents(item, cln_list, extracted_docagents, path + [i])
        
        # Отладка: выводим общее количество найденных блоков при завершении основного поиска
        if not path:
            print(f"Завершение поиска. Всего найдено {found_count} блоков docagent")
            
        return found_count

    def merge_docagents_to_structure(self, structure, docagent_list):
        """
        Добавляет извлеченные блоки docagent в базовую структуру.
        Помещает docagent внутрь pckagent согласно требованиям схемы.
        
        Аргументы:
            structure -- базовая структура JSON без блоков docagent
            docagent_list -- список извлеченных блоков docagent с метаданными
            
        Возвращает:
            Итоговую структуру с добавленными блоками docagent
        """
        # Создаем глубокую копию структуры, чтобы не изменять оригинал
        result = copy.deepcopy(structure)
        
        # Если список docagent_list пуст, просто возвращаем базовую структуру
        if not docagent_list:
            return result
        
        # Логгирование для отладки
        print(f"Добавление {len(docagent_list)} docagent блоков в структуру")
        
        # Проверяем наличие элемента pckagent в структуре
        if "pckagent" not in result:
            print("В структуре отсутствует элемент pckagent, создаем его")
            result["pckagent"] = {"pckagentinfo": {}}
        
        # Создаем массив docagent внутри pckagent
        if "docagent" not in result["pckagent"]:
            result["pckagent"]["docagent"] = []
        
        # Добавляем все извлеченные блоки docagent в массив
        for docagent_info in docagent_list:
            self.update_progress(
                80 + min(10, len(docagent_list)),
                f"Добавление docagent в структуру..."
            )
            
            # Извлекаем полный блок docagent из сохраненных данных
            if "full_data" in docagent_info:
                result["pckagent"]["docagent"].append(copy.deepcopy(docagent_info["full_data"]))
                print(f"Добавлен docagent с CLN: {docagent_info.get('cln', 'Нет CLN')}")
        
        # Если после добавления массив остался пустым, удаляем его
        if not result["pckagent"]["docagent"]:
            del result["pckagent"]["docagent"]
            
        return result
    
    def get_docagent_by_cln(self, cln_value, json_data=None):
        """
        Находит блок docagent по значению CLN
        
        Аргументы:
            cln_value -- значение CLN для поиска (строка)
            json_data -- данные JSON для поиска (если None, повторно запрашивается у пользователя)
            
        Возвращает:
            Блок docagent с указанным CLN или пустой docagent
        """
        # Создаем пустой шаблон на случай, если блок не будет найден
        default_docagent = {
            "docagentinfo": {
                "cln": cln_value
            }
        }
        
        # Если JSON не передан, используем пустой шаблон
        if json_data is None:
            return default_docagent
            
        # Убедимся, что значение CLN - строка для корректного сравнения
        cln_str = str(cln_value)
            
        # Рекурсивная функция для поиска блока docagent по CLN
        def find_docagent(data):
            if isinstance(data, dict):
                # Проверяем, является ли текущий узел искомым docagent
                if "docagentinfo" in data and isinstance(data["docagentinfo"], dict):
                    data_cln = data["docagentinfo"].get("cln")
                    if data_cln is not None and str(data_cln) == cln_str:
                        return data
                
                # Рекурсивно проверяем все вложенные словари и списки
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        found = find_docagent(value)
                        if found is not None:
                            return found
            
            elif isinstance(data, list):
                # Рекурсивно проверяем все элементы списка
                for item in data:
                    if isinstance(item, (dict, list)):
                        found = find_docagent(item)
                        if found is not None:
                            return found
            
            return None
        
        # Ищем блок docagent в данных
        found_docagent = find_docagent(json_data)
        
        # Возвращаем найденный блок или пустой шаблон
        return found_docagent if found_docagent is not None else default_docagent

def main():
    root = tk.Tk()
    app = JSONSchemaValidator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 