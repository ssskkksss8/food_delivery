import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_URL = "http://127.0.0.1:8001"
def display_menu():
    st.title("Меню доставки еды 🍕🍔🥗")
    search_menu()
    try:
        response = requests.get(f"{API_URL}/menu")
        if response.status_code == 200:
            menu_items = response.json()
            movie = ["margarita.jpg", "burger.jpg", "carbonara.jpg", "caesar.jpg"]
            k = 0
            if menu_items:
                for item in menu_items:
                    # col1, col2 = st.columns([1, 2])
                    # with col1:
                    #     # Показываем изображение товара
                    #     st.image(f"static/images/{movie[k]}", use_container_width=True)
                    #     k = k + 1
                    
                    # with col2:
                    st.subheader(item["name"])
                    st.write(item["description"])
                    st.write(f"**Цена**: {item['price']} ₽")

                    quantity = st.number_input(
                        f"Количество для {item['name']}",
                        min_value=1,
                        max_value=10,
                        value=1,
                        key=f"quantity_{item['name']}"
                    )

                    if st.button(f"Добавить {item['name']} в корзину", key=f"add_{item['name']}"):
                        add_to_cart(item["name"], quantity)
                    
                    st.write("Оставьте отзыв:")
                    
                    col_pos, col_neg = st.columns(2)

                    with col_pos:
                        if st.button(f"👍 Отлично", key=f"positive_review_{item['name']}"):
                            send_review(
                                username=st.session_state.get("username"),
                                item_name=item["name"],
                                rating=5,
                                review="Отлично!"
                            )
                            st.success("Положительный отзыв отправлен!")

                    with col_neg:
                        if st.button(f"👎 Плохо", key=f"negative_review_{item['name']}"):
                            send_review(
                                username=st.session_state.get("username"),
                                item_name=item["name"],
                                rating=1,
                                review="Плохо!"
                            )
                            st.success("Отрицательный отзыв отправлен!")
            else:
                st.info("Меню пусто.")
        else:
            st.error(f"Ошибка загрузки меню: {response.status_code}")
    except Exception as e:
        st.error(f"Ошибка: {e}")

def update_address():
    st.subheader("Добавить или обновить адрес")
    username = st.session_state["username"]
    address = st.text_input("Адрес", "")
    if address:
        city = st.text_input("Город", "")
        if city:
            postal_code = st.text_input("Почтовый индекс", "")
            if st.button("Сохранить адрес"):
                if address and city and postal_code:
                    payload = {
                        "username": username,
                        "address": address,
                        "city": city,
                        "postal_code": postal_code
                    }
                    try:
                        response = requests.post(f"{API_URL}/address/save", json=payload)
                        if response.status_code == 200:
                            st.success("Адрес успешно сохранён!")
                        else:
                            st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
                    except Exception as e:
                        st.error(f"Ошибка соединения с сервером: {e}")
                else:
                    st.warning("Заполните все поля!")

def search_menu():
    st.title("Поиск продуктов в меню")
    
    query = st.text_input("Введите строку для поиска")
    if st.button("Поиск"):
        try:
            response = requests.get(f"{API_URL}/menu/search", params={"query": query})
            if response.status_code == 200:
                results = response.json()
                if results:
                    for product in results:
                        st.write(f"**{product['name']}** - {product['price']} руб.")
                        st.write(f"_Описание_: {product['description']}")
                        st.write(f"_Доступно_: {'Да' if product['available'] else 'Нет'}")
                        st.write("---")
                else:
                    st.info("Продукты не найдены.")
            else:
                st.error(f"Ошибка: {response.status_code}")
        except Exception as e:
            st.error(f"Ошибка соединения с сервером: {e}")

def send_review(username, item_name, rating, review):
    payload = {
        "username": username,
        "item_name": item_name,
        "rating": rating,
        "review": review,
    }
    try:
        response = requests.post(f"{API_URL}/reviews/add", json=payload)
    except Exception as e:
        st.error(f"Ошибка при отправке отзыва: {str(e)}")

def add_to_cart(item_name, quantity):
    if "username" not in st.session_state:
        st.error("Пожалуйста, авторизуйтесь, чтобы добавить товары в корзину.")
        return

    payload = {
        "username": st.session_state["username"],
        "item_name": item_name,
        "quantity": quantity
    }

    response = requests.post(f"{API_URL}/cart/add", json=payload)
    if response.status_code == 200:
        st.success(f"{item_name} добавлен в корзину.")
        username = st.session_state["username"]
        updated_response = requests.get(f"{API_URL}/cart/{username}")
        if updated_response.status_code == 200:
            st.session_state["cart_items"] = updated_response.json()
        else:
            st.error("Ошибка синхронизации корзины.")
    else:
        error_detail = response.json().get("detail", "Неизвестная ошибка")
        if "duplicate key value" in error_detail:
            st.warning(f"{item_name} уже находится в корзине. Вы можете обновить количество в корзине.")
        else:
            st.error(f"Ошибка добавления в корзину: {error_detail}")

