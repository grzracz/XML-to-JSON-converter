#   Copyright (c) 2019 Grzegorz Raczek
#   https://github.com/grzracz
#   Files available under MIT license

from threading import Thread
from queue import Queue, LifoQueue as Stack
from datetime import datetime
from re import compile
from sys import argv
import os.path

STARTING_TIME = datetime.now()


def matching_tag(tag):
    """Returns matching tag to the one given

    Args:
        tag (str): Given tag

    Returns:
        str: Matching tag to the one given
    """
    if tag[1] == '/':
        return "<" + tag[2:]
    return "</" + tag[1:]


def last_index(_list, _value):
    """Finds index of value in reversed list and calculates the correct index

    Args:
        _list (list): List of values
        _value (str): Value to be found

    Returns:
        int: Index of value in list

    Raises:
        ValueError: If value was not found in list
    """
    return len(_list) - _list[-1::-1].index(_value) - 1


class Logger:
    """Logging class used for keeping and saving error messages

    Attributes:
        streams (list): List of streams with error messages
        logs_filename (str): Path to logs file
    """

    def __init__(self):
        self.streams = []
        self.logs_filename = "logs.txt"

    def add_stream(self):
        """Creates and returns a new stream that will be used by other classes for logging

        Returns:
            Queue: New error stream
        """
        stream = Queue()
        self.streams.append(stream)
        return stream

    def flush(self, char_count):
        """Flushes all streams with timestamp into logs file

        Args:
            char_count (int): Total number of characters read from input file
        """
        try:
            with open(self.logs_filename, 'a') as logs_file:
                logs_file.write(str(datetime.now()) + '\n# Errors:\n')
                for stream in self.streams:
                    while not stream.empty():
                        logs_file.write(stream.get())
                logs_file.write("#\nDONE: " + str(char_count) + " characters analyzed in " +
                           str((datetime.now() - STARTING_TIME).total_seconds()) + " seconds\n")
                logs_file.write('\n')
                logs_file.close()
        except IOError:
            print("Unable to create " + self.logs_filename + " file.")


