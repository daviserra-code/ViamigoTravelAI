#!/usr/bin/env python3
"""
Test del sistema di routing dinamico
"""

from dynamic_routing import dynamic_router

def test_personalized_routing():
    """Testa il routing personalizzato per diversi scenari"""
    
    test_cases = [
        {
            'name': 'Roma: Trastevere → Villa Borghese',
            'start': 'Trastevere',
            'end': 'Villa Borghese', 
            'city': 'Roma'
        },
        {
            'name': 'Torino: Porta Nuova → Parco Valentino',
            'start': 'Porta Nuova',
            'end': 'Parco del Valentino',
            'city': 'Torino'
        },
        {
            'name': 'Milano: Brera → Navigli',
            'start': 'Brera',
            'end': 'Navigli',
            'city': 'Milano'
        },
        {
            'name': 'Genova: Porto Antico → Nervi',
            'start': 'Porto Antico',
            'end': 'Nervi',
            'city': 'Genova'
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 TEST: {test['name']}")
        print("=" * 50)
        
        try:
            itinerary = dynamic_router.generate_personalized_itinerary(
                test['start'], test['end'], test['city']
            )
            
            if itinerary:
                print(f"✅ Generato itinerario con {len(itinerary)} tappe")
                for i, step in enumerate(itinerary[:4]):  # Prime 4 tappe
                    if step.get('type') == 'tip':
                        print(f"   💡 {step['title']}: {step['description']}")
                    else:
                        time = step.get('time', 'N/A')
                        title = step.get('title', 'N/A')
                        coords = step.get('coordinates', [0,0])
                        print(f"   {time} - {title} [{coords[0]:.4f}, {coords[1]:.4f}]")
            else:
                print("❌ Nessun itinerario generato")
                
        except Exception as e:
            print(f"❌ Errore: {e}")

if __name__ == "__main__":
    test_personalized_routing()