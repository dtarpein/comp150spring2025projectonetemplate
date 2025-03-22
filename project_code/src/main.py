"""
Main module for Canyon of the Lost Engines game.
"""
import json
import random
from typing import List, Optional
from enum import Enum

# For the tests to work, we need to define these classes directly in main.py
# since test_game.py imports them from here

class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"

class Statistic:
    def __init__(self, name: str, value: int = 0, description: str = "", min_value: int = 0, max_value: int = 100):
        self.name = name
        self.value = value
        self.description = description
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self):
        return f"{self.name}: {self.value}"

    def modify(self, amount: int):
        self.value = max(self.min_value, min(self.max_value, self.value + amount))

class Character:
    def __init__(self, name: str = "Bob", class_type: str = "Scrapper"):
        self.name = name
        self.class_type = class_type
        self.strength = Statistic("Strength", description="Physical power.")
        self.dexterity = Statistic("Dexterity", description="Agility and accuracy.")
        self.vitality = Statistic("Vitality", description="Health points.", max_value=30)
        self.intelligence = Statistic("Intelligence", description="Problem-solving ability.")
        self.set_base_stats()
        self.randomize_stats()
        self.max_vitality = self.vitality.value  # Track max for healing
        self.inventory = []  # Track items collected

    def set_base_stats(self):
        """Set base stats based on class type."""
        base_stats = {
            "Scrapper": {"strength": 5, "dexterity": 5, "vitality": 20, "intelligence": 5},
            "Gearshot": {"strength": 3, "dexterity": 7, "vitality": 15, "intelligence": 5},
            "Steamwright": {"strength": 4, "dexterity": 5, "vitality": 18, "intelligence": 7},
            "Rustblade": {"strength": 7, "dexterity": 4, "vitality": 16, "intelligence": 4}
        }
        class_stats = base_stats.get(self.class_type, base_stats["Scrapper"])
        for stat, value in class_stats.items():
            getattr(self, stat).value = value

    def randomize_stats(self):
        """Add random variation to stats."""
        for stat in [self.strength, self.dexterity, self.vitality, self.intelligence]:
            stat.modify(random.randint(-2, 2))

    def take_damage(self, damage: int) -> bool:
        """Reduce vitality and return if alive."""
        self.vitality.modify(-damage)
        return self.vitality.value > 0

    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.vitality.value > 0

    def add_to_inventory(self, item: str):
        """Add an item to the character's inventory."""
        self.inventory.append(item)
        
    def __str__(self):
        return (f"Character: {self.name} ({self.class_type}), "
                f"STR {self.strength.value}, DEX {self.dexterity.value}, "
                f"VIT {self.vitality.value}/{self.max_vitality}, INT {self.intelligence.value}")

    def get_stats(self):
        """Return a list of the character's stats."""
        return [self.strength, self.dexterity, self.vitality, self.intelligence]

class Enemy:
    """Represents an enemy with basic combat stats."""
    def __init__(self, name: str, vitality: int, strength: int, dexterity: int):
        self.name = name
        self.vitality = vitality
        self.strength = strength
        self.dexterity = dexterity

    def take_damage(self, damage: int):
        """Reduce vitality by damage amount."""
        self.vitality = max(0, self.vitality - damage)  # Prevent negative vitality

    def is_alive(self) -> bool:
        """Check if enemy is alive."""
        return self.vitality > 0

    def display_stats(self) -> str:
        """Return formatted stats string."""
        return f"{self.name}: Vitality {self.vitality}, Strength {self.strength}, Dexterity {self.dexterity}"

