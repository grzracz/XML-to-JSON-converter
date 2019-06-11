# XML to JSON converter
*Written on 6 May 2019.*

Written in Python using **threading, queue, datetime, re, sys** and **os.path** libraries.

Reads input code from **input.xml** file (has to be in the same folder as the script) then reads tags from the file based on the hardcoded structure.
Valid XML tags and values are sent to queue for further analysis and conversion.
All errors are saved to logger that will create a **logs.txt** file if the script is used with the command **-l**.
Converted JSON code is saved to **output.json** file.

# Usage:

> python XMLtoJSON.py -l

- Input XML code:

```
<object>
	<obj_name>hero hero</obj_name>
	<field>
		<name>favorite_snack</name>
		<type>string</type>
		<value>Chips</value>
	</field>
	<field>
		<name>hero</name>
		<type>string</type>
		<value>superman</value>
	</field>
	<field>
		<name>age</name>
		<type>int</type>
		<value>43</value>
	</field>
</object>
<object>
	<obj_name>another hero</obj_name>
	<field>
		<name>favorite_movie</name>
		<type>string</type>
		<value>John Wick 3</value>
	</field>
	<field>
		<name>hero</name>
		<type>string</type>
		<value>John Wick</value>
	</field>
	<field>
		<name>age</name>
		<type>int</type>
		<value>19</value>
	</field>
</object>
<object>
	<obj_name>random object</obj_name>
	<field>
		<name>color</name>
		<type>string</type>
		<value>turbo red</value>
	</field>
</object>
<object>
	<obj_name></obj_name>
</object>
<object>
	<obj_name>another random object</obj_name>
	<field>
		<name>color</name>
		<type>string</name>
	</field>
 <wrongfield>heh"</wrongfield>
	<field>
		<name>color</name>
		<type>int</type>
		<value>333</value>
	</field>
</object>
<object>
	<obj_name>Ultimate Gauntlet of Destruction </obj_name>
	<field>
		<name>Strength</name>
		<type>int</type>
		<value>9999</value>
	</field>
</object>
```

- Hardcoded XML structure:

```
# Create XML structure for code validation
"""
<object>
    <obj_name>
    <field> repeatable
        <name>
        <type> only ["int", "string"]
        <value>
"""
field_tag = XMLStructureNode("<field>", True)
field_tag.add_child(XMLStructureNode("<name>"))
field_tag.add_child(XMLStructureNode("<type>", False, ["int", "string"]))
field_tag.add_child(XMLStructureNode("<value>"))
object_tag = XMLStructureNode("<object>", True)
object_tag.add_child(XMLStructureNode("<obj_name>"))
object_tag.add_child(field_tag)
```

- Output JSON code:

```
{
	 "hero hero": {
		"favorite_snack": "Chips",
		"hero": "superman",
		"age": 43
	 },
	 "another hero": {
		"favorite_movie": "John Wick 3",
		"hero": "John Wick",
		"age": 19
	 },
	 "random object": {
		"color": "turbo red"
	 },
	 "another random object": {
		"color": 333
	 },
	 "Ultimate Gauntlet of Destruction ": {
		"Strength": 9999
	 }
}
```

- Output logs.txt file:

```
2019-06-11 11:07:54.031684
# Errors:
Char 930: Found incorrect tag: "<wrongfield>"
Char 943: Found incorrectly placed text: "heh""
Char 946: Found incorrect tag: "</wrongfield>"
String 107: Not a proper closing tag to <type>: "</name>"
Object 4: Object name was not set
Object 5: Required fields were not filled
#
DONE: 1208 characters analyzed in 0.080385 seconds
```
