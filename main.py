import math
import time

class PycacheEntry():
    def __init__(self, client, snowflake, entry, fetched_time, max_age, entry_instance):
        # private reference to client for access to
        # client methods
        self._client = client

        # private reference to the snowflake instance
        # passed to `__init__`
        # this contains the following attributes:
            # - epoch (42 bit integer, the snowflake's epoch timestamp in milliseconds)
            # - snowflake (64 bit integer)
            # - pid (5 bit integer)
            # - seed (5 bit integer)
            # - sequence (12 bit integer)
            # - string() (returns `snowflake.snowflake` in string format)
            # - timestamp(fmt) (returns the snowflake's creation timestamp
            #   in milliseconds by default, or seconds if `fmt` is defined as `s`)
        # the client is responsible for ensuring an instance of a
        # pyflake `Snowflake` class is passed here
        self._snowflake = snowflake

        # record the creation time of this entry
        # this is to reference the initial time
        # the cache stored this entry
        self._cached_time = math.floor(time.time() * 1000)

        # the client is responsible for defining when the entry
        # was obtained from its source
        # this value should reflect the last time the
        # value for this entry was fetched or otherwise updated
        # by the client
        self._fetched_time = fetched_time

        # the client is responsible for defining when the
        # entry should expire. A value of `None` or `0` will
        # ensure the record never expires
        self._max_age = max_age

        # this is to assist with update operations
        # since I don't trust making copies of items
        # when the contents are unknown
        # making either a shallow or a deep copy
        # can leave objects with to little or too much
        # information
        # it is also difficult to leave this up to the
        # requesting client, so we record this to handle
        # rollbacks and patching internally
        # that means it's up to the client to explicitly
        # declare the type of value being stored
        # that also means the client is responsible for
        # implementing both a `serialize()` and an `update()`
        # method on any mutable data type stored in the cache
        # attempting to update mutable data types without
        # those methods will raise a descriptive `AttributeError`
        self._value_instance = entry_instance

        # a permanent ID value that should never change
        # over the lifetime of the entry
        self.idx = snowflake.snowflake

        # a string type version of the record's ID
        # the original ID is expected to be a long integer
        # some applications may consider this a 'bigint'
        # and string values are often easier substitutes
        self.idx_string = snowflake.string()

        # the actual constructed entry value
        # the client is responsible for constructing
        # the entry value prior to storing it in the cache
        # it should need no additional initialization after
        # construction, as rollback and patching activities
        # may reconstruct the value on operation failure
        self.value = entry

    # boolean response
    def is_immutable(self):
        if self._value_instance == int or self._value_instance == str or self._value_instance == float or self._value_instance == complex or self._value_instance == bool or self._value_instance == tuple or self._value_instance == frozenset:
            return True
        else:
            return False


    # boolean response
    # checks if the client has defined a 'max_age' property
    # if the max age (or default) is greater than zero
    # milliseconds the entry's snowflake timestamp is
    # compared to the current timestamp to confirm the
    # age of the record, and report True/False respectively
    def is_stale(self):
        if self._max_age == 0 or self._max_age == None:
            # if the record's max_age is set to zero or none
            # the record should never expire
            return False
        elif (math.floor(time.time() * 1000) - self._fetched_time) > self._max_age:
            # if the record's age in milliseconds is greater than
            # the allowed max_age in milliseconds, the entry
            # is considered 'stale' or 'expired'
            return True
        else:
            # if the age in milliseconds is less than the allowed
            # max_age in millseconds, the record is considered
            # 'fresh' or 'not expired'
            return False

    # wrapper method to update entry values. fetching should
    # not happen within the entry. requesting clients should
    # pass already-fetched values to this function and update
    # them with defined local methods
    def update(self, fetched_time, entry):
        # if the value is immutable, it may be updated with
        # simple attribute value reassignment
        if self.is_immutable():
            # update the value
            setattr(self, 'value', entry)
            # update the fetched time
            setattr(self, '_fetched_time', fetched_time)

        # if the new entry value is immutable, there is little
        # purpose in verifying the current entry value has either an
        # `update()` or a `serialize()` method available
        # let's put the responsibility for validating entry values
        # back on the clients requesting to have them cached
        elif isinstance(entry, str) or isinstance(entry, int) or isinstance(entry, bool) or isinstance(entry, float) or isinstance(entry, complex) or isinstance(entry, tuple) or isinstance(entry, frozenset):
            # update the value
            setattr(self, 'value', entry)
            # update the fetched time
            setattr(self, '_fetched_time', fetched_time)

        # for mutable values, such as class instances, the attached value
        # must have a local `update` method available in order for the value
        # to be updated. This allows the client to flexibly define how
        # each cached record is updated based on the data contained within
        elif hasattr(self.value, 'update'):
            if callable(getattr(self.value, 'update', None)):
                # the client is responsible for handling all updates
                # and returning relevant data, if any, via the
                # entry value's local update method

                # the client is also responsible for handling any
                # exceptions raised once the `update` method has been
                # called.

                # clone the current value in case something goes awry
                # the value's intended instance should accept the entire
                # returned value of the entry's `serialize()` method

                # the client is responsible for handling exceptions
                # raised during instance construction
                clone = self._value_instance(self.serialize())

                # attempt the update
                try:
                    # store the returned update value in case the client
                    # wants something back after the update completes
                    # since the local `update()` method is responsible
                    # for ensurng its update completes successfully
                    # there is little purpose in verifying updates here
                    # the client should be responsible for validating update
                    # operatiions by evaluating values returned from their
                    # defined `update()` methods
                    res = self.value.update(entry)

                    # update the fetched time
                    setattr(self, '_fetched_time', fetched_time)

                    # finally, return the `update()` method response
                    return res

                except Exception as e:
                    # if something goes wrong, we want to roll back the entry
                    # to its state prior to the update, and the `_fetched_time`
                    # value won't be updated
                    setattr(self, 'value', clone)

                    # the client is responsible for defining exceptions
                    # that need to be caught and handling any exceptions
                    # raised by their defined `update()` methods
                    # since the client may define unknown exceptions
                    # there is little purpose in attempting to define them
                    # all here - simply pass the exception through
                    raise e
            else:
                # if the client has defined an `update` attribute, but it
                # is not callable, as may be the case when assigning
                # a static value (not a function) to an attribute
                # named `update`, an AttributeError should be raised
                # the client is responsible for handling this exception
                raise AttributeError('Entry cannot be updated: Available \`UPDATE\` attribute is not callable.')

        else:
            # if the current or provided entry value is mutable and
            # the client has not defined an `update()` method an
            # AttributeError should be raised
            # the client is responsible for handling this exception

            # the option to outright construct a new value using
            # `self._value_instance(entry)` is not invalid - I
            # just think it's good process for the requesting client
            # to validate their own data before trying to store it
            # if PycacheEntry asks for it, it should be defined, no exceptions!
            raise AttributeError('Entry cannot be updated: No available \`UPDATE\` method found.')

    # wrapper method to serialize entry values
    def serialize(self):
        # if the value is immutable, it may be returned as-is
        if self.is_immutable():
            return self.value

        # entries where the value is expected to be unknown
        # they are required to also have a `serialize()` method available
        # returning only the values necessary to reconstruct the entry
        # via its `_value_instance` if necessary
        elif hasattr(self.value, 'serialize'):
            if callable(getattr(self.value, 'serialize', None)):
                return self.value.serialize()

            else:
                # if the client has defined an `serialize` attribute, but it
                # is not callable, as may be the case when assigning
                # a static value (not a function) to an attribute
                # named `serialize`, an AttributeError should be raised
                # the client is responsible for handling this exception
                raise AttributeError('Entry cannot be serialized: Available \`SERIALIZE\` attribute is not callable.')
        else:
            # if the current or provided entry value is mutable and
            # the client has not defined an `update()` method an
            # AttributeError should be raised
            # the client is responsible for handling this exception
            raise AttributeError('Entry cannot be serialized: No available \`SERIALIZE\` method found.')