def remove_from_cart(username, item_name):
    try:
        response = requests.delete(f"{API_URL}/cart/remove", params={"username": username, "item_name": item_name})
        if response.status_code == 200:
            st.success(f"{item_name} успешно удален из корзины.")
        else:
            st.error(f"Ошибка удаления {item_name} из корзины: {response.json().get('detail', 'Неизвестная ошибка')}")
    except Exception as e:
        st.error(f"Ошибка при удалении: {str(e)}")

def display_cart():
    st.title("🛒 Ваша корзина")

    if "username" not in st.session_state:
        st.error("Сначала войдите в систему.")
        return

    username = st.session_state["username"]

    try:
        response = requests.get(f"{API_URL}/cart/{username}")
        if response.status_code == 200:
            cart_items = response.json()
            st.session_state["cart_items"] = cart_items
        else:
            st.error(f"Ошибка загрузки корзины: {response.status_code}")
            return

        cart_items = st.session_state.get("cart_items", [])
        if cart_items:
            total_price = 0
            for index, item in enumerate(cart_items):
                st.subheader(item["item_name"])
                st.write(f"Количество: {item['quantity']}")
                st.write(f"Цена за единицу: {item['price']} ₽")
                st.write(f"Добавлено: {item['created_at']}")

                if st.button(f"Удалить {item['item_name']}", key=f"remove_{item['item_name']}_{index}"):
                    remove_from_cart(username, item["item_name"])

                    updated_response = requests.get(f"{API_URL}/cart/{username}")
                    if updated_response.status_code == 200:
                        st.session_state["cart_items"] = updated_response.json()
                    else:
                        st.error("Ошибка синхронизации корзины")
                    st.rerun()

                total_price += item["price"] * item["quantity"]

            st.subheader(f"Итоговая сумма: {total_price:.2f} ₽")

        else:
            st.info("Ваша корзина пуста.")
    except Exception as e:
        st.error(f"Ошибка загрузки корзины: {str(e)}")


def register():
    st.title("Регистрация")
    username = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    role = st.selectbox("Роль", ["user", "admin"])
    
    if st.button("Зарегистрироваться"):
        if not username or not password:
            st.error("Имя пользователя и пароль обязательны для ввода")
            return
        
        payload = {"username": username, "password": password, "role": role}
        response = requests.post(f"{API_URL}/register", json=payload)
        if response.status_code == 200:
            st.success("Регистрация прошла успешно! Вы можете войти.")
        else:
            st.error(f"Ошибка регистрации: {response.text}")
def login():
    st.title("Авторизация")
    username = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("Успешная авторизация!")
            data = response.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["username"] = username
            st.session_state["user_role"] = str(data["role"]) 
        else:
            st.error("Ошибка авторизации")
        st.rerun()

def format_date(date_string):
    try:
        created_at = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f')
        return created_at.strftime('%d.%m.%Y %H:%M:%S')
    except ValueError:
        return date_string 
        
def display_payments(payments):
    payments_data = []
    for payment in payments:
        payments_data.append({
            "ID заказа": payment['order_id'],
            "Метод оплаты": payment['payment_method'],
            "Сумма": payment['amount'],
            "Статус": payment['status'],
            "Дата": format_date(payment['created_at'])
        })
    df_payments = pd.DataFrame(payments_data)
    df_payments.index = df_payments.index + 1
    st.dataframe(df_payments)

def display_reviews(reviews):
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            "Пользователь": review['user_id'],
            "Товар": review['menu_id'],
            "Рейтинг": review['rating'],
            "Отзыв": review['review'],
            "Дата": format_date(review['created_at'])
        })
    df_reviews = pd.DataFrame(reviews_data)
    df_reviews.index = df_reviews.index + 1
    st.dataframe(df_reviews)

def display_addresses(addresses):
    addresses_data = []
    for address in addresses:
        addresses_data.append({
            "Пользователь": address['user_id'],
            "Адрес": address['address'],
            "Город": address['city'],
            "Индекс": address['postal_code'],
            "Дата": format_date(address['created_at'])
        })
    df_addresses = pd.DataFrame(addresses_data)
    df_addresses.index = df_addresses.index + 1
    st.dataframe(df_addresses)

import requests

