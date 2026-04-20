import copy
import decimal
import hashlib
import re
import struct
from collections import Counter
from datetime import date, datetime, time, timedelta
import cx_Oracle
import numpy
import pandas
from dateutil import parser
from dateutil.tz import tzoffset
from decimal import Decimal

SPACE_RE = re.compile(r"\s+")
CELL_CLEAN_RE = re.compile(r"[\[\]\(\)\{\}\u3010\u3011\uFF08\uFF09,\uFF0C\uFFE5$\'\"\u201c\u201d\u2018\u2019 ]")
NUMERIC_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
DATETIME_HINT_RE = re.compile(r"[-/:T]")
data_dict = {
    "char": "string",
    "nchar": "string",
    "varchar": "string",    "nvarchar": "string",    "sql_variant": "string",    "sysname": "string",    "UNIQUEIDENTIFIER": "string",    "text": "string",    "ntext": "string",    "image": "binary",    "xml": "string",    "tinyint": "number",    "smallint": "number",    "bigint": "number",    "int": "number",    "numeric": "number",    "decimal": "number",    "float": "number",    "real": "number",    "money": "number",    "smallmoney": "number",    "date": "datetime",
    "time": "datetime",
    "datetime": "datetime",    "datetime2": "datetime",    "smalldatetime": "datetime",    "datetimeoffset": "datetime",    "binary": "binary",    "varbinary": "binary",    "hierarchyid": "binary",  # 假设 hierarchyid 归类为 binary（原字典归类不合理，可调整）
    "geometry": "spatial",
    "geomephy": "spatial",
    "timestamp": "other"  # 原字典中 timestamp 归类为 other
}


