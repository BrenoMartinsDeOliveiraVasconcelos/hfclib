import re
import warnings


# Known issues
# - List inside lists raises SytaxError if nstled layers are larger than 2

class NotHFC(Exception):
    pass

class MaxDepth(Exception):
    pass


class langconf:
    COMMENT_CHARS = ["->", "//", "#"]
    SECTION_SEPARATOR = "=="
    SECTION_REGEX = f"^{SECTION_SEPARATOR}.+{SECTION_SEPARATOR}$"
    VARIABLE_SEPARATOR = "="
    STRING_CHAR = '"'
    STRING_REGEX = f'^{STRING_CHAR}.+{STRING_CHAR}$'
    INTEGER_REGEX = "^-?\d+$"
    FLOAT_REGEX = "^\d+([.,]\d+)$"
    STANDARD_FLOAT_SEP = "."
    NON_STANDARD_FLOAT_SEPS = [","]
    ALL_FLOAT_SEP = [",", "."]
    LIST_REGEXES = ["^\[.*\]$", "^\(.*\)$"]  # Match [] and ()
    LIST_CHARS = ["[", "]", "(", ")"]
    LIST_INDEX_SEP = ", "
    BOOLEAN_TRUE = ["yes", "true", "sim", "verdadeiro", "y", "s"]
    BOOLEAN_FALSE = ["no", "false", "nao", "falso", "n"]
    INVALID_NAME_REGEXES = ["^\s*$"] # Contains regexes with invalid naming


def _strip(text: str) -> str:
    remove = ["\n", "\n\n", " "]
    text = text.strip()

    for x in remove:
        text = text.strip(x)

    return text

def _replace(text: str, chars: list, replace_to: str, outside_only=False) -> str:
    fixed_text = ""

    if not outside_only:
        for char in chars:
            text = fixed_text = text.replace(char, replace_to)
    else:
        # Removes only external characters
        for char in chars:
            changed_first = False
            index  = 0
            for s in text:
                if s == char:
                    if index == 0:
                        fixed_text = text[1:]
                        changed_first = True
                    
                    if index == len(text) -1:
                        if not changed_first:
                            fixed_text = text[:-1]
                        else:
                            fixed_text = text[1:-1]

                index +=1
            if fixed_text != text:
                text = fixed_text # Apply changes

    return text


def _validate(regex: str, text: str) -> bool:
    return re.match(regex, text)


def _join_list_with_char(input_list: list, chars: list[str, str], list_separator: str, is_nlist=False) -> list:
    string_index_range = [0, 0]
    ignore_next_index = False
    index = 0
    found_string = False
    output_list = []

    if not input_list or not chars or not list_separator:
        raise ValueError("Input list, chars and list separator cannot be empty")

    for i in input_list:
        if not isinstance(i, str):
            raise ValueError("Input list must contain only strings")

        string_i = i

        if string_i.startswith(chars[0]):
            if string_index_range[0] != 0:
                raise ValueError("Unbalanced string bracket")

            string_index_range[0] = index
            found_string = True

        if found_string and string_i.endswith(chars[1]):
            if string_index_range[1] != 0:
                raise ValueError("Unbalanced string bracket")

            string_index_range[1] = index
            string_list = input_list[string_index_range[0]:string_index_range[1]+1]
            append_str  = list_separator.join(string_list)

            output_list.append(append_str) # The list separator separated the string

            string_index_range = [0, 0]
            found_string = False
            ignore_next_index = True

        if string_i.startswith(chars[0]) and string_i.endswith(chars[1]) and found_string:
            output_list.append(i)
            found_string = False
            string_index_range = [0, 0]
        else:
            if not found_string and not ignore_next_index:
                output_list.append(i)
            elif not found_string and ignore_next_index:
                ignore_next_index = False

        index += 1

    if string_index_range[0] != 0 or string_index_range[1] != 0:
        raise ValueError("Unbalanced string bracket")

    return output_list


