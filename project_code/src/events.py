"""Events module for Canyon of the Lost Engines game."""
import random
from enum import Enum

# Handle imports with try-except for flexibility
try:
    from project_code.src.character import Character, Enemy, Statistic
except ImportError:
    try:
        from character import Character, Enemy, Statistic
    except ImportError:
        from .character import Character, Enemy, Statistic

class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"

class Event:
    """Represents an in-game event with resolution logic."""
    def __init__(self, data):
        # Extract values with defaults
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

    def execute(self, party, parser=None):
        """Execute the event based on its type."""
        print(f"\n{self.prompt_text}")
        
        # Map event types to handlers
        if self.type == "combat":
            return self._handle_combat(party, parser)
        elif self.type == "puzzle":
            return self._handle_puzzle(party, parser)
        elif self.type == "loot":
            return self._handle_loot(party, parser)
        elif self.type == "recruit":
            return self._handle_recruit(party, parser)
        elif self.type == "boss":
            return self._handle_boss(party, parser)
        return False
    
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
            return True
        else:
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
        
        success = self.resolve_loot(character)
        self.status = EventStatus.PASS
        print(self.pass_message if success else self.fail_message)
        
        if success and self.reward and hasattr(character, 'add_to_inventory'):
            print(f"Reward: {self.reward}")
            character.add_to_inventory(self.reward)
            
        return success
    
    def _handle_recruit(self, party, parser):
        self.status = EventStatus.PASS
        choice = self._get_input("Recruit this survivor? 1. Yes 2. No\n> ", parser)
        
        if choice != "1" or not self.recruit:
            print("You leave the survivor behind.")
            return False
            
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
                
    def resolve_choice(self, character, chosen_stat):
        """Resolve event based on chosen statistic."""
        chosen_stat_name = chosen_stat.name.lower()
        primary_attr = self.primary_attribute.lower() if self.primary_attribute else ""
        secondary_attr = self.secondary_attribute.lower() if self.secondary_attribute else ""
        
        # Check attribute matches
        if chosen_stat_name == primary_attr:
            self.status = EventStatus.PASS
            print(self.pass_message)
            return True
        elif secondary_attr and chosen_stat_name == secondary_attr:
            self.status = EventStatus.PARTIAL_PASS
            print(self.partial_pass_message)
            return True
        else:
            self.status = EventStatus.FAIL
            print(self.fail_message)
            return False

    def resolve_combat(self, character, party, parser=None):
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
            
            # Handle player turn
            if action == "1":  # Attack
                hit_chance = 50 + (character.dexterity.value - enemy.dexterity) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = character.strength.value + random.randint(1, 6)
                    enemy.take_damage(damage)
                    print(f"{character.name} hits {enemy.name} for {damage} damage!")
                else:
                    print(f"{character.name}'s attack misses!")
            elif action == "2":  # Flee
                flee_chance = 50 + character.dexterity.value
                if random.randint(1, 100) <= flee_chance:
                    print(f"{character.name} flees successfully!")
                    return False
                else:
                    print("Failed to flee!")
            
            # Handle enemy turn if still alive
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

    def resolve_puzzle(self, character):
        """Resolve a puzzle event with a stat check."""
        print(f"This puzzle requires {self.primary_attribute}.")
        stat_value = getattr(character, self.primary_attribute.lower()).value
        print(f"{character.name}'s {self.primary_attribute}: {stat_value}")
        
        roll = random.randint(1, 6)
        print(f"Rolling dice... Rolled: {roll}")
        
        total = roll + stat_value
        threshold = 10
        print(f"Total (roll + {self.primary_attribute}): {total}")
        print(f"Need {threshold} or higher to succeed.")
        
        return total >= threshold

    def resolve_loot(self, character):
        """Resolve a loot event with a dexterity check."""
        print(f"This requires {self.primary_attribute} to retrieve.")
        stat_value = getattr(character, self.primary_attribute.lower()).value
        print(f"{character.name}'s {self.primary_attribute}: {stat_value}")
        
        roll = random.randint(1, 6)
        print(f"Rolling dice... Rolled: {roll}")
        
        total = roll + stat_value
        threshold = 8
        print(f"Total (roll + {self.primary_attribute}): {total}")
        print(f"Need {threshold} or higher to succeed.")
        
        return total >= threshold

    def resolve_boss(self, party, parser=None):
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
                self._get_input("1. Attack\n> ", parser)  # Only option is to attack
                
                # Player attack
                hit_chance = 50 + (member.dexterity.value - boss.dexterity) * 5
                if random.randint(1, 100) <= hit_chance:
                    damage = member.strength.value + random.randint(1, 6)
                    boss.take_damage(damage)
                    print(f"{member.name} hits {boss.name} for {damage} damage!")
                else:
                    print(f"{member.name}'s attack misses!")
                
                # Boss attack if still alive
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