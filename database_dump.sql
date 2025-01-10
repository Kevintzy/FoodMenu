CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    image_url VARCHAR(255)
);

CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(255),
    price FLOAT,
    image_url VARCHAR(255),
    description TEXT
);

INSERT INTO items VALUES (5, 'Burger', 'food', 8.0, '/static/burger.jpg', 'Juicy beef burger with lettuce and cheese');
INSERT INTO items VALUES (6, 'Pizza', 'food', 12.0, '/static/pizza.jpg', 'Cheesy pepperoni pizza with tomato sauce.');
INSERT INTO items VALUES (7, 'Water', 'beverages', 1.0, '/static/water.jpg', 'Bottled mineral water.');
INSERT INTO items VALUES (8, 'Coffee', 'beverages', 3.0, '/static/coffee.jpg', 'Energizing cup of joe.');
INSERT INTO items VALUES (9, 'Spaghetti', 'food', 14.0, '/static/uploads/spaghetti.jpg', 'Delicious spaghetti with beef sauce.');
