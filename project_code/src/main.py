import json
import sys
import random
from typing import List, Optional
from enum import Enum

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

    def __str__(self):
        return (f"Character: {self.name} ({self.class_type}), "
                f"STR {self.strength}, DEX {self.dexterity}, "
                f"VIT {self.vitality}/{self.max_vitality}, INT {self.intelligence}")

    def get_stats(self):
        return [self.strength, self.dexterity, self.vitality, self.intelligence]

class Event:
    def __init__(self, data: dict):
        self.type = data.get("type", "default")
        self.primary_attribute = data['primary_attribute']
        self.secondary_attribute = data.get('secondary_attribute')
        self.prompt_text = data['prompt_text']
        self.pass_message = data['pass']['message']
        self.fail_message = data['fail']['message']
        self.partial_pass_message = data.get('partial_pass', {}).get('message', "")
        self.reward = data.get('reward')
        self.penalty = data.get('penalty', 0)
        self.recruit = data.get('recruit')
        self.enemy = data.get('enemy')
        self.status = EventStatus.UNKNOWN

    def execute(self, party: List[Character], parser):
        print(f"\n{self.prompt_text}")
        if self.type == "combat":
            character = parser.select_party_member(party)
            if character and self.resolve_combat(character, party):
                self.status = EventStatus.PASS
                print(self.pass_message)
                if self.reward:
                    print(f"Reward: {self.reward}")
            else:
                self.status = EventStatus.FAIL
                print(self.fail_message)
                if not character.is_alive():
                    party.remove(character)
                    print(f"{character.name} has been lost!")
        elif self.type == "puzzle":
            character = parser.select_party_member(party)
            if character and self.resolve_puzzle(character):
                self.status = EventStatus.PASS
                print(self.pass_message)
                if self.reward:
                    print(f"Reward: {self.reward}")
            else:
                self.status = EventStatus.FAIL
                print(self.fail_message)
                if self.penalty:
                    character.take_damage(self.penalty)
                    print(f"{character.name} takes {self.penalty} damage!")
                    if not character.is_alive():
                        party.remove(character)
                        print(f"{character.name} has been lost!")
        elif self.type == "loot":
            self.status = EventStatus.PASS
            print(self.pass_message)
            if self.reward:
                print(f"Reward: {self.reward}")
        elif self.type == "recruit":
            self.status = EventStatus.PASS
            choice = parser.parse("Recruit this survivor? 1. Yes 2. No\n> ")
            if choice == "1":
                new_char = Character(self.recruit["name"], self.recruit["class"])
                new_char.vitality.value = self.recruit["initial_vitality"]
                party.append(new_char)
                print(self.pass_message)
            else:
                print("You leave the survivor behind.")
        elif self.type == "boss":
            if self.resolve_boss(party):
                self.status = EventStatus.PASS
                print(self.pass_message)
            else:
                self.status = EventStatus.FAIL
                print(self.fail_message)

    def resolve_combat(self, character: Character, party: List[Character]) -> bool:
        enemy = Enemy(self.enemy["name"], self.enemy["vitality"], self.enemy["strength"], self.enemy["dexterity"])
        print(f"\n{character.name} engages {enemy.name}!")
        while character.is_alive() and enemy.is_alive():
            
            if action == "1":
                hit_chance = 50 + (character.dexterity.value - enemy.dexterity) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = character.strength.value + random.randint(1, 6)
                    enemy.take_damage(damage)
                    print(f"{character.name} hits {enemy.name} for {damage} damage!")
                else:
                    print(f"{character.name}'s attack misses!")
            elif action == "2":
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
                else:
                    print(f"{enemy.name}'s attack misses!")

        return enemy.vitality <= 0

    def resolve_puzzle(self, character: Character) -> bool:
        roll = random.randint(1, 6) + getattr(character, self.primary_attribute.lower()).value
        return roll >= 10  # Threshold for puzzle success

    def resolve_boss(self, party: List[Character]) -> bool:
        boss = Enemy("Iron Phantom", 25 + 5 * len(party), 4, 5)
        print(f"\n{boss.name} emerges! Vitality: {boss.vitality}")
        while party and boss.vitality > 0:
            for member in party[:]:
                if boss.vitality <= 0:
                    break
                print(f"\n{member.name}'s turn. {boss.display_stats()}")
                action = parser.parse("1. Attack\n> ")
                if action == "1":
                    hit_chance = 50 + (member.dexterity.value - boss.dexterity) * 5
                    if random.randint(1, 100) <= hit_chance:
                        damage = member.strength.value + random.randint(1, 6)
                        boss.take_damage(damage)
                        print(f"{member.name} hits {boss.name} for {damage} damage!")
                    else:
                        print(f"{member.name}'s attack misses!")
                if boss.vitality > 0:
                    target = random.choice(party)
                    hit_chance = 50 + (boss.dexterity - target.dexterity.value) * 5
                    if random.randint(1, 100) <= hit_chance:
                        damage = boss.strength + random.randint(1, 6)
                        target.take_damage(damage)
                        print(f"{boss.name} hits {target.name} for {damage} damage!")
                        if not target.is_alive():
                            party.remove(target)
                            print(f"{target.name} has fallen!")
        return boss.vitality <= 0

