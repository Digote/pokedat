# text_config.py
from collections import namedtuple
from typing import Dict

# Defining the TextLine structure as a namedtuple
TextLine = namedtuple('TextLine', ['offset', 'length', 'flags'])

GAME_VARIABLES: Dict[str, Dict[int, str]] = {
    "LGPE": {   # Pokémon Let's Go Pikachu and Let's Go Eevee
        0xFF00: "COLOR",            # Change the text color
        0x0100: "TRNAME",           # Trainer name
        0x0101: "POKNAME",          # Pokémon name
        0x0102: "PKNICK",           # Pokémon nickname
        0x0103: "TYPE",             # Type Pokémon
        0x0104: "SPECIES",          # Species Pokémon
        0x0105: "LOCATION",         # Location name
        0x0106: "ABILITY",          # Ability name
        0x0107: "MOVE",             # Move name
        0x0108: "ITEM1",            # Item name
        0x0109: "ITEM2",            # Item name
        0x010B: "GERM00",           # Variable german text
        0x010C: "PKMLVUP",          # Name Pokémon level up
        0x010D: "EVSTAT",           # Effort values stats
        0x010E: "TRCLASS",          # Trainer class
        0x0110: "GERM01",           # Variable german text
        0x0112: "BAG",              # Bag
        0x010A: "ITEMBAG",          # Bag item
        0x012D: "FORBIDDENCHAR",    # Forbidden character
        0x012E: "MISTERYCAP",       # I don't know yet, I put ID information
        0x01B0: "WBALLTYPE",        # Weather Ball that changes with the weather
        0x01B1: "STPKM",            # Pokémon status in battle
        0x01C6: "STYLEITEM",        # Style item
        0x01C9: "PGOTRAINER",       # Player's name Pokémon Go
        0x01C8: "SUPPORT",          # Support Player
        0x01CA: "GIFT00",           # Gift 00
        0x01CB: "GOPARKLOCAL",      # Pokémon Go Park Local
        0x01CC: "GOPARKPKM",        # Go Park Pokémon
        0x01CE: "PKMPKEVEE",        # Pokémon name game Pikachu or Eevee
        0x01CD: "RIVALNAME",        # Rival name
        0x019E: "FR|GER|SPA",       # Variable used in French, German and Spanish languages.
        0x1000: "NUM0",             # Number
        0x1001: "NUM10",            # Number
        0x1002: "FRAITA",           # Variable French Italian
        0x1100: "GENDBR",           # Gender-based pronoun
        0x1101: "ITEMPLUR1",        # Plural pronoun
        0x1102: "FRAITA01",         # Variable French Italian 01
        0x1104: "GARTFR",           # Gender Article French
        0x1302: "INDEF_ART",        # Indefinite article ("a" or "an")
        0x1303: "AMOUNT",           # Amount of items
        0x1400: "ARTFRA",           # Article French
        0x1401: "DARTFRA",          # Definite article French
        0x1402: "INARTFRA",         # Indefinite article French
        0x1403: "VARFRA00",         # Variable French 00
        0x1404: "VARFRA01",         # Variable French 01
        0x1406: "VARFRA02",         # Variable French 02
        0x1408: "VARFRA03",         # Variable French 03
        0x140A: "VARFRA03",         # Variable French 04
        0x1500: "VARITA00",         # Variable Italian 00
        0x1501: "VARITA01",         # Variable Italian 01
        0x1502: "VARITA02",         # Variable Italian 02
        0x1503: "VARITA03",         # Variable Italian 03
        0x1504: "VARITA04",         # Variable Italian 04
        0x1506: "VARITA05",         # Variable Italian 05
        0x1508: "VARITA06",         # Variable Italian 06
        0x150A: "VARITA07",         # Variable Italian 07
        0x1603: "VARGER00",         # Variable German 00
        0x1606: "VARGER01",         # Variable German 01
        0x1700: "VARESP00",         # Variable Spanish 00
        0x1701: "VARESP01",         # Variable Spanish 01
        0x1702: "VARESP02",         # Variable Spanish 02
        0x1704: "VARESP03",         # Variable Spanish 03
        0x1706: "VARESP04",         # Variable Spanish 04
        0x1708: "VARESP05",         # Variable Spanish 05
        0x1709: "VARESP06",         # Variable Spanish 06
        0x1900: "VARKOR00",         # Variable Korean 00
        0x0200: "NUM1",             # Number
        0x0201: "NUM2",             # Number
        0x0202: "NUM3",             # Number
        0x0203: "NUM4",             # Number
        0x0204: "NUM5",             # Number
        0x0205: "NUM6",             # Number
        0x0206: "NUM7",             # Number
        0x0207: "NUM8",             # Number
        0x0208: "NUM9",             # Number
        0x0189: "UNKNOWNPOKEMON",   # A Pokémon You Haven't Seen Yet with the Pokedex?
        0xBD03: "SYMBOL",           # Symbol
        0xBD04: "BTLTPFX",          # Battle type prefix
        0xBD06: "BTEFECT",          # Battle Super Effect
        0xBE05: "SFX",              # Sound effect

        # Special caracteres
        0xE300: "₽",               # Pokédollar
    },
    "SWSH": {   # Pokémon Sword and Shield
        0xFF00: "COLOR",    # Change the text color
    },
    "LA": {     # Pokémon Legends: Arceus
        0xFF00: "COLOR",    # Change the text color
    },
    "SV": {     # Pokémon Scarlet and Violet
        0xFF00: "COLOR",    # Change the text color
    },
    "LZA": {    # Pokémon Legends ZA
        0xFF00: "COLOR",            # Change the text color
        0x0100: "TRNAME",           # Trainer name
        0x0101: "POKNAME",          # Pokémon name
        0x0102: "PKNICK",           # Pokémon nickname
        0x0103: "TYPE",             # Type Pokémon
        0x0104: "SPECIES",          # Species Pokémon
        0x0105: "LOCATION",         # Location name
        0x0106: "ABILITY",          # Ability name
        0x0107: "MOVE",             # Move name
        0x0108: "ITEM1",            # Item name
        0x0109: "ITEM2",            # Item name
        0xE300: "₽",                # Pokédollar
        0x1100: "GENDBR",           # Gender-based pronoun
    },
}


