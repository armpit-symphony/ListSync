
import requests
import uuid
import time
import sys
from datetime import datetime

class ShoppingListAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.user_type = None
        self.test_users = []
        self.test_lists = []
        self.test_items = []
        self.test_stores = []
        self.test_products = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def register_user(self, name, email, password):
        """Register a new user"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/api/auth/register",
            200,
            data={"name": name, "email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_type = response.get('user_type', 'household')
            self.test_users.append({"email": email, "password": password})
            return True
        return False

    def login_user(self, email, password):
        """Login with existing user"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "/api/auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_type = response.get('user_type', 'household')
            return True
        return False

    def get_current_user(self):
        """Get current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "/api/auth/me",
            200
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            return True, response
        return False, None

    def create_shopping_list(self, name):
        """Create a new shopping list"""
        success, response = self.run_test(
            "Create Shopping List",
            "POST",
            "/api/lists",
            200,
            data={"name": name}
        )
        
        if success and 'id' in response:
            self.test_lists.append(response)
            return True, response
        return False, None

    def get_shopping_lists(self):
        """Get all shopping lists for current user"""
        success, response = self.run_test(
            "Get Shopping Lists",
            "GET",
            "/api/lists",
            200
        )
        
        return success, response

    def get_shopping_list(self, list_id):
        """Get a specific shopping list"""
        success, response = self.run_test(
            "Get Shopping List",
            "GET",
            f"/api/lists/{list_id}",
            200
        )
        
        return success, response

    def share_list(self, list_id, email):
        """Share a list with another user"""
        success, response = self.run_test(
            "Share Shopping List",
            "POST",
            f"/api/lists/{list_id}/share",
            200,
            data={"email": email}
        )
        
        return success, response

    def delete_shopping_list(self, list_id):
        """Delete a shopping list"""
        success, response = self.run_test(
            "Delete Shopping List",
            "DELETE",
            f"/api/lists/{list_id}",
            200
        )
        
        return success, response

    def add_item(self, list_id, name, quantity="1"):
        """Add an item to a shopping list"""
        success, response = self.run_test(
            "Add Item to List",
            "POST",
            f"/api/lists/{list_id}/items",
            200,
            data={"name": name, "quantity": quantity}
        )
        
        if success and 'id' in response:
            self.test_items.append(response)
            return True, response
        return False, None

    def get_list_items(self, list_id):
        """Get all items in a shopping list"""
        success, response = self.run_test(
            "Get List Items",
            "GET",
            f"/api/lists/{list_id}/items",
            200
        )
        
        return success, response

    def update_item(self, item_id, is_purchased):
        """Update an item's purchased status"""
        success, response = self.run_test(
            "Update Item",
            "PUT",
            f"/api/items/{item_id}",
            200,
            data={"is_purchased": is_purchased}
        )
        
        return success, response

    def delete_item(self, item_id):
        """Delete an item from a shopping list"""
        success, response = self.run_test(
            "Delete Item",
            "DELETE",
            f"/api/items/{item_id}",
            200
        )
        
        return success, response

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, _ = self.run_test(
            "Invalid Login",
            "POST",
            "/api/auth/login",
            401,
            data={"email": "nonexistent@example.com", "password": "wrongpassword"}
        )
        
        return success

    def test_duplicate_registration(self, name, email, password):
        """Test registration with duplicate email"""
        success, _ = self.run_test(
            "Duplicate Registration",
            "POST",
            "/api/auth/register",
            400,
            data={"name": name, "email": email, "password": password}
        )
        
        return success

    def register_store(self, store_name, email, password, address, city, state, zip_code, phone=None):
        """Register a new store"""
        data = {
            "store_name": store_name,
            "email": email,
            "password": password,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code
        }
        if phone:
            data["phone"] = phone
            
        success, response = self.run_test(
            "Store Registration",
            "POST",
            "/api/store/auth/register",
            200,
            data=data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_type = response.get('user_type', 'store')
            self.test_stores.append({"email": email, "password": password})
            return True, response
        return False, None

    def login_store(self, email, password):
        """Login with existing store credentials"""
        success, response = self.run_test(
            "Store Login",
            "POST",
            "/api/store/auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_type = response.get('user_type', 'store')
            return True, response
        return False, None

    def get_current_store(self):
        """Get current store info"""
        success, response = self.run_test(
            "Get Current Store",
            "GET",
            "/api/store/auth/me",
            200
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            return True, response
        return False, None

    def create_subscription(self, plan):
        """Create a store subscription"""
        success, response = self.run_test(
            f"Create {plan.capitalize()} Subscription",
            "POST",
            "/api/store/subscription",
            200,
            data={"plan": plan}
        )
        
        return success, response

    def get_subscription(self):
        """Get current store subscription"""
        success, response = self.run_test(
            "Get Current Subscription",
            "GET",
            "/api/store/subscription",
            200
        )
        
        return success, response

    def add_product(self, name, category, price, description=None, is_advertised=True):
        """Add a product to store inventory"""
        data = {
            "name": name,
            "category": category,
            "price": price,
            "is_advertised": is_advertised
        }
        if description:
            data["description"] = description
            
        success, response = self.run_test(
            "Add Product",
            "POST",
            "/api/store/products",
            200,
            data=data
        )
        
        if success and 'id' in response:
            self.test_products.append(response)
            return True, response
        return False, None

    def get_store_products(self):
        """Get all products for current store"""
        success, response = self.run_test(
            "Get Store Products",
            "GET",
            "/api/store/products",
            200
        )
        
        return success, response

    def update_product(self, product_id, name, category, price, description=None, is_advertised=True):
        """Update a product"""
        data = {
            "name": name,
            "category": category,
            "price": price,
            "is_advertised": is_advertised
        }
        if description:
            data["description"] = description
            
        success, response = self.run_test(
            "Update Product",
            "PUT",
            f"/api/store/products/{product_id}",
            200,
            data=data
        )
        
        return success, response

    def delete_product(self, product_id):
        """Delete a product"""
        success, response = self.run_test(
            "Delete Product",
            "DELETE",
            f"/api/store/products/{product_id}",
            200
        )
        
        return success, response

    def search_products(self, query, zip_code=None):
        """Search for products across stores"""
        endpoint = f"/api/products/search?query={query}"
        if zip_code:
            endpoint += f"&zip_code={zip_code}"
            
        success, response = self.run_test(
            "Search Products",
            "GET",
            endpoint,
            200
        )
        
        return success, response

    def get_product_categories(self):
        """Get all product categories"""
        success, response = self.run_test(
            "Get Product Categories",
            "GET",
            "/api/products/categories",
            200
        )
        
        return success, response

    def get_local_stores(self, zip_code=None, city=None, state=None):
        """Get local stores"""
        endpoint = "/api/stores/local"
        params = []
        
        if zip_code:
            params.append(f"zip_code={zip_code}")
        if city:
            params.append(f"city={city}")
        if state:
            params.append(f"state={state}")
            
        if params:
            endpoint += "?" + "&".join(params)
            
        success, response = self.run_test(
            "Get Local Stores",
            "GET",
            endpoint,
            200
        )
        
        return success, response

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        success, _ = self.run_test(
            "Unauthorized Access",
            "GET",
            "/api/lists",
            401,
            headers={'Content-Type': 'application/json'}
        )
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        # Generate unique test data
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        test_user1 = {
            "name": f"Test User 1 {timestamp}",
            "email": f"testuser1_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        test_user2 = {
            "name": f"Test User 2 {timestamp}",
            "email": f"testuser2_{timestamp}@example.com",
            "password": "TestPassword123!"
        }
        test_store = {
            "store_name": f"Test Store {timestamp}",
            "email": f"teststore_{timestamp}@example.com",
            "password": "StorePass123!",
            "address": "123 Main St",
            "city": "Testville",
            "state": "TS",
            "zip_code": "12345",
            "phone": "555-123-4567"
        }
        
        print("\n===== STARTING API TESTS =====\n")
        print("\n----- HOUSEHOLD USER TESTS -----\n")
        
        # Test 1: Register first user
        if not self.register_user(test_user1["name"], test_user1["email"], test_user1["password"]):
            print("❌ User registration failed, stopping tests")
            return False
        
        # Test 2: Get current user info
        user1_success, user1_data = self.get_current_user()
        if not user1_success:
            print("❌ Get current user failed, stopping tests")
            return False
        
        # Test 3: Create a shopping list
        list1_success, list1_data = self.create_shopping_list(f"Test Shopping List {timestamp}")
        if not list1_success:
            print("❌ Create shopping list failed, stopping tests")
            return False
        
        # Test 4: Get all shopping lists
        lists_success, lists_data = self.get_shopping_lists()
        if not lists_success:
            print("❌ Get shopping lists failed, stopping tests")
            return False
        
        # Test 5: Get specific shopping list
        list_detail_success, _ = self.get_shopping_list(list1_data["id"])
        if not list_detail_success:
            print("❌ Get shopping list detail failed, stopping tests")
            return False
        
        # Test 6: Add items to the shopping list
        item1_success, item1_data = self.add_item(list1_data["id"], f"Test Item 1 {timestamp}", "2")
        if not item1_success:
            print("❌ Add item failed, stopping tests")
            return False
        
        item2_success, item2_data = self.add_item(list1_data["id"], f"Test Item 2 {timestamp}", "3")
        if not item2_success:
            print("❌ Add second item failed, stopping tests")
            return False
        
        # Test 7: Get list items
        items_success, items_data = self.get_list_items(list1_data["id"])
        if not items_success:
            print("❌ Get list items failed, stopping tests")
            return False
        
        # Test 8: Update item (mark as purchased)
        update_success, _ = self.update_item(item1_data["id"], True)
        if not update_success:
            print("❌ Update item failed, stopping tests")
            return False
        
        # Test 9: Register second user for sharing test
        # Save current token
        user1_token = self.token
        
        if not self.register_user(test_user2["name"], test_user2["email"], test_user2["password"]):
            print("❌ Second user registration failed, stopping tests")
            return False
        
        # Get user2 info
        user2_success, user2_data = self.get_current_user()
        if not user2_success:
            print("❌ Get second user info failed, stopping tests")
            return False
        
        # Switch back to user1
        self.token = user1_token
        
        # Test 10: Share list with user2
        share_success, _ = self.share_list(list1_data["id"], test_user2["email"])
        if not share_success:
            print("❌ Share list failed, stopping tests")
            return False
        
        # Test 11: Login as user2
        if not self.login_user(test_user2["email"], test_user2["password"]):
            print("❌ Login as second user failed, stopping tests")
            return False
        
        # Test 12: User2 should see the shared list
        user2_lists_success, user2_lists_data = self.get_shopping_lists()
        if not user2_lists_success:
            print("❌ Get second user's lists failed, stopping tests")
            return False
        
        shared_list_found = False
        for lst in user2_lists_data:
            if lst["id"] == list1_data["id"]:
                shared_list_found = True
                break
        
        if not shared_list_found:
            print("❌ Shared list not found in second user's lists")
            self.tests_run += 1
        else:
            print("✅ Shared list found in second user's lists")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 13: User2 should be able to add items to the shared list
        user2_item_success, user2_item_data = self.add_item(list1_data["id"], f"User2 Item {timestamp}")
        if not user2_item_success:
            print("❌ Second user add item to shared list failed, stopping tests")
            return False
        
        # Test 14: User2 should NOT be able to delete the list (only owner can)
        user2_delete_success, _ = self.run_test(
            "Second User Delete List (Should Fail)",
            "DELETE",
            f"/api/lists/{list1_data['id']}",
            403
        )
        
        if not user2_delete_success:
            print("❌ Access control test failed - second user should not be able to delete list")
        else:
            print("✅ Access control working - second user cannot delete list")
        
        # Switch back to user1
        self.token = user1_token
        
        # Test 15: Delete an item
        delete_item_success, _ = self.delete_item(item2_data["id"])
        if not delete_item_success:
            print("❌ Delete item failed, stopping tests")
            return False
        
        # Test 16: Delete the list
        delete_list_success, _ = self.delete_shopping_list(list1_data["id"])
        if not delete_list_success:
            print("❌ Delete list failed, stopping tests")
            return False
        
        print("\n----- STORE USER TESTS -----\n")
        
        # Test 17: Register a store
        store_reg_success, store_reg_data = self.register_store(
            test_store["store_name"],
            test_store["email"],
            test_store["password"],
            test_store["address"],
            test_store["city"],
            test_store["state"],
            test_store["zip_code"],
            test_store["phone"]
        )
        
        if not store_reg_success:
            print("❌ Store registration failed, stopping tests")
            return False
        
        # Test 18: Get store info
        store_info_success, store_info_data = self.get_current_store()
        if not store_info_success:
            print("❌ Get store info failed, stopping tests")
            return False
        
        # Verify trial status
        if store_info_data.get("subscription_status") != "trial":
            print(f"❌ Expected trial status, got {store_info_data.get('subscription_status')}")
            self.tests_run += 1
        else:
            print("✅ Store has trial status as expected")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 19: Add products
        product1_success, product1_data = self.add_product(
            f"Test Product 1 {timestamp}",
            "Produce",
            2.99,
            "Fresh organic product"
        )
        
        if not product1_success:
            print("❌ Add product failed, stopping tests")
            return False
        
        product2_success, product2_data = self.add_product(
            f"Test Product 2 {timestamp}",
            "Dairy",
            4.99,
            "Organic dairy product",
            False  # Not advertised
        )
        
        if not product2_success:
            print("❌ Add second product failed, stopping tests")
            return False
        
        # Test 20: Get store products
        products_success, products_data = self.get_store_products()
        if not products_success:
            print("❌ Get store products failed, stopping tests")
            return False
        
        if len(products_data) != 2:
            print(f"❌ Expected 2 products, got {len(products_data)}")
            self.tests_run += 1
        else:
            print("✅ Store has 2 products as expected")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 21: Update product
        update_product_success, update_product_data = self.update_product(
            product1_data["id"],
            product1_data["name"],
            product1_data["category"],
            3.49,  # Updated price
            product1_data["description"],
            product1_data["is_advertised"]
        )
        
        if not update_product_success:
            print("❌ Update product failed, stopping tests")
            return False
        
        if update_product_data["price"] != 3.49:
            print(f"❌ Expected updated price 3.49, got {update_product_data['price']}")
            self.tests_run += 1
        else:
            print("✅ Product price updated successfully")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 22: Create subscription
        subscription_success, subscription_data = self.create_subscription("monthly")
        if not subscription_success:
            print("❌ Create subscription failed, stopping tests")
            return False
        
        # Test 23: Get subscription
        get_sub_success, get_sub_data = self.get_subscription()
        if not get_sub_success:
            print("❌ Get subscription failed, stopping tests")
            return False
        
        if get_sub_data["plan"] != "monthly" or get_sub_data["monthly_price"] != 99.99:
            print(f"❌ Unexpected subscription data: {get_sub_data}")
            self.tests_run += 1
        else:
            print("✅ Subscription data is correct")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 24: Delete product
        delete_product_success, _ = self.delete_product(product2_data["id"])
        if not delete_product_success:
            print("❌ Delete product failed, stopping tests")
            return False
        
        # Test 25: Public product search (should only find advertised products)
        # First, clear token to test as unauthenticated user
        store_token = self.token
        self.token = None
        
        search_success, search_results = self.search_products(timestamp)
        if not search_success:
            print("❌ Product search failed, stopping tests")
            return False
        
        # Should only find the advertised product
        advertised_found = False
        non_advertised_found = False
        
        for result in search_results:
            if result["product"]["id"] == product1_data["id"]:
                advertised_found = True
            if result["product"]["id"] == product2_data["id"]:
                non_advertised_found = True
        
        if not advertised_found:
            print("❌ Advertised product not found in search results")
            self.tests_run += 1
        else:
            print("✅ Advertised product found in search results")
            self.tests_run += 1
            self.tests_passed += 1
        
        if non_advertised_found:
            print("❌ Non-advertised product found in search results")
            self.tests_run += 1
        else:
            print("✅ Non-advertised product correctly excluded from search results")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 26: Get product categories
        categories_success, categories_data = self.get_product_categories()
        if not categories_success:
            print("❌ Get product categories failed, stopping tests")
            return False
        
        # Test 27: Get local stores
        local_stores_success, local_stores_data = self.get_local_stores(city="Testville", state="TS")
        if not local_stores_success:
            print("❌ Get local stores failed, stopping tests")
            return False
        
        store_found = False
        for store in local_stores_data:
            if store["id"] == store_info_data["id"]:
                store_found = True
                break
        
        if not store_found:
            print("❌ Store not found in local stores search")
            self.tests_run += 1
        else:
            print("✅ Store found in local stores search")
            self.tests_run += 1
            self.tests_passed += 1
        
        # Test 28: Test invalid login
        invalid_login_success = self.test_invalid_login()
        if not invalid_login_success:
            print("❌ Invalid login test failed")
        
        # Test 29: Test duplicate registration
        duplicate_reg_success = self.test_duplicate_registration(
            test_user1["name"], test_user1["email"], test_user1["password"]
        )
        if not duplicate_reg_success:
            print("❌ Duplicate registration test failed")
        
        # Test 30: Test unauthorized access
        self.token = None
        unauth_success = self.test_unauthorized_access()
        if not unauth_success:
            print("❌ Unauthorized access test failed")
        
        # Test 31: Test cross-user type access control
        # Login as household user
        if not self.login_user(test_user1["email"], test_user1["password"]):
            print("❌ Login as household user failed, stopping tests")
            return False
        
        # Try to access store endpoint
        store_access_success, _ = self.run_test(
            "Household User Access Store Endpoint (Should Fail)",
            "GET",
            "/api/store/products",
            403
        )
        
        if not store_access_success:
            print("❌ Cross-user type access control test failed")
        else:
            print("✅ Cross-user type access control working - household user cannot access store endpoints")
            
        # Login as store user
        self.token = store_token
        
        # Try to access household endpoint
        household_access_success, _ = self.run_test(
            "Store User Access Household Endpoint (Should Fail)",
            "GET",
            "/api/lists",
            403
        )
        
        if not household_access_success:
            print("❌ Cross-user type access control test failed")
        else:
            print("✅ Cross-user type access control working - store user cannot access household endpoints")
        
        print(f"\n===== API TESTS COMPLETED =====")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run} ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        return self.tests_passed == self.tests_run

def main():
    # Get the backend URL from environment
    backend_url = "https://f426259c-dc96-40e1-bd4d-aa7254e15072.preview.emergentagent.com"
    
    # Create tester instance
    tester = ShoppingListAPITester(backend_url)
    
    # Run all tests
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
