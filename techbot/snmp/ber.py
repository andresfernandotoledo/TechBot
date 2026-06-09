# techbot/snmp/ber.py
# Pure-Python ASN.1 BER (Basic Encoding Rules) for SNMP v1/v2c
# No dependencies beyond stdlib.

import struct

# ─── ASN.1 tag constants ───────────────────────────────────
ASN1_BOOLEAN      = 0x01
ASN1_INTEGER      = 0x02
ASN1_BIT_STRING   = 0x03
ASN1_OCTET_STRING = 0x04
ASN1_NULL         = 0x05
ASN1_OBJECT_ID    = 0x06
ASN1_SEQUENCE     = 0x30
ASN1_CONTEXT      = 0x80  # context-specific (for SNMP PDUs)

# ─── Encode helpers ─────────────────────────────────────────

def encode_tlv(tag, value):
    """Encode tag + length + value (BER TLV)."""
    length = _encode_length(len(value))
    return bytes([tag]) + length + value


def encode_int(value):
    """Encode INTEGER as signed big-endian with minimal bytes."""
    if value == 0:
        return encode_tlv(ASN1_INTEGER, b'\x00')
    # Determine byte length
    if value > 0:
        # How many bytes needed
        bits = value.bit_length()
        nbytes = (bits + 7) // 8
        # Add leading zero byte if high bit set (to keep positive)
        val_bytes = value.to_bytes(nbytes, 'big', signed=False)
        if val_bytes[0] & 0x80:
            val_bytes = b'\x00' + val_bytes
    else:
        # Negative: two's complement
        nbytes = (value.bit_length() + 8) // 8
        val_bytes = value.to_bytes(nbytes, 'big', signed=True)
    return encode_tlv(ASN1_INTEGER, val_bytes)


def encode_octet_string(data):
    """Encode OCTET STRING."""
    return encode_tlv(ASN1_OCTET_STRING, data)


def encode_null():
    """Encode NULL (zero-length)."""
    return encode_tlv(ASN1_NULL, b'')


def encode_oid(oid_str):
    """Encode OID string like '1.3.6.1.2.1.1.1.0' → bytes."""
    parts = [int(x) for x in oid_str.strip('.').split('.')]
    if len(parts) < 2:
        raise ValueError("OID must have at least 2 components")
    # First two components encoded as 40*first + second
    result = bytearray()
    result.append(40 * parts[0] + parts[1])
    for p in parts[2:]:
        result.extend(_encode_oid_sub(p))
    return encode_tlv(ASN1_OBJECT_ID, bytes(result))


def _encode_oid_sub(value):
    """Encode a single OID sub-identifier (base-128, high-bit-set per byte)."""
    if value < 128:
        return bytes([value])
    result = bytearray()
    # Encode in base-128, least significant first, then reverse
    while value > 0:
        b = value & 0x7F
        value >>= 7
        result.append(b)
    result.reverse()
    # Set high bit on all but the last byte
    for i in range(len(result) - 1):
        result[i] |= 0x80
    return bytes(result)


def encode_sequence(contents):
    """Encode SEQUENCE wrapper."""
    return encode_tlv(ASN1_SEQUENCE, contents)


def encode_constructed(tag, contents):
    """Encode a constructed (context-specific) type with given contents."""
    return encode_tlv(tag | 0x20, contents)


def encode_varbind(oid, value):
    """Encode a VarBind: SEQUENCE { oid, value }."""
    return encode_sequence(encode_oid(oid) + value)


def encode_boolean(value):
    return encode_tlv(ASN1_BOOLEAN, b'\x01' if value else b'\x00')


# ─── Decode helpers ─────────────────────────────────────────

