"""Carga idempotente de catalogo demostrativo para el marketplace local.

Uso: python -m scripts.seed_demo_catalog
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, Product, ProductCategory, ProductImage, ProductVariant, StockLevel, Store, Warehouse
from app.models.catalog import ProductStatus


CATEGORIES = [
    ("pulseras", "Pulseras"),
    ("collares", "Collares"),
    ("aretes", "Aretes"),
    ("anillos", "Anillos"),
    ("tobilleras", "Tobilleras"),
    ("sets", "Sets y Packs"),
]

PRODUCTS = [
    ("pulsera-esencia-perla", "Pulsera Esencia Perla", "pulseras", 48900, 62000, 24, "Perla", "Perlas de rio con dijes de millefiori y bano de oro.", 1),
    ("collar-burbuja-candy", "Collar Burbuja Candy", "collares", 56900, None, 12, "Rosa", "Cuentas tipo burbuja en tonos pastel con cierre ajustable.", 2),
    ("pulsera-jardin-millefiori", "Pulsera Jardin Millefiori", "pulseras", 51900, 58000, 8, "Multicolor", "Dije de flor millefiori entre perlas y cuentas de colores.", 3),
    ("aretes-gota-lima", "Aretes Gota Lima", "aretes", 32900, None, 30, "Verde", "Aretes ligeros en gota con acento verde lima.", 4),
    ("set-trio-singular", "Set Trio Singular", "sets", 99900, 138000, 6, "Multicolor", "Tres pulseras coordinadas para apilar y regalar.", 5),
    ("tobillera-marea", "Tobillera Marea", "tobilleras", 29900, None, 18, "Turquesa", "Tobillera con dije de concha para el verano.", 1),
    ("anillo-set-petalo", "Set Anillos Petalo", "anillos", 38900, 45000, 21, "Dorado", "Cuatro anillos ajustables para combinar.", 2),
    ("collar-perla-corazon", "Collar Perla Corazon", "collares", 61900, None, 9, "Perla", "Perlas con un dije de corazon dorado al centro.", 3),
]


def main() -> None:
    with SessionLocal() as db:
        store = db.scalar(select(Store).where(Store.slug == "singular"))
        if store is None:
            store = Store(slug="singular", name="Singular", description="Accesorios hechos con cuidado.", active=True)
            db.add(store)
            db.flush()

        warehouse = db.scalar(select(Warehouse).where(Warehouse.store_id == store.id, Warehouse.is_default.is_(True)))
        if warehouse is None:
            warehouse = Warehouse(store_id=store.id, name="Bodega principal", city="Bogota", is_default=True, active=True)
            db.add(warehouse)
            db.flush()

        category_by_slug = {}
        for position, (slug, name) in enumerate(CATEGORIES):
            category = db.scalar(select(Category).where(Category.store_id == store.id, Category.slug == slug))
            if category is None:
                category = Category(store_id=store.id, slug=slug, name=name, sort_order=position, active=True)
                db.add(category)
                db.flush()
            category_by_slug[slug] = category

        for slug, name, category_slug, price, compare_at, stock, color, description, image_number in PRODUCTS:
            product = db.scalar(select(Product).where(Product.store_id == store.id, Product.slug == slug))
            if product is None:
                product = Product(store_id=store.id, slug=slug, name=name, short_desc=description, description=description, status=ProductStatus.active)
                db.add(product)
                db.flush()
                db.add(ProductCategory(product_id=product.id, category_id=category_by_slug[category_slug].id))
                db.add(ProductImage(product_id=product.id, url=f"/products/p{image_number}.jpg", alt=name, sort_order=0))
                variant = ProductVariant(product_id=product.id, sku=f"SNG-{slug[:12].upper()}", color=color, price=price, compare_at=compare_at, active=True)
                db.add(variant)
                db.flush()
                db.add(StockLevel(variant_id=variant.id, warehouse_id=warehouse.id, quantity=stock, threshold=3))

        db.commit()
    print(f"Catalogo demostrativo listo: {len(PRODUCTS)} productos.")


if __name__ == "__main__":
    main()