# Convert the value and output it
def _get_converted(value: str, line_num: int):
    """
    Converts a string value to its appropriate type.

    Args:
        value (str): The value to be converted
        line_num (int): The line number of the value in the parsed HFC file

    Returns:
        Any: The converted value
    """
    converted = ""
    is_list = False

    # First, going to check if it's a list
    for regex in langconf.LIST_REGEXES:
        if _validate(regex, value):
            is_list = True

            # Remove brackets and split by space
            value_fix = _replace(text=value, chars=langconf.LIST_CHARS, replace_to="", outside_only=True)
            
            value_list = value_fix.split(langconf.LIST_INDEX_SEP)
            converted_list = []

            # Convert lists
            index = 0
            for char in langconf.LIST_CHARS:
                if index % 2 == 0: # To separate by pairs.
                    char_1 = char
                    char_2 = langconf.LIST_CHARS[index+1]
                    value_list = _join_list_with_char(input_list=value_list, chars=[char_1, char_2], list_separator=langconf.LIST_INDEX_SEP, is_nlist=True)

                index += 1

            # Value list corrected with strings
            value_list = _join_list_with_char(input_list=value_list, chars=[langconf.STRING_CHAR, langconf.STRING_CHAR], list_separator=langconf.LIST_INDEX_SEP)

            # The corrected list
            for val in value_list:            
                converted_list.append(_get_converted(_strip(val), line_num))
            
            return converted_list

    # Only check in case of not being a list
    if not is_list:
        # Checking variable type
        if _validate(langconf.STRING_REGEX, text=value): # Checking if it's string
            converted = value.replace(langconf.STRING_CHAR, "")
        elif _validate(langconf.INTEGER_REGEX, text=value): # If it's a valid integer
            converted = int(value)
        elif _validate(langconf.FLOAT_REGEX, text=value): # Checking if it's float
            # Convert to universal "." as decimal separator
            converted = float(_replace(text=value, chars=langconf.NON_STANDARD_FLOAT_SEPS, replace_to=langconf.STANDARD_FLOAT_SEP))
        elif value in langconf.BOOLEAN_FALSE:
            converted = False
        elif value in langconf.BOOLEAN_TRUE:
            converted = True
        else:
            raise SyntaxError(f"Invalid variable declaration at line {line_num}.")
        
    return converted
        

# Convert a value to a hfc variable
def _convert_to_hfc(definition, list_char: list[str, str], bool_false: str, bool_true: str, float_separator: str):
    def_list = ""

    if type(definition) == str:
        definition = f'{langconf.STRING_CHAR}{definition}{langconf.STRING_CHAR}'

    if type(definition) == list:
        # Valid hfc list converting
        start_list = ""
        end_list = ""

        index = 0
        for c in list_char:
            if c in list_char:
                if index == 0:
                    start_list = c
                elif index == 1:
                    end_list = c

            index += 1

        def_list += start_list
        def_index = 0
        for i in definition:
            string = langconf.LIST_INDEX_SEP if def_index > 0 else "" # Separator string
            try:
                def_list += f"{string}{_convert_to_hfc(i, list_char, bool_false, bool_true, float_separator)}"
            except Exception as e:
                raise e
            
            def_index += 1

        def_list += end_list

        # If the outcome is a valid list
        valid = False
        for regex in langconf.LIST_REGEXES:
            if _validate(regex, def_list):
                valid = True

        if not valid:
            raise TypeError("list_char values are not valid, so it didn't generate a valid HFC file.")

        definition = def_list

    # In case it's bool
    if type(definition) == bool:
        if definition:
            if bool_true in langconf.BOOLEAN_TRUE:
                definition = bool_true
        else:
            if bool_false in langconf.BOOLEAN_FALSE:
                definition = bool_true

        if type(definition) != str:
            raise NotHFC("One of the booleans value are not valid, so it didn't generate a valid HFC file.")

    
    # In case it's a floa
    if type(definition) == float:
        # Replace for the defined separator
        if float_separator in langconf.ALL_FLOAT_SEP and float_separator != langconf.STANDARD_FLOAT_SEP: # Like if the standard float sep will ever change lol
            definition = str(definition).replace(".", float_separator)
        elif float_separator == langconf.STANDARD_FLOAT_SEP:
            pass
        else:
            raise NotHFC("Invalid float_separator caused a invalid HFC text.")
        
    return definition



