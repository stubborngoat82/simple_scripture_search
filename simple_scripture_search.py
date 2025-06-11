#!/usr/bin/env python3
"""
Simple Scripture Search - No External AI Dependencies
Uses only built-in Python libraries and pandas for basic text search
"""

import sqlite3
import pandas as pd
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
import math

@dataclass
class ScriptureVerse:
    book: str
    chapter: int
    verse: int
    text: str
    volume: str
    volume_id: int = None
    book_id: int = None
    verse_id: int = None
    lds_url: str = None

class ScriptureReferenceParser:
    """Simple parser for scripture references like 'John 3:16', '1 Nephi 1:1-10', etc."""
    
    def __init__(self):
        # Basic book name mappings for common abbreviations
        self.book_mappings = {
            # Bible - New Testament
            'matt': 'Matthew', 'matthew': 'Matthew', 'mt': 'Matthew',
            'mark': 'Mark', 'mk': 'Mark',
            'luke': 'Luke', 'lk': 'Luke',
            'john': 'John', 'jn': 'John',
            'acts': 'Acts',
            'rom': 'Romans', 'romans': 'Romans',
            '1cor': '1 Corinthians', '1 cor': '1 Corinthians',
            '2cor': '2 Corinthians', '2 cor': '2 Corinthians',
            'gal': 'Galatians', 'galatians': 'Galatians',
            'eph': 'Ephesians', 'ephesians': 'Ephesians',
            'phil': 'Philippians', 'philippians': 'Philippians',
            'col': 'Colossians', 'colossians': 'Colossians',
            'heb': 'Hebrews', 'hebrews': 'Hebrews',
            'james': 'James', 'jas': 'James',
            '1pet': '1 Peter', '1 peter': '1 Peter',
            '2pet': '2 Peter', '2 peter': '2 Peter',
            'rev': 'Revelation', 'revelation': 'Revelation',
            
            # Bible - Old Testament  
            'gen': 'Genesis', 'genesis': 'Genesis',
            'ex': 'Exodus', 'exodus': 'Exodus',
            'ps': 'Psalms', 'psalm': 'Psalms', 'psalms': 'Psalms',
            'prov': 'Proverbs', 'proverbs': 'Proverbs',
            'isa': 'Isaiah', 'isaiah': 'Isaiah',
            'jer': 'Jeremiah', 'jeremiah': 'Jeremiah',
            'dan': 'Daniel', 'daniel': 'Daniel',
            
            # Book of Mormon
            '1ne': '1 Nephi', '1 ne': '1 Nephi', '1 nephi': '1 Nephi', '1nephi': '1 Nephi',
            '2ne': '2 Nephi', '2 ne': '2 Nephi', '2 nephi': '2 Nephi', '2nephi': '2 Nephi',
            '3ne': '3 Nephi', '3 ne': '3 Nephi', '3 nephi': '3 Nephi', '3nephi': '3 Nephi',
            '4ne': '4 Nephi', '4 ne': '4 Nephi', '4 nephi': '4 Nephi', '4nephi': '4 Nephi',
            'jacob': 'Jacob', 'enos': 'Enos', 'jarom': 'Jarom', 'omni': 'Omni',
            'mosiah': 'Mosiah', 'alma': 'Alma', 'hel': 'Helaman', 'helaman': 'Helaman',
            'mormon': 'Mormon', 'morm': 'Mormon', 'ether': 'Ether', 'moroni': 'Moroni', 'moro': 'Moroni',
            
            # Doctrine and Covenants
            'dc': 'Doctrine and Covenants', 'd&c': 'Doctrine and Covenants', 'dnc': 'Doctrine and Covenants',
            'doctrine and covenants': 'Doctrine and Covenants',
\
            # Pearl of Great Price
            'moses': 'Moses', 'abr': 'Abraham', 'abraham': 'Abraham',
            'jsm': 'Joseph Smith—Matthew', 'js-m': 'Joseph Smith—Matthew',
            'jsh': 'Joseph Smith—History', 'js-h': 'Joseph Smith—History',
        }
    
    def is_reference_query(self, query):
        """Check if a query looks like a scripture reference"""
        import re
        # Look for patterns like "Book Chapter:Verse" or "Book Chapter"
        patterns = [
            r'^\w+.*?\s+\d+:\d+',      # Book Chapter:Verse
            r'^\w+.*?\s+\d+$',         # Book Chapter
            r'^\d+\s+\w+.*?\s+\d+',    # Number Book Chapter (e.g., "1 Nephi 1")
        ]
        
        for pattern in patterns:
            if re.match(pattern, query.strip(), re.IGNORECASE):
                return True
        return False
    
    def parse_reference(self, reference):
        """
        Parse a scripture reference and return search parameters.
        
        Examples:
        - "John 3:16" -> [{'book': 'John', 'chapter': 3, 'verse': 16}]
        - "1 Nephi 1" -> [{'book': '1 Nephi', 'chapter': 1}]
        - "Alma 32:21-23" -> [{'book': 'Alma', 'chapter': 32, 'verse_start': 21, 'verse_end': 23}]
        """
        import re
        reference = reference.strip()
        
        # Try different reference patterns
        patterns = [
            # Pattern: "Book Chapter:Verse-Verse" (e.g., "John 3:16-17")
            r'^(.+?)\s+(\d+):(\d+)-(\d+)$',
            # Pattern: "Book Chapter:Verse" (e.g., "John 3:16")
            r'^(.+?)\s+(\d+):(\d+)$',
            # Pattern: "Book Chapter" (e.g., "John 3")
            r'^(.+?)\s+(\d+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, reference, re.IGNORECASE)
            if match:
                groups = match.groups()
                book_name = groups[0].strip()
                
                # Normalize book name
                normalized_book = self.normalize_book_name(book_name)
                if not normalized_book:
                    continue
                
                result = {'book': normalized_book}
                
                if len(groups) >= 2:  # Has chapter
                    result['chapter'] = int(groups[1])
                
                if len(groups) >= 3:  # Has verse
                    result['verse'] = int(groups[2])
                
                if len(groups) >= 4:  # Has verse range
                    result['verse_start'] = int(groups[2])
                    result['verse_end'] = int(groups[3])
                    del result['verse']  # Remove single verse
                
                return [result]
        
        return []
    
    def normalize_book_name(self, book_name):
        """Normalize book name using mappings"""
        book_lower = book_name.lower().strip()
        
        # Direct mapping
        if book_lower in self.book_mappings:
            return self.book_mappings[book_lower]
        
        # Try without spaces/punctuation
        book_clean = re.sub(r'[^\w]', '', book_lower)
        if book_clean in self.book_mappings:
            return self.book_mappings[book_clean]
        
        # Try partial matches for longer names
        for abbrev, full_name in self.book_mappings.items():
            if book_lower == full_name.lower():
                return full_name
        
        return None
    
class SimpleScriptureSearch:
    def __init__(self, db_path: str = "simple_scriptures.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.setup_database()
        self.verses = []
        self.reference_parser = ScriptureReferenceParser()
        
    def setup_database(self):
        """Create the database schema"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scriptures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                volume TEXT NOT NULL,
                book TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL,
                text TEXT NOT NULL,
                volume_id INTEGER,
                book_id INTEGER,
                verse_id INTEGER,
                lds_url TEXT,
                source_file TEXT
            )
        ''')
        
        # Create index for faster searching
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_text ON scriptures(text)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_volume ON scriptures(volume)
        ''')
        
        self.conn.commit()
    
    def load_csv_file(self, file_path: str, source_name: str = None):
        """Load a CSV file with scripture data"""
        if source_name is None:
            source_name = Path(file_path).stem
            
        print(f"\n=== Loading {source_name} from {file_path} ===")
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check if this source has already been loaded
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM scriptures WHERE source_file = ?', (source_name,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  {source_name} already loaded ({existing_count} verses). Skipping to avoid duplicates.")
            print("If you want to reload, delete the database file: simple_scriptures.db")
            return existing_count
        
        df = pd.read_csv(file_path)
        print(f"Found {len(df)} verses in {source_name}")
        
        verses = []
        errors = 0
        duplicates_skipped = 0
        
        for idx, row in df.iterrows():
            try:
                volume = str(row['volume_title']).strip()
                book = str(row['book_title']).strip()
                chapter = int(row['chapter_number'])
                verse_num = int(row['verse_number'])
                text = str(row['scripture_text']).strip()
                
                # Check for existing verse to prevent duplicates
                cursor.execute('''
                    SELECT COUNT(*) FROM scriptures 
                    WHERE volume = ? AND book = ? AND chapter = ? AND verse = ?
                ''', (volume, book, chapter, verse_num))
                
                if cursor.fetchone()[0] > 0:
                    duplicates_skipped += 1
                    continue
                
                verse = ScriptureVerse(
                    volume=volume,
                    book=book,
                    chapter=chapter,
                    verse=verse_num,
                    text=text,
                    volume_id=int(row['volume_id']) if pd.notna(row['volume_id']) else None,
                    book_id=int(row['book_id']) if pd.notna(row['book_id']) else None,
                    verse_id=int(row['verse_id']) if pd.notna(row['verse_id']) else None,
                    lds_url=str(row['book_lds_url']).strip() if pd.notna(row['book_lds_url']) else None,
                )
                
                # Insert into database
                cursor.execute('''
                    INSERT INTO scriptures (
                        volume, book, chapter, verse, text,
                        volume_id, book_id, verse_id, lds_url, source_file
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    verse.volume, verse.book, verse.chapter, verse.verse, verse.text,
                    verse.volume_id, verse.book_id, verse.verse_id, verse.lds_url, source_name
                ))
                
                verses.append(verse)
                
                if (idx + 1) % 5000 == 0:
                    print(f"  Processed {idx + 1} verses...")
                    
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"Error processing row {idx}: {e}")
                continue
        
        self.conn.commit()
        
        if errors > 5:
            print(f"  ... and {errors - 5} more errors")
        
        if duplicates_skipped > 0:
            print(f"⚠️  Skipped {duplicates_skipped} duplicate verses")
        
        print(f"✅ Successfully loaded {len(verses)} new verses from {source_name} with {errors} errors")
        
        # Add to master list
        self.verses.extend(verses)
        
        # Show volume breakdown
        volumes = {}
        for verse in verses:
            volumes[verse.volume] = volumes.get(verse.volume, 0) + 1
        
        print(f"Volume breakdown:")
        for vol, count in volumes.items():
            print(f"  {vol}: {count} verses")
        
        return len(verses)
    
    def search_text(self, query: str, limit: int = 20, volume_filter: str = None) -> List[Dict]:
        """Enhanced text search with reference parsing"""
        
        # Check if query looks like a scripture reference
        if self.reference_parser.is_reference_query(query):
            print(f"🔍 Detected reference query: '{query}'")
            reference_params_list = self.reference_parser.parse_reference(query)
            
            if reference_params_list:
                reference_params = reference_params_list[0]
                print(f"📖 Parsed reference: {reference_params}")
                results = self.search_by_reference(reference_params)
                if results:
                    print(f"✅ Found {len(results)} verses for reference")
                    return results
                else:
                    print(f"❌ No verses found for reference '{query}', falling back to text search")
            else:
                print(f"⚠️  Could not parse reference '{query}', falling back to text search")
        
        # Regular text search (your existing code)
        cursor = self.conn.cursor()
        
        # Clean and prepare query
        query_clean = query.strip().lower()
        query_words = re.findall(r'\b\w+\b', query_clean)
        
        results = []
        
        # Strategy 1: Exact phrase match (highest priority)
        if len(query_clean) > 3:
            sql = '''
                SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url
                FROM scriptures 
                WHERE LOWER(text) LIKE ?
            '''
            params = [f'%{query_clean}%']
            
            if volume_filter:
                sql += ' AND volume = ?'
                params.append(volume_filter)
            
            sql += ' ORDER BY LENGTH(text) LIMIT ?'
            params.append(limit // 2)
            
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                results.append({
                    'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                    'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                    'lds_url': row[8], 'reference': f"{row[1]} {row[2]}:{row[3]}",
                    'match_type': 'exact_phrase', 'score': 100
                })
        
        # Strategy 2: All words present (medium priority)
        if query_words and len(results) < limit:
            conditions = []
            params = []
            
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    conditions.append('LOWER(text) LIKE ?')
                    params.append(f'%{word}%')
            
            if conditions:
                sql = f'''
                    SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url
                    FROM scriptures 
                    WHERE {' AND '.join(conditions)}
                '''
                
                if volume_filter:
                    sql += ' AND volume = ?'
                    params.append(volume_filter)
                
                sql += ' ORDER BY LENGTH(text) LIMIT ?'
                params.append(limit - len(results))
                
                cursor.execute(sql, params)
                for row in cursor.fetchall():
                    # Avoid duplicates
                    ref = f"{row[1]} {row[2]}:{row[3]}"
                    if not any(r['reference'] == ref for r in results):
                        results.append({
                            'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                            'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                            'lds_url': row[8], 'reference': ref,
                            'match_type': 'all_words', 'score': 80
                        })
        
        # Strategy 3: Any word present (lower priority)
        if query_words and len(results) < limit:
            word_conditions = []
            params = []
            
            for word in query_words:
                if len(word) > 2:
                    word_conditions.append('LOWER(text) LIKE ?')
                    params.append(f'%{word}%')
            
            if word_conditions:
                sql = f'''
                    SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url
                    FROM scriptures 
                    WHERE ({' OR '.join(word_conditions)})
                '''
                
                if volume_filter:
                    sql += ' AND volume = ?'
                    params.append(volume_filter)
                
                sql += ' ORDER BY LENGTH(text) LIMIT ?'
                params.append(limit - len(results))
                
                cursor.execute(sql, params)
                for row in cursor.fetchall():
                    # Avoid duplicates
                    ref = f"{row[1]} {row[2]}:{row[3]}"
                    if not any(r['reference'] == ref for r in results):
                        results.append({
                            'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                            'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                            'lds_url': row[8], 'reference': ref,
                            'match_type': 'any_word', 'score': 60
                        })
        
        # Calculate relevance scores
        for result in results:
            result['relevance_score'] = self._calculate_relevance(result['text'], query_words)
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:limit]
    
    def _calculate_relevance(self, text: str, query_words: List[str]) -> float:
        """Calculate relevance score for text based on query words"""
        text_lower = text.lower()
        score = 0
        
        for word in query_words:
            if len(word) > 2:
                # Count occurrences
                count = text_lower.count(word.lower())
                if count > 0:
                    # Boost score based on word frequency and length
                    word_score = count * (1 + len(word) / 10)
                    score += word_score
        
        # Normalize by text length to favor more focused verses
        if len(text) > 0:
            score = score / math.log(len(text) + 1)
        
        return score
    
    def get_statistics(self):
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        # Total verses
        cursor.execute('SELECT COUNT(*) FROM scriptures')
        total_verses = cursor.fetchone()[0]
        
        # Volumes
        cursor.execute('SELECT volume, COUNT(*) FROM scriptures GROUP BY volume ORDER BY volume')
        volume_stats = cursor.fetchall()
        
        # Books per volume
        cursor.execute('SELECT volume, COUNT(DISTINCT book) FROM scriptures GROUP BY volume')
        books_per_volume = dict(cursor.fetchall())
        
        print("\n=== Scripture Database Statistics ===")
        print(f"Total verses: {total_verses:,}")
        print(f"Volumes: {len(volume_stats)}")
        
        for volume, verse_count in volume_stats:
            book_count = books_per_volume.get(volume, 0)
            print(f"  {volume}: {verse_count:,} verses in {book_count} books")
        
        return {
            'total_verses': total_verses,
            'volumes': [v[0] for v in volume_stats],
            'volume_stats': dict(volume_stats),
            'books_per_volume': books_per_volume
        }
    
    def interactive_mode(self):
        """Interactive command-line interface"""
        print("\n🔍 Simple Scripture Search - Interactive Mode")
        print("Commands:")
        print("  'search <query>' - Search all scriptures")
        print("  'filter <volume> <query>' - Search within specific volume")
        print("  'stats' - Show database statistics")
        print("  'quit' - Exit")
        print("-" * 50)
        
        # Get available volumes for help
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT volume FROM scriptures ORDER BY volume')
        volumes = [row[0] for row in cursor.fetchall()]
        print(f"Available volumes: {', '.join(volumes)}")
        
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            elif user_input.lower() == 'stats':
                self.get_statistics()
            
            elif user_input.startswith('search '):
                query = user_input[7:]
                try:
                    results = self.search_text(query, limit=10)
                    
                    if results:
                        print(f"\nFound {len(results)} results for '{query}':")
                        for i, result in enumerate(results, 1):
                            print(f"\n{i}. {result['volume']} - {result['reference']}")
                            print(f"   {result['text']}")
                            print(f"   Match: {result['match_type']}, Score: {result['relevance_score']:.2f}")
                            if result['lds_url']:
                                print(f"   URL: {result['lds_url']}")
                    else:
                        print(f"\nNo results found for '{query}'. Try different search terms.")
                        
                except Exception as e:
                    print(f"Error in search: {e}")
            
            elif user_input.startswith('filter '):
                # Better parsing for quoted volume names
                filter_text = user_input[7:].strip()
                
                # Handle quoted volume names
                if filter_text.startswith('"') and '" ' in filter_text:
                    # Find the closing quote
                    end_quote = filter_text.find('" ', 1)
                    if end_quote != -1:
                        volume = filter_text[1:end_quote]
                        query = filter_text[end_quote + 2:].strip()
                    else:
                        volume, query = None, None
                else:
                    # Handle unquoted (fallback to space split)
                    parts = filter_text.split(' ', 1)
                    if len(parts) == 2:
                        volume, query = parts[0], parts[1]
                    else:
                        volume, query = None, None
                
                if volume and query:
                    # Map common variations to exact volume names
                    volume_mapping = {
                        'NewTestament': 'New Testament',
                        'New_Testament': 'New Testament',
                        'OldTestament': 'Old Testament', 
                        'Old_Testament': 'Old Testament',
                        'BookofMormon': 'Book of Mormon',
                        'Book_of_Mormon': 'Book of Mormon',
                        'DoctrineandCovenants': 'Doctrine and Covenants',
                        'Doctrine_and_Covenants': 'Doctrine and Covenants',
                        'PearlofGreatPrice': 'Pearl of Great Price',
                        'Pearl_of_Great_Price': 'Pearl of Great Price'
                    }
                    
                    # Use mapping if available
                    mapped_volume = volume_mapping.get(volume, volume)
                    
                    try:
                        results = self.search_text(query, limit=10, volume_filter=mapped_volume)
                        
                        if results:
                            print(f"\nFound {len(results)} results for '{query}' in {mapped_volume}:")
                            for i, result in enumerate(results, 1):
                                print(f"\n{i}. {result['reference']}")
                                print(f"   {result['text']}")
                                print(f"   Score: {result['relevance_score']:.2f}")
                        else:
                            print(f"\nNo results found for '{query}' in {mapped_volume}.")
                            print(f"Available volumes: {', '.join(volumes)}")
                            
                    except Exception as e:
                        print(f"Error in filtered search: {e}")
                else:
                    print("Usage: filter <volume> <query>")
                    print('Examples:')
                    print('  filter "New Testament" love')
                    print('  filter NewTestament love')
                    print('  filter "Book of Mormon" faith')
                    print(f"Available volumes: {', '.join(volumes)}")
            
            else:
                print("Unknown command. Use 'search <query>', 'filter <volume> <query>', 'stats', or 'quit'")

    def search_by_reference(self, reference_params):
        """Search by specific scripture reference"""
        cursor = self.conn.cursor()
        
        # Build SQL query based on reference parameters
        sql = 'SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url FROM scriptures WHERE book = ?'
        params = [reference_params['book']]
        
        if 'chapter' in reference_params:
            sql += ' AND chapter = ?'
            params.append(reference_params['chapter'])
        
        if 'verse' in reference_params:
            sql += ' AND verse = ?'
            params.append(reference_params['verse'])
        elif 'verse_start' in reference_params and 'verse_end' in reference_params:
            sql += ' AND verse BETWEEN ? AND ?'
            params.extend([reference_params['verse_start'], reference_params['verse_end']])
        
        sql += ' ORDER BY chapter, verse'
        
        cursor.execute(sql, params)
        results = []
        
        for row in cursor.fetchall():
            results.append({
                'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                'lds_url': row[8], 'reference': f"{row[1]} {row[2]}:{row[3]}",
                'match_type': 'reference_lookup', 'relevance_score': 100.0
            })
        
        return results

def test_references():
    """Test the reference search functionality"""
    search = SimpleScriptureSearch()
    
    # Test some references
    test_refs = ["John 3:16", "1 Nephi 1:1", "D&C 76", "Alma 32:21-23"]
    
    for ref in test_refs:
        print(f"\n🔍 Testing: {ref}")
        if search.reference_parser.is_reference_query(ref):
            parsed = search.reference_parser.parse_reference(ref)
            if parsed:
                results = search.search_by_reference(parsed[0])
                print(f"   Found {len(results)} results")
                for result in results[:2]:  # Show first 2
                    print(f"   📖 {result['reference']}: {result['text'][:100]}...")
            else:
                print("   ❌ Could not parse reference")
        else:
            print("   ⚠️  Not detected as reference")

# Uncomment this line to test:
test_references()

def main():
    """Main function"""
    print("🔍 Simple Scripture Search System")
    print("=" * 40)
    print("This version uses only basic text search - no AI dependencies required!")
    
    # Initialize the system
    search = SimpleScriptureSearch()
    
    print("\nTo load your scripture data:")
    print("search.load_csv_file('kjvscriptures.csv', 'KJV Scriptures')")
    print("search.load_csv_file('ldsscriptures.csv', 'LDS Scriptures')")
    print("search.interactive_mode()")




if __name__ == "__main__":
    main()