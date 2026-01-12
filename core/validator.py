
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

UPDATE_RE = re.compile(r"UPDATE_START\s*(\{.*?\})\s*UPDATE_END", re.DOTALL)

@dataclass
class ValidationResult:
    ok: bool
    cleaned_text: str
    inc_ops: Dict[str, float]
    set_ops: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    raw_updates: List[Dict[str, Any]]


ALLOWED_INC_PATHS = {

    "stats.combat.strength": (-2.0, 2.0),
    "stats.combat.agility": (-3.0, 3.0),
    "stats.combat.athletics": (-3.0, 3.0),
    "stats.combat.melee_attack": (-2.0, 2.0),
    "stats.combat.melee_defence": (-2.0, 2.0),
    "stats.combat.toughness": (-2.0, 2.0),
    "stats.combat.ranged": (-2.0, 2.0),

    "stats.utility.engineer": (-2.0, 2.0),
    "stats.utility.field_medic": (-2.0, 2.0),
    "stats.utility.stealth": (-2.0, 2.0),

    "status.integrity": (-30.0, 30.0),
    "status.core_stability": (-25.0, 25.0),
}

ALLOWED_SET_PATHS = {
    "status.location",
}


ABSOLUTE_RANGES = {
    "status.integrity": (0.0, 100.0),
    "status.core_stability": (0.0, 100.0),
}

def extract_updates(raw_text: str) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    """
    Returns: (cleaned_text_without_update_blocks, list_of_update_dicts, errors)
    Supports multiple UPDATE blocks.
    """
    errors: List[str] = []
    updates: List[Dict[str, Any]] = []

    def _strip_block(m: re.Match) -> str:
        return "" 

    matches = list(UPDATE_RE.finditer(raw_text))
    cleaned = UPDATE_RE.sub(_strip_block, raw_text).strip()

    for m in matches:
        block = m.group(1)
        try:
            obj = json.loads(block)
            if isinstance(obj, dict):
                updates.append(obj)
            else:
                errors.append("Update JSON must be an object/dict.")
        except Exception as e:
            errors.append(f"Invalid JSON in UPDATE block: {e}")

    return cleaned, updates, errors

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def validate_and_build_ops(
    update_dict: Dict[str, Any],
    current_state: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, float], Dict[str, Any], List[str], List[str]]:
    """
    Validates one update dict and returns ($inc, $set, errors, warnings).
    Expected keys are dot-paths.
    """
    inc_ops: Dict[str, float] = {}
    set_ops: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []

    for path, value in update_dict.items():
        if _is_number(value):

            if path not in ALLOWED_INC_PATHS:
                errors.append(f"INC path not allowed: {path}")
                continue

            lo, hi = ALLOWED_INC_PATHS[path]
            if not (lo <= float(value) <= hi):
                errors.append(f"INC delta out of range for {path}: {value} (allowed {lo}..{hi})")
                continue

            inc_ops[path] = inc_ops.get(path, 0.0) + float(value)

        else:

            if path not in ALLOWED_SET_PATHS:
                errors.append(f"SET path not allowed: {path}")
                continue


            if path == "status.location" and not isinstance(value, str):
                errors.append("status.location must be a string.")
                continue

            set_ops[path] = value


    if current_state:
        for path, (mn, mx) in ABSOLUTE_RANGES.items():
            if path in inc_ops:
                cur = _get_by_path(current_state, path)
                if _is_number(cur):
                    new_val = float(cur) + float(inc_ops[path])
                    if new_val < mn:
                        warnings.append(f"Clamped {path} to {mn}")
                        inc_ops[path] = mn - float(cur)
                    elif new_val > mx:
                        warnings.append(f"Clamped {path} to {mx}")
                        inc_ops[path] = mx - float(cur)

    return inc_ops, set_ops, errors, warnings

def _get_by_path(obj: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = obj
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

def validate_ai_text(
    raw_text: str,
    current_state: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    cleaned_text, updates, extract_errors = extract_updates(raw_text)

    all_inc: Dict[str, float] = {}
    all_set: Dict[str, Any] = {}
    errors: List[str] = list(extract_errors)
    warnings: List[str] = []

    for upd in updates:
        inc_ops, set_ops, e, w = validate_and_build_ops(upd, current_state=current_state)
        errors.extend(e)
        warnings.extend(w)


        for k, v in inc_ops.items():
            all_inc[k] = all_inc.get(k, 0.0) + float(v)
        for k, v in set_ops.items():
            all_set[k] = v

    ok = len(errors) == 0
    return ValidationResult(
        ok=ok,
        cleaned_text=cleaned_text,
        inc_ops=all_inc,
        set_ops=all_set,
        errors=errors,
        warnings=warnings,
        raw_updates=updates,
    )


if __name__ == "__main__":
    sample = 'Hello UPDATE_START {"status.integrity": -999} UPDATE_END'
    r = validate_ai_text(sample, current_state={"status": {"integrity": 100.0, "core_stability": 100.0}})
    print(r.ok, r.errors, r.inc_ops, r.cleaned_text)
