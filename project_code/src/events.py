import random
from typing import List
from enum import Enum
from character import Character, Enemy

class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"

class Event:
    """Represents an in-game event with resolution logic."""
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
        """Execute the event based on its type."""
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
        """Resolve a combat event."""
        enemy = Enemy(self.enemy["name"], self.enemy["vitality"], self.enemy["strength"], self.enemy["dexterity"])
        print(f"\n{character.name} engages {enemy.name}!")
        while character.is_alive() and enemy.is_alive():
            action = parser.parse("1. Attack 2. Flee\n> ")
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
        """Resolve a puzzle event with a stat check."""
        roll = random.randint(1, 6) + getattr(character, self.primary_attribute.lower()).value
        return roll >= 10  # Threshold for puzzle success

    def resolve_boss(self, party: List[Character]) -> bool:
        """Resolve the final boss combat."""
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