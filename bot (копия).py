from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from datetime import datetime, timedelta
import asyncio

tasks = []
completed_tasks = []
reminders = []
next_reminder_id = 1


async def start(update, context):
    await update.message.reply_text(
        "📝 Бот-органайзер\n\n"
        "Команды:\n"
        "/start - справка\n"
        "/list - все задачи\n" 
        "/edit номер текст - изменить\n"
        "/del номер - удалить\n"
        "/done номер - отметить выполненной\n"
        "/completed - выполненные\n"
        "/find текст - поиск\n"
        "/stats - статистика\n"
        "/clear - очистить все\n"
        "/remind - добавить задачу с напоминанием\n"
        "/remindlist - посмотреть список напоминаний\n"
        "/cancel - отмена напоминания\n\n"
        "Напиши задачу в чат!"
    )

async def add_task(update, context):
    text = update.message.text
    tasks.append(text)
    await update.message.reply_text(f"✅ Добавлено: {text}")

async def show_tasks(update, context):
    if not tasks:
        await update.message.reply_text("📝 Список пуст")
        return
    task_list = "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)])
    await update.message.reply_text(f"📋 Задачи:\n{task_list}")

async def delete_task(update, context):
    if not context.args:
        await update.message.reply_text("❌ Укажи номер: /del 1")
        return
    try:
        task_num = int(context.args[0]) - 1
        if 0 <= task_num < len(tasks):
            removed = tasks.pop(task_num)
            await update.message.reply_text(f"🗑️ Удалено: {removed}")
        else:
            await update.message.reply_text("❌ Неверный номер")
    except ValueError:
        await update.message.reply_text("❌ Номер должен быть числом!")

async def done_task(update, context):
    if not context.args:
        await update.message.reply_text("❌ Укажи номер: /done 1")
        return
    try:
        task_num = int(context.args[0]) - 1
        if 0 <= task_num < len(tasks):
            completed = tasks.pop(task_num)
            completed_tasks.append(completed)
            await update.message.reply_text(f"✅ Выполнено: {completed}")
        else:
            await update.message.reply_text("❌ Неверный номер")
    except ValueError:
        await update.message.reply_text("❌ Номер должен быть числом!")

async def show_completed(update, context):
    if not completed_tasks:
        await update.message.reply_text("📝 Нет выполненных задач")
        return
    result = "\n".join([f"✅ {task}" for task in completed_tasks])
    await update.message.reply_text(f"Выполненные:\n{result}")

