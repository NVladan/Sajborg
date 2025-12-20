from app import create_app, db
from models import LagerCategory

def add_polovni_kompjuteri_category():
    """
    Dodaje novu kategoriju 'POLOVNI KOMPJUTERI' u bazu podataka.
    """
    app = create_app()
    with app.app_context():
        # Provjera da li kategorija već postoji
        existing = LagerCategory.query.filter_by(name='POLOVNI KOMPJUTERI', parent_id=None).first()
        
        if existing:
            print("Kategorija 'POLOVNI KOMPJUTERI' već postoji u bazi.")
            return
        
        # Kreiranje nove kategorije
        new_category = LagerCategory(
            name='POLOVNI KOMPJUTERI',
            slug='polovni-kompjuteri',
            parent_id=None,
            sort_order=190  # Između POLOVNE KOMPONENTE (180) i POLOVNI MONITORI (200)
        )
        
        try:
            db.session.add(new_category)
            db.session.commit()
            print("Uspješno dodana kategorija 'POLOVNI KOMPJUTERI'!")
        except Exception as e:
            db.session.rollback()
            print(f"Greška prilikom dodavanja kategorije: {e}")

if __name__ == '__main__':
    add_polovni_kompjuteri_category()
