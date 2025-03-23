"""Main module for Canyon of the Lost Engines game."""
import json
import random
from typing import List, Optional

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
    def __init__(self, name, events):
        self.name = name
        self.events = events

    def get_event(self):
        """Return a random event from this location."""
        return random.choice(self.events)

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

class Game:
    """Main game controller class."""
    def __init__(self, parser, characters, locations):
        self.parser = parser
        self.party = characters
        self.locations = locations
        self.core_fragments = 0
        self.continue_playing = True

    def start(self):
        """Start the game loop."""
        self._print_intro()
        
        while self.continue_playing:
            self._print_status()
            location = self._select_location()
            print(f"\nTraveling to {location.name}...")
            
            event = location.get_event()
            success = event.execute(self.party, self.parser)
            
            if success and event.reward == "Core Fragment":
                self.core_fragments += 1
                print(f"\nCore Fragments collected: {self.core_fragments}/3")
            
            # Check for game over conditions
            if self.check_game_over() or self.core_fragments >= 3:
                self.final_challenge()
                self.continue_playing = False
                continue
                
            # Ask if player wants to continue
            self.continue_playing = self._get_continue_choice()
        
        print("\nGame Over.")
        
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
        ===============================================
        """)

    def _print_status(self):
        """Print current game status."""
        print("\n==== STATUS ====")
        print(f"Core Fragments: {self.core_fragments}/3")
        print("\nParty Members:")
        for member in self.party:
            print(f"- {member}")
        print("===============")

    def _select_location(self):
        """Let player select a location to visit."""
        print("\nChoose a location to explore:")
        for idx, location in enumerate(self.locations):
            print(f"{idx + 1}. {location.name}")
        
        while True:
            try:
                choice = int(self.parser.parse("Enter the number of your chosen destination: ")) - 1
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

    def final_challenge(self):
        """Handle the final boss challenge."""
        has_fragments = self.core_fragments >= 3
        if has_fragments:
            print("""
            You approach the Forge Gate with 3 Core Fragments.
            As you insert them into the ancient mechanism, the ground trembles.
            The Iron Phantom rises, its voice booming: 'None shall leave!'
            """)
            
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
        else:
            self._print_defeat(False)
    
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