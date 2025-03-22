from typing import Optional, List
import random

class Statistic:
    """Represents a character's statistic with a value and constraints."""
    def __init__(self, name: str, value: int = 0, description: str = "", min_value: int = 0, max_value: int = 100):
        self.name = name
        self.value = value
        self.description = description
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self):
        return f"{self.name}: {self.value}"

    def modify(self, amount: int):
        """Modify the statistic value within bounds."""
        self.value = max(self.min_value, min(self.max_value, self.value + amount))

class Character:
    """Represents a player character with stats and class-specific attributes."""
    # Base stats for different character classes
    BASE_STATS = {
        "Scrapper": {"strength": 5, "dexterity": 5, "vitality": 20, "intelligence": 5},
        "Gearshot": {"strength": 3, "dexterity": 7, "vitality": 15, "intelligence": 5},
        "Steamwright": {"strength": 4, "dexterity": 5, "vitality": 18, "intelligence": 7},
        "Rustblade": {"strength": 7, "dexterity": 4, "vitality": 16, "intelligence": 4}
    }
    
    def __init__(self, name: str = "Bob", class_type: str = "Scrapper"):
        self.name = name
        self.class_type = class_type
        
        # Initialize all statistics
        self.strength = Statistic("Strength", description="Physical power.")
        self.dexterity = Statistic("Dexterity", description="Agility and accuracy.")
        self.vitality = Statistic("Vitality", description="Health points.", max_value=30)
        self.intelligence = Statistic("Intelligence", description="Problem-solving ability.")
        
        # Setup character
        self.set_base_stats()
        self.randomize_stats()
        self.max_vitality = self.vitality.value  # Track max for healing
        self.inventory = []  # Track items collected

    def set_base_stats(self):
        """Set base stats based on class type."""
        # Get stats for this class, or default to Scrapper
        class_stats = self.BASE_STATS.get(self.class_type, self.BASE_STATS["Scrapper"])
        
        # Apply stats to character
        for stat, value in class_stats.items():
            getattr(self, stat).value = value

    def randomize_stats(self):
        """Add random variation to stats."""
        for stat in self.get_stats():
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
        """String representation of character with stats."""
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