class Parser:
    """XML Parser used for reading strings from input file

    Parser reads tags and values, checks if they are correct (on a basic level) and then adds them to queue
    Works as a separate daemon thread to increase working speed
    Code validation is based on XML structure and hardcoded illegal (or non-printable) characters

    Attributes:
        queue (Queue): Queue used for saving parsed strings
        error_stream (Queue): Error stream used for saving error messages
        char_counter (int): Total number of characters read from file
        input_filename (str): Path to input file
        value_tags (list): List of tags with no children (that should have a value inside)
        other_tags (list): List of tags with children
        illegal_characters (str): All illegal characters that should be checked in a single string
        running (bool): True if parser is running, False otherwise
    """

    def __init__(self, _stream, _structure):
        self.queue = Queue()
        self.error_stream = _stream
        self.char_counter = 0
        self.input_filename = "input.xml"
        self.value_tags = []
        self.other_tags = []
        self.build(_structure)
        self.illegal_characters = dict.fromkeys("<>\"'&")
        thread = Thread(target=self.run)
        thread.daemon = True
        thread.start()
        self.running = True

    def build(self, _structure):
        """Recursively adds tags to correct lists based on XML structure

        Args:
            _structure (XMLStructureNode): Top node of XML structure
        """
        if _structure.has_child():
            self.other_tags.append(_structure.value)
            for child in _structure.children:
                self.build(child)
        else:
            self.value_tags.append(_structure.value)

    def error(self, message, string):
        """Sends error message to logger stream in a specific format

        Args:
            message (str): Message describing what happened
            string (str): String on which error occurred
        """
        if len(message) > self.char_counter:
            number = 0
        else:
            number = self.char_counter - len(string)
        if not string.isprintable():
            self.error_stream.put("Char " + str(number) + ": " + message + '\n')
        else:
            self.error_stream.put("Char " + str(number) + ": " + message + ": \"" + string + "\"\n")

    def read_char(self, file):
        """Returns next single character from file

        Args:
            file (file): Open file from which a character should be read

        Returns:
            str: Next single character from file or empty string if file ended
        """
        char = file.read(1)
        if char:
            self.char_counter += 1
            return char
        return None

    def is_value_tag(self, tag):
        """Checks if given tag is in value tags

        Args:
            tag (str): Tag to be checked

        Returns:
            bool: True if tag is childless, False otherwise
        """
        if tag in self.value_tags:
            return True
        return False

    def is_correct_tag(self, tag):
        """Checks if given tag is correct, sends error to logger if not

        Args:
            tag (str): Tag to be checked

        Returns:
            bool: True if tag is viable, False otherwise
        """
        if tag in self.value_tags or tag in self.other_tags:
            return True
        else:
            _matching_tag = matching_tag(tag)
            if _matching_tag in self.value_tags or _matching_tag in self.other_tags:
                return True
        self.error("Found incorrect tag", tag)
        return False

    def is_correct_value(self, value):
        """Checks if given value is correct, sends error to logger if not

        Args:
            value (str): Value to be checked

        Returns:
            bool: True if value is viable, False otherwise
        """
        if any(c in self.illegal_characters for c in value):
            self.error("Found illegal characters in value", value)
            return False
        elif not value.isprintable():
            self.error("Found non-printable characters in value", value)
            return False
        return True

    def run(self):
        """Thread function, parses strings and sends them to queue

        Reads characters from file until eof, logs all errors
        Checks for '<' character to read tag (and '>' to end tag), sends tag to queue if it's correct
        Checks for value after reading value tag, sends it to queue if it's correct
        """
        if not os.path.isfile(self.input_filename):
            print("Could not find " + self.input_filename + " file")
            self.error("Could not find file", self.input_filename)
            self.running = False
        else:
            try:
                with open(self.input_filename) as input_file:
                    read_value = False
                    read_next_char = True
                    while self.running:
                        if not self.queue.full():
                            string = ""
                            if read_next_char:
                                char = self.read_char(input_file)
                            if not char:
                                self.running = False
                                input_file.close()
                                break
                            elif char == '<':
                                read_value = False
                                read_next_char = True
                                string += char
                                while char != '>':
                                    char = self.read_char(input_file)
                                    if not char:
                                        self.running = False
                                        input_file.close()
                                        break
                                    string += char
                                if self.is_correct_tag(string):
                                    if self.is_value_tag(string):
                                        read_value = True
                                    self.queue.put(string)
                            else:
                                read_next_char = False
                                string += char
                                while True:
                                    char = self.read_char(input_file)
                                    if not char:
                                        self.running = False
                                        input_file.close()
                                        break
                                    if char == "<":
                                        break
                                    string += char
                                if read_value:
                                    if self.is_correct_value(string):
                                        self.queue.put(string)
                                    read_value = False
                                else:
                                    if string.strip() != "":
                                        self.error("Found incorrectly placed text", string)
            except IOError:
                self.running = False
                print("Unable to open " + self.input_filename + " file")
                self.error("Unable to open file", self.input_filename)


class XMLStructureNode:
    """Nodes representing XML structure used for building XML objects

    Attributes:
        value (str): Visible in code value of tag (for example <object>)
        parent (XMLStructureNode): Parent node of this node
        children (list): List of XMLStructureNode objects with tags that can be found after this tag
        repeatable (bool): True if tag can be opened multiple times before parent closes, False otherwise
        allowed_values (list): List of allowed values inside tag, None if all allowed or tag is not childless
    """

    def __init__(self, _value, _repeatable=False, _allowed_values=None):
        self.value = _value
        self.parent = None
        self.children = []
        self.repeatable = _repeatable
        self.allowed_values = _allowed_values

    def has_child(self):
        """Checks if node has child

        Returns:
            bool: True if node has children, False otherwise
        """
        if len(self.children) > 0:
            return True
        return False

    def add_child(self, _child):
        """Sets parent of child and adds it to children

        Args:
            _child (XMLStructureNode): Child node to be added
        """
        _child.parent = self
        self.children.append(_child)

    def find_child(self, value):
        """Searches for specific child and returns it if found

        Args:
            value (str): Value to be checked when searching for tag

        Returns:
            XMLStructureNode: Child node with value tag if found, None otherwise
        """
        for child in self.children:
            if child.value == value:
                return child
        return None