def _encode_length(length):
    """BER length encoding."""
    if length < 128:
        return bytes([length])
    # Long form
    length_bytes = length.to_bytes((length.bit_length() + 7) // 8, 'big')
    return bytes([0x80 | len(length_bytes)]) + length_bytes


def _decode_length(data, offset):
    """Decode BER length from data starting at offset.
    Returns (length, new_offset)."""
    first = data[offset]
    if first < 0x80:
        return first, offset + 1
    num_bytes = first & 0x7F
    length = 0
    for i in range(num_bytes):
        length = (length << 8) | data[offset + 1 + i]
    return length, offset + 1 + num_bytes


def decode_tlv(data):
    """Decode single TLV from data.
    Returns ((tag, value_bytes), new_offset)."""
    if not data:
        raise ValueError("Empty data for TLV decode")
    tag = data[0]
    length, offset = _decode_length(data, 1)
    value = data[offset:offset + length]
    return (tag, value), offset + length


def decode_int(data):
    """Decode INTEGER from raw bytes at start of data.
    Returns (value, remaining_bytes)."""
    (tag, value), offset = decode_tlv(data)
    if tag != ASN1_INTEGER:
        raise ValueError(f"Expected INTEGER tag 0x02, got 0x{tag:02x}")
    val = int.from_bytes(value, 'big', signed=True)
    return val, data[offset:]


def decode_oid(data):
    """Decode OID from raw bytes at start of data.
    Returns (oid_string, remaining_bytes)."""
    (tag, value), offset = decode_tlv(data)
    if tag != ASN1_OBJECT_ID:
        raise ValueError(f"Expected OID tag 0x06, got 0x{tag:02x}")
    parts = []
    # First two components from first byte
    first = value[0]
    parts.append(first // 40)
    parts.append(first % 40)
    # Remaining sub-ids
    i = 1
    while i < len(value):
        sub_id = 0
        while True:
            b = value[i]
            sub_id = (sub_id << 7) | (b & 0x7F)
            i += 1
            if not (b & 0x80):
                break
        parts.append(sub_id)
    return ".".join(str(p) for p in parts), data[offset:]


def unwrap_sequence(data):
    """Unwrap SEQUENCE: parse tag+length, return (contents, rest)."""
    (tag, contents), offset = decode_tlv(data)
    if tag != ASN1_SEQUENCE:
        raise ValueError(f"Expected SEQUENCE tag 0x30, got 0x{tag:02x}")
    return contents, data[offset:]


def unwrap_constructed(tag, data):
    """Unwrap a constructed (context-specific) TLV."""
    (inner_tag, inner_data), offset = decode_tlv(data)
    # The inner data already is the value; we return it as-is, and the tag
    return (inner_tag, inner_data), data[offset:]


def skip_octet_string(data):
    """Skip an OCTET STRING. Returns (value, rest)."""
    (tag, value), offset = decode_tlv(data)
    if tag != ASN1_OCTET_STRING:
        raise ValueError(f"Expected OCTET STRING, got 0x{tag:02x}")
    return value, data[offset:]


def decode_octet_string(data):
    """Decode OCTET STRING. Returns (value_bytes, rest)."""
    (tag, value), offset = decode_tlv(data)
    if tag != ASN1_OCTET_STRING:
        raise ValueError(f"Expected OCTET STRING, got 0x{tag:02x}")
    return value, data[offset:]


def format_snmp_value(tag, raw_bytes):
    """Formatea un valor SNMP para mostrar."""
    if tag == ASN1_INTEGER:
        return int.from_bytes(raw_bytes, 'big', signed=True)
    elif tag == ASN1_OCTET_STRING:
        # Try UTF-8 decode, fallback to hex
        try:
            return raw_bytes.decode('utf-8')
        except:
            return raw_bytes.hex()
    elif tag == ASN1_OBJECT_ID:
        oid, _ = decode_oid(encode_tlv(tag, raw_bytes))
        return oid
    elif tag == ASN1_NULL:
        return None
    elif tag == ASN1_BOOLEAN:
        return len(raw_bytes) > 0 and raw_bytes[0] != 0
    elif tag == ASN1_BIT_STRING:
        return raw_bytes.hex()
    # COUNTER, GAUGE, TIMETICKS, etc. use ASN1_CONTEXT tags or APPLICATION tags
    # Try as unsigned int
    try:
        return int.from_bytes(raw_bytes, 'big')
    except:
        return raw_bytes.hex()