async def edit_task(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Используй: /edit 1 новый текст")
        return
    try:
        task_num = int(context.args[0]) - 1
        new_text = " ".join(context.args[1:])
        if 0 <= task_num < len(tasks):
            old = tasks[task_num]
            tasks[task_num] = new_text
            await update.message.reply_text(f"✏️ Изменено:\nБыло: {old}\nСтало: {new_text}")
        else:
            await update.message.reply_text("❌ Неверный номер")
    except ValueError:
        await update.message.reply_text("❌ Номер должен быть числом!")

async def find_task(update, context):
    if not context.args:
        await update.message.reply_text("❌ Что искать? /find текст")
        return
    search = " ".join(context.args).lower()
    found = [f"{i+1}. {task}" for i, task in enumerate(tasks) if search in task.lower()]
    await update.message.reply_text(f"🔍 Найдено:\n" + "\n".join(found) if found else "❌ Ничего не найдено")

async def stats(update, context):
    total = len(tasks)
    completed = len(completed_tasks)
    await update.message.reply_text(f"📊 Статистика:\nАктивных: {total}\nВыполнено: {completed}\nВсего: {total + completed}")

async def clear_tasks(update, context):
    tasks.clear()
    completed_tasks.clear()
    await update.message.reply_text("🧹 Все задачи очищены!")

async def remind_task(update, context):
    global next_reminder_id
    
    if len(context.args) >= 2:
        try:
            minutes = int(context.args[0])
            task_text = " ".join(context.args[1:])
            
            # Проверяем лимиты
            if minutes <= 0:
                await update.message.reply_text("❌ Минуты должны быть больше 0!")
                return
            if minutes > 10080:
                await update.message.reply_text("❌ Максимум 7 дней (10080 минут)!")
                return
            
            # Создаем ID для напоминания
            reminder_id = next_reminder_id
            next_reminder_id += 1
            
            # Добавляем в общий список
            tasks.append(f"⏰ [{reminder_id}] {task_text} (через {minutes} мин)")
            
            # Запускаем таймер
            timer_task = asyncio.create_task(
                send_reminder(update, context, reminder_id, minutes, task_text)
            )
            
            # Сохраняем информацию о напоминании
            reminders.append({
                "id": reminder_id,
                "timer": timer_task,
                "text": task_text,
                "minutes": minutes,
                "user_id": update.effective_user.id
            })
            
            await update.message.reply_text(
                f"⏰ Напоминание #{reminder_id} установлено!\n"
                f"Текст: {task_text}\n"
                f"Через: {minutes} минут\n\n"
                f"Отменить: /cancel {reminder_id}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Минуты должны быть числом!")
    else:
        await update.message.reply_text("❌ Формат: /remind минуты задача")

async def send_reminder(update, context, reminder_id, minutes, task_text):
    """Отправка напоминания"""
    try:
        await asyncio.sleep(minutes * 60)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔔 Напоминание #{reminder_id}: {task_text}"
        )
        # Удаляем из списка после отправки
        remove_reminder(reminder_id)
    except:
        pass

def remove_reminder(reminder_id):
    """Удаление напоминания из списка"""
    global reminders, tasks
    # Удаляем из reminders
    reminders = [r for r in reminders if r["id"] != reminder_id]
    # Удаляем из tasks
    tasks = [t for t in tasks if f"[{reminder_id}]" not in t]

async def cancel_reminder(update, context):
    """Отмена конкретного напоминания"""
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите номер напоминания для отмены\n"
            "Пример: /cancel 1\n\n"
            "Посмотреть все напоминания: /reminderlist"
        )
        return
    
    try:
        reminder_id = int(context.args[0])
        # Ищем напоминание
        for reminder in reminders:
            if reminder["id"] == reminder_id and reminder["user_id"] == update.effective_user.id:
                # Отменяем таймер
                reminder["timer"].cancel()
                # Удаляем из списков
                remove_reminder(reminder_id)
                await update.message.reply_text(f"✅ Напоминание #{reminder_id} отменено!")
                return
        
        await update.message.reply_text("❌ Напоминание не найдено!")
        
    except ValueError:
        await update.message.reply_text("❌ Укажите номер напоминания: /cancel 1")
        

async def list_reminders(update, context):
    """Список всех напоминаний"""
    if not reminders:
        await update.message.reply_text("ℹ️ Нет активных напоминаний")
        return
    
    user_reminders = [r for r in reminders if r["user_id"] == update.effective_user.id]
    
    if not user_reminders:
        await update.message.reply_text("ℹ️ У вас нет активных напоминаний")
        return
    
    reminder_list = "\n".join([
        f"#{r['id']}: {r['text']} (через {r['minutes']} мин)"
        for r in user_reminders
    ])
    
    await update.message.reply_text(f"⏰ Ваши напоминания:\n{reminder_list}")
            
   

def main():
    app = Application.builder().token("ТВОЙ_ТОКЕН").build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", show_tasks))
    app.add_handler(CommandHandler("del", delete_task))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("completed", show_completed))
    app.add_handler(CommandHandler("edit", edit_task))
    app.add_handler(CommandHandler("find", find_task))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("clear", clear_tasks))
    app.add_handler(CommandHandler("remind", remind_task))
    app.add_handler(CommandHandler("cancel", cancel_reminder))
    app.add_handler(CommandHandler("reminderlist", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_task))
    
    app.run_polling()

if __name__ == '__main__':
    main()
