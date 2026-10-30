######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # new_product = response.get_json()
        # self.assertEqual(new_product["name"], test_product.name)
        # self.assertEqual(new_product["description"], test_product.description)
        # self.assertEqual(Decimal(new_product["price"]), test_product.price)
        # self.assertEqual(new_product["available"], test_product.available)
        # self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

    def test_get_product(self):
        """It should retrieve all the fields of a product."""
        product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), product.serialize())

    def test_get_product_not_found(self):
        """It should return 404 for an unknown product."""
        self.assertEqual(self.client.get(f"{BASE_URL}/0").status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should update a product and persist the changes."""
        product = self._create_products()[0]
        data = product.serialize()
        data["description"] = "New description"
        response = self.client.put(f"{BASE_URL}/{product.id}", json=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["id"], product.id)
        self.assertEqual(response.get_json()["description"], "New description")
        found = self.client.get(f"{BASE_URL}/{product.id}").get_json()
        self.assertEqual(found["description"], "New description")
        self.assertEqual(self.get_product_count(), 1)

    def test_update_product_not_found(self):
        """It should return 404 when updating an unknown product."""
        response = self.client.put(f"{BASE_URL}/0", json=ProductFactory().serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_invalid_product(self):
        """It should reject invalid update bodies and content types."""
        product = self._create_products()[0]
        url = f"{BASE_URL}/{product.id}"
        self.assertEqual(self.client.put(url, json={}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.put(url, data="bad").status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_product(self):
        """It should delete a product and allow repeated deletion."""
        product = self._create_products()[0]
        url = f"{BASE_URL}/{product.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")
        self.assertEqual(self.get_product_count(), 0)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)

    def test_list_all_products(self):
        """It should list zero or more products."""
        self.assertEqual(self.client.get(BASE_URL).get_json(), [])
        products = self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({p["id"] for p in response.get_json()}, {p.id for p in products})

    def test_list_by_name(self):
        """It should filter products by exact name."""
        self._create_products(3)
        matching = self.client.post(BASE_URL, json=ProductFactory(name="Unique Hat").serialize()).get_json()
        response = self.client.get(BASE_URL, query_string={"name": "Unique Hat"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [matching])
        self.assertEqual(self.client.get(BASE_URL, query_string={"name": "Missing"}).get_json(), [])

    def test_list_by_category(self):
        """It should return only products in the requested category."""
        products = self._create_products(10)
        response = self.client.get(BASE_URL, query_string={"category": Category.FOOD.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {p.id for p in products if p.category == Category.FOOD}
        self.assertEqual({p["id"] for p in response.get_json()}, expected)

    def test_list_by_availability(self):
        """It should filter on both true and false availability."""
        for available in [True, False, True]:
            self.client.post(BASE_URL, json=ProductFactory(available=available).serialize())
        for available, count in [("true", 2), ("false", 1)]:
            response = self.client.get(BASE_URL, query_string={"available": available})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.get_json()), count)
            self.assertTrue(all(p["available"] == (available == "true") for p in response.get_json()))

    def test_invalid_filters(self):
        """It should reject unknown categories and invalid boolean filters."""
        for query in [{"category": "INVALID"}, {"available": "maybe"}]:
            self.assertEqual(self.client.get(BASE_URL, query_string=query).status_code, status.HTTP_400_BAD_REQUEST)

    def test_location_header(self):
        """It should return a usable resource URL after creating a product."""
        response = self.client.post(BASE_URL, json=ProductFactory().serialize())
        found = self.client.get(response.headers["Location"])
        self.assertEqual(found.status_code, status.HTTP_200_OK)
        self.assertEqual(found.get_json(), response.get_json())