def display_admin_page():
    st.title("Администраторская страница")
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}

    st.header("Просмотр отзывов")
    try:
        response = requests.get(f"{API_URL}/admin/reviews", headers=headers)
        if response.status_code == 200:
            reviews = response.json()
            display_reviews(reviews)
        else:
            st.error(f"Ошибка загрузки отзывов: {response.json().get('detail', 'Неизвестная ошибка')}")
    except Exception as e:
        st.error(f"Ошибка загрузки отзывов: {str(e)}")

    st.header("Просмотр адресов доставки")
    try:
        response = requests.get(f"{API_URL}/admin/addresses", headers=headers)
        if response.status_code == 200:
            addresses = response.json()
            display_addresses(addresses)
        else:
            st.error(f"Ошибка загрузки адресов: {response.json().get('detail', 'Неизвестная ошибка')}")
    except Exception as e:
        st.error(f"Ошибка загрузки адресов: {str(e)}")

    st.header("Просмотр платежей")
    try:
        response = requests.get(f"{API_URL}/admin/payments", headers=headers)
        if response.status_code == 200:
            payments = response.json()
            display_payments(payments)
        else:
            st.error(f"Ошибка загрузки платежей: {response.json().get('detail', 'Неизвестная ошибка')}")
    except Exception as e:
        st.error(f"Ошибка загрузки платежей: {str(e)}")
    
    st.header("Управление резервными копиями")
    
    if st.button("Создать резервную копию"):
        try:
            response = requests.post(f"{API_URL}/admin/backup", headers=headers)
            if response.status_code == 200:
                st.success("Резервная копия успешно создана!")
                st.download_button(
                    label="Скачать резервную копию",
                    data=response.content,
                    file_name="db_backup.sql",
                    mime="application/sql"
                )
            else:
                st.error(f"Ошибка создания резервной копии: {response.json().get('detail', 'Неизвестная ошибка')}")
        except Exception as e:
            st.error(f"Ошибка создания резервной копии: {str(e)}")

    uploaded_file = st.file_uploader("Загрузить резервную копию для восстановления", type=["sql"])
    if uploaded_file is not None and st.button("Восстановить из резервной копии"):
        try:
            files = {"file": uploaded_file}
            response = requests.post(f"{API_URL}/admin/restore", files=files, headers=headers)
            if response.status_code == 200:
                st.success("Данные успешно восстановлены из резервной копии!")
            else:
                st.error(f"Ошибка восстановления: {response.json().get('detail', 'Неизвестная ошибка')}")
        except Exception as e:
            st.error(f"Ошибка восстановления: {str(e)}")


def checkout_cart(username):
    try:
        response = requests.post(f"{API_URL}/checkout/{username}")
        if response.status_code == 200:
            result = response.json()
            st.success(result["message"])
        else:
            error_message = response.json().get("detail", "Неизвестная ошибка")
            st.error(f"Ошибка: {error_message}")
    except Exception as e:
        st.error(f"Ошибка при оформлении заказа: {str(e)}")
def load_cart(username):
    try:
        response = requests.get(f"{API_URL}/cart/{username}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Ошибка при загрузке корзины")
            return []
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return []

def order_page():
    st.title("Оформление заказа")
    username = st.session_state["username"]

    if username:
        cart = load_cart(username)
        if cart:
            print(cart)
            st.write("Ваши товары в корзине:")
            for item in cart:
                st.write(f"{item['item_name']} - {item['quantity']} шт. - {item['price']} руб.")

            if st.button("Оформить заказ"): 
                checkout_cart(username)

def pay_order(order_id, payment_method, amount):
    try:
        payload = {
            "payment_method": payment_method,
            "amount": amount
        }
        response = requests.post(f"{API_URL}/pay_order/{order_id}", json=payload)
        if response.status_code == 200:
            result = response.json()
            st.success(result["message"])
        else:
            error_message = response.json().get("detail", "Неизвестная ошибка")
            st.error(f"Ошибка оплаты: {error_message}")
    except Exception as e:
        st.error(f"Ошибка при оплате: {str(e)}")
        


def load_orders(username):
    try:
        response = requests.get(f"{API_URL}/orders/{username}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Ошибка при загрузке заказов")
            return {}
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return {}

def payment_page():
    username = st.session_state['username']
    order = load_orders(username)

    if not order or "message" in order:
        st.write("У вас нет заказов для оплаты.")
        return

    st.write(f"Пользователь: {username}")
    st.write(f"Общая сумма заказа: {order['total_price']} руб.")
    st.write(f"Количество заказов: {order['order_count']}")
    st.write(f"Статус: {order['status']}")

    if order["status"] == "pending":
        payment_method = st.selectbox(
            "Метод оплаты",
            ["credit_card", "paypal", "cash"]
        )
        amount = st.number_input(
            "Введите сумму для оплаты",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        )
        if st.button("Оплатить"):
            pay_order(order["user_id"], payment_method, amount)
            


if "token" not in st.session_state:
    page = st.sidebar.radio("Навигация", ["Авторизация", "Регистрация"])
    if page == "Авторизация":
        login()
    elif page == "Регистрация":
        register()
else:
    user_role = st.session_state.get("user_role")
    if user_role == "admin":
        page = st.sidebar.radio("Страницы", ["Меню", "Корзина", "Адрес", "Оформить заказ", "Оплата заказа", "Администраторская"])
    else:
        page = st.sidebar.radio("Страницы", ["Меню", "Корзина", "Адрес", "Оформить заказ", "Оплата заказа"])

    if page == "Меню":
        display_menu()
    elif page == "Корзина":
        display_cart()
    elif page == "Адрес":
        update_address()
    elif page == "Оформить заказ":
        order_page()
    elif page == "Оплата заказа":
        payment_page()
    elif page == "Администраторская":
        if user_role == "admin":
            display_admin_page()
        else:
            st.error("У вас нет доступа к этой странице.")