def std_cell(value, col_type="other"):
    col_type = str(col_type or "other").strip().lower()
    col_type = re.sub(r"\(.*?\)", "", col_type).strip()
    kind = data_dict.get(col_type, col_type if col_type in ("string", "number", "datetime", "binary", "spatial", "other") else "other")
    if isinstance(value, cx_Oracle.LOB):
        value = value.read()
    if isinstance(value, memoryview):
        value = value.tobytes().hex().upper() if kind == "binary" else value.tobytes()
    if isinstance(value, numpy.generic):
        value = value.item()
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(std_cell(item, col_type) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f"{std_cell(k, col_type)}:{std_cell(v, col_type)}" for k, v in sorted(value.items(), key=lambda item: str(item[0]))) + "}"
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex().upper()
    if value is None or value == "" or value is pandas.NaT:
        return ""
    if isinstance(value, float) and numpy.isnan(value):
        return ""
    if kind == "datetime":
        dt_value = None
        if isinstance(value, pandas.Timestamp):
            dt_value = value.to_pydatetime()
        elif isinstance(value, datetime):
            dt_value = value
        elif isinstance(value, date) and not isinstance(value, datetime):
            dt_value = datetime.combine(value, time.min)
        elif isinstance(value, time):
            dt_value = datetime.combine(date(1900, 1, 1), value)
        elif isinstance(value, str):
            raw = value.strip()
            if raw == "":
                return ""
            try:
                if ":" in raw and not DATETIME_HINT_RE.search(raw.replace(":", "", 1)):
                    dt_value = datetime.combine(date(1900, 1, 1), parser.parse(raw).time())
                elif ":" in raw and "-" not in raw and "/" not in raw and "T" not in raw:
                    dt_value = datetime.combine(date(1900, 1, 1), parser.parse(raw).time())
                elif ":" not in raw and ("-" in raw or "/" in raw):
                    dt_value = datetime.combine(parser.parse(raw).date(), time.min)
                else:
                    dt_value = parser.parse(raw)
            except Exception:
                return raw
        if dt_value is None:
            return str(value)
        dt_value = dt_value.replace(tzinfo=None)
        return dt_value.strftime("%Y-%m-%d %H:%M:%S.%f")
    if isinstance(value, (pandas.Timestamp, datetime)):
        dt_value = value.to_pydatetime() if isinstance(value, pandas.Timestamp) else value
        dt_value = dt_value.replace(tzinfo=None)
        text = dt_value.strftime("%Y-%m-%d %H:%M:%S.%f").rstrip("0").rstrip(".")
        return text or dt_value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, time):
        text = value.strftime("%H:%M:%S.%f").rstrip("0").rstrip(".")
        return text or value.strftime("%H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (decimal.Decimal, Decimal)):
        normalized = value.normalize()
        text = format(normalized, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if isinstance(value, (int, bool)):
        return str(int(value)) if isinstance(value, bool) else str(value)
    if isinstance(value, float):
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if isinstance(value, str):
        raw = value
        #compact = SPACE_RE.sub("", raw)
        compact=raw
        if compact == "":
            return ""
        if kind == "string":
            return raw
        if kind == "binary":
            return raw.upper()
        if kind == "number" and NUMERIC_RE.match(compact):
            try:
                decimal_value = Decimal(compact)
                text = format(decimal_value.normalize(), "f")
                return text.rstrip("0").rstrip(".") if "." in text else text
            except Exception:
                pass
        cleaned = CELL_CLEAN_RE.sub("", compact if kind != "string" else raw).upper()
        return cleaned
    return str(value)


def hash_compare(s, t,col_type_list :list,tbname):
    messages = []
    errors = []
    src_hashes = []
    tgt_hashes = []
    src_hash_pool = Counter()
    src_row_map = {}

    for i in range(s.shape[0]):
        src_row = [std_cell(s.iloc[i, j], col_type_list[j] if j < len(col_type_list) else "other") for j in range(s.shape[1])]
        src_hasher = hashlib.blake2b(digest_size=16)
        for cell in src_row:
            cell_bytes = cell.encode("utf-8", errors="replace")
            src_hasher.update(len(cell_bytes).to_bytes(4, "big", signed=False))
            src_hasher.update(cell_bytes)
        src_hash = src_hasher.hexdigest()
        src_hashes.append(src_hash)
        src_hash_pool[src_hash] += 1
        if src_hash not in src_row_map:
            src_row_map[src_hash] = src_row

    for i in range(t.shape[0]):
        tgt_row = [std_cell(t.iloc[i, j], col_type_list[j] if j < len(col_type_list) else "other") for j in range(t.shape[1])]
        tgt_hasher = hashlib.blake2b(digest_size=16)
        for cell in tgt_row:
            cell_bytes = cell.encode("utf-8", errors="replace")
            tgt_hasher.update(len(cell_bytes).to_bytes(4, "big", signed=False))
            tgt_hasher.update(cell_bytes)
        tgt_hash = tgt_hasher.hexdigest()
        tgt_hashes.append(tgt_hash)
        if src_hash_pool[tgt_hash] > 0:
            src_hash_pool[tgt_hash] -= 1
        else:
            errors.append((('tgt', tgt_row), None, tgt_hash))

    for remain_hash, remain_count in src_hash_pool.items():
        if remain_count > 0:
            for _ in range(remain_count):
                errors.append((('src',src_row_map.get(remain_hash)), remain_hash, None))
    if errors:
        message = "NO! hash比对存在%d行差异" % len(errors)
    else:
        message = "YES! hash比对通过"
    print(message)
    messages.append(message)

    return {
        "messages": messages,
        "errors": errors,
        "matched": len(errors) == 0 and bool(messages) and messages[-1].startswith("YES!"),
        "src_hashes": src_hashes,
        "tgt_hashes": tgt_hashes,
    }


def std_row(s, t):
    pattern = r"[\[\]（{ }）()【】{}，,￥$\'\"“”‘’]"
    row = []
    err = []
    messages = []
    for i in range(s.shape[0]):
        for j in range(s.shape[1]):
            src_cube = s.iloc[i, j]
            tgt_cube = t.iloc[i, j]
            if isinstance(src_cube, (list, tuple, dict)):
                src_cube = str(src_cube)
            elif isinstance(tgt_cube, (list, tuple, dict)):
                tgt_cube = str(tgt_cube)
            elif isinstance(tgt_cube, numpy.int64):
                tgt_cube = int(tgt_cube)
            if src_cube == tgt_cube:
                row.append((1, type(src_cube)))
                continue
            elif isinstance(src_cube, type(tgt_cube)):
                if src_cube == tgt_cube:
                    row.append((1, type(src_cube)))
                elif isinstance(src_cube, float) and format(tgt_cube, "f") == format(src_cube, "f"):
                    row.append((1, type(src_cube)))
                    continue
                elif isinstance(src_cube, str):
                    if re.sub(r"\s", "", src_cube) == re.sub(r"\s", "", tgt_cube):
                        row.append((1, type(src_cube)))
                        continue
                    else:
                        try:
                            if parser.parse(src_cube).replace(second=0, microsecond=0, tzinfo=None) == parser.parse(
                                tgt_cube
                            ).replace(second=0, microsecond=0, tzinfo=None):
                                row.append((1, type(src_cube)))
                                continue
                            else:
                                row.append((0, (i, j), src_cube, tgt_cube))
                                err.append(((i, j), src_cube, tgt_cube))
                        except Exception:
                            try:
                                if Decimal(src_cube) == Decimal(tgt_cube):
                                    row.append((1, type(src_cube)))
                                    continue
                            except Exception:
                                row.append((0, (i, j), src_cube, tgt_cube))
                                err.append(((i, j), src_cube, tgt_cube))
                            row.append((0, (i, j), src_cube, tgt_cube))
                            err.append(((i, j), src_cube, tgt_cube))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif isinstance(src_cube, decimal.Decimal):
                if isinstance(tgt_cube, numpy.int64):
                    if int(src_cube) == tgt_cube:
                        row.append((1, type(src_cube)))
                elif isinstance(tgt_cube, str):
                    if format(src_cube, "f") == tgt_cube:
                        row.append((1, type(src_cube)))
            elif (src_cube == "" or src_cube is None) and tgt_cube is None:
                row.append((1, type(src_cube)))
            elif (isinstance(src_cube, str) and isinstance(tgt_cube, str)) and re.sub(pattern, "", src_cube).upper() == re.sub(
                pattern, "", tgt_cube
            ).upper():
                row.append((1, type(src_cube)))
            elif isinstance(tgt_cube, str) and not isinstance(src_cube, bytes) and re.sub(
                pattern, "", str(src_cube)
            ).upper() == re.sub(pattern, "", str(tgt_cube)).upper():
                row.append((1, type(src_cube)))
            elif ((type(src_cube) and type(tgt_cube)) == bytes) and src_cube is tgt_cube:
                row.append((1, type(src_cube)))
            elif "time" in str(type(tgt_cube)).lower():
                if isinstance(src_cube, str):
                    if str(tgt_cube) == src_cube:
                        row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif type(tgt_cube) in (pandas._libs.tslibs.timestamps.Timestamp, str) and type(src_cube) == bytes and 1 != 1:
                try:
                    unpacked = struct.unpack("QIhH", src_cube)
                    m = []
                    for tup in unpacked:
                        m.append(tup)
                    days = m[1]
                    microseconds = m[0] / 10 if m[0] else 0
                    timezone = m[2]
                    tz = tzoffset("ANY", timezone * 60)
                    my_date = datetime(*[1900, 1, 1, 0, 0, 0], tzinfo=tz)
                    td = timedelta(days=days, minutes=m[2], microseconds=microseconds)
                    my_date += td
                    print(type(my_date), my_date)
                    if str(my_date)[:-6] == str(tgt_cube):
                        row.append((1, type(src_cube)))
                    elif str(my_date)[:-8] == str(tgt_cube)[:-2]:
                        row.append((1, type(src_cube)))
                    elif re.sub(" ", "", str(my_date))[:18] == re.sub(" ", "", str(tgt_cube))[:18]:
                        row.append((1, type(src_cube)))
                    else:
                        row.append((0, (i, j), src_cube, tgt_cube))
                        err.append(((i, j), src_cube, tgt_cube))
                except struct.error:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif (isinstance(tgt_cube, pandas._libs.tslibs.nattype.NaTType) and not src_cube) or (
                isinstance(src_cube, pandas._libs.tslibs.nattype.NaTType) and not tgt_cube
            ):
                row.append((1, type(src_cube)))
            elif type(src_cube) == pandas._libs.tslibs.timestamps.Timestamp:
                if str(src_cube)[:-4] == str(tgt_cube)[:-4]:
                    row.append((1, type(src_cube)))
                elif str(src_cube)[:17] == str(tgt_cube)[:17]:
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif isinstance(src_cube, time):
                if str(src_cube)[:11] == str(tgt_cube)[:11]:
                    row.append((1, type(src_cube)))
                elif str(src_cube)[:7] == str(tgt_cube)[:7]:
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif isinstance(src_cube, date):
                if str(src_cube) == str(tgt_cube) or re.match(str(src_cube), tgt_cube):
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif (isinstance(src_cube, bool) or isinstance(src_cube, numpy.bool_)) and (
                isinstance(tgt_cube, numpy.float64) or isinstance(tgt_cube, numpy.int64) or isinstance(tgt_cube, decimal.Decimal)
            ):
                if src_cube is False and tgt_cube == 0.0:
                    row.append((1, type(src_cube)))
                elif src_cube is True and tgt_cube == 1.0:
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif type(tgt_cube) == numpy.float64:
                if numpy.isnan(tgt_cube) and src_cube is None:
                    row.append((1, type(src_cube)))
                elif isinstance(src_cube, decimal.Decimal) and float(src_cube) == tgt_cube:
                    row.append((1, type(src_cube)))
                elif float(re.sub(pattern, "", str(src_cube))) == tgt_cube:
                    row.append((1, type(src_cube)))
                elif str(src_cube)[0 : len(str(tgt_cube)) - 2] == str(tgt_cube)[:-2]:
                    row.append((1, type(src_cube)))
                elif numpy.isnan(tgt_cube) and not src_cube:
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif isinstance(tgt_cube, cx_Oracle.LOB) or (isinstance(src_cube, str) and isinstance(tgt_cube, str)) or isinstance(
                src_cube, cx_Oracle.LOB
            ):
                if isinstance(src_cube, str) and isinstance(tgt_cube, str):
                    pass
                elif isinstance(tgt_cube, cx_Oracle.LOB) and not isinstance(src_cube, cx_Oracle.LOB):
                    tgt_cube = tgt_cube.read()
                elif isinstance(src_cube, cx_Oracle.LOB) and not isinstance(tgt_cube, cx_Oracle.LOB):
                    src_cube = src_cube.read()
                else:
                    src_cube = src_cube.read()
                    tgt_cube = tgt_cube.read()
                if tgt_cube == src_cube:
                    row.append((1, type(src_cube)))
                elif isinstance(src_cube, str) and re.sub(r"\s", "", tgt_cube) == re.sub(r"\s", "", src_cube):
                    row.append((1, type(src_cube)))
                elif isinstance(src_cube, str) and (src_cube.startswith("POINT") or src_cube.startswith("LINESTRING")):
                    temp_t = re.findall(r"\((.*?)\)", tgt_cube)[0].split(" ")
                    temp_s = re.findall(r"\((.*?)\)", src_cube)[0].split(" ")
                    if len(temp_t[0]) == len(temp_s[0]) and len(temp_t[1]) == len(temp_s[1]):
                        if temp_t[1][:-3] == temp_s[1][:-3] and temp_t[0][:-3] == temp_s[0][:-3]:
                            row.append((1, type(src_cube)))
                    elif len(temp_t[0]) != len(temp_s[0]) and len(temp_t[1]) == len(temp_s[1]):
                        if temp_t[1][:-3] == temp_s[1][:-3] and temp_t[0][:3] == temp_s[0][:3]:
                            row.append((1, type(src_cube)))
                    elif temp_t[0][:3] == temp_s[0][:3] and temp_t[1][:3] == temp_s[1][:3]:
                        row.append((1, type(src_cube)))
                    else:
                        row.append((0, (i, j), src_cube, tgt_cube))
                        err.append(((i, j), src_cube, tgt_cube))
                elif isinstance(src_cube, str) and src_cube.startswith("POLYGON"):
                    x = 0
                    temp_t = re.findall(r"\(\((.*?)\)\)", tgt_cube)[0].split(",")
                    temp_s = re.findall(r"\(\((.*?)\)\)", src_cube)[0].split(",")
                    for iss, js in zip(temp_t, temp_s):
                        i_front = re.findall(r"(.*?)\s", iss.strip())[0]
                        i_behind = re.findall(r"\s(.+)", iss.strip())[0]
                        j_front = re.findall(r"(.*?)\s", js.strip())[0]
                        j_behind = re.findall(r"\s(.+)", js.strip())[0]
                        for ccx, char in enumerate(i_front):
                            if char == ".":
                                l = ccx
                                break
                        for cct, ccs in enumerate(i_behind):
                            if ccs == ".":
                                k = cct
                                break
                        if i_front[: l + 2] == j_front[: l + 2] and i_behind[: k + 2] == j_behind[: k + 2]:
                            x += 1
                        else:
                            pass
                    if x == len(temp_t):
                        row.append((1, type(src_cube)))
                    else:
                        row.append((0, (i, j), src_cube, tgt_cube))
                        err.append(((i, j), src_cube, tgt_cube))
                elif isinstance(src_cube, str) and src_cube.startswith("COMPOUNDCURVE"):
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
                    continue
                elif isinstance(src_cube, str) and re.sub("\x00.*", "", src_cube) == re.sub("\x00.*", "", tgt_cube):
                    row.append((1, type(src_cube)))
                else:
                    row.append((0, (i, j), src_cube, tgt_cube))
                    err.append(((i, j), src_cube, tgt_cube))
            elif (isinstance(tgt_cube, memoryview) and src_cube == re.findall(r"b[\'\"](.*?)[\'\"]", str(tgt_cube.tobytes()))[0]) or (
                isinstance(src_cube, memoryview) and tgt_cube == re.findall(r"b\'(.*?)\'", str(src_cube.tobytes()))[0]
            ):
                row.append((1, type(src_cube)))
            else:
                row.append((0, (i, j), src_cube, tgt_cube))
                err.append(((i, j), src_cube, tgt_cube))
        row = []
    print(err)
    return {
        "messages": messages,
        "errors": err,
        "matched": len(err) == 0 and bool(messages) and messages[0].startswith("Y"),
        "source_df": s,
        "target_df": t,
    }
