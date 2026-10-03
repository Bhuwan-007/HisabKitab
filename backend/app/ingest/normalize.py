import re

def normalize_invoice_no(raw: str) -> str:
    if not raw:
        return ""
    s = raw.upper()
    s = re.sub(r'[\s/\-\.]', '', s)
    # Strip common FY tokens
    s = re.sub(r'(?:20)?(?:24|25|26|27)(?:25|26|27|28)', '', s)
    # Strip prefixes if followed by a digit
    s = re.sub(r'^(INV|INVOICE|BILL|TI)(?=\d)', '', s)
    # Strip leading zeros of the last digit block
    s = re.sub(r'(^|\D)0+(\d+)$', r'\g<1>\g<2>', s)
    return s

def validate_gstin(g: str) -> bool:
    if not g:
        return False
    pattern = r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z][\dA-Z]$'
    return bool(re.match(pattern, g))

def round_rupees(v: float) -> float:
    return round(v, 2)

def format_inr(v: float) -> str:
    is_neg = v < 0
    v = abs(v)
    s = f"{v:,.2f}"
    parts = s.split('.')
    int_part = parts[0].replace(',', '')
    if len(int_part) > 3:
        last3 = int_part[-3:]
        other = int_part[:-3]
        other_parts = []
        while other:
            other_parts.append(other[-2:])
            other = other[:-2]
        int_part = ",".join(reversed(other_parts)) + "," + last3
    res = f"₹{int_part}.{parts[1]}"
    if is_neg:
        return "-" + res
    return res
