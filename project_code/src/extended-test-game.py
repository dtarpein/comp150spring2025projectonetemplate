import sys
import os
import json
from unittest.mock import patch, MagicMock
import random
import tempfile

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from project_code.src.main import (
    Statistic, Character, Enemy, Event, Location, 
    UserInputParser, Game, EventStatus, load_events_from_json
)
import unittest

class TestStatistic(unittest.TestCase):
    """Tests for the Statistic class."""
    
    def setUp(self):
        self.strength = Statistic("Strength", value=10)

    def test_statistic_initialization(self):
        """Test that statistics are initialized with correct values."""
        self.assertEqual(self.strength.name, "Strength")
        self.assertEqual(self.strength.value, 10)
        self.assertEqual(self.strength.min_value, 0)
        self.assertEqual(self.strength.max_value, 100)
        
        # Test with custom description and bounds
        intel = Statistic("Intelligence", value=15, description="Problem-solving ability", min_value=5, max_value=30)
        self.assertEqual(intel.name, "Intelligence")
        self.assertEqual(intel.value, 15)
        self.assertEqual(intel.description, "Problem-solving ability")
        self.assertEqual(intel.min_value, 5)
        self.assertEqual(intel.max_value, 30)

    def test_statistic_modify(self):
        """Test that modifying statistics works correctly."""
        self.strength.modify(5)
        self.assertEqual(self.strength.value, 15)
        self.strength.modify(-10)
        self.assertEqual(self.strength.value, 5)

    def test_statistic_min_max_bounds(self):
        """Test that statistics respect their min/max bounds."""
        self.strength.modify(1000)
        self.assertEqual(self.strength.value, self.strength.max_value)
        self.strength.modify(-1000)
        self.assertEqual(self.strength.value, self.strength.min_value)
        
    def test_statistic_string_representation(self):
        """Test the string representation of statistics."""
        self.assertEqual(str(self.strength), "Strength: 10")
        
        self.strength.modify(5)
        self.assertEqual(str(self.strength), "Strength: 15")


class TestCharacter(unittest.TestCase):
    """Tests for the Character class."""

    def setUp(self):
        # Fix the random seed for deterministic tests
        random.seed(42)
        self.hero = Character(name="Hero")
        self.gearshot = Character(name="Jace", class_type="Gearshot")
        self.rustblade = Character(name="Brunhilde", class_type="Rustblade")
        self.steamwright = Character(name="Edison", class_type="Steamwright")

    def test_character_initialization(self):
        """Test that characters are initialized with correct attributes."""
        self.assertEqual(self.hero.name, "Hero")
        self.assertEqual(self.hero.class_type, "Scrapper")
        self.assertEqual(self.hero.strength.name, "Strength")
        self.assertEqual(self.hero.dexterity.name, "Dexterity")
        self.assertEqual(self.hero.vitality.name, "Vitality")
        self.assertEqual(self.hero.intelligence.name, "Intelligence")
        self.assertEqual(self.hero.inventory, [])
        
    def test_class_base_stats(self):
        """Test that different character classes have the expected base stats."""
        # Scrapper (balanced)
        self.assertEqual(self.hero.strength.value, 5)
        self.assertEqual(self.hero.dexterity.value, 5)
        self.assertEqual(self.hero.vitality.value, 20)
        self.assertEqual(self.hero.intelligence.value, 5)
        
        # Gearshot (high DEX, low STR)
        self.assertEqual(self.gearshot.strength.value, 3)
        self.assertEqual(self.gearshot.dexterity.value, 7)
        self.assertEqual(self.gearshot.vitality.value, 15)
        self.assertEqual(self.gearshot.intelligence.value, 5)
        
        # Rustblade (high STR, low DEX)
        self.assertEqual(self.rustblade.strength.value, 7)
        self.assertEqual(self.rustblade.dexterity.value, 4)
        self.assertEqual(self.rustblade.vitality.value, 16)
        self.assertEqual(self.rustblade.intelligence.value, 4)
        
        # Steamwright (high INT, medium STR)
        self.assertEqual(self.steamwright.strength.value, 4)
        self.assertEqual(self.steamwright.dexterity.value, 5)
        self.assertEqual(self.steamwright.vitality.value, 18)
        self.assertEqual(self.steamwright.intelligence.value, 7)
        
    def test_take_damage(self):
        """Test that characters can take damage and track vitality correctly."""
        initial_vitality = self.hero.vitality.value
        
        # Take some damage
        result = self.hero.take_damage(5)
        self.assertTrue(result)  # Character is still alive
        self.assertEqual(self.hero.vitality.value, initial_vitality - 5)
        
        # Take fatal damage
        result = self.hero.take_damage(100)
        self.assertFalse(result)  # Character is dead
        self.assertEqual(self.hero.vitality.value, 0)  # Vitality bottoms out at 0
        
    def test_is_alive(self):
        """Test that the is_alive method correctly reports character status."""
        self.assertTrue(self.hero.is_alive())
        
        self.hero.take_damage(100)  # Fatal damage
        self.assertFalse(self.hero.is_alive())
        
    def test_inventory_management(self):
        """Test adding items to character inventory."""
        self.assertEqual(len(self.hero.inventory), 0)
        
        self.hero.add_to_inventory("Core Fragment")
        self.assertEqual(len(self.hero.inventory), 1)
        self.assertEqual(self.hero.inventory[0], "Core Fragment")
        
        self.hero.add_to_inventory("Canteen")
        self.assertEqual(len(self.hero.inventory), 2)
        self.assertEqual(self.hero.inventory[1], "Canteen")
        
    def test_get_stats(self):
        """Test that get_stats returns the correct list of statistics."""
        stats = self.hero.get_stats()
        self.assertEqual(len(stats), 4)
        self.assertEqual(stats[0].name, "Strength")
        self.assertEqual(stats[1].name, "Dexterity")
        self.assertEqual(stats[2].name, "Vitality")
        self.assertEqual(stats[3].name, "Intelligence")
        
    def test_string_representation(self):
        """Test the string representation of a character."""
        # Reset the character's stats to fixed values for the test
        self.hero.strength.value = 6
        self.hero.dexterity.value = 7
        self.hero.vitality.value = 18
        self.hero.max_vitality = 20
        self.hero.intelligence.value = 5
        
        expected = "Character: Hero (Scrapper), STR 6, DEX 7, VIT 18/20, INT 5"
        self.assertEqual(str(self.hero), expected)


