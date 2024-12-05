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