class TextConfig:
    """Configuration for text variable codes based on the game version."""

    def __init__(self, game_version: str) -> None:
        """
        Initializes the configuration based on the game version.

        Args:
            game_version (str): The version of the game.
        
        Raises:
            ValueError: If the game version is not supported.
        """
        self.variables: Dict[int, str] = self.get_variables(game_version)
        if not self.variables:
            raise ValueError(f"Game version '{game_version}' is not supported.")

    def get_variables(self, game_version: str) -> Dict[int, str]:
        """
        Retrieves the variable mappings for the specified game version.
        
        TODO: Fill with actual mappings for each game version.

        Args:
            game_version (str): The version of the game.

        Returns:
            Dict[int, str]: A dictionary mapping codes to variable names.
        """
        return GAME_VARIABLES.get(game_version, {})

    def get_variable_string(self, code: int) -> str:
        """
        Returns the variable name for a given code or its hexadecimal representation if not mapped.
        
        Args:
            code (int): The variable code.
        
        Returns:
            str: The variable name or the hexadecimal representation of the code.
        """
        return self.variables.get(code, f"{code:04X}")

    def get_variable_number(self, name: str) -> int:
        """
        Converts a variable name or hexadecimal string to its code (ushort).
        
        Iterates through the mappings to find a match. If not found,
        attempts to convert the string to an integer (supporting hexadecimal formats).
        
        Args:
            name (str): The variable name or a string representing a number.
        
        Returns:
            int: The code corresponding to the variable.
        
        Raises:
            ValueError: If the name does not correspond to a valid code.
        """
        for code, var_name in self.variables.items():
            if var_name == name:
                return code
        try:
            if name.startswith('0x'):
                return int(name[2:], 16)
            return int(name, 16)
        except ValueError:
            raise ValueError(f"Invalid variable: {name}")