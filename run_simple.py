from simple_scripture_search import SimpleScriptureSearch

def main():
    print("🔍 Simple Scripture Search System")
    print("=" * 40)
    
    # Initialize the system (only needs pandas!)
    search = SimpleScriptureSearch()
    
    # Load your data
    print("Loading scripture data...")
    search.load_csv_file("kjvscriptures.csv", "KJV Scriptures")
    search.load_csv_file("ldsscriptures.csv", "LDS Scriptures")
    
    # Show statistics
    search.get_statistics()
    
    # Start interactive mode
    search.interactive_mode()

if __name__ == "__main__":
    main()