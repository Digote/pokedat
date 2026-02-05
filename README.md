# Tool for Extracting Text from .dat Files in Pokémon Switch Games

A simple Python tool to decrypt and extract text from Pokémon games on the Nintendo Switch.  
It supports `.dat` and `.tbl` files.

Based on the **[pkNX](https://github.com/kwsch/pkNX) project by [kwsch](https://github.com/kwsch).**  
Check out the original implementation in **[Structures/Text/TextFile.cs](https://github.com/kwsch/pkNX/blob/master/pkNX.Structures/Text/TextFile.cs).**

---

## Supported Games

- **LGPE** - Let's Go Pikachu & Eevee
- **SWSH** - Sword & Shield
- **LA** - Legends Arceus
- **SV** - Scarlet & Violet
- **LZA** - Legends Z-A

---

## Usage

```bash
python main.py <command> <input> [output] --version=<VERSION> [--format=<FORMAT>]
```

### Commands

#### 1. **read** - Extract text from .dat files
```bash
# Extract single file to JSON
python main.py read "path/to/file.dat" "output_folder" --version=LZA --format=json

# Extract single file to TXT
python main.py read "path/to/file.dat" "output_folder" --version=LZA --format=txt

# Extract entire folder
python main.py read "path/to/dat_folder" "output_folder" --version=LZA --format=json
```

#### 2. **write** - Compile text files back to .dat
```bash
# Compile single JSON file
python main.py write "path/to/file.json" "output_folder" --version=LZA --format=json

# Compile single TXT file
python main.py write "path/to/file.txt" "output_folder" --version=LZA --format=txt

# Compile entire folder
python main.py write "path/to/text_folder" "output_folder" --version=LZA --format=json
```

#### 3. **merge** - Combine all .dat files from subfolders into single text files
```bash
# Merges common/, script/, sk/ folders into common.txt, script.txt, sk.txt
python main.py merge "path/to/dat_folder" --version=LZA

# Specify output folder
python main.py merge "path/to/dat_folder" "output_folder" --version=LZA
```
**Output:** One text file per subfolder with all .dat contents separated by `filename.dat ~~~~`

#### 4. **split** - Split merged text files back into individual .dat files
```bash
# Splits common.txt, script.txt, sk.txt back into .dat files organized by folders
python main.py split "path/to/merged_folder" "output_folder" --version=LZA
```
**Features:**
- Validates line count against original files
- Warns if lines are missing from edited files

---

## Formats

- **json** - Structured format with ID, hash, and text fields (default)
- **txt** - Plain text format, one line per entry

---

## Features

✅ Multi-threaded processing for fast batch operations  
✅ Automatic subfolder detection  
✅ Line count validation (merge/split)  
✅ UTF-8 encoding support  
✅ Progress tracking with detailed logging  
✅ Error handling with comprehensive error messages  

---

## Workflow Example

### Extract and edit all texts from a game:
```bash
# 1. Merge all .dat files into manageable text files
python main.py merge "game/message/dat" --version=LZA

# 2. Edit the generated common.txt, script.txt, sk.txt files

# 3. Split back into .dat files
python main.py split "game/message/dat" "game/message/dat_translated" --version=LZA

# Done! Your translated .dat files are ready
```

---

## Contributing

If you want to help map the variables of each Pokémon game on the Switch, just open a PR for the module [text_config.py](text_config.py).