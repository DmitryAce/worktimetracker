import tkinter as tk
from datetime import datetime, timedelta
from string import ascii_letters, digits
from fpdf import FPDF
import os
import json
from tkinter import messagebox, ttk
import unicodedata

# Конфигурационный файл
CONFIG_FILE = "config.json"

# Загрузка конфигурации
def load_config():
    default_config = {
        "companies": {
            "WebStead": {
                "positions": ["Бэкэнд-разработчик", "Фронтенд-разработчик"],
                "employees": ["dmitryace", "ivanov_ivan"]
            },
            "TechSolutions": {
                "positions": ["Системный администратор", "DevOps инженер"],
                "employees": ["petrov_petr", "sidorova_anna"]
            }
        },
        "default_company": "WebStead"
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default_config
    return default_config

# Класс PDF с поддержкой Unicode
class UnicodePDF(FPDF):
    def __init__(self):
        super().__init__()
        try:
            self.add_font('DejaVu', '', r'fonts\DejaVuSans.ttf', uni=True)
            self.add_font('DejaVu', 'B', r'fonts\DejaVuSans-Bold.ttf', uni=True)
            self.set_font('DejaVu', '', 12)
        except:
            # Fallback if fonts not found
            self.set_font("Arial", "", 12)
            
    def header(self):
        pass

class StopwatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Профессиональный тайм-трекер")
        self.geometry("500x500")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        
        # Загрузка конфигурации
        self.config_data = load_config()
        self.companies = list(self.config_data["companies"].keys())
        
        # Текущие значения
        self.current_company = self.config_data.get("default_company", self.companies[0])
        self.current_position = self.config_data["companies"][self.current_company]["positions"][0]
        self.current_employee = self.config_data["companies"][self.current_company]["employees"][0]
        
        # Инициализация переменных состояния
        self.has_session = False
        self.is_running = False
        self.accumulated_time = 0
        self.last_start_time = None
        self.sessions = []
        
        # Создаем папки для данных
        self.data_dir = "sessions"
        self.reports_dir = "reports"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Файл данных будет создан при выборе сотрудника
        self.data_file = None
        self.update_data_file()
        
        # Загрузка сохраненных сессий
        self.load_sessions()
        
        # Стили для элементов
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10), padding=6)
        self.style.configure("Title.TLabel", font=("Arial", 14, "bold"), background="#f0f0f0")
        self.style.configure("Time.TLabel", font=("Courier New", 18, "bold"), background="#f0f0f0")
        self.style.configure("TCombobox", padding=5)
        
        # Создание элементов GUI
        self.create_widgets()
        
        # Запуск цикла обновления времени
        self.update_time()
        
        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_data_file(self):
        """Обновляет путь к файлу данных на основе текущего сотрудника"""
        self.data_file = os.path.join(
            self.data_dir, 
            f"sessions_{self.sanitize_filename(self.current_employee)}.json"
        )
    
    def sanitize_filename(self, name):
        """Очищает имя файла от недопустимых символов"""
        valid_chars = "-_.() %s%s" % (ascii_letters, digits)
        cleaned_name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
        return ''.join(c for c in cleaned_name if c in valid_chars)
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Шапка приложения
        self.header_frame = tk.Frame(self, bg="#2c6fbb", height=45)
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.title_label = tk.Label(self.header_frame, 
                                   text="Профессиональный тайм-трекер", 
                                   fg="white", 
                                   bg="#2c6fbb",
                                   font=("Arial", 16, "bold"))
        self.title_label.pack(pady=10)
        
        # Панель выбора компании, должности и сотрудника
        self.select_frame = tk.Frame(self, bg="#e6f2ff", bd=1, relief="groove")
        self.select_frame.pack(fill="x", padx=15, pady=5)
        
        # Выбор компании
        self.company_frame = tk.Frame(self.select_frame, bg="#e6f2ff")
        self.company_frame.pack(fill="x", padx=10, pady=2)
        
        self.company_label = tk.Label(self.company_frame, 
                                     text="Компания:", 
                                     font=("Arial", 9, "bold"),
                                     bg="#e6f2ff")
        self.company_label.pack(side="left")
        
        self.company_var = tk.StringVar(value=self.current_company)
        self.company_combobox = ttk.Combobox(
            self.company_frame, 
            textvariable=self.company_var,
            values=self.companies,
            state="readonly",
            width=25
        )
        self.company_combobox.pack(side="left", padx=5)
        self.company_combobox.bind("<<ComboboxSelected>>", self.on_company_selected)
        
        # Выбор должности
        self.position_frame = tk.Frame(self.select_frame, bg="#e6f2ff")
        self.position_frame.pack(fill="x", padx=10, pady=2)
        
        self.position_label = tk.Label(self.position_frame, 
                                     text="Должность:", 
                                     font=("Arial", 9, "bold"),
                                     bg="#e6f2ff")
        self.position_label.pack(side="left")
        
        # Автоматическое обновление должностей при выборе компании
        positions = self.config_data["companies"][self.current_company]["positions"]
        self.position_var = tk.StringVar(value=self.current_position)
        self.position_combobox = ttk.Combobox(
            self.position_frame, 
            textvariable=self.position_var,
            values=positions,
            state="readonly",
            width=25
        )
        self.position_combobox.pack(side="left", padx=5)
        self.position_combobox.bind("<<ComboboxSelected>>", self.on_position_selected)
        
        # Выбор сотрудника
        self.employee_frame = tk.Frame(self.select_frame, bg="#e6f2ff")
        self.employee_frame.pack(fill="x", padx=10, pady=(2, 5))
        
        self.employee_label = tk.Label(self.employee_frame, 
                                     text="Сотрудник:", 
                                     font=("Arial", 9, "bold"),
                                     bg="#e6f2ff")
        self.employee_label.pack(side="left")
        
        # Автоматическое обновление сотрудников при выборе компании
        employees = self.config_data["companies"][self.current_company]["employees"]
        self.employee_var = tk.StringVar(value=self.current_employee)
        self.employee_combobox = ttk.Combobox(
            self.employee_frame, 
            textvariable=self.employee_var,
            values=employees,
            state="readonly",
            width=25
        )
        self.employee_combobox.pack(side="left", padx=5)
        self.employee_combobox.bind("<<ComboboxSelected>>", self.on_employee_selected)
        
        # Панель времени
        self.time_frame = tk.Frame(self, bg="#f0f0f0")
        self.time_frame.pack(pady=(15, 10))
        
        # Текущая сессия
        self.session_label = tk.Label(self.time_frame, 
                                    text="Текущая сессия:", 
                                    font=("Arial", 10, "bold"),
                                    bg="#f0f0f0")
        self.session_label.grid(row=0, column=0, sticky="e", padx=5)
        
        self.current_session_label = tk.Label(self.time_frame, 
                                             text="00:00:00", 
                                             font=("Courier New", 18, "bold"),
                                             bg="#f0f0f0")
        self.current_session_label.grid(row=0, column=1, sticky="w")
        
        # Общее время
        self.total_label = tk.Label(self.time_frame, 
                                   text="Общее время:", 
                                   font=("Arial", 10, "bold"),
                                   bg="#f0f0f0")
        self.total_label.grid(row=1, column=0, sticky="e", padx=5, pady=(10, 0))
        
        self.total_time_label = tk.Label(self.time_frame, 
                                        text="00:00:00", 
                                        font=("Courier New", 18, "bold"),
                                        bg="#f0f0f0")
        self.total_time_label.grid(row=1, column=1, sticky="w", pady=(10, 0))
        
        # Кнопки управления
        self.button_frame = tk.Frame(self, bg="#f0f0f0")
        self.button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(self.button_frame, 
                                     text="Старт", 
                                     command=self.start_timer,
                                     width=10)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(self.button_frame, 
                                      text="Пауза", 
                                      command=self.pause_timer,
                                      state="disabled",
                                      width=10)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.end_button = ttk.Button(self.button_frame, 
                                    text="Завершить сессию", 
                                    command=self.end_timer,
                                    state="disabled",
                                    width=15)
        self.end_button.grid(row=0, column=2, padx=5)
        
        # Кнопки данных
        self.data_frame = tk.Frame(self, bg="#f0f0f0")
        self.data_frame.pack(pady=(5, 10))
        
        self.clear_button = ttk.Button(self.data_frame,
                                      text="Очистить все данные",
                                      command=self.clear_data,
                                      width=19)
        self.clear_button.grid(row=0, column=0, padx=5)
        
        self.report_button = ttk.Button(self.data_frame, 
                                       text="Создать отчет PDF", 
                                       command=self.generate_report,
                                       width=19)
        self.report_button.grid(row=0, column=1, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set(f"Готов | Сессий: {len(self.sessions)} | Сотрудник: {self.current_employee}")
        self.status_bar = tk.Label(self, 
                                  textvariable=self.status_var, 
                                  bd=1, 
                                  relief="sunken", 
                                  anchor="w",
                                  bg="#e0e0e0",
                                  font=("Arial", 9))
        self.status_bar.pack(side="bottom", fill="x", padx=5, pady=2)
    
    def on_company_selected(self, event):
        """Обработчик выбора компании"""
        new_company = self.company_var.get()
        if new_company != self.current_company:
            # Завершаем текущую сессию при смене компании
            if self.has_session:
                if messagebox.askyesno("Смена компании", 
                                      "При смене компании текущая сессия будет завершена. Продолжить?"):
                    self.end_timer()
                else:
                    self.company_var.set(self.current_company)
                    return
            
            self.current_company = new_company
            self.current_position = self.config_data["companies"][new_company]["positions"][0]
            self.position_var.set(self.current_position)
            self.position_combobox['values'] = self.config_data["companies"][new_company]["positions"]
            
            self.current_employee = self.config_data["companies"][new_company]["employees"][0]
            self.employee_var.set(self.current_employee)
            self.employee_combobox['values'] = self.config_data["companies"][new_company]["employees"]
            
            # Обновляем файл данных и загружаем сессии
            self.update_data_file()
            self.load_sessions()
            self.status_var.set(f"Компания изменена | Сессий: {len(self.sessions)} | Сотрудник: {self.current_employee}")
    
    def on_position_selected(self, event):
        """Обработчик выбора должности"""
        self.current_position = self.position_var.get()
    
    def on_employee_selected(self, event):
        """Обработчик выбора сотрудника"""
        new_employee = self.employee_var.get()
        if new_employee != self.current_employee:
            # Завершаем текущую сессию при смене сотрудника
            if self.has_session:
                if messagebox.askyesno("Смена сотрудника", 
                                      "При смене сотрудника текущая сессия будет завершена. Продолжить?"):
                    self.end_timer()
                else:
                    self.employee_var.set(self.current_employee)
                    return
            
            self.current_employee = new_employee
            
            # Обновляем файл данных и загружаем сессии
            self.update_data_file()
            self.load_sessions()
            self.status_var.set(f"Сотрудник изменен | Сессий: {len(self.sessions)} | Сотрудник: {self.current_employee}")
    
    def load_sessions(self):
        """Загрузка сессий из JSON файла"""
        self.sessions = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертация строковых меток времени в объекты datetime
                    self.sessions = [
                        (
                            datetime.strptime(session[0], "%Y-%m-%d %H:%M:%S"), 
                            datetime.strptime(session[1], "%Y-%m-%d %H:%M:%S"),
                            session[2]
                        )
                        for session in data
                    ]
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить сессии: {str(e)}")
                self.sessions = []
    
    def save_sessions(self):
        """Сохранение сессий в JSON файл"""
        try:
            # Конвертация объектов datetime в строки
            data = [
                (
                    start_time.strftime("%Y-%m-%d %H:%M:%S"), 
                    end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    duration
                )
                for start_time, end_time, duration in self.sessions
            ]
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить сессии: {str(e)}")
    
    def format_time(self, seconds):
        """Форматирование секунд в ЧЧ:ММ:СС"""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    def start_timer(self):
        """Запуск или возобновление таймера"""
        if not self.has_session:
            # Начало новой сессии
            self.has_session = True
            self.accumulated_time = 0
            self.is_running = True
            self.last_start_time = datetime.now()
            self.start_button.config(state="disabled")
            self.pause_button.config(state="enabled")
            self.end_button.config(state="enabled")
            self.status_var.set("Сессия начата")
        elif not self.is_running:
            # Возобновление приостановленной сессии
            self.is_running = True
            self.last_start_time = datetime.now()
            self.start_button.config(state="disabled")
            self.pause_button.config(state="enabled")
            self.status_var.set("Сессия возобновлена")
    
    def pause_timer(self):
        """Приостановка таймера"""
        if self.has_session and self.is_running:
            self.is_running = False
            elapsed = datetime.now() - self.last_start_time
            self.accumulated_time += elapsed.total_seconds()
            self.start_button.config(state="enabled")
            self.pause_button.config(state="disabled")
            self.status_var.set("Сессия приостановлена")
    
    def end_timer(self):
        """Завершение текущей сессии"""
        if self.has_session:
            start_time = self.last_start_time
            if self.is_running:
                elapsed = datetime.now() - start_time
                self.accumulated_time += elapsed.total_seconds()
                self.is_running = False
            
            end_time = datetime.now()
            self.sessions.append((start_time, end_time, self.accumulated_time))
            self.save_sessions()
            
            self.has_session = False
            self.accumulated_time = 0
            self.start_button.config(state="enabled")
            self.pause_button.config(state="disabled")
            self.end_button.config(state="disabled")
            self.status_var.set(f"Сессия завершена. Всего сессий: {len(self.sessions)}")
    
    def update_time(self):
        """Обновление отображения времени каждую секунду"""
        if self.has_session:
            if self.is_running:
                elapsed = self.accumulated_time + (datetime.now() - self.last_start_time).total_seconds()
            else:
                elapsed = self.accumulated_time
        else:
            elapsed = 0
        total_elapsed = sum(session[2] for session in self.sessions) + elapsed
        
        # Обновление форматированного времени
        self.current_session_label.config(text=self.format_time(elapsed))
        self.total_time_label.config(text=self.format_time(total_elapsed))
        
        # Визуальная индикация работающего таймера
        if self.is_running:
            self.current_session_label.config(fg="#006400")  # Темно-зеленый
        else:
            self.current_session_label.config(fg="black")
        
        self.after(1000, self.update_time)
    
    def clear_data(self):
        """Очистка всех сохраненных сессий"""
        if not self.sessions:
            messagebox.showinfo("Информация", "Нет сессий для очистки.")
            return
            
        if messagebox.askyesno("Подтверждение", 
                              "Вы уверены, что хотите удалить все данные сессий?\nЭто действие невозможно отменить."):
            self.sessions = []
            try:
                if os.path.exists(self.data_file):
                    os.remove(self.data_file)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл данных: {str(e)}")
            
            self.status_var.set(f"Данные очищены | Сессий: 0")
            self.update_time()
            messagebox.showinfo("Успех", "Все данные сессий были очищены.")
    
    def generate_report(self):
        """Генерация PDF отчета по рабочим часам с группировкой по днями цветными элементами"""
        if not self.sessions:
            messagebox.showinfo("Нет данных", "Нет записанных сессий для генерации отчета.")
            return
        
        try:
            # Создаем имя файла отчета
            report_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"{self.current_employee}_{self.current_company}_worktime_report_{report_date}.pdf"
            filename = "".join(c for c in filename if c.isalnum() or c in " _-().")
            filepath = os.path.join(self.reports_dir, filename)
            
            # Используем кастомный класс PDF с поддержкой Unicode
            pdf = UnicodePDF()
            pdf.add_page()
            
            # Цветовая палитра
            title_color = (40, 60, 150)     # Темно-синий
            accent_color = (220, 50, 50)    # Красный акцент
            header_color = (50, 120, 50)    # Зеленый для заголовков
            summary_color = (180, 80, 180)  # Фиолетовый для итогов
            
            # Заголовок отчета
            pdf.set_font("DejaVu", "B", 20)
            pdf.set_text_color(*title_color)
            pdf.cell(0, 15, "Отчет по рабочим часам", 0, 1, "C")
            
            # Информация о компании и сотруднике
            pdf.set_font("DejaVu", "B", 9)  # Уменьшен размер шрифта
            pdf.cell(50, 6, "Компания:", 0, 0)  # Уменьшена ширина ячейки
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, self.current_company, 0, 1)
            
            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(50, 6, "Сотрудник:", 0, 0)
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, self.current_employee, 0, 1)
            
            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(50, 6, "Должность:", 0, 0)
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, self.current_position, 0, 1)
            
            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(50, 6, "Дата формирования:", 0, 0)
            pdf.set_font("DejaVu", "", 9)
            # Форматирование даты в две строки при необходимости
            date_str = datetime.now().strftime('%Y-%m-%d')
            pdf.multi_cell(0, 6, date_str, 0, 1)
            
            pdf.ln(5)
            
            # Группировка сессий по дате
            sessions_by_date = {}
            for session in self.sessions:
                date_str = session[0].strftime("%Y-%m-%d")
                if date_str not in sessions_by_date:
                    sessions_by_date[date_str] = []
                sessions_by_date[date_str].append(session)
            
            # Сортировка дат
            sorted_dates = sorted(sessions_by_date.keys(), reverse=True)
            
            # Общие счетчики
            total_time = 0
            total_sessions = 0
            
            # Цвета для плашек дней (чередование)
            day_colors = [
                (200, 230, 255),  # Голубой
                (255, 230, 200),  # Персиковый
                (230, 255, 200)   # Салатовый
            ]
            text_colors = [
                (0, 50, 100),    # Темно-синий
                (100, 50, 0),    # Коричневый
                (0, 100, 50)     # Темно-зеленый
            ]
            
            for i, date_str in enumerate(sorted_dates):
                color_idx = i % len(day_colors)
                date_sessions = sessions_by_date[date_str]
                total_sessions += len(date_sessions)
                
                # Заголовок дня с цветной плашкой
                pdf.set_font("DejaVu", "B", 14)
                pdf.set_fill_color(*day_colors[color_idx])
                pdf.set_text_color(*text_colors[color_idx])
                pdf.cell(0, 10, f"Дата: {date_str}", 0, 1, "L", 1)
                pdf.ln(3)
                
                # Счетчики дня
                day_total_time = 0
                
                # Заголовки таблицы
                pdf.set_font("DejaVu", "B", 11)
                pdf.set_text_color(0, 0, 0)  # Черный
                pdf.cell(65, 8, "Начало работы", 1, 0, "C")
                pdf.cell(65, 8, "Окончание работы", 1, 0, "C")
                pdf.cell(50, 8, "Длительность", 1, 1, "C")
                
                for session in date_sessions:
                    start_time, end_time, duration = session
                    
                    # Подсчет общего времени дня
                    day_total_time += duration
                    total_time += duration
                    
                    # Добавление информации о сессии
                    pdf.set_font("DejaVu", "", 10)
                    pdf.set_text_color(0, 0, 0)  # Черный
                    pdf.cell(65, 8, start_time.strftime("%H:%M:%S"), 1, 0, "C")
                    pdf.cell(65, 8, end_time.strftime("%H:%M:%S"), 1, 0, "C")
                    pdf.cell(50, 8, self.format_time(duration), 1, 1, "C")
                
                # Итог за день
                pdf.set_font("DejaVu", "B", 10)
                pdf.set_text_color(*header_color)  # Зеленый
                pdf.cell(130, 8, f"Итого за {date_str}:", 1, 0, "R")
                pdf.set_text_color(0, 0, 0)  # Черный
                pdf.cell(50, 8, self.format_time(day_total_time), 1, 1, "C")
                pdf.ln(8)
            
            # Общий итог
            pdf.add_page()
            pdf.set_font("DejaVu", "B", 16)
            pdf.set_fill_color(230, 230, 255)  # Лавандовый фон
            pdf.set_text_color(*summary_color)  # Фиолетовый текст
            pdf.cell(0, 10, "Сводка по отчету", 0, 1, "C", 1)
            pdf.ln(12)
            
            pdf.set_font("DejaVu", "B", 12)
            pdf.set_text_color(*accent_color)  # Красный
            pdf.cell(80, 10, "Всего сессий:")
            pdf.set_text_color(0, 0, 0)  # Черный
            pdf.cell(0, 10, str(total_sessions), 0, 1)
            
            pdf.set_font("DejaVu", "B", 12)
            pdf.set_text_color(*accent_color)  # Красный
            pdf.cell(80, 10, "Общее время:")
            pdf.set_text_color(0, 0, 0)  # Черный
            pdf.cell(0, 10, self.format_time(total_time), 0, 1)
            
            pdf.set_font("DejaVu", "B", 12)
            pdf.set_text_color(*accent_color)  # Красный
            pdf.cell(80, 10, "Средняя длительность:")
            pdf.set_text_color(0, 0, 0)  # Черный
            avg = total_time / total_sessions if total_sessions > 0 else 0
            pdf.cell(0, 10, self.format_time(avg), 0, 1)
            
            # Сохранение файла
            pdf.output(filepath)
            
            # Сообщение об успехе
            self.status_var.set(f"Отчет сгенерирован: {filename}")
            messagebox.showinfo("Успех", 
                            f"PDF отчет успешно сгенерирован!\n\n"
                            f"Файл сохранен в:\n{os.path.abspath(filepath)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сгенерировать PDF отчет:\n{str(e)}")
    
    def on_close(self):
        """Обработка события закрытия окна"""
        if self.has_session:
            if messagebox.askyesno("Активная сессия", 
                                  "У вас есть активная сессия. Завершить ее перед выходом?"):
                self.end_timer()
        
        self.destroy()

if __name__ == "__main__":
    app = StopwatchApp()
    app.mainloop()