# 📚 Library Service API

Онлайн-система управління позиками книг для бібліотеки. Проєкт автоматизує облік книг, позик, користувачів та платежів, замінюючи паперову систему обліку зручним API на базі Django REST Framework.

## Зміст

- [Про проєкт](#про-проєкт)
- [Основні можливості](#основні-можливості)
- [Технологічний стек](#технологічний-стек)
- [Структура даних](#структура-даних)
- [Встановлення](#встановлення)
- [Запуск через Docker](#запуск-через-docker)
- [Змінні середовища](#змінні-середовища)
- [API Ендпоінти](#api-ендпоінти)
- [Тестування](#тестування)
- [Документація API](#документація-api)

## Про проєкт

У бібліотеці читачі можуть брати книги в позику й оплачувати оренду залежно від кількості днів використання. Цей сервіс вирішує проблеми застарілого паперового обліку:

- ✅ Облік наявності книг у реальному часі
- ✅ Онлайн-оплата позик (без готівки)
- ✅ Автоматичні сповіщення адміністраторам про нові позики й прострочення
- ✅ Прозорий облік користувачів та їхніх позик

Фронтенд у межах проєкту не реалізовано — увесь функціонал доступний через **browsable API** Django REST Framework.

## Основні можливості

- 🔐 Реєстрація та автентифікація користувачів через JWT
- 📖 CRUD-операції з книгами та контроль інвентарю
- 📅 Створення, перегляд і повернення позик
- 💳 Онлайн-оплата позик через Stripe
- 💰 Автоматичне нарахування штрафів за прострочення
- 🔔 Telegram-сповіщення про нові позики, прострочення та успішні платежі
- 📊 Фільтрація позик за статусом активності та користувачем
- 📑 Swagger-документація API

## Технологічний стек

| Категорія | Технологія |
|---|---|
| Backend | Django, Django REST Framework |
| Автентифікація | JWT (`djangorestframework-simplejwt`) |
| База даних | PostgreSQL |
| Платежі | Stripe API |
| Сповіщення | Telegram Bot API |
| Фонові завдання | Django Q / Django Celery |
| Кешування / черги | Redis |
| Контейнеризація | Docker, Docker Compose |
| Якість коду | flake8, black |

## Структура даних

### Book (Книга)
| Поле | Тип |
|---|---|
| title | str |
| author | str |
| cover | Enum: `HARD`, `SOFT` |
| inventory | positive int |
| daily_fee | decimal (USD) |

### User (Користувач)
| Поле | Тип |
|---|---|
| email | str |
| first_name | str |
| last_name | str |
| password | str |
| is_staff | bool |

### Borrowing (Позика)
| Поле | Тип |
|---|---|
| borrow_date | date |
| expected_return_date | date |
| actual_return_date | date |
| book_id | int |
| user_id | int |

### Payment (Платіж)
| Поле | Тип |
|---|---|
| status | Enum: `PENDING`, `PAID` |
| type | Enum: `PAYMENT`, `FINE` |
| borrowing_id | int |
| session_url | url |
| session_id | str |
| money_to_pay | decimal (USD) |

## Встановлення

```bash
git clone https://github.com/<your-username>/library-service.git
cd library-service

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.sample .env
# заповніть .env власними значеннями

python manage.py migrate
python manage.py runserver
```

## Запуск через Docker

```bash
docker-compose up --build
```

Команда піднімає такі сервіси:
- Django-сервер
- PostgreSQL
- Redis
- Telegram-бот
- Django Q / Celery worker (фонові завдання)

## Змінні середовища

Створіть файл `.env` за зразком `.env.sample`:

```env
DJANGO_SECRET_KEY=your-secret-key
POSTGRES_DB=library
POSTGRES_USER=library_user
POSTGRES_PASSWORD=library_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
```

⚠️ Файл `.env` ніколи не комітиться в репозиторій.

## API Ендпоінти

### Users Service
| Метод | URL | Опис |
|---|---|---|
| POST | `/users/` | Реєстрація нового користувача |
| POST | `/users/token/` | Отримання JWT-токенів |
| POST | `/users/token/refresh/` | Оновлення JWT-токена |
| GET | `/users/me/` | Перегляд власного профілю |
| PUT/PATCH | `/users/me/` | Оновлення профілю |

### Books Service
| Метод | URL | Опис |
|---|---|---|
| POST | `/books/` | Додати нову книгу |
| GET | `/books/` | Список книг |
| GET | `/books/<id>/` | Деталі книги |
| PUT/PATCH | `/books/<id>/` | Оновити книгу (зокрема інвентар) |
| DELETE | `/books/<id>/` | Видалити книгу |

### Borrowings Service
| Метод | URL | Опис |
|---|---|---|
| POST | `/borrowings/` | Створити нову позику (інвентар -1) |
| GET | `/borrowings/?user_id=...&is_active=...` | Список позик із фільтрами |
| GET | `/borrowings/<id>/` | Деталі позики |
| POST | `/borrowings/<id>/return/` | Повернути книгу (інвентар +1) |

### Payments Service
| Метод | URL | Опис |
|---|---|---|
| GET | `/payments/` | Список платежів |
| GET | `/payments/<id>/` | Деталі платежу |
| GET | `/success/` | Підтвердження успішної оплати Stripe |
| GET | `/cancel/` | Повідомлення про призупинену оплату |

> Для непривілейованих користувачів доступні лише власні позики та платежі. Адміністратори (`is_staff=True`) бачать дані всіх користувачів.

## Тестування

```bash
python manage.py tests
```

Покриття тестами власного коду — щонайменше 60%.

Перевірка стилю коду:

```bash
flake8
black --check .
```

## Документація API

Після запуску сервера Swagger-документація доступна за адресою:

```
http://localhost:8000/api/doc/swagger/
```

## Ліцензія

Навчальний проєкт, створений у межах практичного завдання.