class TestEnemy(unittest.TestCase):
    """Tests for the Enemy class."""
    
    def setUp(self):
        self.enemy = Enemy("Steam Scorpion", 10, 2, 6)
        
    def test_enemy_initialization(self):
        """Test that enemies are initialized with correct attributes."""
        self.assertEqual(self.enemy.name, "Steam Scorpion")
        self.assertEqual(self.enemy.vitality, 10)
        self.assertEqual(self.enemy.strength, 2)
        self.assertEqual(self.enemy.dexterity, 6)
        
    def test_take_damage(self):
        """Test that enemies can take damage correctly."""
        self.enemy.take_damage(4)
        self.assertEqual(self.enemy.vitality, 6)
        
        # Taking more damage than remaining vitality
        self.enemy.take_damage(10)
        self.assertEqual(self.enemy.vitality, 0)  # Can't go below 0
        
    def test_is_alive(self):
        """Test that the is_alive method correctly reports enemy status."""
        self.assertTrue(self.enemy.is_alive())
        
        self.enemy.take_damage(10)  # Fatal damage
        self.assertFalse(self.enemy.is_alive())
        
    def test_display_stats(self):
        """Test the display_stats method returns formatted string."""
        expected = "Steam Scorpion: Vitality 10, Strength 2, Dexterity 6"
        self.assertEqual(self.enemy.display_stats(), expected)


