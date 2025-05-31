
import requests
import sys
import time
from datetime import datetime
import uuid
import json

class ShopSyncTester:
    def __init__(self, base_url="https://f426259c-dc96-40e1-bd4d-aa7254e15072.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.store_token = None
        self.household_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_store_id = None
        self.test_list_id = None
        self.test_item_id = None
        self.test_product_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, print_response=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

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
                if print_response:
                    print(f"Response: {json.dumps(response.json(), indent=2)}")
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    print(f"Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # Admin Tests
    def test_admin_login(self):
        """Test admin login with default credentials"""
        print("\n===== ADMIN TESTS =====")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "admin/auth/login",
            200,
            data={"email": "admin@shopsync.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print("Admin login successful, token obtained")
            return True
        return False

    def test_admin_me(self):
        """Test admin profile endpoint"""
        success, response = self.run_test(
            "Admin Profile",
            "GET",
            "admin/auth/me",
            200,
            token=self.admin_token
        )
        return success

    def test_admin_stats(self):
        """Test admin dashboard statistics"""
        success, response = self.run_test(
            "Admin Dashboard Stats",
            "GET",
            "admin/stats",
            200,
            token=self.admin_token,
            print_response=True
        )
        return success

    def test_admin_payment_config(self):
        """Test payment configuration"""
        success, response = self.run_test(
            "Get Payment Config Status",
            "GET",
            "admin/payment/config",
            200,
            token=self.admin_token
        )
        
        # Test updating payment config
        test_config = {
            "stripe_secret_key": "sk_test_example123",
            "stripe_publishable_key": "pk_test_example123",
            "stripe_endpoint_secret": "whsec_example123"
        }
        
        success2, response2 = self.run_test(
            "Update Payment Config",
            "POST",
            "admin/payment/config",
            200,
            data=test_config,
            token=self.admin_token
        )
        
        return success and success2

    def test_admin_subscriptions(self):
        """Test admin subscription monitoring"""
        success, response = self.run_test(
            "Get All Subscriptions",
            "GET",
            "admin/subscriptions",
            200,
            token=self.admin_token,
            print_response=True
        )
        return success

    # Store Tests
    def test_store_registration(self):
        """Test store registration with 7-day trial"""
        print("\n===== STORE TESTS =====")
        store_email = f"store_{int(time.time())}@test.com"
        store_data = {
            "store_name": f"Test Store {int(time.time())}",
            "email": store_email,
            "password": "StorePass123!",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "phone": "555-123-4567"
        }
        
        success, response = self.run_test(
            "Store Registration",
            "POST",
            "store/auth/register",
            200,
            data=store_data
        )
        
        if success and 'access_token' in response:
            self.store_token = response['access_token']
            print("Store registration successful, token obtained")
            return True
        return False

    def test_store_me(self):
        """Test store profile endpoint"""
        success, response = self.run_test(
            "Store Profile",
            "GET",
            "store/auth/me",
            200,
            token=self.store_token,
            print_response=True
        )
        
        if success:
            # Save store ID for later tests
            self.test_store_id = response.get('id')
        
        return success

    def test_store_subscription(self):
        """Test store subscription management"""
        success, response = self.run_test(
            "Get Current Subscription",
            "GET",
            "store/subscription",
            200,
            token=self.store_token
        )
        
        # Test creating a subscription
        subscription_data = {
            "plan": "monthly",
            "provider": "stripe"
        }
        
        success2, response2 = self.run_test(
            "Create Subscription",
            "POST",
            "store/subscription",
            200,
            data=subscription_data,
            token=self.store_token
        )
        
        return success

    def test_store_products(self):
        """Test store product management"""
        # Add a product
        product_data = {
            "name": f"Test Product {int(time.time())}",
            "category": "Groceries",
            "price": 9.99,
            "description": "A test product",
            "is_advertised": True
        }
        
        success, response = self.run_test(
            "Add Product",
            "POST",
            "store/products",
            200,
            data=product_data,
            token=self.store_token
        )
        
        if success:
            self.test_product_id = response.get('id')
        
        # Get all products
        success2, response2 = self.run_test(
            "Get Store Products",
            "GET",
            "store/products",
            200,
            token=self.store_token,
            print_response=True
        )
        
        # Update a product
        if self.test_product_id:
            update_data = {
                "name": f"Updated Product {int(time.time())}",
                "category": "Groceries",
                "price": 12.99,
                "description": "An updated test product",
                "is_advertised": True
            }
            
            success3, _ = self.run_test(
                "Update Product",
                "PUT",
                f"store/products/{self.test_product_id}",
                200,
                data=update_data,
                token=self.store_token
            )
        else:
            success3 = False
        
        return success and success2 and success3

    def test_stripe_checkout(self):
        """Test Stripe checkout session creation"""
        success, response = self.run_test(
            "Create Stripe Checkout Session",
            "POST",
            "stripe/create-checkout-session?plan_type=monthly",
            200,
            token=self.store_token,
            print_response=True
        )
        
        return success

    # Household Tests
    def test_household_registration(self):
        """Test household registration"""
        print("\n===== HOUSEHOLD TESTS =====")
        household_email = f"household_{int(time.time())}@test.com"
        household_data = {
            "name": f"Test User {int(time.time())}",
            "email": household_email,
            "password": "HouseholdPass123!"
        }
        
        success, response = self.run_test(
            "Household Registration",
            "POST",
            "auth/register",
            200,
            data=household_data
        )
        
        if success and 'access_token' in response:
            self.household_token = response['access_token']
            print("Household registration successful, token obtained")
            return True
        return False

    def test_household_me(self):
        """Test household profile endpoint"""
        success, response = self.run_test(
            "Household Profile",
            "GET",
            "auth/me",
            200,
            token=self.household_token
        )
        return success

    def test_shopping_lists(self):
        """Test shopping list creation and management"""
        # Create a list
        list_data = {
            "name": f"Test Shopping List {int(time.time())}"
        }
        
        success, response = self.run_test(
            "Create Shopping List",
            "POST",
            "lists",
            200,
            data=list_data,
            token=self.household_token
        )
        
        if success:
            self.test_list_id = response.get('id')
        
        # Get all lists
        success2, response2 = self.run_test(
            "Get All Shopping Lists",
            "GET",
            "lists",
            200,
            token=self.household_token,
            print_response=True
        )
        
        # Get specific list
        success3 = False
        if self.test_list_id:
            success3, _ = self.run_test(
                "Get Specific Shopping List",
                "GET",
                f"lists/{self.test_list_id}",
                200,
                token=self.household_token
            )
        
        return success and success2 and success3

    def test_list_items(self):
        """Test shopping list item management"""
        if not self.test_list_id:
            print("❌ No test list ID available, skipping item tests")
            return False
        
        # Add an item
        item_data = {
            "name": f"Test Item {int(time.time())}",
            "quantity": "2"
        }
        
        success, response = self.run_test(
            "Add Item to List",
            "POST",
            f"lists/{self.test_list_id}/items",
            200,
            data=item_data,
            token=self.household_token
        )
        
        if success:
            self.test_item_id = response.get('id')
        
        # Get all items
        success2, response2 = self.run_test(
            "Get All List Items",
            "GET",
            f"lists/{self.test_list_id}/items",
            200,
            token=self.household_token,
            print_response=True
        )
        
        # Update an item
        success3 = False
        if self.test_item_id:
            update_data = {
                "is_purchased": True
            }
            
            success3, _ = self.run_test(
                "Mark Item as Purchased",
                "PUT",
                f"items/{self.test_item_id}",
                200,
                data=update_data,
                token=self.household_token
            )
        
        return success and success2 and success3

    def test_product_search(self):
        """Test product search functionality"""
        success, response = self.run_test(
            "Search Products",
            "GET",
            "products/search?query=test",
            200,
            token=self.household_token,
            print_response=True
        )
        
        return success

    def test_local_stores(self):
        """Test local store discovery"""
        success, response = self.run_test(
            "Find Local Stores",
            "GET",
            "stores/local?zip_code=12345",
            200,
            token=self.household_token,
            print_response=True
        )
        
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n🚀 Starting ShopSync API Tests\n")
        
        # Admin Tests
        admin_login = self.test_admin_login()
        if admin_login:
            self.test_admin_me()
            self.test_admin_stats()
            self.test_admin_payment_config()
            self.test_admin_subscriptions()
        
        # Store Tests
        store_reg = self.test_store_registration()
        if store_reg:
            self.test_store_me()
            self.test_store_subscription()
            self.test_store_products()
            self.test_stripe_checkout()
        
        # Household Tests
        household_reg = self.test_household_registration()
        if household_reg:
            self.test_household_me()
            self.test_shopping_lists()
            self.test_list_items()
            self.test_product_search()
            self.test_local_stores()
        
        # Print results
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run} ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ShopSyncTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