class Event:
    """Represents an in-game event with resolution logic."""
    def __init__(self, data: dict):
        self.type = data.get("type", "default")
        self.primary_attribute = data.get('primary_attribute', "")
        self.secondary_attribute = data.get('secondary_attribute', "")
        self.prompt_text = data.get('prompt_text', "")
        self.pass_message = data.get('pass', {}).get('message', "")
        self.fail_message = data.get('fail', {}).get('message', "")
        self.partial_pass_message = data.get('partial_pass', {}).get('message', "")
        self.reward = data.get('reward', "")
        self.penalty = data.get('penalty', 0)
        self.recruit = data.get('recruit', None)
        self.enemy = data.get('enemy', None)
        self.status = EventStatus.UNKNOWN

    def execute(self, party: List[Character], parser=None) -> bool:
        """Execute the event based on its type."""
        print(f"\n{self.prompt_text}")
        
        # Dictionary maps event types to handler methods
        event_handlers = {
            "combat": self._handle_combat,
            "puzzle": self._handle_puzzle,
            "loot": self._handle_loot,
            "recruit": self._handle_recruit,
            "boss": self._handle_boss
        }
        
        # Get the appropriate handler for this event type
        handler = event_handlers.get(self.type)
        return handler(party, parser) if handler else False
    
    def _handle_combat(self, party, parser):
        """Handle a combat event."""
        character = self._select_party_member(party, parser)
        if not character:
            return False

        if self.resolve_combat(character, party, parser):
            self.status = EventStatus.PASS
            print(self.pass_message)
            if self.reward:
                print(f"Reward: {self.reward}")
                if hasattr(character, 'add_to_inventory'):
                    character.add_to_inventory(self.reward)
            return True
        else:
            self.status = EventStatus.FAIL
            print(self.fail_message)
            if character and not character.is_alive():
                party.remove(character)
                print(f"{character.name} has been lost!")
            return False
    
    def _handle_puzzle(self, party, parser):
        character = self._select_party_member(party, parser)
        if not character:
            return False
            
        if self.resolve_puzzle(character):
            self.status = EventStatus.PASS
            print(self.pass_message)
            if self.reward:
                print(f"Reward: {self.reward}")
                if hasattr(character, 'add_to_inventory'):
                    character.add_to_inventory(self.reward)
            return True
        else:
            self.status = EventStatus.FAIL
            print(self.fail_message)
            if self.penalty:
                character.take_damage(self.penalty)
                print(f"{character.name} takes {self.penalty} damage!")
                if not character.is_alive():
                    party.remove(character)
                    print(f"{character.name} has been lost!")
            return False
    
    def _handle_loot(self, party, parser):
        character = self._select_party_member(party, parser)
        if not character:
            return False
        
        self.status = EventStatus.PASS
        print(self.pass_message)
        if self.reward:
            print(f"Reward: {self.reward}")
            if hasattr(character, 'add_to_inventory'):
                character.add_to_inventory(self.reward)
        return True
    
    def _handle_recruit(self, party, parser):
        self.status = EventStatus.PASS
        prompt = "Recruit this survivor? 1. Yes 2. No\n> "
        
        choice = self._get_input(prompt, parser)
        if choice == "1" and self.recruit:
            new_char = Character(self.recruit["name"], self.recruit["class"])
            new_char.vitality.value = self.recruit["initial_vitality"]
            party.append(new_char)
            print(self.pass_message)
            return True
        else:
            print("You leave the survivor behind.")
            return False
    
    def _handle_boss(self, party, parser):
        if self.resolve_boss(party, parser):
            self.status = EventStatus.PASS
            print(self.pass_message)
            return True
        else:
            self.status = EventStatus.FAIL
            print(self.fail_message)
            return False
    
    def _get_input(self, prompt, parser=None):
        """Get input using parser if available, otherwise use direct input."""
        return parser.parse(prompt) if parser else input(prompt)
    
    def _select_party_member(self, party, parser=None):
        """Select a party member using parser if available, else select directly."""
        if not party:
            print("No party members left!")
            return None
        
        if parser:
            return parser.select_party_member(party)
        
        print("Choose a party member:")
        for idx, member in enumerate(party):
            print(f"{idx + 1}. {member}")
            
        while True:
            try:
                choice = int(input("Enter the number of the chosen party member: ")) - 1
                if 0 <= choice < len(party):
                    return party[choice]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
                
    def resolve_choice(self, character: Character, chosen_stat: Statistic):
        """Resolve event based on chosen statistic."""
        chosen_stat_name = chosen_stat.name.lower()
        primary_attr = self.primary_attribute.lower() if self.primary_attribute else ""
        secondary_attr = self.secondary_attribute.lower() if self.secondary_attribute else ""
        
        # Check primary attribute match
        if chosen_stat_name == primary_attr:
            self.status = EventStatus.PASS
            print(self.pass_message)
            return True
            
        # Check secondary attribute match
        if secondary_attr and chosen_stat_name == secondary_attr:
            self.status = EventStatus.PARTIAL_PASS
            print(self.partial_pass_message)
            return True
            
        # No match
        self.status = EventStatus.FAIL
        print(self.fail_message)
        return False

    def resolve_combat(self, character: Character, party: List[Character], parser=None) -> bool:
        """Resolve a combat event."""
        if not self.enemy:
            print("No enemy information available!")
            return False
            
        enemy = Enemy(self.enemy["name"], self.enemy["vitality"], 
                      self.enemy["strength"], self.enemy["dexterity"])
        print(f"\n{character.name} engages {enemy.name}!")
        
        while character.is_alive() and enemy.is_alive():
            action = self._get_input("1. Attack 2. Flee\n> ", parser)
            
            if action == "1":
                # Attack
                hit_chance = 50 + (character.dexterity.value - enemy.dexterity) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = character.strength.value + random.randint(1, 6)
                    enemy.take_damage(damage)
                    print(f"{character.name} hits {enemy.name} for {damage} damage!")
                else:
                    print(f"{character.name}'s attack misses!")
            elif action == "2":
                # Flee
                if random.randint(1, 100) <= 50 + character.dexterity.value:
                    print(f"{character.name} flees successfully!")
                    return False
                else:
                    print("Failed to flee!")
            
            if enemy.is_alive():
                hit_chance = 50 + (enemy.dexterity - character.dexterity.value) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = enemy.strength + random.randint(1, 6)
                    character.take_damage(damage)
                    print(f"{enemy.name} hits {character.name} for {damage} damage!")
                    print(f"{character.name}'s vitality: {character.vitality.value}/{character.max_vitality}")
                else:
                    print(f"{enemy.name}'s attack misses!")

        return enemy.vitality <= 0

    def resolve_puzzle(self, character: Character) -> bool:
        """Resolve a puzzle event with a stat check."""
        print(f"This puzzle requires {self.primary_attribute}.")
        stat_value = getattr(character, self.primary_attribute.lower()).value
        print(f"{character.name}'s {self.primary_attribute}: {stat_value}")
        print("Rolling dice...")
        
        roll = random.randint(1, 6)
        print(f"Rolled: {roll}")
        
        total = roll + stat_value
        print(f"Total (roll + {self.primary_attribute}): {total}")
        
        threshold = 10
        print(f"Need {threshold} or higher to succeed.")
        
        return total >= threshold

    def resolve_loot(self, character: Character) -> bool:
        """Resolve a loot event with a dexterity check."""
        print(f"This requires {self.primary_attribute} to retrieve.")
        stat_value = getattr(character, self.primary_attribute.lower()).value
        print(f"{character.name}'s {self.primary_attribute}: {stat_value}")
        print("Rolling dice...")
        
        roll = random.randint(1, 6)
        print(f"Rolled: {roll}")
        
        total = roll + stat_value
        print(f"Total (roll + {self.primary_attribute}): {total}")
        
        threshold = 8
        print(f"Need {threshold} or higher to succeed.")
        
        return total >= threshold

    def resolve_boss(self, party: List[Character], parser=None) -> bool:
        """Resolve the final boss combat."""
        boss = Enemy("Iron Phantom", 25 + 5 * len(party), 4, 5)
        print(f"\n{boss.name} emerges! Vitality: {boss.vitality}")
        
        # Boss combat loop
        while party and boss.vitality > 0:
            # Each party member's turn
            for member in party[:]:
                if boss.vitality <= 0:
                    break
                    
                print(f"\n{member.name}'s turn. {boss.display_stats()}")
                action = self._get_input("1. Attack\n> ", parser)
                
                # Player attack
                hit_chance = 50 + (member.dexterity.value - boss.dexterity) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = member.strength.value + random.randint(1, 6)
                    boss.take_damage(damage)
                    print(f"{member.name} hits {boss.name} for {damage} damage!")
                else:
                    print(f"{member.name}'s attack misses!")
                
                # Boss attack
                if boss.vitality > 0:
                    target = random.choice(party)
                    hit_chance = 50 + (boss.dexterity - target.dexterity.value) * 5
                    
                    if random.randint(1, 100) <= hit_chance:
                        damage = boss.strength + random.randint(1, 6)
                        target.take_damage(damage)
                        print(f"{boss.name} hits {target.name} for {damage} damage!")
                        print(f"{target.name}'s vitality: {target.vitality.value}/{target.max_vitality}")
                        
                        if not target.is_alive():
                            party.remove(target)
                            print(f"{target.name} has fallen!")
        
        return boss.vitality <= 0

