# 🕊️ Enhanced Scripture Search

A powerful Flask web application for searching and exploring the standard works with advanced text search and scripture reference lookup capabilities.

## ✨ Features

### Text Search
- **Advanced text search** with multiple search strategies
- **Phrase matching** and word-based search
- **Volume filtering** (Old Testament, New Testament, Book of Mormon, etc.)
- **Relevance scoring** for better result ranking

### 📖 Scripture Reference Lookup (NEW!)
- **Direct reference search**: `John 3:16`, `1 Nephi 1:1`, `D&C 76`
- **Book abbreviations**: `Matt`, `1Ne`, `D&C`, `Gen`, `Rev`, etc.
- **Verse ranges**: `Alma 32:21-23`, `John 14:1-6`
- **Interactive UI**: Dropdown selectors for book, chapter, and verse
- **Quick reference buttons** for popular scriptures

### Web Interface
- **Clean, responsive design** that works on desktop and mobile
- **Real-time search** with loading indicators
- **Reference examples** and quick search buttons
- **Links to ChurchofJesusChrist.org** for further study

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install flask pandas
```

### 2. Load Scripture Data
```python
from simple_scripture_search import EnhancedScriptureSearch

search = EnhancedScriptureSearch()
search.load_csv_file("kjvscriptures.csv", "KJV Scriptures")
search.load_csv_file("ldsscriptures.csv", "LDS Scriptures")
```

### 3. Run Web App
```bash
python app.py
```

Open your browser to `http://localhost:8080`

### 4. Or Use Command Line
```bash
python run_simple.py
```

## 📖 Reference Search Examples

### Supported Reference Formats
- **Single verse**: `John 3:16`, `1 Nephi 1:1`
- **Whole chapter**: `John 3`, `Alma 32`
- **Verse range**: `John 14:1-6`, `Alma 32:21-23`
- **Section/Chapter**: `D&C 76`, `Moses 1`

### Book Name Variations
- **Full names**: `John`, `Genesis`, `1 Nephi`, `Doctrine and Covenants`
- **Common abbreviations**: `Matt`, `Gen`, `1Ne`, `D&C`, `JS-H`
- **Alternative forms**: `DC`, `1 Corinthians`, `1 Cor`

### Interactive Commands (CLI)
```bash
> ref John 3:16          # Look up specific reference
> chapter John 3         # Get all verses from chapter
> book John              # Get chapter summary
> search faith hope      # Regular text search
```

## 🛠️ Technical Details

### Database
- **SQLite database** for fast local searches
- **Automatic indexing** for optimal performance
- **Duplicate prevention** when loading data

### Search Strategies
1. **Reference parsing** - Detect and parse scripture references
2. **Exact phrase matching** - Find exact text matches
3. **All words present** - Find verses containing all search terms
4. **Any word present** - Broader search for partial matches

### Architecture
- **Flask web framework** for the web interface
- **SQLite** for data storage and fast queries
- **Pandas** for CSV data loading
- **Pure Python** - no external AI dependencies

## 📁 File Structure
```
scripture-search/
├── simple_scripture_search.py   # Core search engine with reference parsing
├── app.py                      # Flask web application
├── run_simple.py              # Command-line runner
├── index.html                 # Web interface template
├── kjvscriptures.csv          # KJV Bible data
├── ldsscriptures.csv          # LDS scriptures data
└── simple_scriptures.db      # SQLite database (auto-created)
```

## 🔍 Usage Examples

### Web Interface
1. **Text search**: Enter search terms like "faith hope charity"
2. **Reference lookup**: Use dropdowns to select book, chapter, verse
3. **Quick references**: Click example buttons for instant lookup
4. **Volume filtering**: Search within specific volumes

### Command Line
```python
from simple_scripture_search import EnhancedScriptureSearch

search = EnhancedScriptureSearch()
search.load_csv_file("kjvscriptures.csv", "KJV Scriptures")

# Reference lookup
results = search.search_text("John 3:16")

# Text search  
results = search.search_text("faith hope charity")

# Interactive mode
search.interactive_mode()
```

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:
- Additional scripture reference formats
- More book name abbreviations
- Enhanced search algorithms
- Additional scripture volumes
- Mobile app development

## 📄 License

This project is open source and available under the MIT License.