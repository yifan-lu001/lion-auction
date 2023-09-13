from flask import Flask, render_template, request, redirect, session
from datetime import date
import sqlite3 as sql
import pandas as pd
import hashlib
import locale
import re


app = Flask(__name__)
app.secret_key = 'LionAuction'
host = 'http://127.0.0.1:5000/'


@app.route('/', methods=['POST', 'GET'])
def index():
    error = None
    # Only POST request method needed
    if request.method == 'POST':
        result = validate_login(request.form['email'], request.form['password'], request.form['role'])
        if result:
            session['email'] = request.form['email'].lower()
            session['role'] = request.form['role']
            return redirect('/home')
        else:
            return render_template('index_wrong_password.html', error=error)
    else:
        populate_data()
        return render_template('index.html', error=error)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect('/')
    else:
        return render_template('error.html')


@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        role = request.form['roles']
        if role != "":
            session['role'] = role
        return redirect('/home')
    else:
        try:
            roles = get_roles(session['email'])
        except:
            return render_template('error.html')
        categories = find_subcategories('Root')
        if session['role'] == 'Bidder':
            data = get_bidder_data(session['email'])
            if data[3].lower() == 'male':
                avatar = "https://bootdey.com/img/Content/avatar/avatar1.png"
            elif data[3].lower() == 'female':
                avatar = "https://bootdey.com/img/Content/avatar/avatar3.png"
            else:
                avatar = "static/NonBinary.png"
            return render_template('bidderhome.html', email=data[0], firstname=data[1], lastname=data[2], gender=data[3], age=data[4], address=get_address(data[5]), major=data[6].title(), cards=get_cards(data[0]), bids=get_bids(data[0]), avatar=avatar, categories=categories, roles=roles, bought=get_bought(session['email']), pending=get_pending(session['email']), lost=get_lost(session['email']))
        elif session['role'] == 'Seller':
            d = is_local_vendor(session['email'])
            rating = get_average_rating(session['email'])
            rating = round(float(rating), 2)
            if d:
                data = get_vendor_data(session['email'])
                data2 = get_seller_data(session['email'])
                formatted_balance = "${:,.2f}".format(data2[3])
                return render_template('localvendorhome.html', email=data[0], name=data[1], address=get_address(data[2]), phone=data[3], routing=data2[1], account=data2[2], balance=formatted_balance, listings=get_listings(session['email']), categories=categories, rating=rating, roles=roles)
            else:
                data = get_bidder_data(session['email'])
                data2 = get_seller_data(session['email'])
                formatted_balance = "${:,.2f}".format(data2[3])
                if data[3].lower() == 'male':
                    avatar = "https://bootdey.com/img/Content/avatar/avatar1.png"
                elif data[3].lower() == 'female':
                    avatar = "https://bootdey.com/img/Content/avatar/avatar3.png"
                else:
                    avatar = "static/NonBinary.png"
                return render_template('sellerhome.html', email=data[0], firstname=data[1], lastname=data[2], gender=data[3], age=data[4], address=get_address(data[5]), major=data[6].title(), avatar=avatar, routing=data2[1], account=data2[2], balance=formatted_balance, listings=get_listings(session['email']), categories=categories, rating=rating, roles=roles)
        elif session['role'] == 'HelpDesk':
            data = get_bidder_data(session['email'])
            data2 = get_helpdesk_data(session['email'])
            if data[3].lower() == 'male':
                avatar = "https://bootdey.com/img/Content/avatar/avatar1.png"
            elif data[3].lower() == 'female':
                avatar = "https://bootdey.com/img/Content/avatar/avatar3.png"
            else:
                avatar = "static/NonBinary.png"
            return render_template('helpdeskhome.html', email=data[0], firstname=data[1], lastname=data[2], gender=data[3], age=data[4], address=get_address(data[5]), major=data[6].title(), avatar=avatar, position=data2[1], requests=get_requests(session['email']), categories=categories, roles=roles)
        else:
            return render_template('error.html')


@app.route('/browse', methods=['POST', 'GET'])
def browse():
    error = None
    # Only POST request method needed
    if request.method == 'POST':
        category = request.form['category']
        session['category'] = category
        return render_template('browse.html', parent=session['category'], children=find_subcategories(session['category']), listings=get_listings2(session['category']))
    else:
        return render_template('browse.html', parent=session['category'], children=find_subcategories(session['category']), listings=get_listings2(session['category']))


