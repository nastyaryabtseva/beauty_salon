# -*- coding: utf-8 -*-
import json
import os

DATA_FILE = "salon_data.json"

# ----- ЗАГРУЗКА И СОХРАНЕНИЕ ДАННЫХ -----
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            'next_id': 1,
            'masters': {},
            'services': {},
            'appointments': {}
        }
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----- ГЛОБАЛЬНЫЕ ДАННЫЕ -----
data = load_data()
masters = data['masters']
services = data['services']
appointments = data['appointments']
next_id = data['next_id']

def sync():
    """Синхронизирует данные с файлом"""
    data['masters'] = masters
    data['services'] = services
    data['appointments'] = appointments
    data['next_id'] = next_id
    save_data(data)

def new_id():
    global next_id
    i = next_id
    next_id += 1
    sync()
    return i

def time_str_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

def minutes_to_time_str(m):
    return f"{m // 60:02d}:{m % 60:02d}"

# ----- УПРАВЛЕНИЕ МАСТЕРАМИ -----
def add_master(name, specialty):
    mid = str(new_id())
    masters[mid] = {'name': name, 'specialty': specialty}
    sync()
    print(f"✓ Мастер добавлен: {name} (ID: {mid})")
    return mid

def list_masters():
    if not masters:
        print("Нет мастеров")
        return
    print("\n--- СПИСОК МАСТЕРОВ ---")
    for mid, master in masters.items():
        print(f"  ID {mid}: {master['name']} - {master['specialty']}")

def delete_master(master_id):
    if master_id in masters:
        has_appointments = any(
            app['master_id'] == master_id 
            for app in appointments.values()
        )
        if has_appointments:
            print(f"Нельзя удалить мастера: у него есть записи")
            return False
        
        del masters[master_id]
        sync()
        print(f"Мастер удалён")
        return True
    print("Мастер не найден")
    return False

# ----- УПРАВЛЕНИЕ УСЛУГАМИ -----
def add_service(name, duration_min, price):
    sid = str(new_id())
    services[sid] = {'name': name, 'duration': duration_min, 'price': price}
    sync()
    print(f"✓ Услуга добавлена: {name} ({duration_min} мин, {price} руб) ID: {sid}")
    return sid

def list_services():
    if not services:
        print("Нет услуг")
        return
    print("\n--- СПИСОК УСЛУГ ---")
    for sid, service in services.items():
        print(f"  ID {sid}: {service['name']} - {service['duration']} мин - {service['price']} руб")

# ----- ЗАПИСЬ КЛИЕНТОВ -----
def is_master_free(master_id, date_str, start_time, duration_min):
    start = time_str_to_minutes(start_time)
    end = start + duration_min
    
    for app in appointments.values():
        if app['master_id'] == master_id and app['date'] == date_str:
            app_start = time_str_to_minutes(app['start_time'])
            app_end = app_start + app['duration']
            if not (end <= app_start or start >= app_end):
                return False
    return True

def book(client_name, master_id, service_id, date_str, time_str):
    if master_id not in masters:
        print("Ошибка: мастер не найден")
        return None
    if service_id not in services:
        print("Ошибка: услуга не найдена")
        return None
    
    service = services[service_id]
    duration = service['duration']
    
    if not is_master_free(master_id, date_str, time_str, duration):
        master = masters[master_id]
        print(f"Ошибка: мастер {master['name']} занят в {time_str} {date_str}")
        return None
    
    aid = str(new_id())
    appointments[aid] = {
        'client': client_name,
        'master_id': master_id,
        'service_id': service_id,
        'date': date_str,
        'start_time': time_str,
        'duration': duration
    }
    sync()
    
    master = masters[master_id]
    service = services[service_id]
    print(f"✓ Запись #{aid}: {client_name} → {master['name']} ({service['name']}) на {date_str} {time_str}")
    return aid

def cancel(appointment_id):
    if appointment_id in appointments:
        del appointments[appointment_id]
        sync()
        print(f"✗ Запись #{appointment_id} отменена")
        return True
    print(f"Запись #{appointment_id} не найдена")
    return False

def get_appointments_by_client(client_name):
    result = []
    for aid, app in appointments.items():
        if app['client'].lower() == client_name.lower():
            result.append((aid, app))
    return result