class TestEvent(unittest.TestCase):
    """Tests for the Event class."""

    def setUp(self):
        self.combat_data = {
            "type": "combat",
            "primary_attribute": "strength",
            "prompt_text": "A Steam Scorpion scuttles from the shadows, claws snapping!",
            "pass": {"message": "You crush the Steam Scorpion with brute force! Reward: Core Fragment"},
            "fail": {"message": "The Steam Scorpion overpowers you, dealing 5 damage!"},
            "reward": "Core Fragment",
            "penalty": 5,
            "enemy": {"name": "Steam Scorpion", "vitality": 10, "strength": 2, "dexterity": 6}
        }
        
        self.puzzle_data = {
            "type": "puzzle",
            "primary_attribute": "intelligence",
            "prompt_text": "A locked gear mechanism requires precise alignment.",
            "pass": {"message": "You align the gears perfectly! Reward: Canteen"},
            "fail": {"message": "The mechanism jams, dealing 3 damage!"},
            "reward": "Canteen",
            "penalty": 3
        }
        
        self.event_data = {
            "primary_attribute": "Intelligence",
            "secondary_attribute": "Strength",
            "prompt_text": "A mysterious door blocks your path, with a riddle inscribed. What will you do?",
            "pass": {"message": "You solved the riddle and pushed the door open. You may proceed."},
            "fail": {"message": "You failed to solve the riddle and push the door open. You must find another way."},
            "partial_pass": {"message": "You managed to solve the riddle or push the door, but not both."}
        }
        
        self.combat_event = Event(self.combat_data)
        self.puzzle_event = Event(self.puzzle_data)
        self.event = Event(self.event_data)

    def test_event_initialization(self):
        """Test that events are initialized with correct attributes."""
        self.assertEqual(self.event.primary_attribute, "Intelligence")
        self.assertEqual(self.event.secondary_attribute, "Strength")
        self.assertEqual(self.event.prompt_text, self.event_data["prompt_text"])
        self.assertEqual(self.event.pass_message, self.event_data["pass"]["message"])
        self.assertEqual(self.event.fail_message, self.event_data["fail"]["message"])
        self.assertEqual(self.event.partial_pass_message, self.event_data["partial_pass"]["message"])
        self.assertEqual(self.event.status, EventStatus.UNKNOWN)
        
    def test_combat_event_initialization(self):
        """Test that combat events are initialized with correct attributes."""
        self.assertEqual(self.combat_event.type, "combat")
        self.assertEqual(self.combat_event.primary_attribute, "strength")
        self.assertEqual(self.combat_event.reward, "Core Fragment")
        self.assertEqual(self.combat_event.penalty, 5)
        self.assertEqual(self.combat_event.enemy["name"], "Steam Scorpion")
        
    def test_resolve_choice(self):
        """Test that resolve_choice correctly determines outcomes based on stats."""
        character = Character("Tester")
        character.intelligence.value = 10
        character.strength.value = 5
        
        # Test primary attribute match (intelligence)
        intel_stat = character.intelligence
        self.assertTrue(self.event.resolve_choice(character, intel_stat))
        self.assertEqual(self.event.status, EventStatus.PASS)
        
        # Test secondary attribute match (strength)
        str_stat = character.strength  
        self.assertTrue(self.event.resolve_choice(character, str_stat))
        self.assertEqual(self.event.status, EventStatus.PARTIAL_PASS)
        
        # Test non-matching attribute (dexterity)
        dex_stat = character.dexterity
        self.assertFalse(self.event.resolve_choice(character, dex_stat))
        self.assertEqual(self.event.status, EventStatus.FAIL)
        
    @patch('builtins.print')
    @patch('random.randint')
    def test_resolve_puzzle(self, mock_randint, mock_print):
        """Test puzzle resolution."""
        character = Character("Tester")
        character.intelligence.value = 6
        
        # Test successful puzzle (roll 4 + intelligence 6 = 10, just enough to pass)
        mock_randint.return_value = 4
        self.assertTrue(self.puzzle_event.resolve_puzzle(character))
        
        # Test failed puzzle (roll 3 + intelligence 6 = 9, not enough)
        mock_randint.return_value = 3
        self.assertFalse(self.puzzle_event.resolve_puzzle(character))
        
    @patch('builtins.print')
    @patch('random.randint')
    def test_resolve_loot(self, mock_randint, mock_print):
        """Test loot resolution."""
        character = Character("Tester")
        character.dexterity.value = 5
        
        # Loot events require a threshold of 8
        # Test successful loot (roll 4 + dexterity 5 = 9, enough to pass)
        mock_randint.return_value = 4
        self.assertTrue(self.combat_event.resolve_loot(character))
        
        # Test failed loot (roll 2 + dexterity 5 = 7, not enough)
        mock_randint.return_value = 2
        self.assertFalse(self.combat_event.resolve_loot(character))


class TestUserInputParser(unittest.TestCase):
    """Tests for the UserInputParser class."""
    
    def setUp(self):
        self.parser = UserInputParser()
        self.character1 = Character("Alice", "Scrapper")
        self.character2 = Character("Bob", "Gearshot")
        self.party = [self.character1, self.character2]
        
    @patch('builtins.input', return_value="Test Input")
    def test_parse(self, mock_input):
        """Test that parse correctly returns user input."""
        result = self.parser.parse("Enter something: ")
        mock_input.assert_called_once_with("Enter something: ")
        self.assertEqual(result, "Test Input")
        
    @patch('builtins.input', side_effect=["invalid", "3", "0", "1"])
    @patch('builtins.print')
    def test_select_party_member(self, mock_print, mock_input):
        """Test party member selection with various inputs."""
        # Test with valid input
        result = self.parser.select_party_member(self.party)
        self.assertEqual(result, self.character1)
        
        # Test with empty party
        result = self.parser.select_party_member([])
        self.assertIsNone(result)
        
    @patch('builtins.input', side_effect=["invalid", "3", "0", "2"])
    @patch('builtins.print')
    def test_select_stat(self, mock_print, mock_input):
        """Test character stat selection."""
        result = self.parser.select_stat(self.character1)
        self.assertEqual(result, self.character1.dexterity)