@app.route('/details', methods=['POST', 'GET'])
def details():
    error = None
    # Only POST request method needed
    if request.method == 'POST':
        listing_id = request.form['listing']
        session['listing_id'] = listing_id
        session['seller-email'] = request.form['seller-email']
        listing_details = get_listing_details(listing_id, session['seller-email'])
        data = get_bidder_data(listing_details[2])
        if listing_details[1] == '':
            avatar = 'https://cdn-icons-png.flaticon.com/512/3891/3891665.png'
        elif data[3].lower() == 'male':
            avatar = "https://bootdey.com/img/Content/avatar/avatar1.png"
        elif data[3].lower() == 'female':
            avatar = "https://bootdey.com/img/Content/avatar/avatar3.png"
        else:
            avatar = "static/NonBinary.png"
        rating = get_average_rating(listing_details[2])
        if rating:
            rating = round(float(rating), 2)
        else:
            rating = 0.0
        status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}
        remaining_bids = listing_details[10] - get_num_bids(listing_details[2], listing_id)
        max_bid = get_minimum_bid(listing_details[2], listing_id)-1
        locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
        max_bid = locale.currency(max_bid, grouping=True)
        if session['role'] == 'Seller' and listing_details[2] == session['email'] and listing_details[11] != 2:
            return render_template('sellerdetails.html', listing_id=listing_id, avatar=avatar, firstname=listing_details[0], lastname=listing_details[1], email=listing_details[2], category=listing_details[4], auction_title=listing_details[5], product_name=listing_details[6], product_description=listing_details[7], quantity=listing_details[8], reserve_price=listing_details[9], maximum_bids=listing_details[10], status=status_dict[listing_details[11]], rating=rating, remaining_bids=remaining_bids, max_bid=max_bid, categories=find_subcategories('Root'))
        if session['role'] == 'Seller' or session['role'] == 'HelpDesk' or listing_details[11] != 1 or remaining_bids == 0 or get_most_recent_bidder(listing_details[2], listing_id) == session['email'] or listing_details[2] == session['email']:
            return render_template('details.html', listing_id=listing_id, avatar=avatar, firstname=listing_details[0], lastname=listing_details[1], email=listing_details[2], category=listing_details[4], auction_title=listing_details[5], product_name=listing_details[6], product_description=listing_details[7], quantity=listing_details[8], reserve_price=listing_details[9], maximum_bids=listing_details[10], status=status_dict[listing_details[11]], rating=rating, remaining_bids=remaining_bids, max_bid=max_bid, categories=find_subcategories('Root'))
        else:
            return render_template('bidderdetails.html', listing_id=listing_id, avatar=avatar, firstname=listing_details[0], lastname=listing_details[1], email=listing_details[2], category=listing_details[4], auction_title=listing_details[5], product_name=listing_details[6], product_description=listing_details[7], quantity=listing_details[8], reserve_price=listing_details[9], maximum_bids=listing_details[10], status=status_dict[listing_details[11]], rating=rating, remaining_bids=remaining_bids, min_bid=get_minimum_bid(listing_details[2], listing_id), max_bid=max_bid, categories=find_subcategories('Root'))
    else:
        listing_id = session['listing_id']
        listing_details = get_listing_details(listing_id, session['seller-email'])
        data = get_bidder_data(listing_details[2])
        if listing_details[1] == '':
            avatar = 'https://cdn-icons-png.flaticon.com/512/3891/3891665.png'
        elif data[3].lower() == 'male':
            avatar = "https://bootdey.com/img/Content/avatar/avatar1.png"
        elif data[3].lower() == 'female':
            avatar = "https://bootdey.com/img/Content/avatar/avatar3.png"
        else:
            avatar = "static/NonBinary.png"
        rating = get_average_rating(listing_details[2])
        rating = round(float(rating), 2)
        status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}
        remaining_bids = listing_details[10] - get_num_bids(listing_details[2], listing_id)
        max_bid = get_minimum_bid(listing_details[2], listing_id)-1
        locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
        max_bid = locale.currency(max_bid, grouping=True)
        if session['role'] == 'Seller' and listing_details[2] == session['email'] and listing_details[11] != 2:
            return render_template('sellerdetails.html', listing_id=listing_id, avatar=avatar,
                                   firstname=listing_details[0], lastname=listing_details[1], email=listing_details[2],
                                   category=listing_details[4], auction_title=listing_details[5],
                                   product_name=listing_details[6], product_description=listing_details[7],
                                   quantity=listing_details[8], reserve_price=listing_details[9],
                                   maximum_bids=listing_details[10], status=status_dict[listing_details[11]],
                                   rating=rating, remaining_bids=remaining_bids, max_bid=max_bid,
                                   categories=find_subcategories('Root'))
        if session['role'] == 'Seller' or session['role'] == 'HelpDesk' or listing_details[11] != 1 or remaining_bids == 0 or get_most_recent_bidder(listing_details[2], listing_id) == session['email'] or listing_details[2] == session['email']:
            return render_template('details.html', listing_id=listing_id, avatar=avatar, firstname=listing_details[0],
                                   lastname=listing_details[1], email=listing_details[2], category=listing_details[4],
                                   auction_title=listing_details[5], product_name=listing_details[6],
                                   product_description=listing_details[7], quantity=listing_details[8],
                                   reserve_price=listing_details[9], maximum_bids=listing_details[10],
                                   status=status_dict[listing_details[11]], rating=rating,
                                   remaining_bids=remaining_bids, max_bid=max_bid,
                                   categories=find_subcategories('Root'))
        else:
            return render_template('bidderdetails.html', listing_id=listing_id, avatar=avatar,
                                   firstname=listing_details[0], lastname=listing_details[1], email=listing_details[2],
                                   category=listing_details[4], auction_title=listing_details[5],
                                   product_name=listing_details[6], product_description=listing_details[7],
                                   quantity=listing_details[8], reserve_price=listing_details[9],
                                   maximum_bids=listing_details[10], status=status_dict[listing_details[11]],
                                   rating=rating, remaining_bids=remaining_bids, min_bid=get_minimum_bid(listing_details[2], listing_id),
                                   max_bid=max_bid, categories=find_subcategories('Root'))


@app.route('/successful-bid', methods=['POST', 'GET'])
def successful_bid():
    if request.method == 'POST':
        # Enter the bid
        make_bid(session['seller-email'], session['listing_id'], session['email'], request.form['bidamt'])

        # Check if it's the last bid, and it's lower than the reserve price; if so, set it as inactive
        listing = get_listing(session['seller-email'], session['listing_id'])[0]
        if get_num_bids(session['seller-email'], session['listing_id']) == get_max_bids(session['seller-email'], session['listing_id']) and int(request.form['bidamt']) < get_num_from(listing[6]):
            set_inactive(session['seller-email'], session['listing_id'])

        return redirect('/details')
    else:
        return render_template('error.html')