class Enemy:
    def __init__(self, name: str, vitality: int, strength: int, dexterity: int):
        self.name = name
        self.vitality = vitality
        self.strength = strength
        self.dexterity = dexterity

    def take_damage(self, damage: int):
        self.vitality -= damage
        if self.vitality < 0:
            self.vitality = 0

    def is_alive(self) -> bool:
        return self.vitality > 0

    def display_stats(self) -> str:
        return f"{self.name}: Vitality {self.vitality}, Strength {self.strength}, Dexterity {self.dexterity}"

class Location:
    def __init__(self, events: List[Event]):
        self.events = events

    def get_event(self) -> Event:
        return random.choice(self.events)

class Game:
    def __init__(self, parser, characters: List[Character], locations: List[Location]):
        self.parser = parser
        self.party = characters
        self.locations = locations
        self.core_fragments = 0
        self.continue_playing = True

    def start(self):
        print("""
        Welcome to Canyon of the Lost Engines!
        In this steampunk-Western canyon, you must collect 3 Core Fragments from ancient wrecks
        to power an airship and escape. Beware the Iron Phantom!
        """)
        while self.continue_playing:
            location = random.choice(self.locations)
            event = location.get_event()
            event.execute(self.party, self.parser)
            if event.reward == "Core Fragment" and event.status == EventStatus.PASS:
                self.core_fragments += 1
                print(f"Core Fragments collected: {self.core_fragments}/3")
            if self.check_game_over() or self.core_fragments >= 3:
                self.final_challenge()
                self.continue_playing = False
        print("Game Over.")

    def final_challenge(self):
        if self.core_fragments >= 3:
            print("""
            You approach the Forge Gate with 3 Core Fragments.
            The Iron Phantom rises, its voice booming: 'None shall leave!'
            """)
            boss_event = Event({
                "type": "boss",
                "prompt_text": "Prepare to face the Iron Phantom!",
                "pass": {"message": "You defeat the Iron Phantom and power the airship! Victory!"},
                "fail": {"message": "The Iron Phantom destroys your party. The canyon claims you."}
            })
            boss_event.execute(self.party, self.parser)
        else:
            print("Your party perished before collecting enough fragments.")

    def check_game_over(self) -> bool:
        return len(self.party) == 0

class UserInputParser:
    def parse(self, prompt: str) -> str:
        return input(prompt)

    def select_party_member(self, party: List[Character]) -> Optional[Character]:
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
    with open(file_path, 'r') as file:
        data = json.load(file)
    return [Event(event_data) for event_data in data]

def start_game():
    parser = UserInputParser()
    # Custom character creation
    class_options = {"1": "Scrapper", "2": "Gearshot", "3": "Steamwright", "4": "Rustblade"}
    class_choice = parser.parse(
        "Choose your starting class:\n1. Scrapper (Balanced)\n2. Gearshot (Dexterous)\n3. Steamwright (Smart)\n4. Rustblade (Strong)\n> "
    )
    name = parser.parse("Enter your character's name: ")
    characters = [Character(name, class_options.get(class_choice, "Scrapper"))]
    print(f"\n{characters[0]}")

    # Load events from multiple locations
    locations = [
        Location(load_events_from_json('project_code/location_events/rusted_titan.json')),
        Location(load_events_from_json('project_code/location_events/boiler_gulch.json')),
        Location(load_events_from_json('project_code/location_events/smokestack_spire.json'))
    ]
    game = Game(parser, characters, locations)
    game.start()

if __name__ == '__main__':
    start_game()