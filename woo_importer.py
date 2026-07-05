"""
woo_importer.py
WooCommerceXMLImporter — parse a WordPress/WooCommerce product-export XML
and upsert products into the greed database.
"""
from __future__ import annotations

import logging
import requests
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from lxml import etree

if TYPE_CHECKING:
    import database as db

log = logging.getLogger(__name__)

# WooCommerce RSS/XML namespaces
NS = {
    "wp":      "http://wordpress.org/export/1.2/",
    "wc":      "http://www.woothemes.com/woo-commerce/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}


class WooCommerceXMLImporter:
    """
    Parse a WooCommerce product-export XML file and import/update products
    in the greed database.

    Usage:
        importer = WooCommerceXMLImporter(session, xml_path="products.xml")
        count = importer.import_products()
    """

    def __init__(self, session, xml_path: str = "products.xml"):
        self.session = session
        self.xml_path = Path(xml_path)

    # ── Public API ────────────────────────────────────────────────────────
    def import_products(self) -> int:
        """Parse XML and upsert products. Returns number of products processed."""
        if not self.xml_path.exists():
            log.error(f"XML file not found: {self.xml_path}")
            return 0
        try:
            tree = etree.parse(str(self.xml_path))
        except etree.XMLSyntaxError as exc:
            log.error(f"XML parse error: {exc}")
            return 0

        root = tree.getroot()
        items = root.findall(".//item")
        count = 0
        for item in items:
            post_type = self._get_text(item, "wp:post_type")
            if post_type != "product":
                continue
            try:
                self._process_item(item)
                count += 1
            except Exception as exc:
                log.warning(f"Skipped item: {exc}")
        self.session.commit()
        log.info(f"WooCommerce import complete: {count} products processed")
        return count

    # ── Private Helpers ───────────────────────────────────────────────────
    def _process_item(self, item) -> None:
        import database as db

        title = self._get_text(item, "title") or "Unnamed Product"
        description = (
            self._get_text(item, "content:encoded")
            or self._get_text(item, "excerpt:encoded")
            or ""
        )
        # Strip HTML tags from description safely (no string-concatenation injection)
        if description:
            try:
                from html.parser import HTMLParser as _HTMLParser
                class _Stripper(_HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self._parts: list = []
                    def handle_data(self, data: str) -> None:
                        self._parts.append(data)
                    def get_text(self) -> str:
                        return "".join(self._parts).strip()
                stripper = _Stripper()
                stripper.feed(description)
                description = stripper.get_text()
            except Exception:
                description = ""

        # Price from _regular_price or _price meta
        price_str = (
            self._get_meta(item, "_regular_price")
            or self._get_meta(item, "_price")
            or "0"
        )
        try:
            price_float = float(price_str.replace(",", "."))
            # Convert to minimum units (cents), default exp=2
            price_cents = int(price_float * 100)
        except ValueError:
            price_cents = 0

        # SKU
        sku = self._get_meta(item, "_sku") or ""

        # Image URL
        image_url = self._get_text(item, "wp:attachment_url") or ""

        # Check if product already exists by name
        existing: Optional[db.Product] = (
            self.session.query(db.Product)
            .filter_by(name=title, deleted=False)
            .one_or_none()
        )
        if existing:
            existing.description = description[:500] if description else existing.description
            existing.price = price_cents if price_cents > 0 else existing.price
            log.debug(f"Updated product: {title}")
        else:
            product = db.Product(
                name=title[:255],
                description=(description[:500] if description else ""),
                price=price_cents if price_cents > 0 else None,
                deleted=False,
            )
            self.session.add(product)
            log.debug(f"Added product: {title}")
            existing = product

        # Optionally download product image
        if image_url and existing.image is None:
            try:
                r = requests.get(image_url, timeout=10)
                r.raise_for_status()
                existing.image = r.content
                log.debug(f"Downloaded image for: {title}")
            except Exception as exc:
                log.warning(f"Could not download image for {title}: {exc}")

    def _get_text(self, element, tag: str) -> Optional[str]:
        """Find element text, resolving namespace prefixes from NS dict."""
        if ":" in tag:
            prefix, local = tag.split(":", 1)
            ns = NS.get(prefix, "")
            el = element.find(f"{{{ns}}}{local}" if ns else local)
        else:
            el = element.find(tag)
        return el.text.strip() if el is not None and el.text else None

    def _get_meta(self, item, meta_key: str) -> Optional[str]:
        """Extract a WooCommerce _meta value by key."""
        ns = NS.get("wp", "")
        for meta in item.findall(f"{{{ns}}}postmeta"):
            key_el = meta.find(f"{{{ns}}}meta_key")
            val_el = meta.find(f"{{{ns}}}meta_value")
            if key_el is not None and key_el.text == meta_key:
                return val_el.text.strip() if val_el is not None and val_el.text else ""
        return None
