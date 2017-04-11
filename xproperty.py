#!/usr/bin/python
# coding: utf-8

"""
Supports lists of strings and atoms.
"""

import Xlib.display

display = Xlib.display.Display()


def atom_i2s(integer):
    return display.get_atom_name(integer)


def atom_s2i(string):
    i = display.get_atom(string, only_if_exists=True)
    if i == Xlib.X.NONE:
        raise ValueError('No Atom interned with that name.')
    else:
        return i


def get_property(window, name):
    # length field in X11 is 4 bytes, max it out!
    property_int = atom_s2i(name)
    property = window.get_property(property_int, 0, 0, pow(2, 32) - 1)
    if property is None:
        raise ValueError('Window has no property with that name.')
    # bytes_after != 0 if we fetched it too short
    assert property._data['bytes_after'] == 0
    property_type = atom_i2s(property._data['property_type'])
    if property_type == 'STRING':
        # strings should be served byte-wise
        assert property.format == 8
        # string arrays are separated by \x00; some have one at the end as well
        values = property.value.split('\x00')
        return 'STRING', values
    elif property_type == 'ATOM':
        assert property.format == 32
        return 'ATOM', [display.get_atom_name(i) for i in property.value]
    else:
        raise NotImplementedError('I’m sorry, I can handle only STRINGs so far.')


def set_property(window, name, values):
    property_int = atom_s2i(name)
    property = window.get_property(property_int, 0, 0, pow(2, 32) - 1)
    property_type = atom_i2s(property._data['property_type'])
    if property_type == 'STRING':
        value = '\x00'.join(values)
        window.change_property(property_int, atom_s2i('STRING'), 8, str(value))
    elif property_type == 'ATOM':
        import array
        value = array.array('I', [atom_s2i(name) for name in values])
        window.change_property(property_int, atom_s2i('ATOM'), 32, value)

if __name__ == '__main__':
    import sys
    import pipes
    root_window = display.screen().root
    l = len(sys.argv)
    if l <= 1:
        print('No property name given on command line.')
    elif l >= 2:
        property_name = sys.argv[1]
        if l >= 3:
            set_property(root_window, property_name, sys.argv[2:])
        # a final get in any case
        property_type, property_value = get_property(root_window, property_name)
        values = [pipes.quote(value) for value in property_value]
        print(*values)
