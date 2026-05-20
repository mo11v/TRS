"""
TRS Graph Extractor v2
Extracts Torque/Turns graph images from MTT PDF files.
Uses pymupdf (fitz) if available, falls back to pypdf indexed-image extraction.
"""
import io
import re
import logging
import numpy as np

logger = logging.getLogger(__name__)

# ── Try pymupdf first ─────────────────────────────────────────────────────
try:
    import fitz as _fitz
    _HAVE_FITZ = True
except ImportError:
    _HAVE_FITZ = False
    logger.debug("pymupdf not available — using pypdf fallback")


def _render_page_fitz(pdf_bytes: bytes, page_index: int, dpi: int = 150) -> bytes | None:
    """Render full PDF page via pymupdf → cropped PNG (graph area only)."""
    try:
        doc  = _fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_index]
        zoom = dpi / 72.0
        mat  = _fitz.Matrix(zoom, zoom)

        # Get dimensions
        pix   = page.get_pixmap(matrix=mat, alpha=False)
        w, h  = pix.width, pix.height

        # Crop: skip top ~30% (header/table) and bottom ~8% (footer)
        # The graph lives in the lower 55% of the page
        top    = int(h * 0.30)
        bottom = int(h * 0.92)
        clip   = _fitz.Rect(0, top / zoom, page.rect.width, bottom / zoom)
        pix_c  = page.get_pixmap(matrix=mat, alpha=False, clip=clip)
        return pix_c.tobytes("png")
    except Exception as e:
        logger.debug(f"fitz render failed page {page_index}: {e}")
        return None


def _render_page_pypdf(page) -> bytes | None:
    """Extract indexed-color graph image from a PDF page via pypdf."""
    try:
        resources = page.get('/Resources', {})
        xobjects  = resources.get('/XObject', {})
        best = None

        for key in xobjects:
            obj = xobjects[key].get_object()
            if obj.get('/Subtype') != '/Image':
                continue
            w = int(obj.get('/Width',  0))
            h = int(obj.get('/Height', 0))
            if w < 500 or h < 300:
                continue
            area = w * h
            if best is None or area > best[0]:
                best = (area, obj, w, h, obj.get('/ColorSpace'))

        if best is None:
            return None
        _, obj, w, h, cs = best
        raw = obj.get_data()

        if isinstance(cs, list) and str(cs[0]) == '/Indexed':
            palette = np.frombuffer(bytes(cs[3]), dtype=np.uint8).reshape(-1, 3)
            pixels  = np.frombuffer(raw, dtype=np.uint8)
            if len(pixels) != w * h:
                return None
            rgb = palette[pixels].reshape(h, w, 3)
            from PIL import Image as PILImage
            buf = io.BytesIO()
            PILImage.fromarray(rgb, 'RGB').save(buf, format='PNG', optimize=True)
            return buf.getvalue()
    except Exception as e:
        logger.debug(f"pypdf extraction failed: {e}")
    return None


def build_joint_page_map(pdf_bytes: bytes) -> dict:
    """
    Scan PDF and return {(joint_num, run_number): page_index} mapping.
    Uses fitz text extraction if available, else pypdf.
    """
    mapping = {}
    try:
        if _HAVE_FITZ:
            doc = _fitz.open(stream=pdf_bytes, filetype="pdf")
            for pg_idx in range(len(doc)):
                text = doc[pg_idx].get_text()
                m = re.search(r'JOINT\s*#?\s*(\d+)(?:\s*[-–]\s*(?:Remake|Rerun)[:\s]*(\d+)|(_R\d+))?', text)
                if m:
                    jnum  = int(m.group(1))
                    if m.group(2):
                        rnum = int(m.group(2))
                    elif m.group(3):
                        rnum = int(re.search(r'(\d+)', m.group(3)).group(1))
                    else:
                        rnum = 1
                    jlabel = f"{jnum}_R{rnum}" if rnum > 1 else str(jnum)
                    key    = (jnum, rnum)
                    if key not in mapping:
                        mapping[key] = pg_idx
        else:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for pg_idx in range(len(reader.pages)):
                text = reader.pages[pg_idx].extract_text() or ''
                m    = re.search(r'JOINT\s*#?\s*(\d+)(?:\s*[-\u2013]\s*(?:Remake|Rerun)[:\s]*(\d+)|(_R\d+))?', text)
                if m:
                    jnum  = int(m.group(1))
                    if m.group(2):   rnum = int(m.group(2))
                    elif m.group(3): rnum = int(re.search(r'(\d+)', m.group(3)).group(1))
                    else:            rnum = 1
                    key    = (jnum, rnum)
                    if key not in mapping:
                        mapping[key] = pg_idx

        logger.info(f"Graph map: {len(mapping)} joint pages")
    except Exception as e:
        logger.error(f"build_joint_page_map error: {e}")
    return mapping


def extract_joint_graph(pdf_bytes: bytes, joint_num: int, run_number: int = 1,
                         page_map: dict = None) -> bytes | None:
    """
    Extract/render graph PNG for a specific joint.
    Returns PNG bytes or None.
    """
    if page_map is None:
        page_map = build_joint_page_map(pdf_bytes)

    for rn in [run_number, 1]:
        pg_idx = page_map.get((joint_num, rn))
        if pg_idx is None:
            continue
        if _HAVE_FITZ:
            img = _render_page_fitz(pdf_bytes, pg_idx)
        else:
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(pdf_bytes))
                img = _render_page_pypdf(reader.pages[pg_idx])
            except Exception:
                img = None
        if img:
            return img

    # Fallback: text-scan
    try:
        if _HAVE_FITZ:
            doc = _fitz.open(stream=pdf_bytes, filetype="pdf")
            for pg_idx in range(len(doc)):
                if re.search(rf'JOINT\s*#\s*{joint_num}\b', doc[pg_idx].get_text()):
                    img = _render_page_fitz(pdf_bytes, pg_idx)
                    if img: return img
        else:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for pg_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ''
                if re.search(rf'JOINT\s*#\s*{joint_num}\b', text):
                    img = _render_page_pypdf(page)
                    if img: return img
    except Exception as e:
        logger.debug(f"Fallback scan failed: {e}")
    return None


def extract_all_graphs(pdf_bytes: bytes, joint_nums: list = None) -> dict:
    """Extract graphs for a list of joints (or all if None). Returns {joint_num: png_bytes}."""
    page_map = build_joint_page_map(pdf_bytes)
    result   = {}
    targets  = set(joint_nums) if joint_nums else None

    if _HAVE_FITZ:
        try:
            doc = _fitz.open(stream=pdf_bytes, filetype="pdf")
            for (jnum, rnum), pg_idx in page_map.items():
                if targets and jnum not in targets: continue
                if jnum in result: continue
                img = _render_page_fitz(pdf_bytes, pg_idx)
                if img: result[jnum] = img
        except Exception as e:
            logger.error(f"fitz all-graphs error: {e}")
    else:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for (jnum, rnum), pg_idx in page_map.items():
                if targets and jnum not in targets: continue
                if jnum in result: continue
                img = _render_page_pypdf(reader.pages[pg_idx])
                if img: result[jnum] = img
        except Exception as e:
            logger.error(f"pypdf all-graphs error: {e}")

    logger.info(f"Extracted {len(result)} graphs (fitz={_HAVE_FITZ})")
    return result