class XMLStructureStack:
    """Stack representing depth of XML code

    Attributes:
        stack (LifoQueue): Stack for XMLStructureNode objects
        top (XMLStructureNode): Highest node on stack
    """

    def __init__(self):
        self.stack = Stack()
        self.top = None

    def push(self, node):
        """Adds XMLStructureNode to stack and updates top node

        Args:
            node (XMLStructureNode): Node to be pushed onto stack

        Returns:
            bool: True if node was added, False otherwise
        """
        if not self.stack.full():
            self.top = node
            self.stack.put(node)
            return True
        return False

    def pop(self):
        """Takes last XMLStructureNode from stack and updates top node

        Returns:
            XMLStructureNode: Popped node if successful, None otherwise
        """
        if not self.stack.empty():
            popped = self.stack.get()
            if not self.stack.empty():
                self.top = self.stack.get()
                self.stack.put(self.top)
            else:
                self.top = None
            return popped
        return None


class XMLObject:
    """Class used for creating objects based on XML code

    Attributes:
        structure (XMLStructureNode): Top node of XML structure
        tags (list): List of strings with tags from which object was built
        values (list): Corresponding to tags list with values for those tags
    """

    def __init__(self, _structure):
        self.structure = _structure
        self.tags = []
        self.values = []
        self.build(self.structure)

    def build(self, _structure):
        """Recursively adds tags and empty values based on XML structure

        Args:
            _structure (XMLStructureNode): Top node of XML structure
        """
        if _structure.has_child():
            for child in _structure.children:
                self.build(child)
        else:
            self.tags.append(_structure.value)
            self.values.append(None)

    def tag_to_node(self, _structure, _tag):
        """Recursively finds structure node with given tag then returns it

        Args:
            _structure (XMLStructureNode): Top node of XML structure
            _tag (str): Value to be checked when searching for node

        Returns:
            XMLStructureNode: Node with correct tag if found, None otherwise
        """
        if _structure.value == _tag:
            return _structure
        for child in _structure.children:
            node = self.tag_to_node(child, _tag)
            if node is not None:
                return node
        return None

    def get_value(self, tag, starting_index):
        """Returns corresponding value to given tag and it's index (found after starting index)

        Args:
            tag (str): Tag from which value should be read
            starting_index (int): Number of tag after which function should start looking for tag

        Returns:
            str: value of tag if found, None otherwise
            int: index of tag if found, -1 otherwise
        """
        if starting_index is None or starting_index >= len(self.tags):
            return None, -1
        try:
            index = self.tags.index(tag, starting_index)
            return self.values[index], index
        except ValueError:
            return None, -1

    def set_value(self, tag, value, error):
        """Sets value of last tag with given name, sends error if incorrect call

        This function will create additional tags for a repeatable node

        Args:
            tag (str): Tag to which value should be saved
            value (str): Value to be saved
            error (method): Error method used for sending errors to logger

        Returns:
            bool: True if value added without errors, False otherwise
        """
        index = last_index(self.tags, tag)
        node = self.tag_to_node(self.structure, tag)
        if self.values[index] is not None:
            if node is not None and node.parent.repeatable:
                self.build(node.parent)
                index = last_index(self.tags, tag)
            else:
                error("Duplicate value definition", tag)
                return False
        if node.allowed_values is not None:
            if value in node.allowed_values:
                self.values[index] = value
                return True
            else:
                error("Value \"" + value + "\" is not allowed in this tag", tag)
                return False
        else:
            self.values[index] = value
            return True