@app.route('/create-listing', methods=['POST', 'GET'])
def create_listing():
    if request.method == 'POST':
        add_listing(session['email'], request.form['AuctionTitle'], request.form['ProductName'], request.form['ProductDescription'], request.form['categories'], request.form['Quantity'], request.form['ReservePrice'], request.form['MaxBids'])
        return render_template('createlisting.html', categories=get_all_categories(), listings=get_listings(session['email']), cats=find_subcategories('Root'))
    else:
        if session['role'] != 'Seller':
            return render_template('error.html')
        return render_template('createlisting.html', categories=get_all_categories(), listings=get_listings(session['email']), cats=find_subcategories('Root'))


@app.route('/edit-listing', methods=['POST', 'GET'])
def edit_listing():
    if request.method == 'POST':
        edit_listing(session['email'], session['listing_id'], request.form['AuctionTitle'], request.form['ProductName'], request.form['ProductDescription'], request.form['categories'], request.form['Quantity'], request.form['ReservePrice'], request.form['MaxBids'], request.form['status'])
        listing = get_listing(session['email'], session['listing_id'])
        return render_template('editlisting.html', categories=get_all_categories_top(listing[0][1]), listings=listing, cats=find_subcategories('Root'), listing_id=listing[0][0], category=listing[0][1], title=listing[0][2], item_name=listing[0][3], description=listing[0][4], quantity=listing[0][5], reserve_price=int(listing[0][6][1:]), max_bids=listing[0][7], status=listing[0][8], min_remaining=get_num_bids(session['email'], session['listing_id']))
    else:
        if session['role'] != 'Seller':
            return render_template('error.html')
        try:
            listing = get_listing(session['email'], session['listing_id'])
            return render_template('editlisting.html', categories=get_all_categories_top(listing[0][1]), listings=listing, cats=find_subcategories('Root'), listing_id=listing[0][0], category=listing[0][1], title=listing[0][2], item_name=listing[0][3], description=listing[0][4], quantity=listing[0][5], reserve_price=int(listing[0][6][1:]), max_bids=listing[0][7], status=listing[0][8], min_remaining=get_num_bids(session['email'], session['listing_id']))
        except:
            return render_template('error.html')


@app.route('/delete-listing', methods=['POST', 'GET'])
def delete_listing():
    if request.method == 'GET':
        return render_template('error.html')
    else:
        reasoning = request.form['reasoning']
        if reasoning == "":
            delete_listing(session['email'], session['listing_id'])
        else:
            delete_listing(session['email'], session['listing_id'], reasoning)
        return redirect('/home')


@app.route('/pay', methods=['POST', 'GET'])
def pay():
    if request.method == 'POST':
        session['seller-email'] = request.form['seller-email']
        session['listing_id'] = request.form['listing']
        session['payment'] = request.form['payment']
        session['item-name'] = request.form['product-name']
        return redirect('/payment')
    else:
        return render_template('error.html')


@app.route('/payment', methods=['POST', 'GET'])
def payment():
    if request.method == 'POST':
        complete_transaction(session['seller-email'], session['listing_id'], session['email'], session['payment'])
        set_sold(session['seller-email'], session['listing_id'])
        return redirect('/home')
    else:
        if session['role'] != 'Bidder':
            return render_template('error.html')
        try:
            return render_template('payment.html', listing_id=session['listing_id'], item_name=session['item-name'], seller_email=session['seller-email'], bid_price=session['payment'], cards=get_cards(session['email']))
        except:
            return render_template('error.html')


@app.route('/new-card', methods=['POST', 'GET'])
def new_card():
    if request.method == 'POST':
        raw_num = request.form['card_num']
        if request.form['card_type'] == 'American Express':
            formatted_num = raw_num[:4] + '-' + raw_num[4:10] + '-' + raw_num[10:]
        else:
            formatted_num = raw_num[:4] + '-' + raw_num[4:8] + '-' + raw_num[8:12] + '-' + raw_num[12:]
        add_credit_card(formatted_num, request.form['card_type'], request.form['expire_month'], request.form['expire_year'], request.form['security_code'], session['email'])
        complete_transaction(session['seller-email'], session['listing_id'], session['email'], session['payment'])
        set_sold(session['seller-email'], session['listing_id'])
        return redirect('/home')
    else:
        return render_template('error.html')


# Populates all the data needed
def populate_data():
    populate_user_login()
    populate_helpdesk()
    populate_requests()
    populate_bidders()
    populate_cards()
    populate_address()
    populate_zipcode()
    populate_sellers()
    populate_local_vendors()
    populate_categories()
    populate_auction_listings()
    populate_bids()
    populate_transactions()
    populate_ratings()
    populate_deleted_listings()


# Creates the table for Users
def populate_user_login():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Users.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Users'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Users(email TEXT PRIMARY KEY, password TEXT);')
        for row in df.itertuples():
            hashed_password = hashlib.sha256(row.password.encode())
            connection.execute('INSERT INTO Users (email, password) VALUES (?,?);', (row.email, hashed_password.hexdigest()))
        connection.commit()


# Creates the table for Helpdesk
def populate_helpdesk():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Helpdesk.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Helpdesk'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Helpdesk(email TEXT PRIMARY KEY, position TEXT);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Helpdesk (email, position) VALUES (?,?);', (row.email, row.Position))
        connection.commit()


