# tbl_handler.py
import struct
import os
from typing import BinaryIO, List, Dict, Any


class TblHandler:
    """Handles .tbl files containing label information."""
    
    MAGIC = 0x42544841  # "BTHA" in hex
    ENCODING = "cp1252"

    def __init__(self, dat_path: str):
        """
        Initialize the TBL handler.
        
        Args:
            dat_path: Path to the .dat file. The .tbl file path is derived from this.
        """
        self.tbl_path = self._get_tbl_path(dat_path)
        self.labels: List[Dict[str, Any]] = []
        self._load_tbl()
    
    @staticmethod
    def _get_tbl_path(dat_path: str) -> str:
        """
        Convert a .dat file path to its corresponding .tbl file path.
        
        Args:
            dat_path: Path to the .dat file
            
        Returns:
            Path to the corresponding .tbl file
        """
        return os.path.splitext(dat_path)[0] + ".tbl"
        
    def _load_tbl(self) -> None:
        """
        Load label information from the .tbl file.
        
        Raises:
            FileNotFoundError: If the .tbl file doesn't exist
            ValueError: If the .tbl file has an invalid header
        """
        if not os.path.exists(self.tbl_path):
            raise FileNotFoundError(f".tbl file not found: {self.tbl_path}")
        
        with open(self.tbl_path, "rb") as f:
            self._validate_header(f)
            self._read_entries(f)
    
    def _validate_header(self, file_handle: BinaryIO) -> None:
        """
        Validate the .tbl file header.
        
        Args:
            file_handle: Open file handle for the .tbl file
            
        Raises:
            ValueError: If the header is invalid
        """
        magic = struct.unpack("<I", file_handle.read(4))[0]
        if magic != self.MAGIC:
            raise ValueError("Invalid .tbl header!")
    
    def _read_entries(self, file_handle: BinaryIO) -> None:
        """
        Read all label entries from the .tbl file.
        
        Args:
            file_handle: Open file handle for the .tbl file
        """
        num_entries = struct.unpack("<I", file_handle.read(4))[0]
        for _ in range(num_entries):
            hash_value = struct.unpack("<Q", file_handle.read(8))[0]
            name_len = struct.unpack("<H", file_handle.read(2))[0]
            raw_name = file_handle.read(name_len).rstrip(b'\x00')
            name = raw_name.decode(self.ENCODING)
            self.labels.append({"id": name, "hash": hash_value})

    def read_until_null(self, file_handle: BinaryIO) -> str:
        """
        Read bytes from file until a null byte is encountered.
        
        Args:
            file_handle: Open file handle to read from
            
        Returns:
            Decoded string read from the file
        """
        name_bytes = bytearray()
        while True:
            byte = file_handle.read(1)
            if byte == b'\x00' or not byte:
                break
            name_bytes.extend(byte)
        return name_bytes.decode(self.ENCODING)

    def get_labels(self) -> List[Dict[str, Any]]:
        """
        Get all labels from the .tbl file.
        
        Returns:
            List of dictionaries containing label information
        """
        return self.labels