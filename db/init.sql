
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавление пользователей
INSERT INTO users (username, password_hash, role) 
VALUES
    ('admin', 'hashed_password_for_admin', 'admin'),
    ('user1', 'hashed_password_for_user1', 'user'),
    ('user2', 'hashed_password_for_user2', 'user')
ON CONFLICT (username) DO NOTHING; -- Пропускает вставку, если пользователь уже существует

-- Создание таблицы меню
CREATE TABLE IF NOT EXISTS menu (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- Уникальное ограничение
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    available BOOLEAN DEFAULT TRUE
);

-- Добавление товаров в меню
INSERT INTO menu (name, description, price, available) 
VALUES
    ('Pizza Margherita', 'Classic pizza with tomato, mozzarella, and basil', 8.99, TRUE),
    ('Burger', 'Juicy beef burger with lettuce, cheese, and pickles', 5.49, TRUE),
    ('Pasta Carbonara', 'Pasta with creamy sauce, bacon, and Parmesan', 7.99, TRUE),
    ('Salad Caesar', 'Fresh salad with Caesar dressing and croutons', 4.49, TRUE)
ON CONFLICT (name) DO NOTHING; -- Пропускает вставку, если товар уже существует

-- Создание таблицы заказов
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Автоудаление связанных заказов при удалении пользователя
    menu_id INT NOT NULL REFERENCES menu(id) ON DELETE CASCADE, -- Автоудаление заказов при удалении товара
    quantity INT NOT NULL CHECK (quantity > 0), -- Ограничение: количество должно быть положительным
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы корзины
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Автоудаление элементов корзины при удалении пользователя
    menu_id INT NOT NULL REFERENCES menu(id) ON DELETE CASCADE, -- Автоудаление элементов корзины при удалении товара
    quantity INT NOT NULL CHECK (quantity > 0), -- Ограничение: количество должно быть положительным
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи событий
CREATE TABLE IF NOT EXISTS event_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    event_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы адресов доставки
CREATE TABLE IF NOT EXISTS delivery_addresses (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Удаление адресов при удалении пользователя
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE, -- Удаление платежа при удалении заказа
    payment_method VARCHAR(50),
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0), -- Сумма платежа не может быть отрицательной
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы отзывов
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Удаление отзывов при удалении пользователя
    menu_id INT NOT NULL REFERENCES menu(id) ON DELETE CASCADE, -- Удаление отзывов при удалении товара
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5), -- Ограничение: рейтинг от 1 до 5
    review TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE PROCEDURE process_payment(user_id INT, payment_method VARCHAR, amount NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
    total_amount NUMERIC;
    order_ids INT[];
BEGIN
    -- Рассчитываем общую сумму заказов пользователя
    total_amount := calculate_total_amount(user_id);

    -- Проверяем, достаточно ли суммы для оплаты
    IF amount < total_amount THEN
        RAISE EXCEPTION 'Недостаточная сумма для оплаты. Требуется %', total_amount;
    END IF;

    -- Обновляем статус заказов
    UPDATE orders
    SET status = 'paid'
    WHERE user_id = user_id AND status = 'pending';

    -- Добавляем запись в таблицу payments
    INSERT INTO payments (user_id, payment_method, amount, status)
    VALUES (user_id, payment_method, amount, 'completed');
END;
$$;
CREATE OR REPLACE FUNCTION log_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO event_logs (event_type, event_description, created_at)
    VALUES (
        TG_OP, -- Тип операции: INSERT, UPDATE, DELETE
        FORMAT(
            'Table: %s, Old: %s, New: %s',
            TG_TABLE_NAME, -- Имя таблицы
            ROW(OLD.*)::TEXT, -- Старые данные (для DELETE и UPDATE)
            ROW(NEW.*)::TEXT  -- Новые данные (для INSERT и UPDATE)
        ),
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для таблицы users
CREATE TRIGGER log_users_event
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы menu
CREATE TRIGGER log_menu_event
AFTER INSERT OR UPDATE OR DELETE ON menu
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы orders
CREATE TRIGGER log_orders_event
AFTER INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы cart
CREATE TRIGGER log_cart_event
AFTER INSERT OR UPDATE OR DELETE ON cart
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы delivery_addresses
CREATE TRIGGER log_delivery_addresses_event
AFTER INSERT OR UPDATE OR DELETE ON delivery_addresses
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы payments
CREATE TRIGGER log_payments_event
AFTER INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION log_event();

-- Триггеры для таблицы reviews
CREATE TRIGGER log_reviews_event
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION log_event();


CREATE OR REPLACE VIEW unpaid_orders_summary AS
SELECT 
    o.user_id AS user_id,
    SUM(m.price * o.quantity) AS total_price,
    COUNT(o.id) AS order_count
FROM orders o
JOIN menu m ON o.menu_id = m.id
WHERE o.status = 'pending'
GROUP BY o.user_id;
