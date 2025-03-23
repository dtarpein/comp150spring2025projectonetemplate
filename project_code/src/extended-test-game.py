"""Minimized tests for Canyon of the Lost Engines game."""
import sys, os, json, random, tempfile
from unittest.mock import patch, MagicMock
import unittest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import from main.py
from project_code.src.main import (
    Statistic, Character, Enemy, Event, Location, 
    UserInputParser, Game, EventStatus, load_events_from_json
)

# Fix random seed for consistent tests
random.seed(42)

class TestStatistic(unittest.TestCase):
    def setUp(self):
        self.stat = Statistic("Strength", value=10)

    def test_basics(self):
        self.assertEqual(self.stat.name, "Strength")
        self.assertEqual(self.stat.value, 10)
        self.stat.modify(5)
        self.assertEqual(self.stat.value, 15)
        self.assertEqual(str(self.stat), "Strength: 15")
        # Test bounds
        self.stat.modify(1000)
        self.assertEqual(self.stat.value, 100)
        self.stat.modify(-200)
        self.assertEqual(self.stat.value, 0)

class TestCharacter(unittest.TestCase):
    @patch('random.randint', return_value=0)
    def setUp(self, mock_random):
        self.hero = Character("Hero")
        self.gearshot = Character("Jace", "Gearshot")

    def test_basics(self):
        # Test initialization
        self.assertEqual(self.hero.name, "Hero")
        self.assertEqual(self.hero.class_type, "Scrapper")
        self.assertEqual(self.hero.inventory, [])
        
        # Test class stats
        self.assertEqual(self.hero.strength.value, 5)
        self.assertEqual(self.gearshot.dexterity.value, 7)
        
        # Test damage and inventory
        self.assertTrue(self.hero.is_alive())
        self.hero.take_damage(5)
        self.assertEqual(self.hero.vitality.value, 15)
        self.hero.add_to_inventory("Core Fragment")
        self.assertEqual(self.hero.inventory, ["Core Fragment"])

class TestEnemy(unittest.TestCase):
    def test_basics(self):
        enemy = Enemy("Steam Scorpion", 10, 2, 6)
        self.assertEqual(enemy.name, "Steam Scorpion")
        self.assertEqual(enemy.vitality, 10)
        enemy.take_damage(4)
        self.assertEqual(enemy.vitality, 6)
        self.assertTrue(enemy.is_alive())
        enemy.take_damage(10)
        self.assertEqual(enemy.vitality, 0)
        self.assertFalse(enemy.is_alive())

class TestEvent(unittest.TestCase):
    @patch('random.randint', return_value=0)
    def setUp(self, mock_random):
        # Prepare test data
        self.combat_data = {
            "type": "combat",
            "primary_attribute": "strength",
            "prompt_text": "An enemy appears!",
            "pass": {"message": "You win!"},
            "fail": {"message": "You lose!"},
            "reward": "Core Fragment",
            "penalty": 5,
            "enemy": {"name": "Test Enemy", "vitality": 5, "strength": 1, "dexterity": 1}
        }
        self.event_data = {
            "primary_attribute": "Intelligence",
            "secondary_attribute": "Strength",
            "prompt_text": "A puzzle appears!",
            "pass": {"message": "Pass"},
            "fail": {"message": "Fail"},
            "partial_pass": {"message": "Partial"}
        }
        self.event = Event(self.event_data)
        self.character = Character("Tester")
        self.character.intelligence.value = 10
        self.character.strength.value = 5

    @patch('builtins.print')
    def test_resolve_choice(self, mock_print):
        # Test primary attribute success
        intel_stat = self.character.intelligence
        self.assertTrue(self.event.resolve_choice(self.character, intel_stat))
        self.assertEqual(self.event.status, EventStatus.PASS)
        
        # Test secondary attribute partial success
        str_stat = self.character.strength
        self.assertTrue(self.event.resolve_choice(self.character, str_stat))
        self.assertEqual(self.event.status, EventStatus.PARTIAL_PASS)
        
        # Test failure
        dex_stat = self.character.dexterity
        self.assertFalse(self.event.resolve_choice(self.character, dex_stat))
        self.assertEqual(self.event.status, EventStatus.FAIL)

    @patch('builtins.print')
    @patch('random.randint')
    def test_dice_rolls(self, mock_random, mock_print):
        # Test puzzle success
        mock_random.return_value = 4
        self.character.intelligence.value = 6
        event = Event({"type": "puzzle", "primary_attribute": "intelligence"})
        self.assertTrue(event.resolve_puzzle(self.character))
        
        # Test puzzle failure
        mock_random.return_value = 3
        self.assertFalse(event.resolve_puzzle(self.character))

class TestLocation(unittest.TestCase):
    def test_basics(self):
        event1, event2 = MagicMock(), MagicMock()
        location = Location("Test Location", [event1, event2])
        self.assertEqual(location.name, "Test Location")
        with patch('random.choice', return_value=event1):
            self.assertEqual(location.get_event(), event1)

class TestGame(unittest.TestCase):
    @patch('random.randint', return_value=0)
    def test_basics(self, mock_random):
        parser = MagicMock()
        character = Character("Tester")
        location = MagicMock()
        location.name = "Test Location"
        game = Game(parser, [character], [location])
        
        # Test initialization
        self.assertEqual(game.party, [character])
        self.assertEqual(game.core_fragments, 0)
        
        # Test game over condition
        self.assertFalse(game.check_game_over())
        game.party = []
        self.assertTrue(game.check_game_over())

class TestLoadEventsFromJson(unittest.TestCase):
    def test_load_events(self):
        # Test valid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            json.dump([{"type": "combat", "primary_attribute": "strength"}], temp_file)
        
        try:
            events = load_events_from_json(temp_file.name)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].type, "combat")
        finally:
            os.unlink(temp_file.name)
        
        # Test invalid paths
        with patch('builtins.print'):
            events = load_events_from_json("nonexistent_file.json")
            self.assertEqual(events, [])

if __name__ == '__main__':
    unittest.main()