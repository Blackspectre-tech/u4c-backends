from rest_framework.parsers import MultiPartParser, DataAndFiles
from django.http.request import MultiValueDict
import json
import ast  # NEW: to handle Python-style list strings like "['a','b']"


# --- Helper functions for nesting (ensure these are within your parser class or accessible) ---
def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _nested_set(d, key_string, value):
    """
    Sets a value in a nested dictionary/list structure based on a key string.
    Supports keys like 'field_name', 'list_name[index]', 'dict_name[key][sub_key]'.
    """
    parts = []
    temp_part = ''
    in_bracket = False

    for char in key_string:
        if char == '[':
            if temp_part:
                parts.append(temp_part)
            temp_part = ''
            in_bracket = True
        elif char == ']':
            if temp_part:
                # Convert index parts to integers
                parts.append(int(temp_part) if _is_int(temp_part) else temp_part)
            temp_part = ''
            in_bracket = False
        elif char == '.' and not in_bracket:  # Handle dot notation outside brackets
            if temp_part:
                parts.append(temp_part)
            temp_part = ''
        else:
            temp_part += char

    if temp_part:  # Add the last part
        parts.append(temp_part)

    current_level = d
    for i, part in enumerate(parts):
        is_last_part = (i == len(parts) - 1)

        if isinstance(part, int):  # It's an index for a list
            if not isinstance(current_level, list):
                raise ValueError(
                    f"Expected a list at '{'.'.join(str(p) for p in parts[:i])}' but got {type(current_level)}"
                )

            while len(current_level) <= part:
                current_level.append(None)

            if is_last_part:
                current_level[part] = value
            else:
                if current_level[part] is None:
                    next_part_is_int = (i + 1 < len(parts) and isinstance(parts[i + 1], int))
                    current_level[part] = [] if next_part_is_int else {}
                current_level = current_level[part]

        elif isinstance(part, str):  # It's a key for a dictionary
            if not isinstance(current_level, dict):
                raise ValueError(
                    f"Expected a dictionary at '{'.'.join(str(p) for p in parts[:i])}' but got {type(current_level)}"
                )

            if is_last_part:
                current_level[part] = value
            else:
                if part not in current_level or current_level[part] is None:
                    next_part_is_int = (i + 1 < len(parts) and isinstance(parts[i + 1], int))
                    current_level[part] = [] if next_part_is_int else {}
                current_level = current_level[part]


def _maybe_json_decode(obj):
    """
    Recursively decode JSON/Python list strings into real lists/dicts if possible.
    Handles:
      - JSON: '["a","b"]'
      - Python-style: "['a','b']"
      - Leaves plain strings as-is
    """
    if isinstance(obj, dict):
        return {k: _maybe_json_decode(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_maybe_json_decode(v) for v in obj]
    elif isinstance(obj, str):
        # Try JSON
        try:
            decoded = json.loads(obj)
            if isinstance(decoded, (dict, list)):
                return decoded
        except Exception:
            pass

        # Try Python literal
        try:
            decoded = ast.literal_eval(obj)
            if isinstance(decoded, (dict, list)):
                return decoded
        except Exception:
            pass

        return obj
    return obj


def _flatten_query_dict_to_nested_dict(query_dict):
    """
    Converts a Django QueryDict (flat structure) into a nested Python dictionary,
    interpreting keys like 'parent[0][child]' as nested structures.
    """
    parsed_data = {}
    for key, value in query_dict.items():
        _nested_set(parsed_data, key, value)
    return parsed_data


# --- End Helper functions ---


class NestedMultipartAndFileParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', 'utf-8')

        # 1. Parse multipart into QueryDict + files
        parsed_result = super().parse(stream, media_type, parser_context)
        initial_data = parsed_result.data
        files_from_super = parsed_result.files

        # 2. Convert flat QueryDict into nested dict
        parsed_data = _flatten_query_dict_to_nested_dict(initial_data)

        # 3. Merge files into parsed_data
        for key, file_list in files_from_super.lists():
            if len(file_list) == 1:
                parsed_data[key] = file_list[0]
            else:
                parsed_data[key] = file_list

        # 4. Decode possible JSON/Python-style lists
        parsed_data = _maybe_json_decode(parsed_data)

        # 5. Return combined data
        return DataAndFiles(parsed_data, MultiValueDict())
    