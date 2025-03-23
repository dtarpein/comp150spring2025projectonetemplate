"""Main module for Canyon of the Lost Engines game."""
import json
import random
import time
from typing import List, Optional, Dict, Any, Tuple

# Import necessary modules
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

# Re-export these classes for backward compatibility with tests
__all__ = ['Character', 'Statistic', 'Enemy', 'Event', 'EventStatus', 'Location', 'UserInputParser', 'Game', 'load_events_from_json']

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

class Game:
    """Main game controller class."""
    def __init__(self, parser, characters, locations):
        self.parser = parser
        self.party = characters
        self.locations = locations
        self.core_fragments = 0
        self.continue_playing = True
        self.day = 1
        self.special_items = {
            "Repair Kit": self._use_repair_kit,
            "Steam Tonic": self._use_steam_tonic,
            "Engineer's Tools": self._use_engineers_tools,
            "Canteen": self._use_canteen,
            "Steam Pistol": self._use_steam_pistol,
            "Goggles": self._use_goggles
        }
        self.airship_repaired = False

    def start(self):
        """Start the game loop."""
        self._print_intro()
        
        while self.continue_playing:
            self._print_status()
            
            # Daily choice menu
            print("\nWhat would you like to do today?")
            print("1. Explore a location")
            print("2. Make camp and rest")
            print("3. Review inventory and use items")
            print("4. Repair the airship")
            print("5. Leave the canyon (End Game)")
            
            choice = self.parser.parse("> ")
            
            if choice == "1":
                self._explore_location()
            elif choice == "2":
                self._make_camp()
            elif choice == "3":
                self._manage_inventory()
            elif choice == "4":
                self._repair_airship()
            elif choice == "5":
                self._attempt_departure()
                continue
            else:
                print("Invalid choice. Try again.")
                continue
            
            # Check for game over conditions
            if self.check_game_over():
                self._print_defeat(self.core_fragments >= 3)
                self.continue_playing = False
                continue
                
            # End the day
            self.day += 1
            print(f"\nDay {self.day} dawns over the canyon...")
        
        print("\nGame Over.")
        
    def _explore_location(self):
        """Explore a location."""
        location = self._select_location()
        if not location:
            return
            
        print(f"\nTraveling to {location.name}...")
        print(location.description)
        
        # Give the player options at the location
        while True:
            print(f"\nYou are at {location.name}.")
            print("What would you like to do?")
            print("1. Search for events")
            print("2. Scavenge for resources")
            print("3. Return to camp")
            
            choice = self.parser.parse("> ")
            
            if choice == "1":
                # Get and execute a random event
                event = location.get_event()
                success = event.execute(self.party, self.parser)
                
                if success and event.reward == "Core Fragment":
                    self.core_fragments += 1
                    print(f"\nCore Fragments collected: {self.core_fragments}/3")
                    
                if self.check_game_over():
                    return
                    
            elif choice == "2":
                # Scavenge for resources
                character = self.parser.select_party_member(self.party)
                if not character:
                    continue
                    
                message, success = location.scavenge(character)
                print(message)
                
            elif choice == "3":
                # Return to camp
                print("You return to your camp.")
                location.mark_visited()
                break
                
            else:
                print("Invalid choice. Try again.")
    
    def _make_camp(self):
        """Make camp and rest for the day."""
        print("\nYou set up camp for the night, tending to wounds and sharing stories...")
        
        # Rest restores some vitality
        for member in self.party:
            healing = 2 + random.randint(1, 3)
            old_vitality = member.vitality.value
            member.vitality.value = min(member.max_vitality, member.vitality.value + healing)
            print(f"{member.name} rests and recovers {member.vitality.value - old_vitality} vitality.")
        
        # Random events at camp
        camp_events = [
            "The night passes uneventfully.",
            "Strange noises keep you on edge, but nothing attacks.",
            "You spot distant lights in the canyon, but they fade before dawn.",
            "A gentle rain provides fresh water for your canteens.",
            "The stars are unusually bright tonight."
        ]
        print(random.choice(camp_events))
    
    def _manage_inventory(self):
        """Review and use items in inventory."""
        character = self.parser.select_party_member(self.party)
        if not character:
            return
            
        if not character.inventory:
            print(f"{character.name} has no items.")
            return
            
        print(f"\n{character.name}'s inventory:")
        for idx, item in enumerate(character.inventory, 1):
            print(f"{idx}. {item}")
            
        item = self.parser.select_from_inventory(character)
        if not item:
            return
            
        # Use the item
        if item in self.special_items:
            self.special_items[item](character, item)
        else:
            print(f"You examine the {item} but find no immediate use for it.")
    
    def _repair_airship(self):
        """Work on repairing the airship."""
        if self.airship_repaired:
            print("The airship is already repaired and ready to fly!")
            return
            
        if self.core_fragments < 3:
            print(f"You need 3 Core Fragments to power the airship. You currently have {self.core_fragments}.")
            return
            
        # Check for necessary parts
        required_parts = ["Scrap Metal", "Spare Parts", "Copper Wire"]
        has_parts = True
        missing_parts = []
        
        # Count all parts across all characters' inventories
        all_items = []
        for member in self.party:
            all_items.extend(member.inventory)
            
        for part in required_parts:
            if part not in all_items:
                has_parts = False
                missing_parts.append(part)
        
        if not has_parts:
            print("You need the following parts to repair the airship:")
            for part in missing_parts:
                print(f"- {part}")
            print("Continue exploring and scavenging to find the necessary parts.")
            return
            
        # Repair the airship
        print("\nYou and your party work tirelessly on the airship...")
        print("Fitting the Core Fragments into the engine...")
        print("Patching the hull with scrap metal...")
        print("Reconnecting wires and tuning the machinery...")
        print("The ancient engine sputters to life!")
        
        self.airship_repaired = True
        
        # Remove the used items
        for member in self.party:
            for part in required_parts[:]:
                if part in member.inventory:
                    member.inventory.remove(part)
                    required_parts.remove(part)
                    if not required_parts:
                        break
            if not required_parts:
                break
                    
        print("\nThe airship is now repaired and ready for flight!")
    
    def _attempt_departure(self):
        """Attempt to leave the canyon."""
        if not self.airship_repaired:
            print("The airship isn't repaired yet! You can't leave without it.")
            return
            
        print("\nAs you prepare the airship for departure, the ground trembles...")
        print("The Iron Phantom rises, its voice booming: 'None shall leave!'")
        
        # Final boss fight
        boss_event = Event({
            "type": "boss",
            "prompt_text": "Prepare to face the Iron Phantom!",
            "pass": {"message": "You defeat the Iron Phantom and power the airship! Victory!"},
            "fail": {"message": "The Iron Phantom destroys your party. The canyon claims you."}
        })
        
        victory = boss_event.execute(self.party, self.parser)
        if victory:
            self._print_victory()
        else:
            self._print_defeat(True)
            
        self.continue_playing = False
            
    def _use_repair_kit(self, character, item):
        """Use a repair kit to restore vitality."""
        healing = 8 + random.randint(1, 4)
        old_vitality = character.vitality.value
        character.vitality.value = min(character.max_vitality, character.vitality.value + healing)
        
        print(f"{character.name} uses the {item} and recovers {character.vitality.value - old_vitality} vitality.")
        character.inventory.remove(item)
    
    def _use_steam_tonic(self, character, item):
        """Use a steam tonic to boost stats temporarily."""
        # In a full implementation, this would add a timed buff
        print(f"{character.name} drinks the {item}. All stats are boosted for the next encounter!")
        character.strength.modify(2)
        character.dexterity.modify(2)
        character.intelligence.modify(2)
        character.inventory.remove(item)
    
    def _use_engineers_tools(self, character, item):
        """Use engineering tools to fix something or improve a stat."""
        print(f"{character.name} uses the {item} to make some adjustments...")
        print("Intelligence permanently increased by 1!")
        character.intelligence.modify(1)
        character.inventory.remove(item)
    
    def _use_canteen(self, character, item):
        """Use a canteen to restore some vitality."""
        healing = 5 + random.randint(1, 3)
        old_vitality = character.vitality.value
        character.vitality.value = min(character.max_vitality, character.vitality.value + healing)
        
        print(f"{character.name} drinks from the {item} and recovers {character.vitality.value - old_vitality} vitality.")
        character.inventory.remove(item)
    
    def _use_steam_pistol(self, character, item):
        """Steam pistol gives combat advantage."""
        print(f"{character.name} checks the {item}. It will provide an advantage in the next combat!")
        # This would normally set a flag for combat advantage
        character.strength.modify(1)
        # Don't remove the item as it can be used repeatedly
    
    def _use_goggles(self, character, item):
        """Goggles improve perception."""
        print(f"{character.name} puts on the {item}. They will help spot hidden items!")
        # This would normally set a flag for improved scavenging
        character.dexterity.modify(1)
        # Don't remove the item as it can be used repeatedly
    
    def _print_intro(self):
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

    def _print_status(self):
        """Print current game status."""
        print(f"\n==== STATUS: Day {self.day} ====")
        print(f"Core Fragments: {self.core_fragments}/3")
        print(f"Airship Repair: {'Complete!' if self.airship_repaired else 'Incomplete'}")
        print("\nParty Members:")
        for member in self.party:
            print(f"- {member}")
            if member.inventory:
                inv_list = ", ".join(member.inventory)
                print(f"  Inventory: {inv_list}")
        print("===============")

    def _select_location(self):
        """Let player select a location to visit."""
        print("\nChoose a location to explore:")
        for idx, location in enumerate(self.locations):
            visited_mark = " (Visited)" if location.visited else ""
            scavenged_mark = " (Scavenged)" if location.scavenged else ""
            print(f"{idx + 1}. {location.name}{visited_mark}{scavenged_mark}")
        print(f"{len(self.locations) + 1}. Cancel")
        
        while True:
            try:
                choice = int(self.parser.parse("Enter the number of your chosen destination: ")) - 1
                if choice == len(self.locations):
                    return None
                if 0 <= choice < len(self.locations):
                    return self.locations[choice]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _get_continue_choice(self):
        """Ask if player wants to continue."""
        print("\nContinue exploring the canyon?")
        print("1. Yes")
        print("2. No (End Game)")
        
        while True:
            choice = self.parser.parse("> ")
            if choice in ["1", "2"]:
                break
            print("Invalid choice. Try again.")
        
        if choice == "2":
            print("\nYou decide to give up on your quest. The canyon claims another victim.")
            return False
        return True
    
    def _print_victory(self):
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
    
    def _print_defeat(self, with_fragments):
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

    def check_game_over(self):
        """Check if the game is over (party wiped out)."""
        return len(self.party) == 0

def load_events_from_json(file_path):
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
    
    # Create locations with events
    try:
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