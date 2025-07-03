from rest_framework.parsers import MultiPartParser, DataAndFiles
from django.http.request import QueryDict, MultiValueDict
import json # Potentially useful if you had JSON strings in your query_dict values

# --- Helper functions for nesting (ensure these are within your parser class or accessible) ---
def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# This function creates/updates nested dictionaries/lists
# It's essential for parsing keys like 'milestones[0][title]'
def _nested_set(d, key_string, value):
    """
    Sets a value in a nested dictionary/list structure based on a key string.
    Supports keys like 'field_name', 'list_name[index]', 'dict_name[key][sub_key]'
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
        elif char == '.' and not in_bracket: # Handle dot notation outside brackets
            if temp_part:
                parts.append(temp_part)
            temp_part = ''
        else:
            temp_part += char
            
    if temp_part: # Add the last part
        parts.append(temp_part)

    current_level = d
    for i, part in enumerate(parts):
        is_last_part = (i == len(parts) - 1)

        if isinstance(part, int):  # It's an index for a list
            if not isinstance(current_level, list):
                # This indicates a structural mismatch in the input key_string
                raise ValueError(f"Expected a list at '{'.'.join(str(p) for p in parts[:i])}' but got {type(current_level)}")
            
            # Pad list with None if index is out of bounds
            while len(current_level) <= part:
                current_level.append(None)
            
            if is_last_part:
                current_level[part] = value
            else:
                if current_level[part] is None:
                    # Guess type for next level based on next part: dict or list
                    next_part_is_int = (i + 1 < len(parts) and isinstance(parts[i+1], int))
                    current_level[part] = [] if next_part_is_int else {}
                current_level = current_level[part]

        elif isinstance(part, str):  # It's a key for a dictionary
            if not isinstance(current_level, dict):
                # This indicates a structural mismatch in the input key_string
                raise ValueError(f"Expected a dictionary at '{'.'.join(str(p) for p in parts[:i])}' but got {type(current_level)}")
            
            if is_last_part:
                current_level[part] = value
            else:
                if part not in current_level or current_level[part] is None:
                    # Guess type for next level based on next part: dict or list
                    next_part_is_int = (i + 1 < len(parts) and isinstance(parts[i+1], int))
                    current_level[part] = [] if next_part_is_int else {}
                current_level = current_level[part]

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

        # 1. Use the parent's parse method to get initial data (QueryDict) and files (MultiValueDict).
        # This step correctly handles the raw HTTP parsing into request.POST and request.FILES.
        parsed_result = super().parse(stream, media_type, parser_context)
        initial_data = parsed_result.data
        files_from_super = parsed_result.files  
        # 2. Convert initial_data (flat QueryDict) into a nested Python dictionary.
        # This is the core 'nesting' feature.
        parsed_data = _flatten_query_dict_to_nested_dict(initial_data)

        # 3. --- NEW FEATURE: Merge files from files_from_super directly into parsed_data ---
        # This makes the file object available in request.data, so ImageField can find it.
        for key, file_list in files_from_super.lists(): # .lists() handles multiple files for same key
            if len(file_list) == 1:
                # If only one file, assign the single file object directly
                parsed_data[key] = file_list[0]
            else:
                # If multiple files for the same key, assign the list of file objects
                parsed_data[key] = file_list
        # --- END NEW FEATURE ---

        # 4. Return the combined data and an empty MultiValueDict for files.
        # We return an empty MultiValueDict for files because they've been merged into 'data'.
        # DRF expects a DataAndFiles namedtuple from parsers.
        return DataAndFiles(parsed_data, MultiValueDict())
