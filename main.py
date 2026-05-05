import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Загрузка избранных пользователей
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Обновление списка избранных
        self.update_favorites_list()
    
    def create_widgets(self):
        # Верхняя панель поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Поиск пользователя GitHub:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_users())
        
        self.search_button = ttk.Button(search_frame, text="Найти", command=self.search_users)
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Основное содержимое (две колонки)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая колонка - результаты поиска
        left_frame = ttk.LabelFrame(main_frame, text="Результаты поиска", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Список результатов с прокруткой
        self.results_listbox = tk.Listbox(left_frame, height=20, font=("Arial", 10))
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        results_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.config(yscrollcommand=results_scrollbar.set)
        
        # Правая колонка - избранное
        right_frame = ttk.LabelFrame(main_frame, text="Избранные пользователи", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.favorites_listbox = tk.Listbox(right_frame, height=20, font=("Arial", 10))
        self.favorites_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        fav_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.favorites_listbox.yview)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.favorites_listbox.config(yscrollcommand=fav_scrollbar.set)
        
        # Нижняя панель с кнопками действий
        action_frame = ttk.Frame(self.root, padding="10")
        action_frame.pack(fill=tk.X)
        
        self.add_favorite_button = ttk.Button(action_frame, text="★ Добавить в избранное", command=self.add_to_favorites)
        self.add_favorite_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_favorite_button = ttk.Button(action_frame, text="☆ Удалить из избранного", command=self.remove_from_favorites)
        self.remove_favorite_button.pack(side=tk.LEFT, padx=5)
        
        self.view_profile_button = ttk.Button(action_frame, text="👤 Просмотреть профиль", command=self.view_profile)
        self.view_profile_button.pack(side=tk.LEFT, padx=5)
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_favorites(self):
        """Загрузка избранных пользователей из JSON файла"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_favorites(self):
        """Сохранение избранных пользователей в JSON файл"""
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)
    
    def search_users(self):
        """Поиск пользователей через GitHub API"""
        username = self.search_entry.get().strip()
        
        # Проверка на пустое поле
        if not username:
            messagebox.showwarning("Предупреждение", "Поле поиска не должно быть пустым!")
            self.status_var.set("Ошибка: поле поиска пустое")
            return
        
        self.status_var.set(f"Поиск пользователей по запросу: {username}...")
        self.results_listbox.delete(0, tk.END)
        
        try:
            # Использование GitHub Search API
            url = f"https://api.github.com/search/users?q={username}&per_page=20"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('items', [])
                
                if users:
                    for user in users:
                        display_text = f"{user['login']} (Репозиториев: ?)"
                        self.results_listbox.insert(tk.END, display_text)
                        # Сохраняем данные пользователя в атрибут
                        if not hasattr(self, 'users_data'):
                            self.users_data = {}
                        self.users_data[display_text] = user
                    
                    # Асинхронно получаем информацию о репозиториях
                    self.root.after(100, self.fetch_repo_counts, users)
                    self.status_var.set(f"Найдено пользователей: {len(users)}")
                else:
                    self.status_var.set("Пользователи не найдены")
                    messagebox.showinfo("Результат", "Пользователи не найдены")
            else:
                self.status_var.set(f"Ошибка API: {response.status_code}")
                messagebox.showerror("Ошибка", f"Ошибка при запросе к GitHub API: {response.status_code}")
                
        except requests.RequestException as e:
            self.status_var.set(f"Ошибка сети: {str(e)}")
            messagebox.showerror("Ошибка сети", f"Не удалось подключиться к GitHub API\n{str(e)}")
    
    def fetch_repo_counts(self, users):
        """Получение количества репозиториев для каждого пользователя"""
        for user in users:
            try:
                url = f"https://api.github.com/users/{user['login']}"
                response = requests.get(url)
                if response.status_code == 200:
                    user_data = response.json()
                    repo_count = user_data.get('public_repos', 0)
                    
                    # Обновляем отображение в списке
                    for i in range(self.results_listbox.size()):
                        item = self.results_listbox.get(i)
                        if item.startswith(user['login']):
                            self.results_listbox.delete(i)
                            updated_text = f"{user['login']} (Репозиториев: {repo_count})"
                            self.results_listbox.insert(i, updated_text)
                            if hasattr(self, 'users_data') and updated_text in self.users_data:
                                pass  # Данные уже есть
                            else:
                                if not hasattr(self, 'users_data'):
                                    self.users_data = {}
                                self.users_data[updated_text] = user
                            break
            except:
                pass
    
    def add_to_favorites(self):
        """Добавление выбранного пользователя в избранное"""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Сначала выберите пользователя из результатов поиска!")
            return
        
        selected_user = self.results_listbox.get(selection[0])
        username = selected_user.split(" (Репозиториев:")[0]
        
        # Проверяем, нет ли уже в избранном
        for fav in self.favorites:
            if fav['username'] == username:
                messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном!")
                return
        
        # Получаем полную информацию о пользователе
        user_info = self.get_user_info(username)
        
        if user_info:
            favorite = {
                'username': username,
                'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'profile_url': user_info.get('html_url', f'https://github.com/{username}'),
                'avatar_url': user_info.get('avatar_url', ''),
                'public_repos': user_info.get('public_repos', 0),
                'followers': user_info.get('followers', 0),
                'following': user_info.get('following', 0),
                'bio': user_info.get('bio', 'Нет описания')
            }
            
            self.favorites.append(favorite)
            self.save_favorites()
            self.update_favorites_list()
            self.status_var.set(f"Пользователь {username} добавлен в избранное")
            messagebox.showinfo("Успех", f"Пользователь {username} добавлен в избранное!")
    
    def get_user_info(self, username):
        """Получение полной информации о пользователе через API"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def remove_from_favorites(self):
        """Удаление пользователя из избранного"""
        selection = self.favorites_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Сначала выберите пользователя из избранного!")
            return
        
        selected = self.favorites_listbox.get(selection[0])
        username = selected.split(" (добавлен:")[0]
        
        # Удаляем из списка
        self.favorites = [fav for fav in self.favorites if fav['username'] != username]
        self.save_favorites()
        self.update_favorites_list()
        self.status_var.set(f"Пользователь {username} удалён из избранного")
    
    def update_favorites_list(self):
        """Обновление отображения списка избранных"""
        self.favorites_listbox.delete(0, tk.END)
        for fav in self.favorites:
            display_text = f"{fav['username']} (добавлен: {fav['added_at']})"
            self.favorites_listbox.insert(tk.END, display_text)
    
    def view_profile(self):
        """Просмотр профиля выбранного пользователя"""
        # Проверяем, выбран ли пользователь в результатах поиска или в избранном
        selection_results = self.results_listbox.curselection()
        selection_favorites = self.favorites_listbox.curselection()
        
        username = None
        
        if selection_results:
            selected = self.results_listbox.get(selection_results[0])
            username = selected.split(" (Репозиториев:")[0]
        elif selection_favorites:
            selected = self.favorites_listbox.get(selection_favorites[0])
            username = selected.split(" (добавлен:")[0]
        else:
            messagebox.showwarning("Предупреждение", "Выберите пользователя из результатов поиска или избранного!")
            return
        
        # Получаем информацию о пользователе
        user_info = self.get_user_info(username)
        
        if user_info:
            # Создаём окно с детальной информацией
            profile_window = tk.Toplevel(self.root)
            profile_window.title(f"Профиль: {username}")
            profile_window.geometry("500x400")
            
            # Отображаем информацию
            info_text = f"""
📝 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Имя пользователя: {user_info.get('login', 'N/A')}
📛 Полное имя: {user_info.get('name', 'Не указано')}
🔗 Профиль: {user_info.get('html_url', 'N/A')}
📅 Дата регистрации: {user_info.get('created_at', 'N/A')[:10]}
🏢 Компания: {user_info.get('company', 'Не указана')}
📍 Локация: {user_info.get('location', 'Не указана')}

📊 СТАТИСТИКА
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Публичные репозитории: {user_info.get('public_repos', 0)}
👥 Подписчики: {user_info.get('followers', 0)}
🌟 Подписки: {user_info.get('following', 0)}

📝 О себе:
{user_info.get('bio', 'Нет описания')}
            """
            
            text_widget = tk.Text(profile_window, wrap=tk.WORD, font=("Courier", 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, info_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопка закрытия
            ttk.Button(profile_window, text="Закрыть", command=profile_window.destroy).pack(pady=10)
        else:
            messagebox.showerror("Ошибка", f"Не удалось получить информацию о пользователе {username}")

def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()