class Converter:
    """Converter reading strings from parser queue, analyzing them and converting to JSON code

    Converter reads tags and values and checks if they are correct together (complex checks)
    Creates a new XMLObject for each object tag then sends it to a list of objects if the object ended correctly
    Creates JSON code based on created objects then flushes it to output file

    Attributes:
        stack (XMLStructureStack): Stack of XMLStructureNode objects representing XML code depth
        error_stream (Queue): Error stream used for saving error messages
        parser (Parser): Parser responsible for creating queue of strings from file
        string_counter (int): Total number of strings read from parser
        output_filename (str): Path to output file
        structure (XMLStructureNode): Top node of XML structure
        current_object (XMLObject): Object that is currently being created
        objects (list): List of created XML objects
    """

    def __init__(self, _stream, _parser, _structure):
        self.stack = XMLStructureStack()
        self.error_stream = _stream
        self.parser = _parser
        self.string_counter = 0
        self.output_filename = "output.json"
        self.structure = _structure
        self.current_object = XMLObject(self.structure)
        self.objects = []

    def error(self, message, string):
        """Sends error message to logger stream in a specific format

        Args:
            message (str): Message describing what happened
            string (str): String on which error occurred
        """
        if string is not None:
            self.error_stream.put("String " + str(self.string_counter) + ": " + message + ": \"" + string + "\"\n")
        else:
            self.error_stream.put("String " + str(self.string_counter) + ": " + message + '\n')

    def obj_error(self, number, message):
        """Sends error message to logger stream in a specific format

        Args:
            number (int): Object number
            message (str): Message describing what happened
        """
        if number == -1:
            self.error_stream.put(message + '\n')
        else:
            self.error_stream.put("Object " + str(number) + ": " + message + '\n')

    def read_string(self):
        """Reads next string from parser queue

        Returns:
            str: Next string in queue, None if queue is empty
        """
        if not self.parser.queue.empty():
            self.string_counter += 1
            return self.parser.queue.get()
        return None

    def flush(self, json):
        """Flushes JSON code to output file, checks for trailing comma errors

        Args:
            json (Queue): Lines of JSON code
        """
        if json.empty():
            self.error("Nothing to write to file", self.output_filename)
            return
        string1 = json.get()
        string2 = json.get()
        if json.empty():
            self.obj_error(-1, "Final object: JSON body is empty, nothing to write")
            return
        try:
            no_trailing_comma = ["}", "\t },\n"]
            with open(self.output_filename, 'w') as output_file:
                output_file.write(string1)
                while not json.empty() and string1 is not None:
                    string1 = string2
                    string2 = json.get()
                    if string2 in no_trailing_comma:
                        string1 = string1.replace(',', "", len(string1) - 2)
                    output_file.write(string1)
                output_file.write(string2)
                output_file.close()
        except IOError:
            print("Unable to create " + self.output_filename + " file")
            self.error("Unable to create file", self.output_filename)

    def convert(self):
        """Converts created objects to JSON code

        Converts list of created objects to JSON code, putting all lines of code into queue
        Checks if object fields are filled and if filled values are correct
        This is the only hardcoded function in the script, needs to be changed if structure changes

        Returns:
            Queue: Lines of JSON code
        """
        json = Queue()
        json.put("{\n")
        object_number = 0
        object_names = []
        for xml_object in self.objects:
            index = 0
            object_number += 1
            object_name, index = xml_object.get_value("<obj_name>", index)
            if object_name in object_names:
                self.obj_error(object_number, "Duplicate object name: \"" + object_name + "\"")
                continue
            elif object_name is not None:
                correct_object = False
                while index != -1:
                    f_name, index = xml_object.get_value("<name>", index + 1)
                    if index == -1:
                        break
                    f_type, index = xml_object.get_value("<type>", index + 1)
                    f_value, index = xml_object.get_value("<value>", index + 1)
                    if f_name is None or f_type is None or f_value is None:
                        self.obj_error(object_number, "Required fields were not filled")
                        continue
                    elif f_type == "int" and not f_value.isdigit():
                        self.obj_error(object_number, "Field value is not an integer: \"" + f_value + "\"")
                        continue
                    else:
                        if not correct_object:
                            object_names.append(object_name)
                            json.put("\t \"" + object_name + "\": {\n")
                            correct_object = True
                        json.put("\t\t\"" + f_name + "\": " + ("\"" if f_type == "string" else "") +
                                 f_value + ("\"" if f_type == "string" else "") + ",\n")
                if correct_object:
                    json.put("\t },\n")
            else:
                self.obj_error(object_number, "Object name was not set")
                continue
        json.put("}")
        return json

    def run(self):
        """Main script function, reads all strings from parser queue, analyzes them and creates output file

        Uses XMLStructureStack to remember current depth of XML code and pushes/pops values from it based on what is
        read from queue and XML structure
        Builds a new XMLObject for each highest level tag,
        sends that object to a list of objects if that tag ends correctly

        Decision tree:
        while there is something to read:
            A) if object was opened:
                a) if string is a closing tag:
                    pop stack
                b) if string is an incorrect closing tag:
                    send error
                c) if current xml tag has children:
                    1) if string opens child:
                        push child onto stack
                    2) if string is the same as current xml tag:
                        send error
                    3) if other:
                        send error, pop stack to correct point
                d) if current xml tag has no children:
                    1) if string is a tag:
                        send error, pop stack to correct point
                    2) if string is a value:
                        set value to object, get closing tag and check it, pop stack
            B) if object was not opened:
                a) if string is object opening tag:
                    create object, push top level structure to stack
                b) else:
                    send error
        then convert created objects to JSON code and flush it to file
        """
        while self.parser.running or not self.parser.queue.empty():
            if self.stack.top is not None:
                string = self.read_string()
                if string is not None:
                    if string == matching_tag(self.stack.top.value):
                        if self.stack.top.value == self.structure.value:
                            self.objects.append(self.current_object)
                        self.stack.pop()
                    elif len(string) > 2 and string[1] == "/":
                        self.error("Not a proper closing tag to " + self.stack.top.value,
                                   string)
                    elif self.stack.top.has_child():
                        child_node = self.stack.top.find_child(string)
                        if child_node is not None:
                            self.stack.push(child_node)
                        elif self.stack.top.value == string:
                            self.error("Current tag was opened again", string)
                        else:
                            self.error("This does not belong after " + self.stack.top.value + " tag", string)
                            self.stack.pop()
                            while self.stack.top is not None:
                                child_node = self.stack.top.find_child(string)
                                if child_node is not None:
                                    self.stack.push(child_node)
                                    break
                                elif string == self.structure.value and self.stack.top == self.structure:
                                    break
                                self.stack.pop()
                    else:
                        value = string
                        if value is not None:
                            if value[0] == "<":
                                self.error("Found tag instead of value", value)
                                self.stack.pop()
                                while self.stack.top is not None:
                                    child_node = self.stack.top.find_child(value)
                                    if child_node is not None:
                                        self.stack.push(child_node)
                                        break
                                    elif value == self.structure.value and self.stack.top == self.structure:
                                        break
                                    self.stack.pop()
                            else:
                                self.current_object.set_value(self.stack.top.value, value, self.error)
                                closing_tag = self.read_string()
                                if closing_tag is not None:
                                    if closing_tag == matching_tag(self.stack.top.value):
                                        self.stack.pop()
                                    else:
                                        self.error("Not a proper closing tag to " + self.stack.top.value,
                                                   closing_tag)
                                        self.stack.pop()
            else:
                string = self.read_string()
                if string is not None:
                    if string == self.structure.value:
                        self.stack.push(self.structure)
                        self.current_object = XMLObject(self.structure)
                    else:
                        self.error("Found text before " + self.structure.value + " tag was opened", string)
        if len(self.objects) > 0:
            json = self.convert()
            self.flush(json)


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

# Create error logger and XML code parser
logger = Logger()
parser = Parser(logger.add_stream(), object_tag)

# Create XML to JSON converter and run it (after parser starts running)
converter = Converter(logger.add_stream(), parser, object_tag)
converter.run()

# Create logs file if user asks for it
if len(argv) > 1 and argv[1] == "-l":
    logger.flush(parser.char_counter)