def _section_exists(hfc_list: list[dict[dict]], section_name: str) -> bool:
    for section in hfc_list:
        if section_name in section.keys():
            return True

    return False


def _variable_exists(hfc_list: list[dict[dict]], section_name: str, variable_name: str) -> bool:
    if not _section_exists(hfc_list, section_name):
        return False
    
    for section in hfc_list:
        for section_name in section.keys():
            if variable_name in section[section_name].keys():
                return True

    return False


def _clear_empty_sections(hfc_list: list[dict[dict]]):
    for section in hfc_list:
        if not section:
            hfc_list.remove(section)
        else:
            for section_name in section.keys():
                if section_name == "":
                    hfc_list.remove(section)

    return hfc_list


def parseHfc(hfc_path="", hfc_text="", json_path = "", json_indent=4) -> list[dict[dict]]:
    """
    Parse a HFC text/file to a list of dictionaries.

    Parameters
    ----------
    hfc_path : str
        The path to the HFC file.
    hfc_text : str
        The HFC text to parse.
    json_path : str
        The path to save the parsed HFC as a JSON file. If empty, it won't save.
    json_indent : int
        The indentation of the JSON file. If json_path is empty, it will be ignored.

    Returns
    -------
    list[dict[dict]]
        The parsed HFC as a list of dictionaries, where each dictionary is a section.

    Raises
    ------
    NotHFC
        If the input HFC is invalid.
    SyntaxError
        If the input HFC has invalid syntax.
    """
    parsed = []
    hfc = ""

    # Open the path containing the file
    if hfc_path != "":
        hfc = open(hfc_path, "r").readlines()
        hfc = [_strip(line) for line in hfc] # Let's remove "\n" 
    elif hfc_text != "":
        hfc = hfc_text.split("\n")

    if hfc == "":
        raise NotHFC("Nothing to do.")
    
    # Iterate over it
    sections = 0
    list_index = -1
    section_name = ""
    line_num = 0

    for line in hfc:
        line_num += 1 # The current line  

        # Ignore any line starting with a comment
        for commentchar in langconf.COMMENT_CHARS:
                
            if line.startswith(commentchar):
                continue

        # Section
        if _validate(regex=langconf.SECTION_REGEX, text=line):
            sections += 1
            list_index += 1

            # Separated section name
            section_name = _strip(_replace(line, chars=[langconf.SECTION_SEPARATOR], replace_to=""))
            
            # Check if it's a invalid section name
            for regex in langconf.INVALID_NAME_REGEXES:
                if _validate(regex, section_name):
                    raise SyntaxError(f"Invalid section name at line {line_num}")
            
            parsed.append({f"{section_name}": {}})

        # Variable
        variable_raw = line.split(langconf.VARIABLE_SEPARATOR)
        variable = []
        
        # Let's remove comments from variable declarations
        for declaration in variable_raw:
            dec_correct = [declaration]
            for commentchar in langconf.COMMENT_CHARS:
                dec_correct = dec_correct[0].split(commentchar)

            dec_correct = dec_correct[0] # The final declaration without comments
            
            variable.append(_strip(dec_correct)) # Append to the variable list

        if len(variable) >= 1:
            if variable[0] != "":
                for regex in langconf.INVALID_NAME_REGEXES:
                    if _validate(regex, variable[0]):
                        raise SyntaxError(f"Invalid variable name at line {line_num}")

                # Raise SyntaxError if a variable is declarated outside a section
                if sections <= 0:
                    raise SyntaxError(f"Invalid variable declaration outside a section at line {line_num}.")
                else:
                    value = ""

                    # If variable has no defined value, define it as None
                    if len(variable) <= 1:
                        parsed[list_index][section_name][variable[0]] = None
                    else:
                        value = _get_converted(value=variable[1], line_num=line_num)
                        parsed[list_index][section_name][variable[0]] = value


    if json_path != "":
        # Save as JSON
        import json

        json_p = open(json_path, "w+")
        json.dump(parsed, fp=json_p, indent=json_indent)
        json_p.close()

    return parsed


