# text_file.py
import struct
from io import StringIO
from typing import Iterable, List

from text_config import TextConfig, TextLine

# Constants for text formatting
BASE_KEY = 0x7C89
ADVANCE_KEY = 0x2983
VARIABLE_KEY = 0x0010
TERMINATOR_KEY = 0x0000
RETURN_TEXT_KEY = 0xBE00
CLEAR_TEXT_KEY = 0xBE01
WAIT_TEXT_KEY = 0xBE02
NULL_TEXT_KEY = 0xBDFF
RUBY_TEXT_KEY = 0xFF01

REMAP_CHAR_MAP = {
    0xE07F: 0x202F,
    0xE08D: 0x2026,
    0xE08E: 0x2642,
    0xE08F: 0x2640,
}

# Default empty text file data (20 bytes)
EMPTY_TEXT_FILE = bytearray([0x01, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00,
                            0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00,
                            0x04, 0x00, 0x00, 0x00])

class TextFile:
    """Class to handle Pokémon Switch game text binaries."""
    
    def decrypt_line(self, index: int) -> str:
        return self.get_line(index)
    
    def __init__(self, data=None, config=None, remap_characters: bool = False):
        """Initialize with binary data or default empty data."""
        self.data = bytearray(data) if data is not None else bytearray(EMPTY_TEXT_FILE)
        self.config = config or TextConfig("default")  # Replace "default" with actual game version
        self.remap_characters = remap_characters
        self.set_empty_text = False
        self._cached_section_data_offset = None
        self._cached_line_offsets = None
        
        # Validate initial conditions
        if self.initial_key != 0:
            raise ValueError("Invalid initial key! Expected 0.")
        if self.section_data_offset + self.total_length != len(self.data) or self.text_sections != 1:
            raise ValueError("Invalid text file format.")
        if self.section_length != self.total_length:
            raise ValueError("Section length and total length mismatch.")

    @classmethod
    def from_lines(cls, lines: Iterable[str], flags: Iterable[int], config=None, remap_characters: bool = False):
        """Create an instance from text lines and flags."""
        instance = cls(config=config, remap_characters=remap_characters)
        instance.lines = lines
        instance.flags = flags
        return instance

    # Properties to access/modify header fields
    @property
    def text_sections(self):
        return struct.unpack_from('<H', self.data, 0x00)[0]
    
    @text_sections.setter
    def text_sections(self, value):
        struct.pack_into('<H', self.data, 0x00, value)

    @property
    def line_count(self):
        return struct.unpack_from('<H', self.data, 0x02)[0]
    
    @line_count.setter
    def line_count(self, value):
        struct.pack_into('<H', self.data, 0x02, value)

    @property
    def total_length(self):
        return struct.unpack_from('<I', self.data, 0x04)[0]
    
    @total_length.setter
    def total_length(self, value):
        struct.pack_into('<I', self.data, 0x04, value)

    @property
    def initial_key(self):
        return struct.unpack_from('<I', self.data, 0x08)[0]
    
    @initial_key.setter
    def initial_key(self, value):
        struct.pack_into('<I', self.data, 0x08, value)

    @property
    def section_data_offset(self):
        if self._cached_section_data_offset is None:
            self._cached_section_data_offset = struct.unpack_from('<I', self.data, 0x0C)[0]
        return self._cached_section_data_offset
    
    @section_data_offset.setter
    def section_data_offset(self, value):
        struct.pack_into('<I', self.data, 0x0C, value)
        self._cached_section_data_offset = value

    @property
    def section_length(self):
        return struct.unpack_from('<I', self.data, self.section_data_offset)[0]
    
    @section_length.setter
    def section_length(self, value):
        struct.pack_into('<I', self.data, self.section_data_offset, value)

    @property
    def line_offsets(self):
        """Get/set line offsets and metadata as a list of TextLine objects."""
        if self._cached_line_offsets is None:
            result = []
            base = self.section_data_offset + 4  # After SectionLength
            for i in range(self.line_count):
                offset, length, flags = struct.unpack_from('<iHH', self.data, base + i * 8)
                result.append(TextLine(offset, length, flags))
            self._cached_line_offsets = result
        return self._cached_line_offsets
    
    @line_offsets.setter
    def line_offsets(self, value):
        base = self.section_data_offset + 4
        for i, line in enumerate(value):
            struct.pack_into('<iHH', self.data, base + i * 8, line.offset, line.length, line.flags)
        self._cached_line_offsets = value

    @property
    def lines(self):
        """Get text lines as a list of strings."""
        key = BASE_KEY
        result = []
        for line in self.line_offsets:
            start = self.section_data_offset + line.offset
            end = start + line.length * 2
            encrypted = self.data[start:end]
            decrypted = self.encrypt_line_data(encrypted, key)
            result.append(self.parse_line_string(decrypted))
            key = (key + ADVANCE_KEY) & 0xFFFF
        return result

    @lines.setter
    def lines(self, value):
        line_data = self.convert_lines_to_data(value)
        self.line_data = line_data

    @property
    def flags(self):
        """Get/set flags for each line."""
        return [line.flags for line in self.line_offsets]
    
    @flags.setter
    def flags(self, value):
        offsets = self.line_offsets
        offsets = [offsets[i]._replace(flags=flag) for i, flag in enumerate(value)]
        self.line_offsets = offsets

    @property
    def line_data(self):
        """Get/set encrypted line data as a list of bytearrays."""
        result = []
        lines = self.line_offsets
        sdo = self.section_data_offset
        key = BASE_KEY
        for line in lines:
            start = sdo + line.offset
            end = start + line.length * 2
            encrypted = self.data[start:end]
            decrypted = self.encrypt_line_data(encrypted, key)
            result.append(decrypted)
            key = ((key << 3) | (key >> 13)) & 0xFFFF
        return result
    
    @line_data.setter
    def line_data(self, value):
        # Calculate total size and rebuild offsets
        lines = [TextLine(0, len(v) // 2, 0) for v in value]  # Temporary offsets
        bytes_used = 4 + len(value) * 8  # SectionLength + LineOffsets
        for i, v in enumerate(value):
            lines[i] = lines[i]._replace(offset=bytes_used)
            bytes_used += len(v)
            if bytes_used % 4 == 2:  # 4-byte alignment padding
                bytes_used += 2
        
        # Resize data and set values
        sdo = self.section_data_offset
        self.data = self.data[:sdo] + bytearray(bytes_used)
        self.section_length = bytes_used
        self.total_length = bytes_used
        self.line_count = len(value)
        self.line_offsets = lines
        
        # Copy encrypted data
        for i, encrypted in enumerate(value):
            start = sdo + lines[i].offset
            self.data[start:start + len(encrypted)] = encrypted

    def get_encrypted_line(self, index):
        """Get encrypted byte data for a specific line."""
        line = self.line_offsets[index]
        sdo = self.section_data_offset
        start = sdo + line.offset
        return self.data[start:start + line.length * 2]

    def get_line(self, index):
        """Get decrypted string for a specific line."""
        encrypted = self.get_encrypted_line(index)
        key = self.get_line_key(index)
        decrypted = self.encrypt_line_data(encrypted, key)
        return self.parse_line_string(decrypted)

    def get_line_key(self, index):
        """Calculate encryption key for a specific line."""
        return (BASE_KEY + index * ADVANCE_KEY) & 0xFFFF

    def encrypt_line_data(self, data: bytes | bytearray, key: int) -> bytearray:
        """Encrypt/decrypt line data using XOR (symmetric operation)."""
        result = bytearray(data)
        key_mask = 0xFFFF
        for i in range(0, len(result), 2):
            u16 = struct.unpack_from('<H', result, i)[0]
            u16 ^= key
            struct.pack_into('<H', result, i, u16)
            key = ((key << 3) | (key >> 13)) & key_mask
        return result

    def parse_line_string(self, data: bytes | bytearray) -> str:
        """Convert decrypted byte data into a readable string."""
        s = StringIO()
        i = 0
        while i < len(data):
            val = struct.unpack_from('<H', data, i)[0]
            i += 2
            if val == TERMINATOR_KEY:
                break
            elif val == VARIABLE_KEY:
                var_str, consumed = self.parse_variable_string(data, i)
                s.write(var_str)
                i += consumed
            elif val == 0x0A:  # '\n'
                s.write('\\n')
            elif val == ord('\\'):
                s.write('\\\\')
            elif val == ord('['):
                s.write('\\[')
            elif val == ord('{'):
                s.write('\\{')
            else:
                mapped = self.config.get_variable_string(val)
                if mapped != f"{val:04X}":
                    s.write(mapped)
                else:
                    s.write(chr(self.try_remap_character(val)))
        return s.getvalue()

    def parse_variable_string(self, data: bytes | bytearray, start: int) -> tuple[str, int]:
        """Process variable data and return string representation with bytes consumed."""
        i = start
        count = struct.unpack_from('<H', data, i)[0]
        i += 2
        variable = struct.unpack_from('<H', data, i)[0]
        i += 2

        if variable == RETURN_TEXT_KEY:
            return "\\r", i - start
        elif variable == CLEAR_TEXT_KEY:
            return "\\c", i - start
        elif variable == WAIT_TEXT_KEY:
            time = struct.unpack_from('<H', data, i)[0]
            i += 2
            return f"[WAIT {time}]", i - start
        elif variable == NULL_TEXT_KEY:
            line = struct.unpack_from('<H', data, i)[0]
            i += 2
            return f"[~ {line}]", i - start
        elif variable == RUBY_TEXT_KEY:
            base_len = struct.unpack_from('<H', data, i)[0]
            i += 2
            ruby_len = struct.unpack_from('<H', data, i)[0]
            i += 2
            base1 = data[i:i + base_len * 2]
            i += base_len * 2
            ruby = data[i:i + ruby_len * 2]
            i += ruby_len * 2
            base2 = data[i:i + base_len * 2]
            i += base_len * 2
            s = ['{', self.parse_line_string(base1), '|', self.parse_line_string(ruby)]
            if base1 != base2:
                s.extend(['|', self.parse_line_string(base2)])
            s.append('}')
            return ''.join(s), i - start
        else:
            var_name = self.config.get_variable_string(variable)
            s = [f"[VAR {var_name}"]
            if count > 1:
                s.append('(')
                args = []
                for _ in range(count - 1):
                    arg = struct.unpack_from('<H', data, i)[0]
                    i += 2
                    args.append(f"{arg:04X}")
                s.append(','.join(args))
                s.append(')')
            s.append(']')
            return ''.join(s), i - start

    def try_remap_character(self, val: int) -> int:
        """Remap special characters to Unicode equivalents if remap_characters is True."""
        if not self.remap_characters:
            return val
        return REMAP_CHAR_MAP.get(val, val)

    def convert_lines_to_data(self, lines: Iterable[str]) -> List[bytearray]:
        """Convert a list of strings into encrypted line data."""
        key = BASE_KEY
        result = []
        for i, text in enumerate(lines):
            if text is None:
                text = ''
            else:
                text = text.strip()
            if not text and self.set_empty_text:
                text = f"[~ {i}]"
            decrypted = self.string_to_line_data(text)
            encrypted = self.encrypt_line_data(decrypted, key)
            result.append(encrypted)
            key = (key + ADVANCE_KEY) & 0xFFFF
        return result

    def string_to_line_data(self, line: str) -> bytes:
        """Convert a string into decrypted bytearray."""
        result = []
        i = 0
        while i < len(line):
            c = line[i]
            i += 1
            if c == '[':
                end = line.find(']', i)
                if end < 0:
                    raise ValueError("Unterminated variable text")
                var_text = line[i:end]
                result.extend(self.parse_variable_values(var_text))
                i = end + 1
            elif c == '{':
                end = line.find('}', i)
                if end < 0:
                    raise ValueError("Unterminated ruby text")
                ruby_text = line[i:end]
                result.extend(self.parse_ruby_values(ruby_text))
                i = end + 1
            elif c == '\\':
                result.extend(self.parse_escape_values(line[i]))
                i += 1
            else:
                # Checks if the character is mapped as a variable
                for code, var_str in self.config.variables.items():
                    if var_str == c:  # Ex.: "₽" mapeado para 0xE300
                        result.append(code)
                        break
                else:  # If it is not a variable, treat it as a normal character.
                    val = ord(c)
                    val = self.try_remap_character(val)
                    result.append(val)
        result.append(TERMINATOR_KEY)
        return struct.pack('<' + 'H' * len(result), *result)

    def parse_escape_values(self, esc: str) -> List[int]:
        """Convert escape sequences into their ushort values."""
        ESC_MAP = {
            'n': [0x0A],
            '\\': [ord('\\')],
            '[': [ord('[')],
            '{': [ord('{')],
            'r': [VARIABLE_KEY, 1, RETURN_TEXT_KEY],
            'c': [VARIABLE_KEY, 1, CLEAR_TEXT_KEY]
        }
        if esc in ESC_MAP:
            return ESC_MAP[esc]
        raise ValueError(f"Invalid escape character: \\{esc}")

    def parse_variable_values(self, text: str) -> List[int]:
        """Convert variable text into a list of ushort values."""
        space = text.find(' ')
        if space == -1:
            raise ValueError(f"Malformed variable: {text}")
        command, args = text[:space], text[space + 1:]
        result = [VARIABLE_KEY]
        if command == '~':
            result.extend([2, NULL_TEXT_KEY, int(args)])
        elif command == 'WAIT':
            result.extend([2, WAIT_TEXT_KEY, int(args)])
        elif command == 'VAR':
            if '(' in args:
                var, arg_str = args.split('(', 1)
                arg_list = arg_str.rstrip(')').split(',')
                result.extend([1 + len(arg_list), self.config.get_variable_number(var)])
                result.extend(int(arg, 16) for arg in arg_list)
            else:
                result.extend([1, self.config.get_variable_number(args)])
        else:
            raise ValueError(f"Unknown variable type: {command}")
        return result

    def parse_ruby_values(self, text: str) -> List[int]:
        """Convert ruby text into a list of ushort values."""
        parts = text.split('|')
        if len(parts) not in (2, 3):
            raise ValueError(f"Malformed ruby text: {text}")
        base1, ruby = parts[0], parts[1]
        base2 = parts[2] if len(parts) == 3 else base1
        if len(base1) != len(base2):
            raise ValueError(f"Ruby base texts mismatch: {text}")
        result = [VARIABLE_KEY, 3 + len(base1) + len(ruby), RUBY_TEXT_KEY, len(base1), len(ruby)]
        for c in base1:
            result.append(self.try_remap_character(ord(c)))
        for c in ruby:
            result.append(self.try_remap_character(ord(c)))
        for c in base2:
            result.append(self.try_remap_character(ord(c)))
        return result