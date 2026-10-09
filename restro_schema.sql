-- Matches entity_table / entity_id_field / detail_fields / child_table in restro_config.py

CREATE TABLE menu_items (
    item_id     VARCHAR(50)  PRIMARY KEY,
    dish_name   VARCHAR(255) NOT NULL,
    price       DECIMAL(10,2) NOT NULL,
    category    VARCHAR(100),         -- e.g. "starter", "main", "dessert"
    spice_level VARCHAR(50)           -- e.g. "mild", "medium", "hot"
);

CREATE TABLE menu_item_ingredients (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    item_id         VARCHAR(50) NOT NULL,
    ingredient_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE CASCADE
);

-- Example rows
INSERT INTO menu_items (item_id, dish_name, price, category, spice_level) VALUES
    ('m001', 'Chicken Momo', 250.00, 'starter', 'medium'),
    ('m002', 'Dal Bhat Set', 350.00, 'main', 'mild');

INSERT INTO menu_item_ingredients (item_id, ingredient_name) VALUES
    ('m001', 'chicken'),
    ('m001', 'flour'),
    ('m001', 'onion'),
    ('m002', 'lentils'),
    ('m002', 'rice'),
    ('m002', 'vegetables');