# Creates the table for Requests
def populate_requests():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Requests.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Requests'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Requests(request_id INTEGER PRIMARY KEY, sender_email TEXT NOT NULL, helpdesk_staff_email TEXT NOT NULL, request_type TEXT, request_desc TEXT, request_status INTEGER, FOREIGN KEY(sender_email) REFERENCES Users(email) ON DELETE CASCADE, FOREIGN KEY(helpdesk_staff_email) REFERENCES Helpdesk(email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Requests (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) VALUES (?,?,?,?,?,?);', (row.request_id, row.sender_email, row.helpdesk_staff_email, row.request_type, row.request_desc, row.request_status))
        connection.commit()


# Creates the table for Bidders
def populate_bidders():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Bidders.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Bidders'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Bidders(email TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, gender TEXT, age INT, home_address_id TEXT, major TEXT, FOREIGN KEY (email) REFERENCES Users (email) ON DELETE CASCADE, FOREIGN KEY (home_address_id) REFERENCES Address (address_id));')
        for row in df.itertuples():
            connection.execute('INSERT INTO Bidders (email, first_name, last_name, gender, age, home_address_id, major) VALUES (?,?,?,?,?,?,?);', (row.email, row.first_name, row.last_name, row.gender, row.age, row.home_address_id, row.major))
        connection.commit()


# Creates the table for Credit_Cards
def populate_cards():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Credit_Cards.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Credit_Cards'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Credit_Cards(credit_card_num INT PRIMARY KEY, card_type TEXT, expire_month INT, expire_year INT, security_code INT, Owner_email TEXT, FOREIGN KEY (Owner_email) REFERENCES Users (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email) VALUES (?,?,?,?,?,?);', (row.credit_card_num, row.card_type, row.expire_month, row.expire_year, row.security_code, row.Owner_email))
        connection.commit()


# Creates the table for Address
def populate_address():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Address.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Address'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Address(address_id TEXT PRIMARY KEY, zipcode INT, street_num INT, street_name TEXT, FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode));')
        for row in df.itertuples():
            connection.execute('INSERT INTO Address (address_id, zipcode, street_num, street_name) VALUES (?,?,?,?);', (row.address_id, row.zipcode, row.street_num, row.street_name))
        connection.commit()


# Creates the table for Zipcode_Info
def populate_zipcode():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Zipcode_Info.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Zipcode_Info'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Zipcode_Info(zipcode INT PRIMARY KEY, city TEXT, state TEXT);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?,?,?);', (row.zipcode, row.city, row.state))
        connection.commit()


