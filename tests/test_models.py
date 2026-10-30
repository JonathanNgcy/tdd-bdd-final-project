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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, DataValidationError, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_product(self):
        """It should read every persisted product attribute."""
        product = ProductFactory()
        product.create()
        logging.debug("Created product: %s", product)
        self.assertIsNotNone(product.id)
        self.assertEqual(Product.find(product.id).serialize(), product.serialize())
        self.assertIsNone(Product.find(0))

    def test_update_product(self):
        """It should persist an updated description without adding a row."""
        product = ProductFactory()
        product.create()
        product_id = product.id
        product.description = "Updated description"
        product.update()
        self.assertEqual(len(Product.all()), 1)
        found = Product.find(product_id)
        self.assertEqual(found.id, product_id)
        self.assertEqual(found.description, "Updated description")

    def test_update_without_id(self):
        """It should reject updates to an unsaved product."""
        product = ProductFactory(id=None)
        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_product(self):
        """It should remove the saved product."""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(Product.all(), [])
        self.assertIsNone(Product.find(product.id))

    def test_list_all_products(self):
        """It should list every saved product."""
        self.assertEqual(Product.all(), [])
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        self.assertEqual({p.id for p in Product.all()}, {p.id for p in products})

    def test_find_by_name(self):
        """It should return only products with an exact matching name."""
        products = [ProductFactory(name=name) for name in ["Hat", "Shoes", "Hat"]]
        for product in products:
            product.create()
        found = list(Product.find_by_name("Hat"))
        self.assertEqual({p.id for p in found}, {products[0].id, products[2].id})
        self.assertTrue(all(p.name == "Hat" for p in found))
        self.assertEqual(list(Product.find_by_name("Missing")), [])

    def test_find_by_category(self):
        """It should return only products in the requested category."""
        products = [ProductFactory(category=value) for value in [Category.FOOD, Category.TOOLS, Category.FOOD]]
        for product in products:
            product.create()
        found = list(Product.find_by_category(Category.FOOD))
        self.assertEqual({p.id for p in found}, {products[0].id, products[2].id})
        self.assertTrue(all(p.category == Category.FOOD for p in found))

    def test_find_by_availability(self):
        """It should find both available and unavailable products."""
        products = [ProductFactory(available=value) for value in [True, False, True]]
        for product in products:
            product.create()
        for available in [True, False]:
            found = list(Product.find_by_availability(available))
            expected = {p.id for p in products if p.available == available}
            self.assertEqual({p.id for p in found}, expected)
            self.assertTrue(all(p.available == available for p in found))

    def test_find_by_price(self):
        """It should query prices supplied as Decimal or string."""
        product = ProductFactory(price=Decimal("12.50"))
        product.create()
        self.assertEqual(list(Product.find_by_price(Decimal("12.50"))), [product])
        self.assertEqual(list(Product.find_by_price(' "12.50" ')), [product])

    def test_serialize_deserialize(self):
        """It should preserve all fields in a serialization round trip."""
        product = ProductFactory()
        data = product.serialize()
        restored = Product().deserialize(data)
        restored.id = product.id
        self.assertEqual(restored.serialize(), data)

    def test_deserialize_invalid_data(self):
        """It should reject missing, invalid, and incorrectly typed input."""
        data = ProductFactory().serialize()
        for invalid in [None, {}, dict(data, available="true"), dict(data, category="INVALID")]:
            with self.subTest(data=invalid):
                with self.assertRaises(DataValidationError):
                    Product().deserialize(invalid)