# ----- ПРОСМОТР РАСПИСАНИЯ -----
def show_schedule(date_str):
    print(f"\n{'='*50}")
    print(f"РАСПИСАНИЕ НА {date_str}")
    print(f"{'='*50}\n")
    
    if not masters:
        print("Нет мастеров в салоне\n")
        return
    
    for mid, master in masters.items():
        print(f"👩‍🎤 {master['name']} ({master['specialty']}):")
        found = False
        
        day_apps = []
        for app in appointments.values():
            if app['master_id'] == mid and app['date'] == date_str:
                day_apps.append(app)
        
        if not day_apps:
            print("   Свободен")
        else:
            day_apps.sort(key=lambda x: x['start_time'])
            for app in day_apps:
                sid = app['service_id']
                service = services.get(sid, {'name': '???', 'price': 0})
                end_time = time_str_to_minutes(app['start_time']) + app['duration']
                print(f"   {app['start_time']}-{minutes_to_time_str(end_time)} | {app['client']} | {service['name']} ({service['price']} руб)")
        
        print()

def show_all_appointments():
    if not appointments:
        print("\nНет записей")
        return
    
    print(f"\n{'='*50}")
    print("ВСЕ ЗАПИСИ")
    print(f"{'='*50}\n")
    
    for aid, app in appointments.items():
        master = masters.get(app['master_id'], {'name': '???'})
        service = services.get(app['service_id'], {'name': '???'})
        print(f"#{aid}: {app['client']} | {master['name']} | {service['name']} | {app['date']} {app['start_time']}")

# ----- ОТЧЁТЫ -----
def revenue_report(date_str=None):
    total = 0
    count = 0
    
    for app in appointments.values():
        if date_str is None or app['date'] == date_str:
            service = services.get(app['service_id'])
            if service:
                total += service['price']
                count += 1
    
    if date_str:
        print(f"\n--- ВЫРУЧКА ЗА {date_str} ---")
    else:
        print(f"\n--- ОБЩАЯ ВЫРУЧКА ---")
    
    print(f"Количество услуг: {count}")
    print(f"Выручка: {total} руб")
    return total

# ----- ИНТЕРАКТИВНОЕ МЕНЮ -----
def menu():
    print("\n" + "="*50)
    print("САЛОН КРАСОТЫ - СИСТЕМА УПРАВЛЕНИЯ")
    print("="*50)
    print("1. Записать клиента")
    print("2. Отменить запись")
    print("3. Показать расписание на день")
    print("4. Список мастеров")
    print("5. Список услуг")
    print("6. Добавить мастера")
    print("7. Добавить услугу")
    print("8. Все записи")
    print("9. Отчёт по выручке")
    print("0. Выход")
    print("-"*50)

def interactive():
    while True:
        menu()
        choice = input("Выберите действие: ").strip()
        
        if choice == '1':
            client = input("Имя клиента: ")
            list_masters()
            master_id = input("ID мастера: ")
            list_services()
            service_id = input("ID услуги: ")
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            time_str = input("Время начала (ЧЧ:ММ): ")
            book(client, master_id, service_id, date_str, time_str)
        
        elif choice == '2':
            show_all_appointments()
            aid = input("ID записи для отмены: ")
            cancel(aid)
        
        elif choice == '3':
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            show_schedule(date_str)
        
        elif choice == '4':
            list_masters()
        
        elif choice == '5':
            list_services()
        
        elif choice == '6':
            name = input("Имя мастера: ")
            specialty = input("Специализация: ")
            add_master(name, specialty)
        
        elif choice == '7':
            name = input("Название услуги: ")
            duration = int(input("Длительность (минут): "))
            price = int(input("Цена (руб): "))
            add_service(name, duration, price)
        
        elif choice == '8':
            show_all_appointments()
        
        elif choice == '9':
            choice2 = input("1 - за день, 2 - за всё время: ")
            if choice2 == '1':
                date_str = input("Дата (ГГГГ-ММ-ДД): ")
                revenue_report(date_str)
            else:
                revenue_report()
        
        elif choice == '0':
            print("До свидания!")
            break
        
        else:
            print("Неверный выбор!")

# ----- ДЕМОНСТРАЦИЯ + ИНТЕРАКТИВ -----
if __name__ == "__main__":
    if not masters and not services:
        add_master("Анна", "Парикмахер")
        add_master("Елена", "Маникюр")
        add_service("Стрижка", 60, 1500)
        add_service("Окрашивание", 120, 3500)
        add_service("Маникюр", 90, 2000)
        book("Мария", "2", "3", "2025-01-20", "11:00")
    
    interactive()