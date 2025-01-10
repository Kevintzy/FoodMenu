CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    image_url VARCHAR(255)
);

-- Updated items table to include 'options' column
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(255),
    price FLOAT,
    image_url VARCHAR(255),
    description TEXT,
    options VARCHAR(255)  -- Added 'options' column
);

-- Insert updated sample items with 'options' values
INSERT INTO items VALUES (5, 'Burger', 'food', 7.00, '/static/burger.jpg', 'Juicy beef burger with lettuce and cheese.', 'Veg,No Veg');
INSERT INTO items VALUES (6, 'Pizza', 'food', 12.00, '/static/pizza.jpg', 'Cheesy pepperoni pizza with tomato sauce.', 'Thin,Thick,Stuffed Crust');
INSERT INTO items VALUES (7, 'Water', 'beverages', 1.00, '/static/water.jpg', 'Bottled mineral water.', 'Cold,Room Temp');
INSERT INTO items VALUES (8, 'Coffee', 'beverages', 3.00, '/static/coffee.jpg', 'Hot cup of coffee.', 'Hot,Iced');
INSERT INTO items VALUES (9, 'Spaghetti', 'food', 14.00, '/uploads/spaghetti.jpg', 'Delicious spaghetti with beef sauce.', NULL);
