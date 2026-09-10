TEXT = """SYNTHETIC SERVICES AGREEMENT — NOT A REAL CONTRACT

1. Services
Example Provider will prepare a website prototype for Example Customer.

2. Payment
Example Customer must pay invoices within fifteen days of receipt.

3. Liability
The Provider's total aggregate liability shall not exceed fees paid by the Customer during the preceding thirty days.

4. Termination
Either party may terminate with thirty days written notice.
"""


def pdf_bytes():
    import pymupdf
    with pymupdf.open() as pdf:
        paragraphs = TEXT.split('\n\n')
        for group in (paragraphs[:3], paragraphs[3:]):
            page = pdf.new_page(width=620, height=800)
            y = 70
            for paragraph in group:
                page.insert_text((45, y), paragraph.replace('—', '-'), fontsize=9)
                y += 110
        return pdf.tobytes(no_new_id=True)


def findings(source):
    block = next(b for b in source["blocks"] if "preceding thirty days" in b["text"])
    quote = "The Provider's total aggregate liability shall not exceed fees paid by the Customer during the preceding thirty days."
    start = block["text"].index(quote)
    return [{"id": "sample-liability", "title": "Confirm whether the cap matches your exposure",
             "explanation": "A cap based on thirty days of fees may be smaller than the loss you want covered. This is an illustrative observation, not a legal assessment.",
             "impact": "Not assessed", "uncertainty": "Actual fees, exceptions, objectives and governing law need human confirmation.",
             "action": "Ask your legal reviewer to check the cap, related provisions and intended exposure.",
             "business_preference": "Unknown", "evidence_status": "Synthetic fixture — not AI analysis",
             "citations": [{"block_id": block["id"], "quote": quote, "start": start, "end": start + len(quote), "location": block["location"]}]}]
