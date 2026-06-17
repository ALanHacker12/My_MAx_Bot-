from flask import Flask, request, jsonify
import requests
import json
import database as db
import re

import os

TOKEN = "f9LHodD0cOIGHfDooh5fax5zJxeBU3LX6PTWHhDqg-t9aEeBoKW2VT643bHy92YUWARvQkmZtfy-1CRGm6Tr"
ADMIN_ID = 59879495

app = Flask(__name__)

# Инициализация БД
db.init_db()

# Хранилище состояний
user_states = {}
user_temp_data = {}

def send_message(user_id, text):
    url = f"https://platform-api.max.ru/messages?user_id={user_id}"
    headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
    data = {"text": text}
    
    try:
        r = requests.post(url, headers=headers, json=data)
        print(f"   Статус: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Ошибка: {e}")
        return False

def send_message_to_admin(text):
    send_message(ADMIN_ID, text)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    print(f"\n📨 Получен: {update.get('update_type')}")
    
    if update.get('update_type') == 'bot_started':
        user = update.get('user', {})
        user_id = user.get('user_id')
        user_name = user.get('name', 'Пользователь')
        username = user.get('username', '')
        
        db.register_user(user_id, username, user_name, 30)
        
        msg = f"""👋 Привет, {user_name}!

🌟 ДОБРО ПОЖАЛОВАТЬ В БОТ 'МАЯК для СВОих' 🌟

📋 Доступные команды:

/start - Главное меню
/help - Справка
/offer - Предложить помощь
/need - Запросить помощь
/support - Меры поддержки
/child - Помощь детям
/volunteer - Волонтерский раздел
/family - Создать семью
/my_stats - Моя статистика
/leaderboard - Рейтинг волонтеров
/family_leaderboard - Рейтинг семей
/my_deeds - Мои добрые дела
/add_deed - Добавить доброе дело
/feedback - Оставить отзыв
/gratitude - Стена благодарности

Просто напиши команду!"""
        
        send_message(user_id, msg)
        send_message_to_admin(f"👤 Новый пользователь: {user_name} (@{username})\n🆔 {user_id}")
    
    elif update.get('update_type') == 'message_created':
        message = update.get('message', {})
        sender = message.get('sender', {})
        user_id = sender.get('user_id')
        user_name = sender.get('name', 'Пользователь')
        text = message.get('body', {}).get('text', '').strip()
        text_lower = text.lower()
        
        print(f"💬 {user_name}: {text}")
        
        state = user_states.get(user_id)
        
        # ==================== КОМАНДЫ ====================
        
        if text_lower == '/start':
            msg = """🌟 ГЛАВНОЕ МЕНЮ 🌟

📋 Доступные команды:

/offer - 🤝 Хочу помочь
/need - 🆘 Нужна помощь
/support - 🏛️ Меры поддержки
/child - 👶 Помощь детям
/volunteer - 🤝 Волонтерский раздел
/gratitude - 🙏 Стена благодарности
/feedback - ⭐ Оставить отзыв

Другие команды:
/help - Справка
/my_stats - Моя статистика
/leaderboard - Рейтинг волонтеров

Выбери нужную команду!"""
            send_message(user_id, msg)
            user_states[user_id] = None
        
        elif text_lower == '/help':
            msg = """📚 СПРАВКА

Я бот для поддержки участников СВО и их семей.

🔹 ОСНОВНЫЕ КОМАНДЫ:
/start - Главное меню
/offer - Предложить помощь
/need - Запросить помощь
/support - Меры поддержки государства
/child - Помощь детям СВО

🔹 ВОЛОНТЕРСКИЙ РАЗДЕЛ:
/volunteer - Вступить в волонтеры
/my_stats - Моя статистика (баллы)
/leaderboard - Рейтинг волонтеров
/add_deed - Добавить доброе дело
/my_deeds - Мои добрые дела

🔹 СЕМЕЙНЫЙ РАЗДЕЛ:
/family - Создать семью
/my_family - Моя семья
/family_leaderboard - Рейтинг семей

🔹 ОБРАТНАЯ СВЯЗЬ:
/feedback - Оставить отзыв
/gratitude - Стена благодарности

По всем вопросам: @zilya_gafarova"""
            send_message(user_id, msg)
        
        # ==================== ПОМОЩЬ ====================
        
        elif text_lower == '/offer':
            user_states[user_id] = 'offer_waiting'
            user_temp_data[user_id] = {}
            msg = """🤝 ПРЕДЛОЖЕНИЕ ПОМОЩИ

Шаг 1: Выбери категорию помощи

Напиши номер:
1 - 💰 Деньгами
2 - 📦 Отправить продукцию
3 - 🍎 Купить питание
4 - 🧵 Своими руками
5 - 🧠 Психологическая поддержка
6 - 🆘 Другое

Или напиши свою категорию"""
            send_message(user_id, msg)
        
        elif text_lower == '/need':
            user_states[user_id] = 'need_waiting'
            user_temp_data[user_id] = {}
            msg = """🆘 ЗАПРОС ПОМОЩИ

Шаг 1: Выбери категорию

Напиши номер:
1 - 🥫 Продукты
2 - 👕 Одежда/экипировка
3 - 💊 Лекарства
4 - 🧠 Психологическая поддержка
5 - 📝 Другое

Или напиши свою категорию"""
            send_message(user_id, msg)
        
        # ==================== ВОЛОНТЕРСКИЙ РАЗДЕЛ ====================
        
        elif text_lower == '/volunteer':
            user_states[user_id] = 'volunteer_age'
            msg = """🤝 ВОЛОНТЕРСКАЯ ПРОГРАММА

Мы объединяем поколения: старшее поколение (55+) и подростков (10-16 лет)

Сколько тебе лет? (Напиши число)"""
            send_message(user_id, msg)
        
        elif text_lower == '/my_stats':
            user_data = db.get_user(user_id)
            if user_data:
                msg = f"""📊 ТВОЯ СТАТИСТИКА

👤 Имя: {user_data.get('full_name', 'Не указано')}
🎂 Возраст: {user_data.get('age', '?')}
🌟 Всего баллов: {user_data.get('total_points', 0)}
🤝 Добрых дел: {user_data.get('help_count', 0)}
📅 Участник с: {user_data.get('registration_date', 'недавно')[:10]}
🏙️ Город: {user_data.get('city', 'Не указан')}
📞 Телефон: {user_data.get('phone', 'Не указан')}

Используй /add_deed чтобы добавить доброе дело!"""
            else:
                msg = "❌ Ты еще не зарегистрирован. Напиши /volunteer"
            send_message(user_id, msg)
        
        elif text_lower == '/leaderboard':
            leaders = db.get_leaderboard(10)
            if not leaders:
                msg = "🏆 Пока нет участников с баллами. Будь первым!"
            else:
                msg = "🏆 ТОП-10 ВОЛОНТЕРОВ 🏆\n\n"
                for i, u in enumerate(leaders, 1):
                    msg += f"{i}. {u['full_name']} — {u['total_points']} 🌟 ({u['help_count']} добрых дел)\n"
            send_message(user_id, msg)
        
        elif text_lower == '/add_deed':
            user_states[user_id] = 'deed_type'
            msg = """📝 ДОБРОЕ ДЕЛО

Выбери тип доброго дела:

1 - 🛒 Помощь с покупками (10 баллов)
2 - 🤝 Простое общение (5 баллов)
3 - 🏠 Помощь по дому (15 баллов)
4 - 📚 Помощь с уроками (15 баллов)
5 - 🚶 Сопровождение (10 баллов)
6 - 📦 Доставка продуктов (10 баллов)
7 - 💊 Помощь с лекарствами (10 баллов)
8 - 🎨 Творческий мастер-класс (20 баллов)

Напиши номер (1-8)"""
            send_message(user_id, msg)
        
        elif text_lower == '/my_deeds':
            deeds = db.get_good_deeds(user_id, 10)
            if not deeds:
                msg = "📝 У тебя пока нет добрых дел. Используй /add_deed чтобы добавить!"
            else:
                msg = "📝 МОИ ДОБРЫЕ ДЕЛА 📝\n\n"
                for d in deeds:
                    status_icon = "✅" if d['status'] == 'verified' else "⏳"
                    msg += f"{status_icon} {d['deed_type']}: {d['description'][:50]}... (+{d['points']} баллов)\n"
            send_message(user_id, msg)
        
        # ==================== СЕМЕЙНЫЙ РАЗДЕЛ ====================
        
        elif text_lower == '/family':
            user_states[user_id] = 'family_child_id'
            msg = """👨‍👦 СОЗДАНИЕ СЕМЬИ

Для создания семьи нужно:
1. Ты должен быть старше 55 лет
2. Ребенок (10-16 лет) должен зарегистрироваться в боте (/volunteer)
3. Введи ID ребенка (число)

Или напиши /skip чтобы пропустить"""
            send_message(user_id, msg)
        
        elif text_lower == '/my_family':
            family = db.get_family(user_id)
            if family:
                msg = f"""👨‍👦 МОЯ СЕМЬЯ

🏷️ Название: {family.get('family_name')}
🌟 Баллов: {family.get('total_points', 0)}
👴 Старший: {family.get('adult_name')}
🧒 Младший: {family.get('child_name')}"""
            else:
                msg = "❌ Ты еще не состоишь в семье. Используй /family чтобы создать!"
            send_message(user_id, msg)
        
        elif text_lower == '/family_leaderboard':
            families = db.get_family_leaderboard(10)
            if not families:
                msg = "🏅 Пока нет семей с баллами. Создай свою семью!"
            else:
                msg = "🏅 ТОП-10 СЕМЕЙ 🏅\n\n"
                for i, f in enumerate(families, 1):
                    msg += f"{i}. {f['family_name']} — {f['total_points']} 🌟\n"
            send_message(user_id, msg)
        
        # ==================== ОСТАЛЬНЫЕ КОМАНДЫ ====================
        
        elif text_lower == '/support':
            msg = """🏛️ МЕРЫ ПОДДЕРЖКИ

Социальные льготы:
• Бесплатный проезд к месту лечения
• Путевки в санатории
• Бесплатное лекарственное обеспечение

Для семей:
• Первоочередное зачисление детей в сады/школы
• Бесплатное питание в школах
• Компенсация ЖКХ (50%)

Куда обратиться:
• Военкомат
• МФЦ
• Фонд «Защитники Отечества»
• Горячая линия 117 или 122"""
            send_message(user_id, msg)
        
        elif text_lower == '/child':
            msg = """👶 ПОМОЩЬ ДЕТЯМ

Что доступно:
• Бесплатные путевки в лагеря
• Бесплатное питание в школе
• Психологическая поддержка
• Помощь с учебой
• Организация досуга

Как получить помощь:
Напиши /need и опиши, что нужно ребенку

Как помочь детям:
Напиши /offer и предложи свою помощь"""
            send_message(user_id, msg)
        
        elif text_lower == '/feedback':
            user_states[user_id] = 'feedback_waiting'
            msg = """⭐ ОСТАВИТЬ ОТЗЫВ

Напиши свое мнение о работе бота:
• Что понравилось?
• Что можно улучшить?
• Твои пожелания

Будем благодарны за обратную связь!"""
            send_message(user_id, msg)
        
        elif text_lower == '/gratitude':
            leaders = db.get_leaderboard(10)
            if leaders:
                msg = "🙏 СТЕНА БЛАГОДАРНОСТИ 🙏\n\n"
                for i, u in enumerate(leaders[:5], 1):
                    msg += f"{i}. {u['full_name']} — {u['total_points']} 🌟\n"
                msg += "\nСпасибо всем, кто помогает! ❤️"
            else:
                msg = "🙏 Спасибо всем, кто помогает! Каждое доброе дело важно. Вместе мы сила! 💪"
            send_message(user_id, msg)
        
        # ==================== ОБРАБОТКА СОСТОЯНИЙ ====================
        
        elif state == 'offer_waiting':
            user_temp_data[user_id]['category'] = text
            user_states[user_id] = 'offer_details'
            msg = "📝 Шаг 2: Опиши подробно, что ты предлагаешь (что, сколько, и т.д.)"
            send_message(user_id, msg)
        
        elif state == 'offer_details':
            category = user_temp_data[user_id].get('category', 'Помощь')
            details = text
            user_states[user_id] = 'offer_phone'
            msg = "📞 Шаг 3: Оставь номер телефона для связи"
            send_message(user_id, msg)
        
        elif state == 'offer_phone':
            phone = text
            user_states[user_id] = 'offer_city'
            msg = "🏙️ Шаг 4: Из какого ты города?"
            send_message(user_id, msg)
        
        elif state == 'offer_city':
            city = text
            data = user_temp_data.get(user_id, {})
            category = data.get('category', 'Помощь')
            details = data.get('details', '')
            phone = data.get('phone', '')
            
            # Сохраняем заявку в БД
            request_id = db.add_request(user_id, user_name, phone, city, category, details, 'offer')
            
            # Уведомление админу
            admin_msg = f"""🔔 НОВОЕ ПРЕДЛОЖЕНИЕ ПОМОЩИ #{request_id}

👤 {user_name}
🆔 ID: {user_id}
📋 Категория: {category}
📝 Детали: {details}
🏙️ Город: {city}
📞 Телефон: {phone}
⏰ {__import__('datetime').datetime.now().strftime('%H:%M %d.%m.%Y')}

Команда для отметки: /done_{request_id}"""
            send_message_to_admin(admin_msg)
            
            send_message(user_id, f"✅ Спасибо! Твое предложение (#{request_id}) передано волонтерам. С тобой свяжутся.\n\nНапиши /start для главного меню")
            user_states[user_id] = None
            user_temp_data[user_id] = {}
        
        elif state == 'need_waiting':
            user_temp_data[user_id]['category'] = text
            user_states[user_id] = 'need_details'
            msg = "📝 Шаг 2: Опиши подробно, что тебе нужно"
            send_message(user_id, msg)
        
        elif state == 'need_details':
            category = user_temp_data[user_id].get('category', 'Запрос помощи')
            details = text
            user_states[user_id] = 'need_phone'
            msg = "📞 Шаг 3: Оставь номер телефона для связи"
            send_message(user_id, msg)
        
        elif state == 'need_phone':
            phone = text
            user_states[user_id] = 'need_city'
            msg = "🏙️ Шаг 4: Из какого ты города?"
            send_message(user_id, msg)
        
        elif state == 'need_city':
            city = text
            data = user_temp_data.get(user_id, {})
            category = data.get('category', 'Запрос помощи')
            details = data.get('details', '')
            phone = data.get('phone', '')
            
            request_id = db.add_request(user_id, user_name, phone, city, category, details, 'need')
            
            admin_msg = f"""🆘 НОВЫЙ ЗАПРОС ПОМОЩИ #{request_id}

👤 {user_name}
🆔 ID: {user_id}
📋 Категория: {category}
📝 Детали: {details}
🏙️ Город: {city}
📞 Телефон: {phone}
⏰ {__import__('datetime').datetime.now().strftime('%H:%M %d.%m.%Y')}

Команда для отметки: /done_{request_id}"""
            send_message_to_admin(admin_msg)
            
            send_message(user_id, f"✅ Твой запрос (#{request_id}) принят! Волонтеры свяжутся с тобой.\n\nНапиши /start для главного меню")
            user_states[user_id] = None
            user_temp_data[user_id] = {}
        
        elif state == 'volunteer_age':
            try:
                age = int(text)
                if age < 5 or age > 120:
                    send_message(user_id, "❌ Введи реальный возраст (5-120 лет)")
                    return jsonify(status="ok"), 200
                
                db.register_user(user_id, sender.get('username', ''), user_name, age)
                
                if age >= 55:
                    msg = f"✅ Ты зарегистрирован как волонтер старшего поколения!\n\nТы можешь:\n• Стать наставником\n• Создать семью (/family)\n• Получать баллы за добрые дела (/add_deed)"
                elif 10 <= age <= 16:
                    msg = f"✅ Ты зарегистрирован как юный волонтер!\n\nТы можешь:\n• Участвовать в добрых делах\n• Вступить в семью\n• Получать баллы (/add_deed)"
                else:
                    msg = f"✅ Ты зарегистрирован как волонтер!\n\nТы можешь:\n• Добавлять добрые дела (/add_deed)\n• Получать баллы\n• Участвовать в рейтинге"
                
                send_message(user_id, msg)
                user_states[user_id] = None
            except ValueError:
                send_message(user_id, "❌ Введи число (твой возраст)")
        
        elif state == 'deed_type':
            deed_map = {
                '1': '🛒 Помощь с покупками',
                '2': '🤝 Простое общение',
                '3': '🏠 Помощь по дому',
                '4': '📚 Помощь с уроками',
                '5': '🚶 Сопровождение',
                '6': '📦 Доставка продуктов',
                '7': '💊 Помощь с лекарствами',
                '8': '🎨 Творческий мастер-класс'
            }
            points_map = {
                '1': 10, '2': 5, '3': 15, '4': 15,
                '5': 10, '6': 10, '7': 10, '8': 20
            }
            
            if text in deed_map:
                user_temp_data[user_id] = {
                    'deed_type': deed_map[text],
                    'points': points_map[text]
                }
                user_states[user_id] = 'deed_description'
                send_message(user_id, f"📝 Опиши подробно, что ты сделал.\nБазовые баллы: {points_map[text]} 🌟")
            else:
                send_message(user_id, "❌ Выбери номер от 1 до 8")
        
        elif state == 'deed_description':
            user_temp_data[user_id]['description'] = text
            user_states[user_id] = 'deed_phone'
            send_message(user_id, "📞 Оставь номер телефона для связи")
        
        elif state == 'deed_phone':
            user_temp_data[user_id]['phone'] = text
            user_states[user_id] = None
            
            data = user_temp_data.get(user_id, {})
            deed_id = db.add_good_deed(
                user_id,
                data.get('deed_type', 'Доброе дело'),
                data.get('description', ''),
                data.get('points', 10)
            )
            
            admin_msg = f"""📝 НОВОЕ ДОБРОЕ ДЕЛО #{deed_id}

👤 {user_name}
📋 Тип: {data.get('deed_type')}
📝 Описание: {data.get('description')}
🌟 Баллы: {data.get('points', 10)}
📞 Телефон: {data.get('phone', 'Не указан')}

Команды:
✅ /approve_{deed_id} - подтвердить
❌ /reject_{deed_id} - отклонить"""
            send_message_to_admin(admin_msg)
            
            send_message(user_id, f"✅ Доброе дело #{deed_id} зарегистрировано! Оно будет проверено модератором.\n\nНапиши /start для главного меню")
            user_temp_data[user_id] = {}
        
        elif state == 'family_child_id':
            if text.lower() == '/skip':
                user_states[user_id] = None
                send_message(user_id, "OK. Ты можешь создать семью позже командой /family")
            else:
                try:
                    child_id = int(text)
                    success, msg = db.create_family(user_id, child_id)
                    send_message(user_id, msg)
                    user_states[user_id] = None
                except ValueError:
                    send_message(user_id, "❌ Введи числовой ID ребенка или /skip")
        
        elif state == 'feedback_waiting':
            db.add_feedback(user_id, sender.get('username', ''), user_name, text)
            send_message_to_admin(f"⭐ НОВЫЙ ОТЗЫВ\n👤 {user_name}\n📝 {text}")
            send_message(user_id, "✅ Спасибо за отзыв! Мы ценим твое мнение.\n\nНапиши /start для главного меню")
            user_states[user_id] = None
        
        elif text_lower.startswith('/done_') or text_lower.startswith('/approve_') or text_lower.startswith('/reject_'):
            # Только для админа
            if user_id == ADMIN_ID:
                if text_lower.startswith('/done_'):
                    req_id = int(text.replace('/done_', ''))
                    db.mark_request_answered(req_id)
                    send_message(user_id, f"✅ Заявка #{req_id} отмечена как выполненная")
                elif text_lower.startswith('/approve_'):
                    deed_id = int(text.replace('/approve_', ''))
                    db.verify_deed(deed_id, user_id, True)
                    send_message(user_id, f"✅ Доброе дело #{deed_id} подтверждено! Баллы начислены.")
                elif text_lower.startswith('/reject_'):
                    deed_id = int(text.replace('/reject_', ''))
                    db.verify_deed(deed_id, user_id, False)
                    send_message(user_id, f"❌ Доброе дело #{deed_id} отклонено.")
            else:
                send_message(user_id, "❌ У тебя нет прав для этой команды")
        
        else:
            msg = f"""❓ Неизвестная команда: {text}

Доступные команды:
/start - Главное меню
/help - Справка
/offer - Предложить помощь
/need - Запросить помощь
/volunteer - Стать волонтером
/my_stats - Моя статистика
/leaderboard - Рейтинг волонтеров

Напиши /start чтобы начать!"""
            send_message(user_id, msg)
    
    return jsonify(status="ok"), 200

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 БОТ 'МАЯК для СВОих' - ПОЛНАЯ ВЕРСИЯ")
    print("📲 Найди бота: id023817677510_bot")
    print("=" * 70)
    print("🌟 ДОСТУПНЫЕ КОМАНДЫ:")
    print("   /start - Главное меню")
    print("   /offer - Предложить помощь")
    print("   /need - Запросить помощь")
    print("   /volunteer - Стать волонтером")
    print("   /add_deed - Добавить доброе дело")
    print("   /my_stats - Моя статистика")
    print("   /leaderboard - Рейтинг волонтеров")
    print("   /family - Создать семью")
    print("   /feedback - Оставить отзыв")
    print("=" * 70)
    app.run(host='0.0.0.0', port=8080, debug=False)