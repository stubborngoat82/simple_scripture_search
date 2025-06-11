#!/usr/bin/env python3
"""
Scripture Search Web Application - Fixed Threading Issue
A Flask web interface for the Simple Scripture Search system
"""

import sys
import os
import sqlite3
from threading import Lock
print("🔍 Starting Scripture Search Web App...")

try:
    from flask import Flask, render_template, request, jsonify, g
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import error: {e}")
    sys.exit(1)

try:
    from simple_scripture_search import SimpleScriptureSearch
    print("✅ SimpleScriptureSearch imported successfully")
except ImportError as e:
    print(f"❌ SimpleScriptureSearch import error: {e}")
    print("Make sure simple_scripture_search.py is in the same directory")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = 'scripture_search_secret_key_2024'

# Database path
DATABASE_PATH = 'simple_scriptures.db'
init_lock = Lock()
data_loaded = False

def get_db():
    """Get a database connection for the current thread"""
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of each request"""
    if hasattr(g, 'db'):
        g.db.close()

def initialize_data_once():
    """Initialize data only once, thread-safely"""
    global data_loaded
    
    with init_lock:
        if not data_loaded:
            print("Initializing scripture data...")
            
            # Create a temporary search system just for loading data
            temp_search = SimpleScriptureSearch()
            
            # Check if we need to load CSV files
            stats = temp_search.get_statistics()
            print(f"Database has {stats['total_verses']} verses")
            
            if stats['total_verses'] == 0:
                print("Loading CSV files...")
                csv_files = [
                    ('kjvscriptures.csv', 'KJV Scriptures'),
                    ('ldsscriptures.csv', 'LDS Scriptures')
                ]
                
                for csv_file, name in csv_files:
                    if os.path.exists(csv_file):
                        try:
                            print(f"Loading {csv_file}...")
                            temp_search.load_csv_file(csv_file, name)
                            print(f"✅ Loaded {name}")
                        except Exception as e:
                            print(f"❌ Error loading {csv_file}: {e}")
                    else:
                        print(f"⚠️  CSV file not found: {csv_file}")
            
            data_loaded = True
            print("✅ Data initialization complete")

def search_scriptures_thread_safe(query, limit=20, volume_filter=None):
    """Enhanced thread-safe scripture search with reference parsing"""
    db = get_db()
    
    # Create search instance for reference parsing
    from simple_scripture_search import SimpleScriptureSearch, ScriptureReferenceParser
    parser = ScriptureReferenceParser()
    
    # Check if query looks like a scripture reference
    if parser.is_reference_query(query):
        print(f"🔍 Detected reference query: '{query}'")
        reference_params_list = parser.parse_reference(query)
        
        if reference_params_list:
            reference_params = reference_params_list[0]
            print(f"📖 Parsed reference: {reference_params}")
            
            # Build SQL query based on reference parameters
            cursor = db.cursor()
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
            
            if volume_filter and volume_filter != 'all':
                sql += ' AND volume = ?'
                params.append(volume_filter)
            
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
            
            if results:
                print(f"✅ Found {len(results)} verses for reference")
                return results
            else:
                print(f"❌ No verses found for reference '{query}', falling back to text search")
        else:
            print(f"⚠️  Could not parse reference '{query}', falling back to text search")
    
    # Fall back to regular text search (your existing code)
    cursor = db.cursor()
    
    # Clean and prepare query
    import re
    query_clean = query.strip().lower()
    query_words = re.findall(r'\b\w+\b', query_clean)
    
    results = []
    
    # Strategy 1: Exact phrase match
    if len(query_clean) > 3:
        sql = '''
            SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url
            FROM scriptures 
            WHERE LOWER(text) LIKE ?
        '''
        params = [f'%{query_clean}%']
        
        if volume_filter and volume_filter != 'all':
            sql += ' AND volume = ?'
            params.append(volume_filter)
        
        sql += ' ORDER BY LENGTH(text) LIMIT ?'
        params.append(limit)
        
        cursor.execute(sql, params)
        for row in cursor.fetchall():
            results.append({
                'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                'lds_url': row[8], 'reference': f"{row[1]} {row[2]}:{row[3]}",
                'match_type': 'exact_phrase', 'relevance_score': 10.0
            })
    
    # Strategy 2: All words present (only if we need more results)
    if query_words and len(results) < limit:
        conditions = []
        params = []
        
        for word in query_words:
            if len(word) > 2:
                conditions.append('LOWER(text) LIKE ?')
                params.append(f'%{word}%')
        
        if conditions:
            sql = f'''
                SELECT volume, book, chapter, verse, text, volume_id, book_id, verse_id, lds_url
                FROM scriptures 
                WHERE {' AND '.join(conditions)}
            '''
            
            if volume_filter and volume_filter != 'all':
                sql += ' AND volume = ?'
                params.append(volume_filter)
            
            sql += ' ORDER BY LENGTH(text) LIMIT ?'
            params.append(limit - len(results))
            
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                ref = f"{row[1]} {row[2]}:{row[3]}"
                if not any(r['reference'] == ref for r in results):
                    results.append({
                        'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                        'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                        'lds_url': row[8], 'reference': ref,
                        'match_type': 'all_words', 'relevance_score': 8.0
                    })
    
    # Calculate better relevance scores
    for result in results:
        score = 0
        text_lower = result['text'].lower()
        for word in query_words:
            if len(word) > 2:
                count = text_lower.count(word.lower())
                if count > 0:
                    score += count * (1 + len(word) / 10)
        
        import math
        if len(result['text']) > 0:
            score = score / math.log(len(result['text']) + 1)
        
        result['relevance_score'] = round(score, 2)
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    db = get_db()
    cursor = db.cursor()
    
    # Clean and prepare query
    import re
    query_clean = query.strip().lower()
    query_words = re.findall(r'\b\w+\b', query_clean)
    
    results = []
    
    # Strategy 1: Exact phrase match
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
        params.append(limit)  # Changed from limit // 2 to full limit
        
        cursor.execute(sql, params)
        for row in cursor.fetchall():
            results.append({
                'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                'lds_url': row[8], 'reference': f"{row[1]} {row[2]}:{row[3]}",
                'match_type': 'exact_phrase', 'relevance_score': 10.0
            })
    
    # Strategy 2: All words present (only if we need more results)
    if query_words and len(results) < limit:
        conditions = []
        params = []
        
        for word in query_words:
            if len(word) > 2:
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
                ref = f"{row[1]} {row[2]}:{row[3]}"
                if not any(r['reference'] == ref for r in results):
                    results.append({
                        'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                        'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                        'lds_url': row[8], 'reference': ref,
                        'match_type': 'all_words', 'relevance_score': 8.0
                    })
    
    # Strategy 3: Any word present (only if we still need more results)
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
                ref = f"{row[1]} {row[2]}:{row[3]}"
                if not any(r['reference'] == ref for r in results):
                    results.append({
                        'volume': row[0], 'book': row[1], 'chapter': row[2], 'verse': row[3],
                        'text': row[4], 'volume_id': row[5], 'book_id': row[6], 'verse_id': row[7],
                        'lds_url': row[8], 'reference': ref,
                        'match_type': 'any_word', 'relevance_score': 6.0
                    })
    
    # Calculate better relevance scores
    for result in results:
        score = 0
        text_lower = result['text'].lower()
        for word in query_words:
            if len(word) > 2:
                count = text_lower.count(word.lower())
                if count > 0:
                    score += count * (1 + len(word) / 10)
        
        import math
        if len(result['text']) > 0:
            score = score / math.log(len(result['text']) + 1)
        
        result['relevance_score'] = round(score, 2)
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return results[:limit]

def get_stats_thread_safe():
    """Thread-safe statistics"""
    db = get_db()
    cursor = db.cursor()
    
    # Total verses
    cursor.execute('SELECT COUNT(*) FROM scriptures')
    total_verses = cursor.fetchone()[0]
    
    # Volumes
    cursor.execute('SELECT volume, COUNT(*) FROM scriptures GROUP BY volume ORDER BY volume')
    volume_stats = cursor.fetchall()
    
    # Books per volume
    cursor.execute('SELECT volume, COUNT(DISTINCT book) FROM scriptures GROUP BY volume')
    books_per_volume = dict(cursor.fetchall())
    
    return {
        'total_verses': total_verses,
        'volumes': [v[0] for v in volume_stats],
        'volume_stats': dict(volume_stats),
        'books_per_volume': books_per_volume
    }

@app.route('/')
def index():
    """Main search page"""
    print("📄 Serving index page...")
    
    try:
        initialize_data_once()
        stats = get_stats_thread_safe()
        print(f"Stats: {stats['total_verses']} verses")
        return render_template('index.html', stats=stats)
        
    except Exception as e:
        print(f"❌ Error in index route: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading page: {e}", 500

@app.route('/search')
def search():
    """Handle search requests"""
    print("🔍 Search request received...")
    
    try:
        initialize_data_once()
        
        query = request.args.get('q', '').strip()
        volume = request.args.get('volume', 'all')
        limit = int(request.args.get('limit', 20))  # Changed default from 10 to 20
        
        print(f"Query: '{query}', Volume: '{volume}', Limit: {limit}")
        
        if not query:
            return jsonify({'error': 'No search query provided', 'results': []})
        
        # Use volume filter if specified
        volume_filter = None if volume == 'all' else volume
        
        results = search_scriptures_thread_safe(query, limit=limit, volume_filter=volume_filter)
        print(f"Found {len(results)} results")
        
        # Format results for JSON response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'volume': result['volume'],
                'book': result['book'],
                'chapter': result['chapter'],
                'verse': result['verse'],
                'text': result['text'],
                'reference': result['reference'],
                'score': result['relevance_score'],
                'match_type': result['match_type'],
                'lds_url': result.get('lds_url', '')
            })
        
        return jsonify({
            'query': query,
            'volume': volume,
            'total_results': len(formatted_results),
            'results': formatted_results
        })
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Search error: {str(e)}', 'results': []})

@app.route('/stats')
def stats():
    """Get database statistics"""
    try:
        initialize_data_once()
        stats = get_stats_thread_safe()
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Stats error: {str(e)}'})

@app.route('/test')
def test():
    """Test route to check if Flask is working"""
    return "🎉 Flask is working! The web app is running correctly."

@app.route('/debug_reference')
def debug_reference():
    """Debug route to test reference parsing"""
    try:
        query = request.args.get('q', 'John 3:16')
        
        # Test the reference parser
        from simple_scripture_search import SimpleScriptureSearch
        search = SimpleScriptureSearch()
        
        is_ref = search.reference_parser.is_reference_query(query)
        parsed = search.reference_parser.parse_reference(query) if is_ref else None
        
        return jsonify({
            'query': query,
            'is_reference': is_ref,
            'parsed': parsed,
            'debug': 'Reference parser test'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'debug': 'Debug failed'})

if __name__ == '__main__':
    try:
        print("\n🕊️ Scripture Search Web Application")
        print("=" * 50)
        print("Starting web server...")
        print("🌐 Open your browser to: http://localhost:8080")
        print("🧪 Test page: http://localhost:8080/test")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=8080)
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()