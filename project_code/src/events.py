import random
import sys
import os
from typing import List, Optional, Tuple, Dict, Callable
from enum import Enum

# Handle imports differently when running as a script vs being imported
if __name__ == "__main__":
    # Running as script - add project root to path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from project_code.src.character import Character, Enemy, Statistic
else:
    # Being imported - use either absolute or relative imports based on context
    try:
        # Try absolute import first
        from project_code.src.character import Character, Enemy, Statistic
    except ImportError:
        # If that fails, try direct import (assumes files are in same directory)
        try:
            from character import Character, Enemy, Statistic
        except ImportError:
            # Last resort - relative import
            from .character import Character, Enemy, Statistic

class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"

class Event:
    """Represents an in-game event with resolution logic."""
    def __init__(self, data: dict):
        # Extract values from data dict with defaults for missing keys
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
        
        # Get the appropriate handler for this event type or return False if not found
        handler = event_handlers.get(self.type)
        return handler(party, parser) if handler else False
    
    def _handle_combat(self, party, parser):
        """Handle a combat event."""
        character = self._select_party_member(party, parser)
        if not character:
            return False

        success = self.resolve_combat(character, party, parser)
        self.status = EventStatus.PASS if success else EventStatus.FAIL
        
        if success:
            print(self.pass_message)
            if self.reward and hasattr(character, 'add_to_inventory'):
                print(f"Reward: {self.reward}")
                character.add_to_inventory(self.reward)
        else:
            print(self.fail_message)
            if character and not character.is_alive():
                party.remove(character)
                print(f"{character.name} has been lost!")
                
        return success
    
    def _handle_puzzle(self, party, parser):
        character = self._select_party_member(party, parser)
        if not character:
            return False
            
        success = self.resolve_puzzle(character)
        self.status = EventStatus.PASS if success else EventStatus.FAIL
        
        if success:
            print(self.pass_message)
            if self.reward and hasattr(character, 'add_to_inventory'):
                print(f"Reward: {self.reward}")
                character.add_to_inventory(self.reward)
        else:
            print(self.fail_message)
            if self.penalty:
                character.take_damage(self.penalty)
                print(f"{character.name} takes {self.penalty} damage!")
                if not character.is_alive():
                    party.remove(character)
                    print(f"{character.name} has been lost!")
                    
        return success
    
    def _handle_loot(self, party, parser):
        character = self._select_party_member(party, parser)
        if not character:
            return False
        
        success = self.resolve_loot(character)
        self.status = EventStatus.PASS
        print(self.pass_message if success else self.fail_message)
        
        if success and self.reward and hasattr(character, 'add_to_inventory'):
            print(f"Reward: {self.reward}")
            character.add_to_inventory(self.reward)
            
        return success
    
    def _handle_recruit(self, party, parser):
        self.status = EventStatus.PASS
        prompt = "Recruit this survivor? 1. Yes 2. No\n> "
        
        choice = self._get_input(prompt, parser)
        
        # Early return for "No" choice or no recruit data
        if choice != "1" or not self.recruit:
            print("You leave the survivor behind.")
            return False
            
        # Handle "Yes" choice
        new_char = Character(self.recruit["name"], self.recruit["class"])
        new_char.vitality.value = self.recruit["initial_vitality"]
        party.append(new_char)
        print(self.pass_message)
        return True
    
    def _handle_boss(self, party, parser):
        success = self.resolve_boss(party, parser)
        self.status = EventStatus.PASS if success else EventStatus.FAIL
        print(self.pass_message if success else self.fail_message)
        return success
    
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
        primary_attr = self.primary_attribute.lower()
        secondary_attr = self.secondary_attribute.lower() if self.secondary_attribute else None
        
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
        
        # Combat loop
        while character.is_alive() and enemy.is_alive():
            action = self._get_input("1. Attack 2. Flee\n> ", parser)
            
            # Handle player action
            if action == "1":  # Attack
                self._player_attack(character, enemy)
            elif action == "2":  # Flee
                flee_success = self._attempt_flee(character)
                if flee_success:
                    return False
            
            # Handle enemy turn if still alive
            if enemy.is_alive():
                self._enemy_attack(enemy, character)

        return enemy.vitality <= 0
    
    def _player_attack(self, character: Character, enemy: Enemy) -> None:
        """Handle player attack on enemy."""
        hit_chance = 50 + (character.dexterity.value - enemy.dexterity) * 5
        hit = random.randint(1, 100) <= hit_chance
        
        if hit:
            damage = character.strength.value + random.randint(1, 6)
            enemy.take_damage(damage)
            print(f"{character.name} hits {enemy.name} for {damage} damage!")
        else:
            print(f"{character.name}'s attack misses!")
    
    def _attempt_flee(self, character: Character) -> bool:
        """Attempt to flee from combat. Returns True if successful."""
        flee_chance = 50 + character.dexterity.value
        success = random.randint(1, 100) <= flee_chance
        
        print(f"{character.name} flees successfully!" if success else "Failed to flee!")
        return success
    
    def _enemy_attack(self, enemy: Enemy, character: Character) -> None:
        """Handle enemy attack on character."""
        hit_chance = 50 + (enemy.dexterity - character.dexterity.value) * 5
        hit = random.randint(1, 100) <= hit_chance
        
        if hit:
            damage = enemy.strength + random.randint(1, 6)
            character.take_damage(damage)
            print(f"{enemy.name} hits {character.name} for {damage} damage!")
            print(f"{character.name}'s vitality: {character.vitality.value}/{character.max_vitality}")
        else:
            print(f"{enemy.name}'s attack misses!")

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