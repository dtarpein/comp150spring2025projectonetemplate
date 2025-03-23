"""Core game elements for Canyon of the Lost Engines game."""
import json
import random
from typing import List, Tuple, Dict, Any, Optional

# Import necessary modules with fallbacks
try:
    from project_code.src.character import Character, Statistic, Enemy
    from project_code.src.events import Event, EventStatus
except ImportError:
    try:
        from character import Character, Statistic, Enemy
        from events import Event, EventStatus
    except ImportError:
        from .character import Character, Statistic, Enemy
        from .events import Event, EventStatus

class Location:
    """Represents a location with multiple possible events."""
    def __init__(self, name, events, description="A mysterious location"):
        self.name = name
        self.events = events
        self.description = description
        self.visited = False
        self.scavenged = False

    def get_event(self):
        """Return a random event from this location."""
        return random.choice(self.events)
    
    def mark_visited(self):
        """Mark the location as visited."""
        self.visited = True
    
    def can_scavenge(self):
        """Check if the location can be scavenged."""
        return not self.scavenged
    
    def scavenge(self, character: Character) -> Tuple[str, bool]:
        """Scavenge the location for resources."""
        if self.scavenged:
            return "You've already picked this area clean.", False
        
        self.scavenged = True
        
        # Use dexterity for scavenging success chance
        success_chance = 40 + character.dexterity.value * 5
        if random.randint(1, 100) <= success_chance:
            # Determine what the player finds
            items = [
                "Scrap Metal", "Spare Parts", "Copper Wire", 
                "Rusty Gear", "Steam Valve", "Boiler Plate", "Brass Fitting"
            ]
            found_item = random.choice(items)
            character.add_to_inventory(found_item)
            
            # Chance to find something special
            if random.randint(1, 10) == 1:
                special_items = ["Repair Kit", "Steam Tonic", "Engineer's Tools"]
                special_item = random.choice(special_items)
                character.add_to_inventory(special_item)
                return f"You found {found_item} and a rare {special_item}!", True
            
            return f"You found some useful {found_item}.", True
        else:
            return "You search but find nothing of value.", False

class UserInputParser:
    """Handles user input parsing."""
    def parse(self, prompt):
        """Get input from the user with the given prompt."""
        return input(prompt)

    def select_party_member(self, party):
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
    
    def select_stat(self, character):
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

    def select_from_inventory(self, character):
        """Let the user select an item from inventory."""
        if not character.inventory:
            print(f"{character.name} has no items!")
            return None
            
        print(f"Select an item from {character.name}'s inventory:")
        for idx, item in enumerate(character.inventory):
            print(f"{idx + 1}. {item}")
            
        while True:
            try:
                choice = int(self.parse("Enter the item number (0 to cancel): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(character.inventory):
                    return character.inventory[choice - 1]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")

def load_events_from_json(file_path):
    """Load events from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return [Event(event_data) for event_data in data]
    except Exception as e:
        print(f"Error loading events from {file_path}: {e}")
        return []

def create_character(parser):
    """Create and return a new character based on user input."""
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
    
    # Get class choice
    class_choice = ""
    while class_choice not in class_options:
        class_choice = parser.parse("> ")
        if class_choice not in class_options:
            print("Invalid choice. Try again.")
    
    name = parser.parse("Enter your character's name: ")
    
    # Create character
    character = Character(name, class_options[class_choice])
    print(f"\nCharacter created: {character}")
    return character
    
def load_game_locations():
    """Load all locations for the game."""
    # Load all locations
    locations = []
    location_data = [
        ("Rusted Titan", 'project_code/location_events/rusted_titan.json', 
         "A massive mechanical giant, long dormant, its metallic hull half-buried in sand."),
        ("Boiler Gulch", 'project_code/location_events/boiler_gulch.json',
         "A narrow ravine where scalding geysers erupt at irregular intervals."),
        ("Smokestack Spire", 'project_code/location_events/smokestack_spire.json',
         "A towering column of metal with several broken steam vents still billowing."),
    ]
    
    for name, path, desc in location_data:
        events = load_events_from_json(path)
        if events:  # Only add location if it has events
            locations.append(Location(name, events, desc))
    
    return locations

# Common UI elements
def print_game_intro():
    """Print game introduction."""
    print("""
    ===============================================
    CANYON OF THE LOST ENGINES
    ===============================================
    In this steampunk-Western canyon, you must collect 3 Core Fragments from ancient wrecks
    to power an airship and escape. Beware the Iron Phantom!
    
    Use Strength for combat, Dexterity for loot, and Intelligence for puzzles.
    Keep your vitality high to survive!
    
    You'll need to:
    - Explore the canyon's locations
    - Scavenge for resources
    - Rest to recover vitality
    - Repair the airship
    - Collect 3 Core Fragments
    - Defeat the Iron Phantom
    ===============================================
    """)

def print_game_status(game):
    """Print current game status."""
    print(f"\n==== STATUS: Day {game.day} ====")
    print(f"Core Fragments: {game.core_fragments}/3")
    print(f"Airship Repair: {'Complete!' if game.airship_repaired else 'Incomplete'}")
    print("\nParty Members:")
    for member in game.party:
        print(f"- {member}")
        if member.inventory:
            inv_list = ", ".join(member.inventory)
            print(f"  Inventory: {inv_list}")
    print("===============")

def print_victory():
    """Print victory message."""
    print("""
    ===============================================
    VICTORY!
    ===============================================
    With the Iron Phantom defeated and the Core Fragments installed,
    the ancient airship roars to life! You escape the canyon,
    soaring into the sunset toward new adventures.
    
    Thank you for playing Canyon of the Lost Engines!
    ===============================================
    """)

def print_defeat(with_fragments):
    """Print defeat message."""
    message = ("The Iron Phantom was too powerful. Your quest ends here,\n"
              "your bones to be picked clean by the canyon scavengers." 
              if with_fragments else 
              "Your party perished before collecting enough Core Fragments.\n"
              "The canyon claims another group of adventurers.")
    
    print(f"""
    ===============================================
    DEFEAT
    ===============================================
    {message}
    
    Better luck next time!
    ===============================================
    """)
