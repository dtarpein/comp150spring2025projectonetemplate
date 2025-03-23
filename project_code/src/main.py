"""Main module for Canyon of the Lost Engines game."""
import random
from typing import List, Dict, Any

# Import necessary modules
try:
    from project_code.src.character import Character
    from project_code.src.events import Event, EventStatus
    from project_code.src.game_core import (
        Location, UserInputParser, load_events_from_json, 
        load_game_locations, create_character,
        print_game_intro, print_game_status, print_victory, print_defeat
    )
    # Try to import the adventure system module if available
    try:
        from project_code.src.adventure_system import (
            enhance_game_with_scavenging, 
            enhance_game_with_repairs, 
            add_scavenging_to_location,
            RepairSystem
        )
        HAS_ADVENTURE_SYSTEM = True
    except ImportError:
        HAS_ADVENTURE_SYSTEM = False
except ImportError:
    # Local imports
    try:
        from character import Character
        from events import Event, EventStatus
        from game_core import (
            Location, UserInputParser, load_events_from_json, 
            load_game_locations, create_character,
            print_game_intro, print_game_status, print_victory, print_defeat
        )
        try:
            from adventure_system import (
                enhance_game_with_scavenging, 
                enhance_game_with_repairs, 
                add_scavenging_to_location,
                RepairSystem
            )
            HAS_ADVENTURE_SYSTEM = True
        except ImportError:
            HAS_ADVENTURE_SYSTEM = False
    except ImportError:
        # Relative imports
        from .character import Character
        from .events import Event, EventStatus
        from .game_core import (
            Location, UserInputParser, load_events_from_json, 
            load_game_locations, create_character,
            print_game_intro, print_game_status, print_victory, print_defeat
        )
        try:
            from .adventure_system import (
                enhance_game_with_scavenging, 
                enhance_game_with_repairs, 
                add_scavenging_to_location,
                RepairSystem
            )
            HAS_ADVENTURE_SYSTEM = True
        except ImportError:
            HAS_ADVENTURE_SYSTEM = False

# Re-export these classes for backward compatibility with tests
__all__ = ['Character', 'Event', 'EventStatus', 'Location', 'UserInputParser', 'Game', 'load_events_from_json']

class Game:
    """Main game controller class."""
    def __init__(self, parser, characters, locations):
        self.parser = parser
        self.party = characters
        self.locations = locations
        self.core_fragments = 0
        self.continue_playing = True
        self.day = 1
        self.airship_repaired = False
        self.special_items = {
            "Repair Kit": self._use_repair_kit,
            "Steam Tonic": self._use_steam_tonic,
            "Engineer's Tools": self._use_engineers_tools,
            "Canteen": self._use_canteen,
            "Steam Pistol": self._use_steam_pistol,
            "Goggles": self._use_goggles
        }
        
        # Apply adventure system enhancements if available
        if HAS_ADVENTURE_SYSTEM:
            # Reset repair system
            RepairSystem.reset_repairs()
            
            # Save original methods before enhancement
            self._scavenge_original = getattr(self, "_scavenge_location", None)
            
            # Enhance with scavenging system
            enhanced_game = enhance_game_with_scavenging(self)
            if hasattr(enhanced_game, "_scavenge_location"):
                self._scavenge_location = enhanced_game._scavenge_location
            
            # Enhance with repair system - store enhanced method with a different name
            enhanced_game = enhance_game_with_repairs(self)
            if hasattr(enhanced_game, "_repair_airship") and enhanced_game._repair_airship != self._repair_airship:
                self._enhanced_repair_airship = enhanced_game._repair_airship

    def start(self):
        """Start the game loop."""
        print_game_intro()
        
        while self.continue_playing:
            print_game_status(self)
            
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
                print_defeat(self.core_fragments >= 3)
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
            
        # Add enhanced scavenging if adventure system is available
        if HAS_ADVENTURE_SYSTEM:
            location = add_scavenging_to_location(location)
            
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
                # Use the enhanced scavenging if available
                if hasattr(self, "_scavenge_location"):
                    self._scavenge_location(location)
                else:
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
        # Use the enhanced repair system if available
        if hasattr(self, "_enhanced_repair_airship"):
            self._enhanced_repair_airship()
            return
        
        # Original simple repair logic
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
            print_victory()
        else:
            print_defeat(True)
            
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

    def check_game_over(self):
        """Check if the game is over (party wiped out)."""
        return len(self.party) == 0

def start_game():
    """Initialize and start the game."""
    # Initialize parser
    parser = UserInputParser()
    
    # Create character
    character = create_character(parser)
    
    try:
        # Load all locations
        locations = load_game_locations()
        
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