# Creates the table for Sellers
def populate_sellers():
    # Obtains data from the CSV file
    userdata = pd.read_csv('CSV/Sellers.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Sellers'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Sellers(email TEXT PRIMARY KEY, routing_number INT, account_number INT, balance INT, FOREIGN KEY (email) REFERENCES Users (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Sellers (email, routing_number, account_number, balance) VALUES (?,?,?,?);', (row.email, row.bank_routing_number, row.bank_account_number, row.balance))
        connection.commit()


# Creates the table for Local_Vendors
def populate_local_vendors():
    userdata = pd.read_csv('CSV/Local_Vendors.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Local_Vendors'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Local_Vendors(Email TEXT PRIMARY KEY, Business_Name TEXT, Business_Address_ID Text, Customer_Service_Phone_Number INT, FOREIGN KEY (Email) REFERENCES Sellers (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Local_Vendors (Email, Business_Name, Business_Address_ID, Customer_Service_Phone_Number) VALUES (?,?,?,?);', (row.Email, row.Business_Name, row.Business_Address_ID, row.Customer_Service_Phone_Number))
        connection.commit()


# Creates the table for Categories
def populate_categories():
    userdata = pd.read_csv('CSV/Categories.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Categories'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Categories(parent_category TEXT, category_name TEXT PRIMARY KEY, FOREIGN KEY (parent_category) REFERENCES Categories (category_name) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Categories (parent_category, category_name) VALUES (?,?);', (row.parent_category, row.category_name))
        connection.commit()


# Creates a table for Auction_Listings
def populate_auction_listings():
    userdata = pd.read_csv('CSV/Auction_Listings.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Auction_Listings'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Auction_Listings(Seller_Email TEXT, Listing_ID INTEGER, Category TEXT, Auction_Title TEXT, Product_Name TEXT, Product_Description TEXT, Quantity INT, Reserve_Price INT, Max_bids INT, Status INT, PRIMARY KEY (Seller_Email,Listing_ID), FOREIGN KEY (Category) REFERENCES Categories (category_name), FOREIGN KEY (Seller_Email) REFERENCES Sellers (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Auction_Listings (Seller_Email, Listing_ID, Category, Auction_Title, Product_Name, Product_Description, Quantity, Reserve_Price, Max_bids, Status) VALUES (?,?,?,?,?,?,?,?,?,?);', (row.Seller_Email, row.Listing_ID, row.Category, row.Auction_Title, row.Product_Name, row.Product_Description, row.Quantity, row.Reserve_Price, row.Max_bids, row.Status))
        connection.commit()


# Creates a table for Bids
def populate_bids():
    userdata = pd.read_csv('CSV/Bids.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Bids'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Bids(Bid_ID INT PRIMARY KEY, Seller_Email TEXT, Listing_ID INT, Bidder_Email TEXT, Bid_Price INT, FOREIGN KEY (Seller_Email) REFERENCES Sellers (email), FOREIGN KEY (Bidder_Email) REFERENCES Bidders (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Bids (Bid_ID, Seller_Email, Listing_ID, Bidder_Email, Bid_Price) VALUES (?,?,?,?,?);', (row.Bid_ID, row.Seller_Email, row.Listing_ID, row.Bidder_Email, row.Bid_Price))
        connection.commit()


# Creates a table for Transactions
def populate_transactions():
    userdata = pd.read_csv('CSV/Transactions.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Transactions'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Transactions(Transaction_ID INT PRIMARY KEY, Seller_Email TEXT, Listing_ID INT, Bidder_Email TEXT, Date TEXT, Payment INT, FOREIGN KEY (Seller_Email) REFERENCES Sellers (email), FOREIGN KEY (Bidder_Email) REFERENCES Bidders (email) ON DELETE CASCADE);')
        for row in df.itertuples():
            connection.execute('INSERT INTO Transactions (Transaction_ID, Seller_Email, Listing_ID, Bidder_Email, Date, Payment) VALUES (?,?,?,?,?,?);', (row.Transaction_ID, row.Seller_Email, row.Listing_ID, row.Bidder_Email, row.Date, row.Payment))
        connection.commit()


# Creates a table for Ratings
def populate_ratings():
    userdata = pd.read_csv('CSV/Ratings.csv')
    df = pd.DataFrame(userdata)

    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Ratings'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Ratings(Bidder_Email TEXT, Seller_Email Text, Date TEXT, Rating INT, Rating_Desc TEXT, PRIMARY KEY (Bidder_Email, Seller_Email, Date), FOREIGN KEY (Bidder_Email) REFERENCES Bidders (email), FOREIGN KEY (Seller_Email) REFERENCES Sellers (email));')
        for row in df.itertuples():
            connection.execute('INSERT INTO Ratings (Bidder_Email, Seller_Email, Date, Rating, Rating_Desc) VALUES (?,?,?,?,?);', (row.Bidder_Email, row.Seller_Email, row.Date, row.Rating, row.Rating_Desc))
        connection.commit()


# Creates a table for Deleted_Listings
def populate_deleted_listings():
    # SQL statements
    connection = sql.connect('database.db')
    # Checks if the table exists by counting the number of tables named 'users'
    exists = connection.execute('SELECT count(*) FROM sqlite_master WHERE type = ? AND name = ?;', ('table', 'Deleted_Listings'))
    if exists.fetchall()[0][0] == 0:
        connection.execute('CREATE TABLE IF NOT EXISTS Deleted_Listings(Seller_Email TEXT, Listing_ID INTEGER, Category TEXT, Auction_Title TEXT, Product_Name TEXT, Product_Description TEXT, Quantity INT, Reserve_Price INT, Max_bids INT, Remaining_Bids INT, Reasoning TEXT, PRIMARY KEY (Seller_Email,Listing_ID), FOREIGN KEY (Category) REFERENCES Categories (category_name), FOREIGN KEY (Seller_Email) REFERENCES Sellers (email));')
        connection.commit()


# Determines if a given username and password is valid
def validate_login(username, password, role):
    connection = sql.connect('database.db')
    adjusted_username = username.lower()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor = connection.execute('SELECT * FROM Users WHERE email=? AND password=?;', (adjusted_username, hashed_password))
    if cursor.fetchall():
        if role == 'Bidder':
            cursor = connection.execute('SELECT * FROM Bidders WHERE email=?;', (adjusted_username,))
        elif role == 'Seller':
            cursor = connection.execute('SELECT * FROM Sellers WHERE email=?;', (adjusted_username,))
        elif role == 'HelpDesk':
            cursor = connection.execute('SELECT * FROM Helpdesk WHERE email=?;', (adjusted_username,))
    return cursor.fetchall()


# Determines a bidder's data given their email
def get_bidder_data(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Bidders B WHERE email=?;', (email,))
    r = cursor.fetchall()
    if len(r) == 0:
        return []
    return r[0]


# Determines seller data given their email
def get_seller_data(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Sellers S WHERE S.email=?;', (email,))
    r = cursor.fetchall()
    return r[0]


# Determines local vendor data given their email
def get_vendor_data(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Local_Vendors L WHERE L.Email=?;', (email,))
    r = cursor.fetchall()
    return r[0]


# Determines helpdesk data given their email
def get_helpdesk_data(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Helpdesk H WHERE H.email=?;', (email,))
    r = cursor.fetchall()
    return r[0]


# Determines a user's address given their address id
def get_address(address_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Address A WHERE A.address_id=?;', (address_id,))
    r1 = cursor.fetchall()[0]
    cursor = connection.execute('SELECT * FROM Zipcode_Info Z WHERE Z.zipcode=?;', (r1[1],))
    r2 = cursor.fetchall()[0]
    return str(r1[2]) + " " + r1[3] + ", " + r2[1] + ", " + r2[2] + ", " + str(r2[0])


# Determines a user's credit cards given their email
def get_cards(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Credit_Cards C WHERE C.Owner_email=?;', (email,))
    r = cursor.fetchall()
    r2 = []
    for card in r:
        if card[1] == 'American Express':
            formatted_card = '****-******-' + card[0][-5:]
        else:
            formatted_card = '****-****-****-' + card[0][-4:]
        r2.append((formatted_card, card[1], card[2], card[3], card[4], card[5]))
    return r2


# Determines a user's bids given their email
def get_bids(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Bids B WHERE B.Bidder_Email=?;', (email,))
    r = cursor.fetchall()
    if len(r) == 0:
        return r
    r2 = []
    for bid in r:
        cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE A.Listing_ID=?;', (bid[2],))
        listing = cursor.fetchall()[0]
        status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}
        if listing[9] == 1:
            locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
            bid_price = locale.currency(bid[4], grouping=True)
            r2.append((bid[2], listing[4], bid[1], bid_price, status_dict[listing[9]]))

    # Helper function to sort listings
    def get_id(item):
        return item[0]

    # Sort the listings
    r2.sort(key=get_id)
    return r2


# Determines a seller's listings given their email
def get_listings(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT L.Listing_ID, L.Category, L.Product_Name, L.Quantity, L.Status FROM Auction_Listings L WHERE L.Seller_Email=?;', (email,))
    r = cursor.fetchall()
    status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}
    r2 = []
    for listing in r:
        r2.append((listing[0], listing[1], listing[2], listing[3], status_dict[listing[4]]))

    # Helper function to sort listings
    def get_status(item):
        if item[4] == 'Active':
            return 0
        elif item[4] == 'Inactive':
            return 1
        elif item[4] == 'Sold':
            return 2
        else:
            return 3

    # Sort the listings
    r2.sort(key=get_status)
    return r2


# Determines a helpdesk's requests given their email
def get_requests(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT R.request_id, R.sender_email, R.request_type, R.request_desc FROM Requests R WHERE R.helpdesk_staff_email=?;', (email,))
    return cursor.fetchall()


# Determines if a seller is a local vendor
def is_local_vendor(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Local_Vendors L WHERE L.Email=?;', (email,))
    return cursor.fetchall()


# Finds the sub-categories given a parent
def find_subcategories(parent):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Categories C WHERE C.parent_category=?;', (parent,))
    return cursor.fetchall()


# Helper for finding all sub-categories given a parent
def helper_find_all_subcategories(parent):
    temp = find_subcategories(parent)
    if len(temp) == 0:
        return [parent]
    else:
        return temp + [find_subcategories(i[1]) for i in temp]


# Finds all auctions under a given category
def get_listings2(parent):
    # Gets all the subcategories from the parent category
    subcategories = []

    def remove_nesting(l):
        for i in l:
            if type(i) == list or type(i) == tuple:
                remove_nesting(i)
            else:
                subcategories.append(i)
    remove_nesting(helper_find_all_subcategories(parent))
    subcategories = list(set(subcategories))

    # Executes the SQL commands
    listings = []
    connection = sql.connect('database.db')
    for subcategory in subcategories:
        cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE A.Category=?;', (subcategory,))
        listings = listings + cursor.fetchall()

    # Remove duplicates
    listings = list(set(listings))

    # Helper function to sort listings
    def get_listing_id(item):
        return item[1]

    # Sort the listings
    listings.sort(key=get_listing_id)

    # Remove non-active and sold listings
    listings = [listing for listing in listings if listing[9] == 1]

    # Auction status dictionary
    status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}

    # New listings with fixed status
    temp = []
    for listing in listings:
        temp.append((listing[0], listing[1], listing[2], listing[3], listing[4], listing[5], listing[6], listing[7], listing[8], status_dict[listing[9]]))

    # Return
    return temp


# Finds details of a listing given the listing_id
def get_listing_details(listing_id, email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE A.Listing_ID=? AND A.Seller_Email=?;', (listing_id, email))
    d1 = cursor.fetchall()[0]
    seller_email = d1[0]
    cursor = connection.execute('SELECT B.first_name, B.last_name FROM Bidders B WHERE B.email=?;', (seller_email,))
    d2 = cursor.fetchall()
    if len(d2) == 0:
        cursor = connection.execute('SELECT L.Business_Name FROM Local_Vendors L WHERE L.email=?;', (seller_email,))
        d2 = cursor.fetchall()
    d2 = d2[0]
    if len(d2) == 1:
        d2 = (d2[0], "")
    return d2 + d1


# Gets a seller's average rating given their email
def get_average_rating(email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT AVG(R.Rating) FROM Ratings R WHERE R.Seller_Email=?;', (email,))
    r = cursor.fetchall()
    if len(r) == 0:
        return "N/A"
    return r[0][0]


# Gets all categories
def get_all_categories():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Categories C;')
    r = cursor.fetchall()
    categories = []
    for item in r:
        categories.append(item[0])  # parent category
        categories.append(item[1])  # category ame
    categories = list(set(categories))
    categories.sort()
    return categories


# Gets all categories
def get_all_categories_top(top):
    categories = get_all_categories()
    categories.insert(0, categories.pop(categories.index(top)))
    return categories


# Adds a listing to the database
def add_listing(email, title, pname, pdesc, cat, quantity, reserve, max_bids):
    connection = sql.connect('database.db')
    reserve = "$" + str(reserve)
    connection.execute('INSERT INTO Auction_Listings (Seller_Email, Listing_ID, Category, Auction_Title, Product_Name, Product_Description, Quantity, Reserve_Price, Max_bids, Status) VALUES (?,?,?,?,?,?,?,?,?,?);', (email, get_id(email), cat, title, pname, pdesc, quantity, reserve, max_bids, 1))
    connection.commit()


# Gets the next ID to use of a given seller
def get_id(email):
    connection = sql.connect('database.db')

    # Get the highest ID from Auction_Listings
    cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE A.Seller_Email=?;', (email,))
    if cursor.fetchall():
        cursor = connection.execute('SELECT MAX(A.Listing_ID) FROM Auction_Listings A WHERE A.Seller_Email=?;', (email,))
        max_active = cursor.fetchall()[0][0] + 1
    else:
        max_active = 1

    # Get the highest ID from Deleted_Listings
    cursor = connection.execute('SELECT * FROM Deleted_Listings D WHERE D.Seller_Email=?;', (email,))
    if cursor.fetchall():
        cursor = connection.execute('SELECT MAX(D.Listing_ID) FROM Deleted_Listings D WHERE D.Seller_Email=?;', (email,))
        max_deleted = cursor.fetchall()[0][0] + 1
    else:
        max_deleted = 1

    return max(max_active, max_deleted)


# Gets the current number of bids on a given listing
def get_num_bids(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT COUNT(*) FROM Bids B WHERE Seller_Email=? AND Listing_ID=?', (email, auction_id))
    return cursor.fetchall()[0][0]


# Deletes the given auction listing
def delete_listing(email, auction_id, reasoning="No reasoning provided"):
    connection = sql.connect('database.db')
    deleted_data = []

    # Get the data from Auction_Listings
    cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE Seller_Email=? AND Listing_ID=?;', (email, auction_id))
    r = cursor.fetchall()[0]
    for item in r:
        deleted_data.append(item)
    deleted_data.pop()

    # Get the number of remaining bids
    r = get_num_bids(email, auction_id)
    deleted_data.append(deleted_data[8] - r)

    # Get the reasoning
    deleted_data.append(reasoning)

    # Add the data to Deleted_Listings
    connection.execute('INSERT INTO Deleted_Listings (Seller_Email, Listing_ID, Category, Auction_Title, Product_Name, Product_Description, Quantity, Reserve_Price, Max_bids, Remaining_Bids, Reasoning) VALUES (?,?,?,?,?,?,?,?,?,?,?);', (deleted_data[0], deleted_data[1], deleted_data[2], deleted_data[3], deleted_data[4], deleted_data[5], deleted_data[6], deleted_data[7], deleted_data[8], deleted_data[9], deleted_data[10]))
    connection.commit()

    # Delete the data from Auction_Listings
    connection.execute('DELETE FROM Auction_Listings WHERE Seller_Email=? AND Listing_ID=?;', (email, auction_id))
    connection.commit()


# Gets the given auction listing
def get_listing(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT L.Listing_ID, L.Category, L.Auction_Title, L.Product_Name, L.Product_Description, L.Quantity, L.Reserve_Price, L.Max_bids, L.Status FROM Auction_Listings L WHERE L.Seller_Email=? AND L.Listing_ID=?;', (email, auction_id))
    r = cursor.fetchall()
    status_dict = {1: "Active", 0: "Inactive", 2: "Sold"}
    r2 = []
    for listing in r:
        r2.append((listing[0], listing[1], listing[2], listing[3], listing[4], listing[5], listing[6], listing[7], status_dict[listing[8]]))
    return r2


# Edits the given auction listing
def edit_listing(email, auction_id, title, pname, pdesc, cat, quantity, reserve, max_bids, status):
    connection = sql.connect('database.db')
    reserve = "$" + str(reserve)
    status_dict = {"Active": 1, "Inactive": 0, "Sold": 2}
    connection.execute('UPDATE Auction_Listings SET Category=?, Auction_Title=?, Product_Name=?, Product_Description=?, Quantity=?, Reserve_Price=?, Max_bids=?, Status=? WHERE Seller_Email=? AND Listing_ID=?', (cat, title, pname, pdesc, quantity, reserve, max_bids, status_dict[status], email, auction_id))
    connection.commit()


# Gets all of a user's roles
def get_roles(email):
    connection = sql.connect('database.db')
    roles = [""]

    # See if user is a Bidder
    cursor = connection.execute('SELECT * FROM Bidders B WHERE B.email=?;', (email,))
    if cursor.fetchall():
        roles.append('Bidder')

    # See if user is a Seller
    cursor = connection.execute('SELECT * FROM Sellers S WHERE S.email=?;', (email,))
    if cursor.fetchall():
        roles.append('Seller')

    # See if user is a HelpDesk
    cursor = connection.execute('SELECT * FROM Helpdesk H WHERE H.email=?;', (email,))
    if cursor.fetchall():
        roles.append('HelpDesk')

    return roles


# Gets the minimum bid on an item (taking into account reserve price)
def get_minimum_bid2(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT MAX(B.Bid_Price) FROM Bids B WHERE B.Seller_Email=? AND B.Listing_ID=?;', (email, auction_id))
    r1 = cursor.fetchall()[0][0]
    if r1:
        r1 = r1 + 1
    else:
        r1 = 1

    cursor = connection.execute('SELECT * FROM Auction_Listings A WHERE A.Seller_Email=? AND A.Listing_ID=?;', (email, auction_id))
    r2 = cursor.fetchall()
    if r2:
        r2 = r2[0][7]
    else:
        r2 = '0'

    return max(r1, get_num_from(r2))


# Gets the minimum bid on an item (ignoring reserve price)
def get_minimum_bid(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT MAX(B.Bid_Price) FROM Bids B WHERE B.Seller_Email=? AND B.Listing_ID=?;', (email, auction_id))
    r1 = cursor.fetchall()[0][0]
    if r1:
        return r1 + 1
    else:
        return 1


# Gets the next bid ID to be used
def get_next_bid_id():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT MAX(B.Bid_ID) FROM Bids B;')
    r = cursor.fetchall()[0][0]
    if r:
        return r + 1
    else:
        return 1


# Gets the bidder email of the most recent bidder on a given item
def get_most_recent_bidder(seller_email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT B.Bidder_Email, MAX(B.Bid_ID) FROM Bids B WHERE B.Seller_Email=? AND B.Listing_ID=?;', (seller_email, auction_id))
    r = cursor.fetchall()
    if r:
        return r[0][0]
    else:
        return ""


# Makes a bid
def make_bid(seller_email, listing_id, bidder_email, amount):
    connection = sql.connect('database.db')
    bid_id = get_next_bid_id()
    connection.execute('INSERT INTO Bids (Bid_ID, Seller_Email, Listing_ID, Bidder_Email, Bid_Price) VALUES (?,?,?,?,?);', (bid_id, seller_email, listing_id, bidder_email, amount))
    connection.commit()


# Gets the listings that a given bidder is pending; i.e. requires payment
def get_pending(bidder_email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM (SELECT B.Listing_ID, B.Seller_Email, B.Bidder_Email, B.Bid_Price, MAX(B.Bid_ID) FROM Bids B GROUP BY B.Listing_ID) AS TMP WHERE TMP.Bidder_Email=?;', (bidder_email,))
    r = cursor.fetchall()
    pending = []
    if r:
        for transaction in r:
            listing = get_listing(transaction[1], transaction[0])[0]
            if listing[8] == 'Active' and get_num_bids(transaction[1], transaction[0]) == listing[7] and get_num_from(listing[6]) <= transaction[3]:
                locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
                bid_price = locale.currency(transaction[3], grouping=True)
                l = (transaction[1],) + listing + (bid_price, transaction[4])
                pending.append(l)
    return pending


# Gets the listings that a given bidder has bought; i.e. already paid
def get_bought(bidder_email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Transactions T WHERE T.Bidder_Email=?;', (bidder_email,))
    r = cursor.fetchall()
    bought = []
    if r:
        for transaction in r:
            locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
            bid_price = locale.currency(transaction[5], grouping=True)
            l = (transaction[0], transaction[4], bid_price, transaction[1]) + get_listing(transaction[1], transaction[2])[0]
            bought.append(l)
    return bought


# Gets the listings that a given bidder has lost
def get_lost(bidder_email):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Transactions T WHERE T.Bidder_Email=?;', (bidder_email,))
    r = cursor.fetchall()
    bought = []
    if r:
        for transaction in r:
            l = (transaction[1],) + get_listing(transaction[1], transaction[2])[0]
            bought.append(l)

    cursor = connection.execute('SELECT *, MAX(TMP.Bid_ID) FROM (SELECT B.Listing_ID, B.Seller_Email, B.Bidder_Email, B.Bid_ID, B.Bid_Price FROM Bids B WHERE B.Bidder_Email=?) AS TMP GROUP BY TMP.Listing_ID;', (bidder_email,))
    r = cursor.fetchall()
    bids = []
    bid_prices = []
    for bid in r:
        locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
        bid_price = locale.currency(bid[4], grouping=True)
        bid_prices.append(bid_price)
        l = (bid[1],) + get_listing(bid[1], bid[0])[0]
        bids.append(l)

    transactions = []
    cursor = connection.execute('SELECT * FROM Transactions;')
    r = cursor.fetchall()
    for transaction in r:
        l = (transaction[1],) + get_listing(transaction[1], transaction[2])[0]
        transactions.append(l)

    lost = []
    for item in bids:
        if item in transactions and item not in bought:
            locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
            bid_price = locale.currency(get_winning_bid(item[0], item[1]), grouping=True)
            your_price = bid_prices[bids.index(item)]
            l = item + (bid_price,your_price)
            lost.append(l)
    return lost


# Gets the winning bid of an item given seller email and id
def get_winning_bid(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT * FROM Transactions T WHERE T.Seller_Email=? AND T.Listing_ID=?;', (email, auction_id,))
    r = cursor.fetchall()
    if r:
        return r[0][5]
    else:
        return 0


# Gets the maximum number of bids of a listing
def get_max_bids(email, auction_id):
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT A.Max_bids FROM Auction_Listings A WHERE A.Seller_Email=? AND A.Listing_ID=?;', (email, auction_id,))
    r = cursor.fetchall()
    if r:
        return r[0][0]
    else:
        return 0


# Converts a money string INT (i.e. $5,341) to an int
def get_num_from(s):
    return int(re.sub("[^0-9]", "", s))


# Converts a money string DOUBLE (i.e. $5,341.11) to an int
def get_num_from_double(s):
    stripped = re.sub("[^0-9]", "", s)
    return int(stripped[:-2])


# Sets a listing to be inactive
def set_inactive(email, auction_id):
    connection = sql.connect('database.db')
    connection.execute('UPDATE Auction_Listings SET Status=0 WHERE Seller_Email=? AND Listing_ID=?', (email, auction_id,))
    connection.commit()


# Sets a listing to be sold
def set_sold(email, auction_id):
    connection = sql.connect('database.db')
    connection.execute('UPDATE Auction_Listings SET Status=2 WHERE Seller_Email=? AND Listing_ID=?', (email, auction_id,))
    connection.commit()


# Gets the next transaction id
def get_transaction_id():
    connection = sql.connect('database.db')
    cursor = connection.execute('SELECT MAX(Transaction_ID) FROM Transactions')
    r = cursor.fetchall()
    if r:
        return r[0][0] + 1
    else:
        return 1


# Adds a credit card
def add_credit_card(credit_card_num, card_type, expire_month, expire_year, security_code, owner_email):
    connection = sql.connect('database.db')
    expire_month = expire_month[-2:]
    connection.execute('INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email) VALUES (?,?,?,?,?,?);', (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email))
    connection.commit()


# Creates a transaction
def complete_transaction(seller_email, listing_id, bidder_email, lpayment):
    transaction_id = get_transaction_id()
    today = date.today()
    num_payment = get_num_from_double(lpayment)
    curr_date = today.strftime("%-m/%-d/%y")
    connection = sql.connect('database.db')
    connection.execute('INSERT INTO Transactions (Transaction_ID, Seller_Email, Listing_ID, Bidder_Email, Date, Payment) VALUES (?,?,?,?,?,?);', (transaction_id, seller_email, listing_id, bidder_email, curr_date, num_payment))
    print(lpayment)
    connection.execute('UPDATE Sellers SET balance=balance+? WHERE email=?;', (num_payment, seller_email))
    connection.commit()


if __name__ == "__main__":
    app.run()
