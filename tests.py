import unittest

from appointment import get_appointment_category
from business import get_business_detail
from category import get_category
from inventory import get_inventory_details


class TestAIServices(unittest.TestCase):

    def setUp(self):
        self.user_input_appointment = "I will come this Friday at 2PM"
        self.user_input_reschedule_appointment = "I can not make it this friday"
        self.user_input_cancel_appointment = "I will not come as I have bought already a new car"
        self.user_input_business = "Provide the working hours and Is it open on sunday?"
        self.user_input_inventory = "I am looking for buy a hyundai car do you have that?."

    def test_get_category(self):
        result = get_category(self.user_input_appointment)
        self.assertEqual('1', result.lower())
        result = get_category(self.user_input_inventory)
        self.assertEqual('2', result.lower())
        result = get_category(self.user_input_business)
        self.assertEqual('3', result.lower())

    def test_get_appointment_category(self):
        result = get_appointment_category(self.user_input_appointment)
        self.assertEqual('1', result)
        result = get_appointment_category(self.user_input_reschedule_appointment)
        self.assertEqual('2', result)
        result = get_appointment_category(self.user_input_cancel_appointment)
        self.assertEqual('3', result)

    def test_get_business_detail(self):
        result = get_business_detail(self.user_input_business)
        self.assertIn('it is closed on sunday', result.lower())

    def test_conversational_chat(self):
        result = get_inventory_details(self.user_input_inventory)
        self.assertIn('we have hyundai cars in our inventory', result.lower())


if __name__ == '__main__':
    unittest.main()
