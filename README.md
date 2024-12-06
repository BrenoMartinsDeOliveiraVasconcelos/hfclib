# Human-friendly configuration file (HFC)

Personal project trying to make a more human readable and writable configuration file standard.

Made in Python, but wanting to make a library for other languages too. Feel free to make a version for your favorite language.

# How to write a valid HFC file
## The basics

Basically, the file is separated in sections. Each section has its own variables.

### Sections

Sections are separated by two `==`, following this syntax:

```
== Section Name ==
[...]
== Section 2 ==
[...]
```
The name can be anything, but **cannot** be an empty value.

### Variables

Variables are separated by a `=` and are dynamically typed based on its content. The following list shows the types.

| Type | Content |
| ------ | ------ |
| string | Anything starting and ending with `"` |
| integer | Any non-float point number |
| float | Any number containg exactly `.` or `,` between variable content |
| true_boolean | `yes`, `true`, `sim`, `verdadeiro`, `y` or `s`|
| false_boolean | `no`, `false`, `nao`, `false` or `n`|
| void | No content |

Variable naming can contain spaces, special charcters, alphanumerics, just numbers and anything but only spaces or `=`. 

This is a valid variable:

```
name = "breno"
```

Also valid vaarible:

```
user name = "breno"
```

Invalid variable:

```
user=name = "breno"
```

### Lists

Lists are anything that starts and ends with either `[` and `]` or `(` and `)`. They can have any type of value, following the variable type definitions (except for void, which are not accepted in any list). List indexes are separated with `, `. Knowing this, you can write any list as you would do at any programming language.

Valid list:
```
admins = []
```

Also valid:

```
admins = ["root"]
```

Also valid:

```
admins = ["root", "breno"]
```
**Disclaimer: Nestled lists are partially supported, raising error after 2 layers.**

### Comments

This configuration file standard supports one-line comments, which will be ignored while parsing. Comments can be written using `->`, `#` and `//`.

```
-> Comment
// Coment 2
# Comment 3
```

## Example

Here's an example of a valid hfc file.

```
== Server ==

ip = "192.168.1.10" -> Server ip
port = 8080 // Server port
uri_list = ["home", "panel", "userProfile", "settings"] # List of uris
mode = 1 # 0 is production, 1 is development

== User Management ==

admins = ["root", "robert", "john", "jacob", "victoria"]

== Database ==

db_server = "192.168.1.11" // IP of database server
port = 1433
login = "root"
password = "root"
database = "webserver"
```

Run sample.py for testing if you want to.

# Documentation
## Python (hfclib.py)

hfclib.py is the Python implementation of hfc file format.

### parseHFC(hfc_path="", hfc_text="", json_path = "", json_indent=4)

parseHFC() is a function that parses either a .hfc file or a hfc-valid string to a json-like object or a .json file.

It has the following arguments.

| Arg | Optional? | Content |Type |
| ------ | ------ | ------ | ------ |
| hfc_path | Yes | Path to a .hfc file | str |
| hfc_text | Yes | A hfc-valid string | str |
| json_path | Yes | Path to write a .json erquivalent if desired | str |
| json_ident | Yes | Identation to write .json | int |

Always outputs a json-like object.

**Disclaimer: It's mandatory to specify either a hfc_path or a hfc_text, otherwise it will raise an error.**


### parseList(hfc_list: list[dict[dict]], write_path="", newline_after_section=True, spacing=True, list_char=['[', ']'], bool_false="false", bool_true="true", float_separator=".")

parseList() is a function that parses a json-like hfc-valid object to a hfc-valid string or a .hfc file.

It has the following argumments.

| Arg | Optional? | Content |Type |
| ------ | ------ | ------ | ------ |
| hfc_list | No | json-like hfc-valid object | list[dict[dict]] |
| write_path | Yes | Path to write to | str |
| newline_after_section | Yes | Boolean. True will add a newline after a section | bool |
| spacing | Yes | Boolean. If True, it will add spacing to declarations | bool |
| list_char | Yes | Chars that defines a list | list[str, str] |
| bool_false | Yes | The word used for false booleans | str |
| bool_true | Yes | The word used for true booleans | str |
| float_separator | Yes | Float separator | str |

Always returns a hfc-like string.

**Disclaimer: If you change a value to something invalid, it may generate an invalid .hfc file.**

### addComments(comments: list[list[int, str]], comment_char="->", input_path="", hfc="", output_path="")

Add comments to a hfc file or string.

Args:

| Arg | Optional? | Content |Type |
| ------ | ------ | ------ | ------ |
| comments | No | List containing lists defining the line and the comment | list[list[int, str]] |
| comment_char | Yes | String used to comment | str |
| input_path | Yes | The file that the hfc string will be extracted from | str |
| hfc | Yes | An hfc-like string | str |
| output_path | Yes | Path where the hfc string will be outputed | str |

Always returns a hfc-like string. 

**Disclaimer: Invalid args may generate an invalid hfc string.**


**Disclaimer 2: You need to specify either an input_path or a hfc. Not specifing any of them will raise an error.**