class Location:
    """Represents a location with multiple possible events."""
    def __init__(self, name: str, events: List[Event]):
        self.name = name
        self.events = events

    def get_event(self) -> Event:
        """Return a random event from this location."""
        return random.choice(self.events)

class UserInputParser:
    """Handles user input parsing."""
    def parse(self, prompt: str) -> str:
        """Get input from the user with the given prompt."""
        return input(prompt)

    def select_party_member(self, party: List[Character]) -> Optional[Character]:
        """Let the user select a party member."""
        if not party:
            print("No party members left!")
            return None
            
        print("Choose a party member:")
        for idx, member in enumerate(party):
            print(f"{idx + 1}. {member}")
            
        while True:
            try:
                choice = int(self.parse("Enter the number of the chosen party member: ")) - 1
                if 0 <= choice < len(party):
                    return party[choice]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def select_stat(self, character: Character) -> Statistic:
        """Let the user select a character statistic."""
        print(f"Choose a stat for {character.name}:")
        stats = character.get_stats()
        for idx, stat in enumerate(stats):
            print(f"{idx + 1}. {stat}")
            
        while True:
            try:
                choice = int(self.parse("Enter the number of the stat to use: ")) - 1
                if 0 <= choice < len(stats):
                    return stats[choice]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")

def load_events_from_json(file_path: str) -> List[Event]:
    """Load events from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return [Event(event_data) for event_data in data]
    except Exception as e:
        print(f"Error loading events from {file_path}: {e}")
        return []

def start_game():
    """Initialize and start the game."""
    # Initialize parser
    parser = UserInputParser()
    
    # Character creation
    print("=== CHARACTER CREATION ===")
    class_options = {
        "1": "Scrapper", 
        "2": "Gearshot", 
        "3": "Steamwright", 
        "4": "Rustblade"
    }
    
    print("Choose your starting class:")
    print("1. Scrapper (Balanced STR/DEX/VIT/INT)")
    print("2. Gearshot (High DEX, Low STR)")
    print("3. Steamwright (High INT, Medium STR)")
    print("4. Rustblade (High STR, Low DEX)")
    
    class_choice = ""
    while class_choice not in class_options:
        class_choice = parser.parse("> ")
        if class_choice not in class_options:
            print("Invalid choice. Try again.")
    
    name = parser.parse("Enter your character's name: ")
    
    # Create character
    character = Character(name, class_options[class_choice])
    print(f"\nCharacter created: {character}")
    
    # Create locations with events
    try:
        # Load all locations
        locations = []
        location_data = [
            ("Rusted Titan", 'project_code/location_events/rusted_titan.json'),
            ("Boiler Gulch", 'project_code/location_events/boiler_gulch.json'),
            ("Smokestack Spire", 'project_code/location_events/smokestack_spire.json')
        ]
        
        for name, path in location_data:
            events = load_events_from_json(path)
            if events:  # Only add location if it has events
                locations.append(Location(name, events))
        
        if not locations:
            print("Error: No locations could be loaded. Check your event files.")
            return
            
        # Start game
        game = Game(parser, [character], locations)
        game.start()
        
    except Exception as e:
        print(f"Error initializing game: {e}")

if __name__ == '__main__':
    start_game()