# 🛠️ Setup Instructions

Complete setup guide for the Simple Scripture Search application.

## 📋 Prerequisites

- **Python 3.8+** (Check with `python3 --version`)
- **Git** (for cloning the repository)
- **Scripture CSV data files** (see Data Requirements below)

## 🚀 Installation Methods

### Method 1: Quick Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/stubborngoat82/simple_scripture_search.git
cd simple_scripture_search

# 2. Run the setup script
chmod +x setup.sh
./setup.sh
```

### Method 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/stubborngoat82/simple_scripture_search.git
cd simple_scripture_search

# 2. Create virtual environment
python3 -m venv scripture-env

# 3. Activate virtual environment
# On macOS/Linux:
source scripture-env/bin/activate
# On Windows:
scripture-env\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Add your CSV data files (see below)

# 6. Run the application
python3 app.py
```

## 📊 Data Requirements

### Required CSV Files

You need two CSV files in your project directory:

1. **`kjvscriptures.csv`** - King James Version Bible
2. **`ldsscriptures.csv`** - LDS Standard Works (including Book of Mormon, D&C, Pearl of Great Price)

### CSV Format

Each CSV file must have these columns:

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `volume_id` | Integer | Unique volume identifier | 1 |
| `book_id` | Integer | Unique book identifier | 45 |
| `chapter_id` | Integer | Unique chapter identifier | 1234 |
| `verse_id` | Integer | Unique verse identifier | 56789 |
| `volume_title` | String | Volume name | "Book of Mormon" |
| `book_title` | String | Book name | "1 Nephi" |
| `volume_long_title` | String | Full volume title | "The Book of Mormon: Another Testament of Jesus Christ" |
| `book_long_title` | String | Full book title | "The First Book of Nephi" |
| `volume_subtitle` | String | Volume subtitle (optional) | "" |
| `book_subtitle` | String | Book subtitle (optional) | "" |
| `volume_short_title` | String | Short volume name | "BoM" |
| `book_short_title` | String | Short book name | "1 Ne." |
| `volume_lds_url` | String | Volume URL path | "bofm" |
| `book_lds_url` | String | Book URL path | "bofm/1-ne" |
| `chapter_number` | Integer | Chapter number | 3 |
| `verse_number` | Integer | Verse number | 7 |
| `scripture_text` | String | Full verse text | "And it came to pass that I, Nephi..." |
| `verse_title` | String | Verse title (optional) | "" |
| `verse_short_title` | String | Short verse title (optional) | "" |

### Sample CSV Row

```csv
volume_id,book_id,chapter_id,verse_id,volume_title,book_title,volume_long_title,book_long_title,volume_subtitle,book_subtitle,volume_short_title,book_short_title,volume_lds_url,book_lds_url,chapter_number,verse_number,scripture_text,verse_title,verse_short_title
3,67,1234,56789,"Book of Mormon","1 Nephi","The Book of Mormon: Another Testament of Jesus Christ","The First Book of Nephi","","","BoM","1 Ne.","bofm","bofm/1-ne",3,7,"And it came to pass that I, Nephi, said unto my father: I will go and do the things which the Lord hath commanded, for I know that the Lord giveth no commandments unto the children of men, save he shall prepare a way for them that they may accomplish the thing which he commandeth them.","",""
```

## 🔧 Configuration Options

### Environment Variables

Create a `.env` file in your project root (optional):

```env
# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Database configuration
DATABASE_PATH=simple_scriptures.db

# Server configuration
HOST=localhost
PORT=8080
```

### Application Settings

Edit these settings in `app.py`:

```python
# Server settings
HOST = '0.0.0.0'  # Change to 'localhost' for local-only access
PORT = 8080       # Change port if needed

# Database settings
DATABASE_PATH = 'simple_scriptures.db'  # Change database location

# Search settings
DEFAULT_SEARCH_LIMIT = 20  # Number of results per search
```

## 🧪 Testing the Installation

### 1. Basic Functionality Test

```bash
# Start the application
python3 app.py

# You should see:
# ✅ Flask imported successfully
# ✅ SimpleScriptureSearch imported successfully
# 🌐 Open your browser to: http://localhost:8080
```

### 2. Web Interface Test

1. Open `http://localhost:8080` in your browser
2. You should see the scripture search interface
3. Try a search like "faith" or "love"
4. Verify results appear with proper formatting

### 3. Command Line Test

```bash
# Test the command line interface
python3 run_simple.py

# Try these commands:
# > stats
# > search faith
# > filter "New Testament" love
# > quit
```

## 🐛 Troubleshooting

### Common Issues

#### Issue: "No module named 'flask'"
**Solution:**
```bash
# Make sure virtual environment is activated
source scripture-env/bin/activate
pip install -r requirements.txt
```

#### Issue: "No verses loaded" or "0 total verses"
**Solutions:**
1. **Check CSV files exist:**
   ```bash
   ls -la *.csv
   ```
2. **Verify CSV format:**
   ```bash
   head -1 kjvscriptures.csv  # Should show column headers
   ```
3. **Check file permissions:**
   ```bash
   chmod 644 *.csv
   ```

#### Issue: "Address already in use" (Port 8080)
**Solutions:**
1. **Kill existing processes:**
   ```bash
   lsof -ti:8080 | xargs kill
   ```
2. **Use different port:**
   ```bash
   # Edit app.py, change the last line to:
   app.run(debug=True, host='0.0.0.0', port=8081)
   ```

#### Issue: Database locked error
**Solution:**
```bash
# Remove database file and restart
rm simple_scriptures.db
python3 app.py
```

#### Issue: Slow search performance
**Solutions:**
1. **Check database size:**
   ```bash
   ls -lh simple_scriptures.db
   ```
2. **Rebuild database:**
   ```bash
   rm simple_scriptures.db
   python3 app.py  # Will rebuild from CSV
   ```

### Performance Optimization

#### For Large Datasets (100,000+ verses)

1. **Increase batch size** in `simple_scripture_search.py`:
   ```python
   # In load_csv_file method, change:
   if (idx + 1) % 10000 == 0:  # Was 5000
   ```

2. **Optimize search limits**:
   ```python
   # In search functions, adjust limits:
   limit = min(limit, 50)  # Cap at 50 results
   ```

#### Memory Usage

- **Expected RAM usage:** ~50MB per 10,000 verses
- **Database size:** ~5MB per 10,000 verses
- **Recommend minimum:** 4GB RAM for 100,000+ verses

## 🔒 Security Notes

### For Production Deployment

1. **Set proper Flask configuration:**
   ```python
   app.config['SECRET_KEY'] = 'your-secret-key-here'
   app.config['DEBUG'] = False
   ```

2. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8080 app:app
   ```

3. **Secure file permissions:**
   ```bash
   chmod 644 *.py *.csv
   chmod 755 .
   ```

### Data Privacy

- Scripture CSV files contain only public domain religious texts
- No personal data is collected or stored
- Local SQLite database contains only scripture content
- No external API calls made (except for OpenAI if enabled)

## 📚 Additional Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLite Documentation:** https://www.sqlite.org/docs.html
- **Python Virtual Environments:** https://docs.python.org/3/tutorial/venv.html

## 🆘 Getting Help

If you encounter issues not covered here:

1. **Check the main README.md** for basic troubleshooting
2. **Search existing issues:** https://github.com/stubborngoat82/simple_scripture_search/issues
3. **Create a new issue** with:
   - Your operating system and Python version
   - Complete error message
   - Steps to reproduce the problem
   - Screenshots if applicable

---

**Setup complete! Enjoy studying the scriptures! 🕊️**