# LionAuction

This project implements the complete functionality for the LionAuction project. It provides a working interface for an auctioning system, whereby sellers can create listings and bidders can bid on said listings.

## Installation

Download the Yifan_Lu_LionAuction.zip file and open the project in a supported environment, such as PyCharm Professional. There should be fifteen (15) functional files:

```angular2html
index.html
index_wrong_password.html
bidderhome.html
sellerhome.html
localvendorhome.html
helpdeskhome.html
browse.html
details.html
bidderdetails.html
sellerdetails.html
createlisting.html
editlisting.html
payment.html
error.html
app.py
```

Each of the ```.html``` files represents a webpage (the login pages, the home pages, the browsing page, details of a listing pages, create listing page, edit listing page, payment page, and error page, respectively).

The ```app.py``` file is used to extract and input data into the database, and also to assist with site navigation and functionality.

To run the project, click the 'Run' button in Pycharm Professional (or whatever environment you are using) and then click on the generated server.
## Usage


#### Login Page
Enter a user's email and password, click on the radio button corresponding to their role, and then click the 'Sign In' button.

#### Home Page
All roles are able to view relevant personal data and browse the category hierarchy on the homepage.

Bidders are able to view their active bids, pending payments (i.e. bids that they have won but not yet paid for), purchased items, and lost bids. From the pending payments section, bidders can choose to pay for their winning bids.

Sellers are able to view their listings, and navigate to each listing to edit or delete them (take them off the market). They may also create a new listing by clicking the button.

HelpDesk staff are able to view their requests.

#### Browsing
All roles are able to browse the category hierarchy and view any of the active items currently on the market. However, only bidders are able to bid on products (and they are not able to bid on their own products), and only sellers are able to edit / delete their own listings.

#### Details
From the details page, bidders can bid on listings by entering a bid in the input field. Sellers may edit or delete the listings by clicking on the respective buttons.

#### Create Listing
Only sellers are able to access this page, which allows them to create a new listing by entering all the required information.

#### Edit Listing
Similar to create listing, only sellers are able to access this page, which allows them to edit one of their pre-existing listings.

#### Payment
Only bidders are able to access this page, which they do so by clicking on the pending payments tab in the homepage. Bidders can choose to use an existing credit card to complete the transaction, or enter a new card, which will automatically be saved into the database.

#### Error
This page will only appear if the user tries to enter a page that they are not permitted to; i.e. if a user tries to manually enter the homepage without logging in. In the case that it does, the user can simply go back and try again.

## Authors

This project was created by Yifan Lu (yifan@psu.edu) for Mr. Dude, with guidance from the CMPSC 431W teaching team at Penn State University.

