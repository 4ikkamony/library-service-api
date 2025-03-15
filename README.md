# Library Service API

The Library Service API is a practical, forward-thinking solution designed to modernize the way libraries manage their inventory, book borrowings, and customer payments. Tired of the paper chase? This project replaces outdated manual processes with a fully functional online API, making library management efficient, transparent, and downright enjoyable.

## 📌 Project Overview

Imagine your local library – a charming place where books are borrowed and returned with a bit of cash and a lot of paperwork. The current system struggles to track inventory, monitor timely returns, and handle payments in any modern way. Our solution brings order to the chaos by:

- **Managing Books Inventory:** Quickly view and update the availability of books.
- **Streamlining Borrowing Records:** Create, list, and track borrowings while automatically handling fines for late returns.
- **Handling Customer Data:** Securely manage users and their borrowing history.

## 🚀 Key Features

- **Browsable API Interface:** Interact with the system directly via API endpoints. It’s as simple as making an HTTP request and watching your commands come to life.
- **Role-Based Permissions:** Regular users can view books and manage their own borrowings, while admins enjoy additional privileges to maintain the inventory.
- **Automated Payment Handling:** Integrated payment sessions (leveraging Stripe) ensure fines and fees are processed seamlessly.
- **Real-Time Notifications:** Stay updated with automated alerts (via Telegram) for key events like new borrowings and payment confirmations.
- **Robust Error Handling:** With Django's transaction management and detailed logging, the system is built to handle hiccups gracefully.

## 🛠 Tech Stack

- **Backend Framework:** Django, Django REST Framework
- **Payment Integration:** Stripe
- **Task Management:** Celery (for asynchronous tasks like notifications)
- **Notification Service:** Telegram (for real-time alerts)


---
## Database Diagram
![library_db](https://github.com/user-attachments/assets/7921a73e-d113-433b-bd0f-e136fb48b9a8)


## Available Endpoints

#### ![Schema .yaml file](docs/library_service_api.yaml)

### Book Service

![image](https://github.com/user-attachments/assets/b4913cb6-2ca7-4c7e-8924-db99d0feb09a)


### Borrowing Service

![image](https://github.com/user-attachments/assets/7f9811b4-3427-4cdf-a886-6fd1fbf035d2)


### Payment Service

![image](https://github.com/user-attachments/assets/7114a15d-3cd6-4e1c-8846-bcb542e6b14d)


### User Service

![image](https://github.com/user-attachments/assets/95b73436-268a-4e95-8fed-cd796a5df0e1)


## 🚀 Try it out
   Make sure you have Python and Docker up and running

### 🐳 Run the App with Docker Compose

1. **Clone the repository**  
   ```sh
   git clone -b develop git@github.com:4ikkamony/library-service-api.git
   ```  
   ```sh
   cd library-service-api
   ```  

2. **Set up environment variables**  

   ```sh
   mv .env.sample .env
   ```
   **Make sure that:**
   ```markdown
   DJANGO_SETTINGS_MODULE=core.settings.build # to use PosgreSQL as DB
   ```
   ```markdown
   POSTGRES_HOST=db
   ```

   ```markdown
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=redis_password
   ```

   [Stripe API Keys](https://support.stripe.com/questions/what-are-stripe-api-keys-and-how-to-find-them) are mandatory to be able to create Borrowings  
     - STRIPE_PUBLISHABLE_KEY=
     - STRIPE_SECRET_KEY=

   For notifications to be sent:
   - Fill in [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot) and [Chat Id](https://docs.tracardi.com/qa/how_can_i_get_telegram_bot/)(to which send notifications)
     - TELEGRAM_BOT_TOKEN=
     - TELEGRAM_CHAT_ID=
    
   The rest can be left as-is for local testing

3. **📦 Start the containers**

   ```sh
   docker compose up
   ```

4. **🧪 Run tests**  

   ```sh
   docker exec -it library-backend python manage.py test  
   ```

5. **🔒 To get admin access:**

  - **Create a superuser:**
    ```sh
    docker exec -it library-backend python manage.py createsuperuser
    ```
  - [COMING SOON] Or load a fixture with some premade data:
    ```sh
    docker exec -it library-backend python manage.py loaddata fixtures/demo_data.json
    ```
    it has users:
      ```json
      {
        "email": "user@user.com",
        "password": "1qazcde3"
      }
     ```
     ```json
      {
        "email": "user2@user.com",
        "password": "1qazcde3"
      }
     ```
      ```json
      {
        "email": "admin@admin.com",
        "password": "1qazcde3"
      }
     ```

  - **Visit http://127.0.0.1:8000/api/doc/swagger/**
    
    To get a token pair, send POST request to /api/users/token/ with credentials:

     ```json
     {
       "email": "",
       "password": ""
     }
     ```

---

# The Team

- [bodiakof](https://github.com/bodiakof)
- [Arsenmyron](https://github.com/Arsenmyron)
- [valerii-kashpur](https://github.com/valerii-kashpur)
- [ihorhalyskiy](https://github.com/ihorhalyskiy)
- [IvankaKuzin](https://github.com/IvankaKuzin)
- [4ikkamony](https://github.com/4ikkamony)