class TestLocation(unittest.TestCase):
    """Tests for the Location class."""
    
    def setUp(self):
        self.event1 = MagicMock()
        self.event2 = MagicMock()
        self.events = [self.event1, self.event2]
        self.location = Location("Test Location", self.events)
        
    def test_location_initialization(self):
        """Test that locations are initialized correctly."""
        self.assertEqual(self.location.name, "Test Location")
        self.assertEqual(self.location.events, self.events)
        
    @patch('random.choice')
    def test_get_event(self, mock_choice):
        """Test that get_event returns a random event."""
        mock_choice.return_value = self.event1
        result = self.location.get_event()
        mock_choice.assert_called_once_with(self.events)
        self.assertEqual(result, self.event1)


class TestGame(unittest.TestCase):
    """Tests for the Game class."""
    
    def setUp(self):
        self.parser = MagicMock()
        self.character = Character("Tester")
        
        self.location1 = MagicMock()
        self.location1.name = "Location 1"
        self.location2 = MagicMock()
        self.location2.name = "Location 2"
        
        self.locations = [self.location1, self.location2]
        self.game = Game(self.parser, [self.character], self.locations)
        
    def test_game_initialization(self):
        """Test that the game is initialized correctly."""
        self.assertEqual(self.game.parser, self.parser)
        self.assertEqual(self.game.party, [self.character])
        self.assertEqual(self.game.locations, self.locations)
        self.assertEqual(self.game.core_fragments, 0)
        self.assertTrue(self.game.continue_playing)
        
    def test_check_game_over(self):
        """Test game over condition check."""
        # Not game over with party members
        self.assertFalse(self.game.check_game_over())
        
        # Game over when party is empty
        self.game.party = []
        self.assertTrue(self.game.check_game_over())
        
    @patch('builtins.print')
    def test_print_status(self, mock_print):
        """Test status display."""
        self.game._print_status()
        # We're just checking that the method completes without errors
        self.assertTrue(mock_print.called)
        
    @patch('builtins.print')
    def test_print_victory(self, mock_print):
        """Test victory message display."""
        self.game._print_victory()
        self.assertTrue(mock_print.called)
        
    @patch('builtins.print')
    def test_print_defeat(self, mock_print):
        """Test defeat message display."""
        # Test with fragments
        self.game._print_defeat(True)
        self.assertTrue(mock_print.called)
        
        mock_print.reset_mock()
        
        # Test without fragments
        self.game._print_defeat(False)
        self.assertTrue(mock_print.called)


class TestLoadEventsFromJson(unittest.TestCase):
    """Tests for the load_events_from_json function."""
    
    def test_load_valid_json(self):
        """Test loading events from a valid JSON file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            json.dump([
                {
                    "type": "combat",
                    "primary_attribute": "strength",
                    "prompt_text": "A test enemy appears!",
                    "pass": {"message": "You win!"},
                    "fail": {"message": "You lose!"},
                    "enemy": {"name": "Test Enemy", "vitality": 5, "strength": 1, "dexterity": 1}
                }
            ], temp_file)
        
        try:
            events = load_events_from_json(temp_file.name)
            self.assertEqual(len(events), 1)
            self.assertIsInstance(events[0], Event)
            self.assertEqual(events[0].type, "combat")
        finally:
            # Clean up
            os.unlink(temp_file.name)
    
    @patch('builtins.print')
    def test_load_invalid_json(self, mock_print):
        """Test handling of invalid JSON files."""
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("This is not valid JSON")
        
        try:
            events = load_events_from_json(temp_file.name)
            self.assertEqual(events, [])
            self.assertTrue(mock_print.called)
        finally:
            # Clean up
            os.unlink(temp_file.name)
    
    @patch('builtins.print')
    def test_load_nonexistent_file(self, mock_print):
        """Test handling of nonexistent files."""
        events = load_events_from_json("this_file_does_not_exist.json")
        self.assertEqual(events, [])
        self.assertTrue(mock_print.called)


if __name__ == '__main__':
    unittest.main()