def parseList(hfc_list: list[dict[dict]], write_path="", newline_after_section=True, spacing=True, list_char=['[', ']'], bool_false="false", bool_true="true", float_separator=".") -> str:
    """
    Parse a list of HFC dictionaries to a HFC string.

    Parameters
    ----------
    hfc_list : list[dict[dict]]
        A list of dictionaries, where each dictionary is a section.
    write_path : str
        The path to write the HFC string to. If empty, it won't write.
    newline_after_section : bool
        If True, it will add a newline after each section.
    spacing : bool
        If True, it will add a space after the section separator and before the variable name.
    list_char : list[str, str]
        The characters to use for lists. The first element is the start character, the second is the end character.
    bool_false : str
        The string to use for False boolean values.
    float_separator : str
        The separator to use for floats. If not specified, it will use the default separator for the language (e.g. "." for English).

    Returns
    -------
    str
        The HFC string.
    """
    
    
    hfc = ""
    space = ""
    newline = ""

    # if spacing is enabled, space is " "
    if spacing:
        space = " "
    
    # New line after section
    if newline_after_section:
        newline = "\n"
    
    hfc_list = _clear_empty_sections(hfc_list)

    for index in hfc_list:
        # Iterate on section dict
        for key, value in index.items():
            hfc += f"{newline}{langconf.SECTION_SEPARATOR}{space}{key}{space}{langconf.SECTION_SEPARATOR}\n{newline}"
            
            for variable, definition in value.items():
                try:
                    conv_definition = _convert_to_hfc(definition, list_char, bool_false, bool_true, float_separator)
                except Exception as e:
                    raise e

                hfc += f"{variable}{space}{langconf.VARIABLE_SEPARATOR}{space}{conv_definition}\n"

    # If write_on is not empty, write the file
    if write_path != "":
        open(f"{write_path}", "w+").write(hfc)

    return hfc


# Add comments to a hfc file or string
def addComments(comments: list[list[int, str]], comment_char="->", input_path="", hfc="", output_path=""):
    """
    Add comments to a HFC file or string.

    Parameters
    ----------
    comments : list[list[int, str]]
        A list of comments, where each comment is a list of two elements: the line number and the comment string.
    comment_char : str
        The character to use for comments.
    input_path : str
        The path to the HFC file to read from. If empty, it won't read from file.
    hfc : str
        The HFC string to write to. If empty, it won't write to a string.
    output_path : str
        The path to write the output to. If empty, it won't write to a file.

    Returns
    -------
    str
        The HFC string with comments.
    """
    hfc_str = ""
    
    if input_path != "":
        hfc_str = open(input_path, "r").readlines()
        # Remove \n on each index
        for index in range(len(hfc_str)):
            hfc_str[index] = hfc_str[index].strip("\n")
    
    if hfc != "":
        hfc_str = hfc.split("\n")

    # If both input_path and hfc are empty, raise error
    if input_path == "" and hfc == "":
        raise ValueError("No input file or HFC string provided")

    # Add comments to the HFC string
    line = 0

    for ln in hfc_str:
        # Look for current line on comments list
        for comment in comments:
            if comment[0] == line+1:
                hfc_str[line] = f"{ln}{comment_char} {comment[1]}"
                break

        line += 1
    
    # Parse to check validity
    try:
        parseHfc("\n".join(hfc_str))
    except Exception as e:
        warnings.warn(f"Generated invalid .hfc string: {e}")

    hfc_str = "\n".join(hfc_str)
    if output_path != "":
        open(output_path, "w+").write(hfc_str)

    return hfc_str


def getComments(hfc_path="", hfc_text="") -> list[list[int, str]]:
    """
    Get comments from a HFC file or string.

    Parameters
    ----------
    hfc_path : str
        The path to the HFC file to read from. If empty, it won't read from file.
    hfc_text : str
        The HFC string to read from. If empty, it won't read from file.

    Returns
    -------
    list[list[int, str]]
        A list of comments, where each comment is a list of two elements: the line number and the comment string.
    """
    comments = []

    if hfc_path != "":
        hfc_str = open(hfc_path, "r").readlines()
        # Remove \n on each index
        for index in range(len(hfc_str)):
            hfc_str[index] = hfc_str[index].strip("\n")
    elif hfc_text != "":
        hfc_str = hfc_text.split("\n")
    else:
        raise ValueError("No input file or HFC string provided")

    # Look for comments
    for comment_char in langconf.COMMENT_CHARS:
        line = 0
        for ln in hfc_str:
            split_ln = ln.split(comment_char)
            split_ln[-1] = _strip(split_ln[-1])

            if len(split_ln) > 1:
                comments.append([line+1, split_ln[1]])
            elif len(split_ln) == 1:
                if ln.startswith(comment_char):
                    comments.append([line+1, ln[len(comment_char):]])

            line += 1

    return comments


