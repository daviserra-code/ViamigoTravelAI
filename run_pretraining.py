#!/usr/bin/env python3
"""
Script per eseguire il pre-training del database
Usage: python run_pretraining.py [italia|europa|mondiale]
"""

import sys
from pretraining_system import PretrainingSystem

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pretraining.py [italia|europa|mondiale|stats|clear]")
        return
    
    command = sys.argv[1].lower()
    pretrainer = PretrainingSystem()
    
    if command in ['italia', 'europa', 'mondiale']:
        print(f"🚀 Avvio pre-training livello: {command}")
        processed = pretrainer.run_pretraining(command)
        print(f"✅ Completato! Processati {processed} luoghi")
        
    elif command == 'stats':
        stats = pretrainer.get_cache_stats()
        print("📊 Statistiche Cache:")
        print(f"  Totale luoghi: {stats['total_cached']}")
        for level, count in stats['by_level'].items():
            print(f"  {level}: {count} luoghi")
            
    elif command == 'clear':
        level = sys.argv[2] if len(sys.argv) > 2 else None
        deleted = pretrainer.clear_cache(level)
        print(f"🗑️ Eliminati {deleted} record dalla cache")
        
    else:
        print("Comando non riconosciuto. Usa: italia, europa, mondiale, stats, clear")

if __name__ == "__main__":
    main()