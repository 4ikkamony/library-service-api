# Library Service API

DRF-Powered Team Project

---
## Database Diagram
![library_db](https://github.com/user-attachments/assets/7921a73e-d113-433b-bd0f-e136fb48b9a8)


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

## Available Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | [/api/books/](#getapibooks) | List of Books |
| POST | [/api/books/](#postapibooks) | Create a Book |
| GET | [/api/books/{id}/](#getapibooksid) | Retrieve a Book |
| PUT | [/api/books/{id}/](#putapibooksid) | Update a Book |
| PATCH | [/api/books/{id}/](#patchapibooksid) | Partially update a Book |
| DELETE | [/api/books/{id}/](#deleteapibooksid) | Delete a Book |
| GET | [/api/borrowings/](#getapiborrowings) | List of Borrowings (non-admin users see only theirs) |
| POST | [/api/borrowings/](#postapiborrowings) | Create a Borrowing (if user has no pending Payments or overdue Borrowings) |
| GET | [/api/borrowings/{id}/](#getapiborrowingsid) | Retrieve a Borrowing |
| POST | [/api/borrowings/{id}/return/](#postapiborrowingsidreturn) | Return a Borrowing (if returned after expected return date - a fine Payment will be created) |
| GET | [/api/payments/](#getapipayments) | List of Payments (non-admin users see only theirs) |
| GET | [/api/payments/{id}/](#getapipaymentsid) | Retrieve a Payment |
| GET | [/api/payments/cancel/](#getapipaymentscancel) | Stripe Session redirects here on cancellation of payment |
| POST | [/api/payments/renew/](#postapipaymentsrenew) | Renew a Payment(if it's Stripe Session has expired) |
| POST | [/api/payments/success/](#postapipaymentssuccess) | Stripe Session redirects here on payment success |
| POST | [/api/users/](#postapiusers) | Create(register) a User |
| GET | [/api/users/me/](#getapiusersme) | Retrieve current User's info |
| PUT | [/api/users/me/](#putapiusersme) | Update current User's info |
| PATCH | [/api/users/me/](#patchapiusersme) | Partially Update current User's info |
| POST | [/api/users/token/](#postapiuserstoken) | Obtain JWT-token pair using credentials |
| POST | [/api/users/token/refresh/](#postapiuserstokenrefresh) | Obtain new access token using a refresh token |
| POST | [/api/users/token/verify/](#postapiuserstokenverify) | Verify that a token is valid |

# The Team

- [bodiakof](https://github.com/bodiakof)
- [Arsenmyron](https://github.com/Arsenmyron)
- [valerii-kashpur](https://github.com/valerii-kashpur)
- [ihorhalyskiy](https://github.com/ihorhalyskiy)
- [IvankaKuzin](https://github.com/IvankaKuzin)
- [4ikkamony](https://github.com/4ikkamony)
