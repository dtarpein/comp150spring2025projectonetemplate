"""Advanced adventure systems for Canyon of the Lost Engines game."""
import random
from typing import List, Tuple, Dict, Any, Optional

# This file adds enhanced interactive elements for scavenging and repairing
# It can be imported into main.py but is designed not to break existing functionality
# if missing or not imported

class ScavengingSystem:
    """Enhanced scavenging system with mini-games and interactive elements."""
    
    COMMON_ITEMS = [
        "Scrap Metal", "Spare Parts", "Copper Wire", 
        "Rusty Gear", "Steam Valve", "Boiler Plate", "Brass Fitting"
    ]
    
    SPECIAL_ITEMS = ["Repair Kit", "Steam Tonic", "Engineer's Tools"]
    
    SCAVENGE_SPOTS = [
        "ancient wreckage", "rusted machinery", "twisted metal heap",
        "broken control panel", "abandoned toolbox", "half-buried chest",
        "cracked boiler", "collapsed scaffolding", "broken console"
    ]
    
    @staticmethod
    def get_scavenging_options(location_name: str) -> List[Dict[str, Any]]:
        """Generate location-specific scavenging spots."""
        # Create 3 scavenging spots with varying difficulty and rewards
        spots = []
        used_spots = set()
        
        # Location-specific modifiers
        if "Titan" in location_name:
            item_bonus = ["Reinforced Plating", "Memory Core", "Hydraulic Pump"]
            difficulty_mod = 0
        elif "Gulch" in location_name:
            item_bonus = ["Heat Exchanger", "Pressure Valve", "Thermal Coating"]
            difficulty_mod = -5  # Easier
        elif "Spire" in location_name:
            item_bonus = ["Steam Capacitor", "Filter Membrane", "Altitude Sensor"]
            difficulty_mod = 5  # Harder
        else:
            item_bonus = []
            difficulty_mod = 0
            
        # Create 3 different spots to scavenge
        for i in range(3):
            # Get a unique spot description
            while True:
                spot = random.choice(ScavengingSystem.SCAVENGE_SPOTS)
                if spot not in used_spots:
                    used_spots.add(spot)
                    break
            
            # Determine difficulty (affects success chance and rewards)
            difficulty = 10 * (i + 1) + difficulty_mod
            
            # Create potential rewards
            rewards = ScavengingSystem.COMMON_ITEMS.copy()
            if item_bonus:
                rewards.extend(item_bonus)
                
            spots.append({
                "name": spot,
                "difficulty": difficulty,
                "rewards": rewards,
                "special_chance": 5 + (i * 5),  # 5%, 10%, 15% chance for special items
                "description": f"A {spot} that looks {['fairly easy', 'somewhat challenging', 'quite difficult'][i]} to search."
            })
            
        return spots
    
    @staticmethod
    def attempt_scavenge(character, spot: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Attempt to scavenge a specific spot, returning a message and any found items."""
        difficulty = spot["difficulty"]
        success_threshold = 40 + character.dexterity.value * 5 - difficulty
        
        roll = random.randint(1, 100)
        found_items = []
        
        # Critical success (natural 1-5)
        if roll <= 5:
            # Always find something good on a critical success
            found_items.append(random.choice(spot["rewards"]))
            
            # Chance for special item
            if random.randint(1, 100) <= spot["special_chance"] * 2:  # Double chance on critical
                found_items.append(random.choice(ScavengingSystem.SPECIAL_ITEMS))
                return f"Jackpot! You expertly dismantle the {spot['name']} and find some valuable items!", found_items
            
            return f"Success! You skillfully search the {spot['name']} and find something useful!", found_items
            
        # Regular success
        elif roll <= success_threshold:
            # Find a regular item
            found_items.append(random.choice(spot["rewards"]))
            
            # Small chance for special item
            if random.randint(1, 100) <= spot["special_chance"]:
                found_items.append(random.choice(ScavengingSystem.SPECIAL_ITEMS))
                return f"Great find! While searching the {spot['name']}, you discover multiple items!", found_items
            
            return f"You carefully search the {spot['name']} and find something useful.", found_items
            
        # Critical failure (natural 96-100)
        elif roll >= 96:
            # Potentially take damage on critical failure
            damage = random.randint(1, 3)
            character.take_damage(damage)
            return f"Disaster! The {spot['name']} collapses as you search it, causing {damage} damage! You find nothing.", []
            
        # Regular failure
        else:
            failure_messages = [
                f"You search the {spot['name']} but find nothing useful.",
                f"Despite your efforts, the {spot['name']} yields no useful components.",
                f"The {spot['name']} seems to have been picked clean already."
            ]
            return random.choice(failure_messages), []

class RepairSystem:
    """Interactive airship repair system."""
    
    REPAIR_ZONES = [
        {
            "name": "Engine Core",
            "description": "The heart of the airship, requiring Core Fragments to power.",
            "requires": ["Core Fragment"],
            "difficulty": 20,
            "repaired": False
        },
        {
            "name": "Hull Plating",
            "description": "The outer shell of the airship, riddled with holes and dents.",
            "requires": ["Scrap Metal", "Boiler Plate", "Reinforced Plating"],
            "difficulty": 10,
            "repaired": False
        },
        {
            "name": "Control Systems",
            "description": "Navigational and flight controls, currently non-responsive.",
            "requires": ["Copper Wire", "Spare Parts", "Memory Core"],
            "difficulty": 15,
            "repaired": False
        },
        {
            "name": "Steam Generator",
            "description": "Produces the steam needed for propulsion and systems.",
            "requires": ["Pressure Valve", "Steam Valve", "Heat Exchanger"],
            "difficulty": 25,
            "repaired": False
        }
    ]
    
    @staticmethod
    def get_repair_status(core_fragments: int, party_inventory: List[str]) -> Dict[str, Any]:
        """Get the current repair status of all zones."""
        status = {
            "total_zones": len(RepairSystem.REPAIR_ZONES),
            "repaired_zones": 0,
            "zones": [],
            "can_complete": False
        }
        
        all_repaired = True
        
        for zone in RepairSystem.REPAIR_ZONES:
            zone_copy = zone.copy()
            
            # Check which requirements are met
            if zone["name"] == "Engine Core":
                # Special handling for Engine Core which needs all fragments
                has_requirements = core_fragments >= 3
                zone_copy["requirements_met"] = [True if core_fragments >= 3 else False]
                zone_copy["requirements_text"] = [f"Core Fragments: {core_fragments}/3"]
            else:
                # For other zones, check each required part
                requirements_met = []
                requirements_text = []
                
                for req in zone["requires"]:
                    if req in party_inventory:
                        requirements_met.append(True)
                        requirements_text.append(f"{req}: ✓")
                    else:
                        requirements_met.append(False)
                        requirements_text.append(f"{req}: ✗")
                        
                has_requirements = all(requirements_met)
                zone_copy["requirements_met"] = requirements_met
                zone_copy["requirements_text"] = requirements_text
            
            zone_copy["can_repair"] = has_requirements and not zone["repaired"]
            
            if zone["repaired"]:
                status["repaired_zones"] += 1
            else:
                all_repaired = False
                
            status["zones"].append(zone_copy)
            
        status["can_complete"] = all_repaired
        return status
    
    @staticmethod
    def attempt_repair(character, zone: Dict[str, Any], party_inventory: List[str]) -> Tuple[bool, str]:
        """Attempt to repair a specific zone of the airship."""
        if zone["repaired"]:
            return False, "This zone is already repaired."
            
        # Special handling for Engine Core
        if zone["name"] == "Engine Core" and "Core Fragment" in zone["requires"]:
            # This is handled separately as it requires 3 Core Fragments
            # and is managed by the Game class's core_fragments counter
            pass
        else:
            # Check if all requirements are met
            for req in zone["requires"]:
                if req not in party_inventory:
                    return False, f"You need {req} to repair this zone."
        
        # Calculate success chance based on character's intelligence and zone difficulty
        success_chance = 50 + (character.intelligence.value * 5) - zone["difficulty"]
        roll = random.randint(1, 100)
        
        if roll <= success_chance:
            # Success!
            for zone_ref in RepairSystem.REPAIR_ZONES:
                if zone_ref["name"] == zone["name"]:
                    zone_ref["repaired"] = True
                    break
                    
            # Remove used components from inventory
            if zone["name"] != "Engine Core":  # Core Fragments are handled separately
                for req in zone["requires"]:
                    if req in party_inventory:
                        party_inventory.remove(req)
            
            return True, f"You successfully repair the {zone['name']}!"
        else:
            # Failure
            damage = random.randint(1, 2)
            character.take_damage(damage)
            
            return False, f"The repair fails and you sustain {damage} damage in the process. Try again."

    @staticmethod
    def reset_repairs():
        """Reset all repairs (used when starting a new game)."""
        for zone in RepairSystem.REPAIR_ZONES:
            zone["repaired"] = False

# Helper functions to integrate with the main game code in main.py
def enhance_game_with_scavenging(game_obj):
    """Patch the game object with enhanced scavenging functionality."""
    original_scavenge = getattr(game_obj, "_scavenge_location", None)
    
    def enhanced_scavenge(location):
        # Select character to do the scavenging
        character = game_obj.parser.select_party_member(game_obj.party)
        if not character:
            return
        
        # Get scavenging spots
        spots = ScavengingSystem.get_scavenging_options(location.name)
        
        print(f"\n{character.name} searches {location.name} for useful items.")
        print("Choose a spot to search:")
        
        for idx, spot in enumerate(spots, 1):
            print(f"{idx}. {spot['description']}")
        print(f"{len(spots) + 1}. Cancel")
        
        while True:
            try:
                choice = int(game_obj.parser.parse("> ")) - 1
                if choice == len(spots):
                    return
                if 0 <= choice < len(spots):
                    break
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Attempt to scavenge the chosen spot
        spot = spots[choice]
        message, found_items = ScavengingSystem.attempt_scavenge(character, spot)
        print(message)
        
        # Add found items to inventory
        for item in found_items:
            character.add_to_inventory(item)
            print(f"Added {item} to {character.name}'s inventory.")
        
        # Check if character is still alive (in case of hazards)
        if not character.is_alive():
            game_obj.party.remove(character)
            print(f"{character.name} has been lost!")
    
    # Only replace if original method doesn't exist
    if original_scavenge is None:
        setattr(game_obj, "_scavenge_location", enhanced_scavenge)
    
    return game_obj

def enhance_game_with_repairs(game_obj):
    """Patch the game object with enhanced repair functionality."""
    original_repair = getattr(game_obj, "_repair_airship", None)
    
    def enhanced_repair():
        if game_obj.airship_repaired:
            print("The airship is already repaired and ready to fly!")
            return
            
        # Get collective inventory of the whole party
        party_inventory = []
        for member in game_obj.party:
            party_inventory.extend(member.inventory)
            
        # Get repair status
        repair_status = RepairSystem.get_repair_status(game_obj.core_fragments, party_inventory)
        
        # Show repair status
        print("\n=== AIRSHIP REPAIR STATUS ===")
        print(f"Zones Repaired: {repair_status['repaired_zones']}/{repair_status['total_zones']}")
        
        if game_obj.core_fragments < 3:
            print(f"Core Fragments: {game_obj.core_fragments}/3 (Need 3 to power the Engine Core)")
        
        # Display each zone
        repairable_zones = []
        for idx, zone in enumerate(repair_status['zones'], 1):
            status = "REPAIRED" if zone.get('repaired', False) else "NOT REPAIRED"
            print(f"\n{idx}. {zone['name']} - {status}")
            print(f"   {zone.get('description', '')}")
            
            # Show requirements
            if 'requirements_text' in zone:
                print("   Requirements:")
                for req in zone['requirements_text']:
                    print(f"   - {req}")
            
            if zone.get('can_repair', False):
                repairable_zones.append(zone)
        
        # Check if all zones are repaired
        if repair_status['can_complete']:
            print("\nAll zones repaired! The airship is ready to fly!")
            game_obj.airship_repaired = True
            return
        
        # If no zones can be repaired, inform the player
        if not repairable_zones:
            print("\nYou don't have the necessary parts to repair any zones.")
            print("Continue exploring and scavenging to find the required components.")
            return
        
        # Let the player choose a zone to repair
        print("\nChoose a zone to repair:")
        for idx, zone in enumerate(repairable_zones, 1):
            print(f"{idx}. {zone['name']}")
        print(f"{len(repairable_zones) + 1}. Cancel")
        
        while True:
            try:
                choice = int(game_obj.parser.parse("> ")) - 1
                if choice == len(repairable_zones):
                    return
                if 0 <= choice < len(repairable_zones):
                    break
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Select a character to perform the repair
        character = game_obj.parser.select_party_member(game_obj.party)
        if not character:
            return
        
        # Attempt the repair
        zone = repairable_zones[choice]
        success, message = RepairSystem.attempt_repair(character, zone, party_inventory)
        print(message)
        
        # Update inventory by removing used items
        if success:
            # Remove used items from character inventories
            for member in game_obj.party:
                for req in zone.get('requires', []):
                    if req in member.inventory and req != "Core Fragment":
                        member.inventory.remove(req)
                        break
            
            # Handle Core Fragments separately
            if zone['name'] == "Engine Core" and success:
                # Core fragments are spent
                game_obj.core_fragments = 0
        
        # Check repair completion
        updated_status = RepairSystem.get_repair_status(game_obj.core_fragments, party_inventory)
        if updated_status['can_complete']:
            print("\nAll zones repaired! The airship is ready to fly!")
            game_obj.airship_repaired = True
        
        # Check if character is still alive (in case of repair hazards)
        if not character.is_alive():
            game_obj.party.remove(character)
            print(f"{character.name} has been lost!")
    
    # Only replace if original method doesn't exist
    if original_repair is None:
        setattr(game_obj, "_repair_airship", enhanced_repair)
    
    return game_obj

def add_scavenging_to_location(location):
    """Add scavenging methods to a location object."""
    
    # Add scavenging method if it doesn't exist
    if not hasattr(location, "scavenge"):
        def scavenge(character):
            """Scavenge the location for resources."""
            if location.scavenged:
                return "You've already picked this area clean.", False
            
            location.scavenged = True
            
            # Get scavenging spots
            spots = ScavengingSystem.get_scavenging_options(location.name)
            spot = random.choice(spots)
            
            message, found_items = ScavengingSystem.attempt_scavenge(character, spot)
            
            # Add found items to inventory
            for item in found_items:
                character.add_to_inventory(item)
            
            return message, bool(found_items)
            
        setattr(location, "scavenge", scavenge)
        
    return location

# Example of how to use this module in main.py:
#
# from adventure_system import enhance_game_with_scavenging, enhance_game_with_repairs, add_scavenging_to_location
#
# def _explore_location(self):
#     location = self._select_location()
#     if not location:
#         return
#     
#     # Add scavenging functionality to the location
#     location = add_scavenging_to_location(location)
#     
#     # Now you can use location.scavenge(character)
#     
# # In the Game.__init__ method:
# def __init__(self, ...):
#     # Initialize the game...
#     
#     # Enhance the game with the advanced systems
#     self = enhance_game_with_scavenging(self)
#     self = enhance_game_with_repairs(self)
