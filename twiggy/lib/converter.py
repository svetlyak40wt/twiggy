import copy

class Converter(object):
    """Holder for ConversionTable items

    :ivar key: the key to apply the conversion to
    :ivar function convertValue: one-argument function to convert the value
    :ivar function convertItem: two-argument function converting the key & converted value
    :ivar bool required: is the item required to present
    """

    __slots__ = ['key', 'convertValue', 'convertItem', 'required']

    def __init__(self, key, convertValue, convertItem, required = False):
        self.key = key
        self.convertValue = convertValue
        self.convertItem = convertItem
        self.required = required

    def __repr__(self):
        # XXX perhaps poke around in convertValue/convertItem to see if we can extract a meaningul
        # `"some_string".format`? eh.
        return "<Converter('{}', {}, {}, {})>".format(self.key, self.convertValue, self.convertItem, self.required)

class ConversionTable(list):
    """Converts dictionaries using Converters

    For each item, one or more corresponding Converters *c* are found by
    matching key. A list is built by calling c.convertItem(item_key,
    c.convertValue(item_value)) in the same order as converters are supplied.
    Any values for which no Converter is found are sorted by key, passed to
    genericValue/genericItem and appended. If any required items are missing,
    ValueError is raised. The resulting list is passed to aggregate, and its
    return value is returned as the result of the conversion.

    Users may override genericValue/genericItem/aggregate by subclassing or
    assigning a new function on a ConversionTable instance.

    Really, it's pretty intuitive.

    >>> 8*8
    64

    Math is hard:

    >>> 2+2
    4

    """

    def __init__(self, seq):
        """
        :arg seq: a sequence of Converters, arg tuples or kwarg dicts (which
        will be used to create Converters)
        """

        super(ConversionTable, self).__init__([])
        for i in seq:
            if isinstance(i, Converter):
                self.append(i)
            elif isinstance(i, (tuple, list)) and len(i) in (3, 4):
                self.add(*i)
            elif isinstance(i, dict):
                self.add(**i)
            else:
                raise ValueError("Bad converter: {0!r}".format(i))

        # XXX cache converts & requireds below

    @staticmethod
    def genericValue(value):
        """convert values for which no specific Converter is supplied"""
        return value

    @staticmethod
    def genericItem(key, value):
        """convert items for which no specific Converter is supplied"""
        return key, value

    @staticmethod
    def aggregate(converteds):
        """aggregate the list of converted items"""
        return dict(converteds)

    def convert(self, d):
        """do the conversion.  See class docstring"""
        # XXX I could be much faster & efficient!
        # XXX I have written this pattern at least 10 times
        converts = set(x.key for x in self)
        avail = set(d.iterkeys())
        required = set(x.key for x in self if x.required)
        missing = required - avail

        if missing:
            raise ValueError("Missing fields {0}".format(list(missing)))

        l = []
        for c in self:
            if c.key in d:
                item = c.convertItem(c.key, c.convertValue(d[c.key]))
                if item is not None:
                    l.append(item)

        for key in sorted(avail - converts):
            item = self.genericItem(key, self.genericValue(d[key]))
            if item is not None:
                l.append(item)

        return self.aggregate(l)

    def copy(self):
        """Make an independent copy"""
        return copy.deepcopy(self)

    def get(self, key):
        """return the *first* Converter for key"""
        for c in self:
            if c.key == key:
                return c

    def getAll(self, key):
        """return a list of all Converters for key"""
        return [c for c in self if c.key == key]

    def add(self, *args, **kwargs):
        """Append a `Converter`. Args & kwargs will be passed through"""
        self.append(Converter(*args, **kwargs))

    def delete(self, key):
        """delete the *all* converters for key"""
        for i, c in enumerate(self):
            if c.key == key:
                del self[i]