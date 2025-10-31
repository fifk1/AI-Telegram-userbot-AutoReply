#!/usr/bin/env python3
"""
Telegram Userbot - Автоматический ответчик для архивных чатов Telegram
"""

import asyncio
import sys
import os
import random

# Устанавливаем кодировку UTF-8 для Windows консоли
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from bot.browser import UndetectedBrowserManager
from bot.telegram import UndetectedTelegramHandler
from utils.logger import get_logger, setup_logger
from config import APP_CONFIG, TELEGRAM_SITE_CONFIG
from selenium.webdriver.common.by import By

# Инициализируем логгер
logger = setup_logger("main")
logger.info("Telegram Userbot - Автоматический ответчик загружен")


class TelegramArchiveBot:
    """Бот для автоматических ответов в архивных чатах Telegram"""
    
    def __init__(self):
        logger.info("Инициализация бота...")
        self.browser_manager = UndetectedBrowserManager()
        self.site_handler = None
        self.is_running = False
        self.ai_model = None
        
        logger.info("Бот инициализирован для работы с Telegram")
    
    async def check_telegram_auth(self) -> bool:
        """Проверка авторизации в Telegram и подтверждение через консоль"""
        try:
            logger.info("🔐 Проверка авторизации в Telegram...")
            
            # Открываем Telegram
            await self.browser_manager.navigate_to_site(TELEGRAM_SITE_CONFIG["url"])
            await asyncio.sleep(3)  # Даем время загрузиться
            
            # Проверяем наличие элементов, которые появляются только после авторизации
            driver = self.browser_manager.driver
            auth_indicators = [
                ".sidebar",  # Сайдбар появляется после авторизации
                ".chatlist",  # Список чатов
                "main",  # Основной контейнер
            ]
            
            is_authorized = False
            for selector in auth_indicators:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        is_authorized = True
                        break
                except:
                    continue
            
            # Если не авторизован, открываем браузер и ждем
            if not is_authorized:
                logger.info("⚠️ Telegram не авторизован. Браузер открыт для авторизации...")
                logger.info("🌐 Пожалуйста, авторизуйтесь в открывшемся браузере")
                
                # Ждем авторизации (проверяем каждые 2 секунды)
                max_wait_time = APP_CONFIG["auth_wait_timeout"]  # 5 минут
                waited = 0
                
                while waited < max_wait_time:
                    await asyncio.sleep(2)
                    waited += 2
                    
                    # Проверяем снова
                    for selector in auth_indicators:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                            if element and element.is_displayed():
                                is_authorized = True
                                break
                        except:
                            continue
                    
                    if is_authorized:
                        break
                    
                    if waited % 10 == 0:  # Каждые 10 секунд показываем статус
                        logger.info(f"⏳ Ожидание авторизации... ({waited}/{max_wait_time} сек)")
            
            if is_authorized:
                logger.info("✅ Telegram авторизован!")
                
                # Запрашиваем подтверждение в консоли
                print("\n" + "="*60)
                print("✅ Авторизация в Telegram обнаружена!")
                print("="*60)
                
                while True:
                    response = input("\nАвторизовали? (y/n): ").strip().lower()
                    if response == 'y':
                        logger.info("✅ Пользователь подтвердил авторизацию")
                        return True
                    elif response == 'n':
                        logger.warning("⚠️ Пользователь не подтвердил авторизацию")
                        return False
                    else:
                        print("❌ Пожалуйста, введите 'y' или 'n'")
            else:
                logger.error("❌ Авторизация не выполнена в течение отведенного времени")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке авторизации: {e}")
            return False
    
    async def start(self) -> None:
        """Запуск бота"""
        try:
            logger.info(f"🚀 Запуск {APP_CONFIG['name']} v{APP_CONFIG['version']} для Telegram...")
            
            # Запускаем браузер
            logger.info("🌐 Запуск браузера...")
            await self.browser_manager.start()
            logger.info("✅ Браузер запущен")
            
            # Проверяем авторизацию в Telegram
            auth_result = await self.check_telegram_auth()
            if not auth_result:
                logger.error("❌ Авторизация не подтверждена. Завершаю работу.")
                await self.browser_manager.close()
                return
            
            # Переходим на Telegram
            logger.info("📱 Переход на Telegram...")
            await self.browser_manager.navigate_to_site(TELEGRAM_SITE_CONFIG["url"])
            logger.info("✅ Telegram загружен")
            
            # Создаем обработчик для Telegram
            logger.info("🔧 Создание обработчика для Telegram...")
            self.site_handler = UndetectedTelegramHandler(self.browser_manager.driver, TELEGRAM_SITE_CONFIG)
            logger.info("✅ Обработчик создан")
            
            # Загружаем AI модель
            await self.load_ai_model()
            
            # Устанавливаем флаг запуска
            self.is_running = True
            logger.info("✅ Бот готов к работе!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
    
    async def load_ai_model(self) -> None:
        """Загрузка AI модели"""
        try:
            logger.info("🤖 Загрузка AI модели...")
            
            from chat.ai import AIModel
            
            self.ai_model = AIModel()
            
            if self.ai_model.load_model():
                logger.info("✅ AI модель загружена успешно")
            else:
                logger.error("❌ Не удалось загрузить AI модель")
                raise Exception("Ошибка загрузки AI модели")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке AI модели: {e}")
            raise
    
    async def stop(self) -> None:
        """Остановка бота"""
        try:
            logger.info("🛑 Остановка бота...")
            self.is_running = False
            
            if self.browser_manager:
                await self.browser_manager.close()
            
            logger.info("✅ Бот остановлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    async def auto_reply_loop(self) -> None:
        """Основной цикл автоматических ответов"""
        if not self.is_running:
            logger.warning("⚠️ Бот не запущен")
            return

        logger.info("🔄 Запуск основного цикла автоответов...")
        
        # Открываем архив ОДИН РАЗ в начале
        logger.info("📁 Открытие архива чатов...")
        archive_opened = await self.site_handler.open_archive_folder()
        
        if not archive_opened:
            logger.error("❌ Не удалось открыть архив, завершаю работу")
            return
        
        logger.info("✅ Архив открыт, начинаю мониторинг...")
        
        iteration = 0
        
        while self.is_running:
            try:
                iteration += 1
                logger.info(f"\n{'='*50}")
                logger.info(f"🔄 Поиск непрочитанных #{iteration}")
                logger.info(f"{'='*50}")
                
                # Получаем список архивных чатов с непрочитанными (БЕЗ повторного открытия архива)
                unread_chats = await self.site_handler.get_archived_chats_with_unread()
                
                if not unread_chats:
                    logger.info("📭 Нет непрочитанных сообщений в архиве")
                    
                    # Случайная пауза перед следующей проверкой
                    wait_time = random.randint(10, 30)
                    logger.info(f"⏳ Жду {wait_time} секунд перед следующей проверкой...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Обрабатываем первый чат с непрочитанными
                chat = unread_chats[0]
                logger.info(f"\n📬 Обработка чата: {chat['name']}")
                logger.info(f"   Непрочитанных: {chat['unread_count']}")
                
                # Открываем чат
                success = await self.site_handler.select_chat_by_name(chat['name'])
                if not success:
                    logger.error(f"❌ Ошибка при открытии чата: {chat['name']}")
                    await self.site_handler.exit_current_chat()
                    continue
                
                logger.info(f"✅ Чат '{chat['name']}' открыт")
                
                # Получаем историю сообщений для контекста (только видимые)
                logger.info("📚 Загрузка истории сообщений...")
                messages = await self.site_handler.get_recent_messages(max_messages=30)
                
                if not messages:
                    logger.warning("⚠️ Не удалось загрузить историю сообщений")
                    await self.site_handler.exit_current_chat()
                    continue
                
                logger.info(f"✅ Загружено {len(messages)} сообщений для контекста")
                
                # Получаем непрочитанные входящие сообщения
                unread_messages = await self.site_handler.get_unread_messages_in_current_chat()
                
                if not unread_messages:
                    logger.info("ℹ️ Непрочитанных входящих не найдено")
                    await self.site_handler.exit_current_chat()
                    continue
                
                # Формируем текст последнего сообщения для AI
                last_message_text = messages[-1]['text'] if messages else ""
                
                # Генерируем ответ через AI
                logger.info("🤖 Генерация ответа через AI...")
                response = await self.ai_model.generate_response(messages, last_message_text)
                
                if response is None:
                    logger.info("🚫 AI решил не отвечать (разговор завершен)")
                    await self.site_handler.exit_current_chat()
                    await asyncio.sleep(random.randint(3, 10))
                    continue
                
                if not response or response.startswith("❌"):
                    logger.warning(f"⚠️ AI не смог сгенерировать ответ: {response}")
                    await self.site_handler.exit_current_chat()
                    continue
                
                logger.info(f"💬 Сгенерированный ответ: {response}")
                
                # Отправляем ответ
                logger.info("📤 Отправка ответа...")
                send_success = await self.site_handler.send_message(response)
                
                if send_success:
                    logger.info(f"✅ Ответ отправлен в чат '{chat['name']}'")
                else:
                    logger.warning("⚠️ Не удалось отправить ответ")
                
                # Выходим из чата
                await self.site_handler.exit_current_chat()
                
                # Случайная пауза перед следующим чатом (имитация человека)
                wait_time = random.randint(3, 15)
                logger.info(f"⏳ Пауза {wait_time} секунд перед следующим чатом...")
                await asyncio.sleep(wait_time)
                
            except KeyboardInterrupt:
                logger.info("⚠️ Получен сигнал прерывания")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле автоответов: {e}")
                logger.info("🔄 Продолжаю работу через 30 секунд...")
                
                # Пытаемся выйти из чата при ошибке
                try:
                    await self.site_handler.exit_current_chat()
                except:
                    pass
                
                await asyncio.sleep(30)


async def main():
    """Главная функция"""
    logger.info("🚀 Запуск главной функции...")
    
    bot = TelegramArchiveBot()
    
    try:
        # Запускаем бота
        await bot.start()
        
        # Запускаем основной цикл автоответов
        await bot.auto_reply_loop()
        
    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал прерывания (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Останавливаем бота
        await bot.stop()


if __name__ == "__main__":
    logger.info("🎬 Запуск скрипта...")
    asyncio.run(main())