class Pycache():
    def __init__(self, client):
        self._client = client
        self._cache = dict()

    # dict wrapper functions
    def clear(self):
        return self._cache.clear()

    def copy(self):
        return self._cache.copy()

    def fromkeys(self):
        return self._cache.fromkeys()

    def pop(self, idx):
        return self._cache.pop(idx)

    def popitem(self):
        return self._cache.popitem()

    def setdefault(self, prop, val):
        return self._cache.setdefault(prop, val)

    def keys(self):
        return self._cache.keys()

    def values(self):
        return self._cache.values()

    def items(self):
        return self._cache.items()

    def get(self, idx):
        if self._cache.get(idx):
            # requesting clients have no use for our wrapper class
            # so let's just return the value the client asked us
            # to store

            # if clients really want to peek at the info stored in
            # the wrapper class, they can call the 'get()' method on
            # the entry manually via the `_cache` attribute

            # clients are expected to update their entries via
            # acceptable methods, so if updates are made to
            # the value returned, the Pycache may not respect them
            # until updates are explicitely pushed
            return self._cache.get(idx).value
        else:
            raise AttributeError(f'Entry cannot be found: No entry with the ID \`{idx}\` could be found in the cache.')

    # local methods not found in dict

    # to return the total qty of records stored in the cache
    def length(self):
        return len(self._cache)

    # find a number of records that meet a condition
    def find(self, condition):
        # create a dictionary that will store entries that meet
        # the client's requested condition
        res = dict()

        for idx, entry in self.items():
            # conditions are expected to return either True or False
            # if a condition returns True, the client considers this
            # an entry matching the find request and prepares to return
            # the entry to the client

            # the condition should accept only the entry as an argument
            # and should only return either True or False
            if condition(entry) == True:
                res.update([(idx, entry.value)])

        # if the find operation found more than 'zero' entries
        # matching the requested condition, return the dict
        if len(res) > 0:
            return res

        # if no matching entries are found during the find operation
        # an KeyError exception should be raised
        else:
            raise KeyError('Find unsuccessful: No entries found matching the requested conditions.')
            

    # add a new entry to the cache
    # the client is responsible for assigning an ID to the
    # new entry, and the Pycache expects this ID to be an
    # instance of a `Pyflake` class
    def add(self, snowflake, entry, fetched_time, max_age, entry_instance):
        # create an instance of the PycacheEntry class with the client
        # provided values

        # the client is responsible for handling any exceptions raised
        # during PycacheEntry construction
        res = PycacheEntry(self, snowflake, entry, fetched_time, max_age, entry_instance)
        if not self.get(res.idx):
            # add the newly constructed entry to the cache
            self._cache.update([(res.idx, res)])

            # finally, return the new entry to the client
            # requesting clients have no use for our wrapper class
            # so lets just return the value the client asked us
            # to store
            return self.get(res.idx).value
        else:
            raise AttributeError(f'Entry cannot be added: An entry with the provided ID \`{res.idx}\`already exists in the cache.')

    # this method functions differently than `dict.update()`
    # and makes use of a relevant entry's local `update()`
    # method instead of inserting or updating `self._cache`
    # as would be expected with `dict.update()`
    def update(self, idx, entry, fetched_time):
        # instances of PycacheEntry have a local `update` method
        # that method is a pass-thru method that provides some
        # validation in the form of ensuring a valid method
        # to update the entry exists

        # both an `update()` method and a `serialize()` method
        # must be available on mutable data types in order
        # for the cache to be capable of updating them

        # if the cache is unable to update the entry,
        # an AttributeError exception will be raised
        return self.get(idx).update(entry, fetched_time)

    def remove(self, snowflake):
        # if the provided snowflake is a pyflake Snowflake instance
        if hasattr(snowflake, 'snowflake'):
            if self.get(snowflake.snowflake):
                self._cache.pop(snowflake.snowflake)
        else:
            # if the snowflake is just the 64-bit ID
            if isinstance(snowflake, str) or isinstance(snowflake, int):
                if self.get(snowflake):
                    self._cache.pop(snowflake)
        # in all other cases return False
        snowflake_type = type(snowflake)
        raise TypeError(f'Entry cannot be removed: Snowflake expected to be an instance of: \`Pyflake\`, \`str\`, or \`int\`. Received instance of: \`{snowflake_type}\`')

    # returns all records that are stale, based on the `max_age`
    # of the stored record
    def stale(self):
        def is_stale(entry):
            return entry.is_stale()

        return self.find(is_stale)

    # entries that are considered `fresh` or not expired
    # based on the entry's defined `max_age`
    def fresh(self):
        def is_fresh(entry):
            return not entry.is_stale()

        return self.find(is_fresh)

    # this will return values that are instances of
    # dicts, lists, non-frozen sets, and user-defined
    # classes

    # the client expects all mutable objects to have
    # both an `update()` and `serialize()` method
    # or the data will not be updatable and attempts
    # to do so will raise an `AttributeError` exception
    def mutable(self):
        def is_mutable(entry):
            return not entry.is_immutable()

        return self.find(is_mutable)

    # methods to return various subsets of immutable
    # entry values in the cache

    def immutable(self):
        def is_immutable(entry):
            return entry.is_immutable()

        return self.find(is_immutable)

    def str(self):
        def is_str(entry):
            return isinstance(entry.value, str)

        return self.find(is_str)

    def int(self):
        def is_int(entry):
            return isinstance(entry.value, int)

        return self.find(is_int)

    def complex(self):
        def is_complex(entry):
            return isinstance(entry.value, complex)

        return self.find(is_complex)

    def bool(self):
        def is_bool(entry):
            return isinstance(entry.value, bool)

        return self.find(is_bool)

    def frozenset(self):
        def is_frozenset(entry):
            return isinstance(entry.value, frozenset)

        return self.find(is_frozenset)

    def float(self):
        def is_float(entry):
            return isinstance(entry.value, float)

        return self.find(is_float)

    def tuple(self):
        def is_tuple(entry):
            return isinstance(entry.value, tuple)

        return self.find(is_tuple)