# Add a section to a hfc list
def addSection(section_name: str, hfc_list: list[dict[dict]]):
    """
    Add a section to a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the new section.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.
    """
    
    list_add = hfc_list
    list_add.append({section_name: {}})
    
    return list_add


# Remove a section from a hfc text or list
def removeSection(section_name: str, hfc_list: list[dict[dict]]):
    """
    Remove a section from a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section to be removed.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list.
    """
    
    list_remove = hfc_list

    if not _section_exists(list_remove, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")
    
    list_remove.remove({section_name: {}})

    return list_remove


# Edit a section in a hfc list
def editSection(section_name: str, new_section_name: str, hfc_list: list[dict[dict]]):
    """
    Edit a section name in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section to be edited.
    new_section_name : str
        The new name for the section.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list.
    """
    
    list_edit = hfc_list

    # Look for section
    index = 0
    if not _section_exists(list_edit, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")

    for section in hfc_list:
        if section_name in section.keys():
            # Edit section name
            list_edit[index][new_section_name] = list_edit[index].pop(section_name)
            break

        index += 1

    
    return list_edit


# Get all sections from a hfc list
def getSections(hfc_list: list[dict[dict]]) -> list[str]:
    """
    Get all sections from a HFC list.

    Parameters
    ----------
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[str]
        A list of all sections in the HFC list.
    """
    
    sections = []
    for i in hfc_list:
        sections.append(list(i.keys())[0])

    return sections


# Get all variables from a section
def getVariables(section_name: str, hfc_list: list[dict[dict]]) -> dict:
    """
    Get all variables from a specified section in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section to get variables from.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    dict
        A dictionary with all variables from the specified section.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list.
    """
    
    list_get = hfc_list

    # Look for section
    if not _section_exists(list_get, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")

    for section in list_get:
        if section_name in section.keys():
            # Get variables
            return section[section_name]
    
    return []

# Get the value of a specific variable (full hfc list)
def getVariableValue(section_name: str, variable_name: str, hfc_list: list[dict[dict]]):
    """
    Get the value of a specific variable in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section where the variable is located.
    variable_name : str
        The name of the variable to get the value of.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    any
        The value of the specified variable.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list or if the variable is not found in the section.
    """
    
    list_get = hfc_list

    # Look for section
    if not _section_exists(list_get, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")

    for section in list_get:
        if section_name in section.keys():
            # Get variable value
            if _variable_exists(list_get, section_name, variable_name):
                return section[section_name][variable_name]
            else:
                raise ValueError(f"Variable {variable_name} not found in section {section_name}")


# Get variable value from a dictionary
def getVariableValueFromDict(variable_name: str, dictionary: dict):
    try:
        return dictionary[variable_name]
    except KeyError:
        raise ValueError(f"Variable {variable_name} not found in dictionary.")


# Add a variable to a hfc list
def addVariable(section_name: str, variable_name: str, variable_value, hfc_list: list[dict[dict]]):
    """
    Add a variable to a specified section in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section where the variable will be added.
    variable_name : str
        The name of the variable to be added.
    variable_value : any
        The value of the variable to be added.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.
    """
    
    list_add = hfc_list
   
    # Look for section
    if not _section_exists(list_add, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")
    
    # Look for section index on list
    index = 0
    for section in list_add:
        if section_name in section.keys():
            # Add variable
            list_add[index][section_name][variable_name] = variable_value
            break

        index += 1
    
    return list_add


# Remove a variable from a hfc list
def removeVariable(section_name: str, variable_name: str, hfc_list: list[dict[dict]]):
    """
    Remove a variable from a specified section in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section where the variable will be removed.
    variable_name : str
        The name of the variable to be removed.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list or if the variable is not found in the section.
    """
    
    list_remove = hfc_list

    if not _section_exists(list_remove, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")
    
    # Look for section index on list
    index = 0
    for section in list_remove:
        if section_name in section.keys():
            # Remove variable
            if _variable_exists(list_remove, section_name, variable_name):
                list_remove[index][section_name].pop(variable_name)
            else:
                raise ValueError(f"Variable {variable_name} not found in section {section_name}")
            break

        index += 1

    # Look for section
    index = 0

    return list_remove


# Rename a variable in a hfc list
def renameVariable(section_name: str, old_variable_name: str, new_variable_name: str, hfc_list: list[dict[dict]]):
    """
    Rename a variable in a specified section in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section where the variable will be renamed.
    old_variable_name : str
        The name of the variable to be renamed.
    new_variable_name : str
        The new name for the variable.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list or if the variable is not found in the section.
    """
    
    list_rename = hfc_list

    # Look for section
    if not _section_exists(list_rename, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")

    index = 0
    for section in hfc_list:
        if section_name in section.keys():
            # Rename variable in section
            if not _variable_exists(list_rename, section_name, old_variable_name):
                raise ValueError(f"Variable {old_variable_name} not found in section {section_name}")
            
            list_rename[index][section_name][new_variable_name] = list_rename[index][section_name].pop(old_variable_name)
            break

        index += 1

    return list_rename


# Edit a variable in a hfc list
def editVariable(section_name: str, variable_name: str, new_variable_value, hfc_list: list[dict[dict]]):
    """
    Edit a variable's value in a specified section of a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section where the variable will be edited.
    variable_name : str
        The name of the variable to be edited.
    new_variable_value : any
        The new value for the variable.
    hfc_list : list[dict[dict]]
        The HFC list to be modified.

    Returns
    -------
    list[dict[dict]]
        The modified HFC list.

    Raises
    ------
    ValueError
        If the section is not found in the HFC list or if the variable is not found in the section.
    """
    list_edit = hfc_list

    # Look for section
    if not _section_exists(list_edit, section_name):
        raise ValueError(f"Section {section_name} not found in HFC list")
    
    index = 0
    for section in hfc_list:
        if section_name in section.keys():
            # Edit variable in section
            if not _variable_exists(list_edit, section_name, variable_name):
                raise ValueError(f"Variable {variable_name} not found in section {section_name}")

            list_edit[index][section_name][variable_name] = new_variable_value
            break

        index += 1

    return list_edit


# Looks for section in hfc list
def findSection(section_name: str, hfc_list: list[dict[dict]]):
    """
    Look for a section in a HFC list.

    Parameters
    ----------
    section_name : str
        The name of the section to be found.
    hfc_list : list[dict[dict]]
        The HFC list to be searched.

    Returns
    -------
    bool
        False if is not found
    dict
        The section and its variables if is found
    """
    if not _section_exists(hfc_list, section_name):
        return False

    for i in hfc_list:
        if section_name in i.keys():
            return i[section_name]
        

# Find all occurrences of a variable in a hfc list
def findVariable(variable_name: str, hfc_list: list[dict[dict]]):
    """
    Find all occurrences of a variable in a HFC list.

    Parameters
    ----------
    variable_name : str
        The name of the variable to be found.
    hfc_list : list[dict[dict]]
        The HFC list to be searched.

    Returns
    -------
    list
        A list of all occurrences of the variable in the HFC list.
    """
    variables = []
    for i in hfc_list:
        for key, value in i.items():
            if variable_name in value.keys():
                variables.append({f"{key}": {variable_name: value[variable_name]}})

    return variables


# Generate a ready-to-use hfc list
def generateHFC():
    """
    Generate an empty HFC list.

    Returns
    -------
    list[dict[dict]]
        An empty HFC list.
    """
    return [{"": {}}]


if __name__ == "__main__":
    hfc_list = parseHfc(hfc_path="speed.hfc")
    print(getVariables("Section 1", hfc_list))
    print(getVariableValue("Section 1", "Variable_1", hfc_list))
    
    print("hfclib.py is not intended to be run directly")
