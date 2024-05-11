-- Users Table
USE madensell;

CREATE TABLE IF NOT EXISTS users (
    user_id		INT AUTO_INCREMENT NOT NULL,
    username	VARCHAR (20) NOT NULL UNIQUE,
    email		VARCHAR(50) NOT NULL UNIQUE,
    password	VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_type	INT (5) NOT NULL,
    address     VARCHAR(255) NOT NULL,
    phone_number VARCHAR(255) NOT NULL UNIQUE,
    primary key (user_id)
	);

CREATE TABLE IF NOT EXISTS admins (
	user_id	INT (10) NOT NULL,
    primary key (user_id),
    foreign key (user_id) references users(user_id)
	);

CREATE TABLE IF NOT EXISTS business (
	user_id            INT (10) NOT NULL,
    business_name      VARCHAR(20) NOT NULL,
    overall_point      NUMERIC(1,1) NOT NULL,
    profile_image      VARCHAR(255) NOT NULL,
    primary key (user_id),
    foreign key (user_id) references users(user_id)
	);

CREATE TABLE IF NOT EXISTS customer (
	user_id              INT (10) NOT NULL,
    first_name           VARCHAR(20) NOT NULL,
    last_name            VARCHAR(20) NOT NULL,
    profile_image        VARCHAR(255) NOT NULL,
    primary key (user_id),
    foreign key (user_id) references users(user_id)
	);

CREATE TABLE IF NOT EXISTS wallet (
	user_id		INT (10) NOT NULL,
    wallet_id       INT AUTO_INCREMENT NOT NULL,
    balance         INT(10) NOT NULL,
    primary key (wallet_id),
    foreign key (user_id) references users(user_id)
	);

CREATE TABLE IF NOT EXISTS category (
	category_id			INT AUTO_INCREMENT NOT NULL,
    category_name		VARCHAR(20) NOT NULL,
    primary key (category_id)
);

CREATE TABLE IF NOT EXISTS subcategory (
    category_id             INT NOT NULL,
	subcategory_id		    INT AUTO_INCREMENT NOT NULL,
    subcategory_name		VARCHAR(20) NOT NULL,
    primary key (subcategory_id, category_id),
    foreign key (category_id) references category(category_id)
);

CREATE TABLE IF NOT EXISTS product (
    business_id       INT (10) NOT NULL,
	product_id		INT AUTO_INCREMENT NOT NULL,
    price			INT (10) NOT NULL,
    title           VARCHAR (200) NOT NULL,
    description		VARCHAR (600) NOT NULL,
    stock_num        INT (3) NOT NULL,
    subcategory_id   INT (10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    primary key (product_id),
    foreign key (business_id) references business(user_id)
	);

CREATE TABLE IF NOT EXISTS images (
    product_id   INT (10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_url      VARCHAR(255) NOT NULL,

    primary key (product_id, image_url),
    foreign key (product_id) references product(product_id)
	);

CREATE TABLE IF NOT EXISTS favorites (
	cust_id		INT (10) NOT NULL,
    product_id   INT (10) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    primary key (product_id, cust_id),
    foreign key (product_id) references product(product_id),
    foreign key (cust_id) references customer(user_id)
	);

CREATE TABLE IF NOT EXISTS comments (
	customer_id		INT (10) NOT NULL,
    product_id   INT (10) NOT NULL,
    comment_id   INT AUTO_INCREMENT NOT NULL,
    comment     VARCHAR(255) NOT NULL,
    primary key (comment_id),
    foreign key (product_id) references product(product_id),
    foreign key (customer_id) references customer(user_id)
	);

CREATE TABLE IF NOT EXISTS basket (
	customer_id		INT (10) NOT NULL,
    product_id   INT (10) NOT NULL,
    basket_id   INT AUTO_INCREMENT NOT NULL,
    num_of_products     INT (3) NOT NULL,
    primary key (basket_id),
    foreign key (product_id) references product(product_id),
    foreign key (customer_id) references customer(user_id)
	);

CREATE TABLE IF NOT EXISTS shipping_info (
    info_id             INT AUTO_INCREMENT NOT NULL,
	customer_id		    INT (10) NOT NULL,
    phone_number        VARCHAR(255) NOT NULL UNIQUE,
    address_title       VARCHAR(255) NOT NULL,
    address             VARCHAR(255) NOT NULL,
    city                VARCHAR(255) NOT NULL,
    town                VARCHAR(255) NOT NULL,
    postal_code         INT (10) NOT NULL,
    primary key (info_id),
    foreign key (customer_id) references customer(user_id)
    );

CREATE TABLE IF NOT EXISTS orders (
    order_id            INT AUTO_INCREMENT NOT NULL,
	info_id	            INT (10) NOT NULL,
    product_id          INT (10) NOT NULL,
    num_of_products     INT (3) NOT NULL,
    status              INT (3) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    primary key (order_id, info_id, product_id),
    foreign key (product_id) references product(product_id),
    foreign key (info_id) references shipping_info(info_id)
    );

CREATE TABLE IF NOT EXISTS review (
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  review_id INT AUTO_INCREMENT NOT NULL,
  comment VARCHAR(250) NULL,
  speed INT NOT NULL,
  quality INT NOT NULL,
  interest INT NOT NULL,
  avg_point INT NOT NULL,
  username VARCHAR(45) NOT NULL,
  PRIMARY KEY (review_id),
  foreign key (product_id) references product(product_id),
  foreign key (customer_id) references customer(user_id));
