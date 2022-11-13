# pycacher
A simple Python 3.10 entry-based data cacher that supports mutable and immutable data types, including user-defined class instances.

# Features
- `PycacheEntry` - A wrapper class that allows `Pycache` instances to easily manage cache entries
- `Pycache` - A `dict` manager class to aid in the management of `PycacheEntries` for their life within the cache

# Requirements
- Python 3.10

## Indirect requirements
- Pyflake v0.0.0 - While not imported, this package is required to generate the `Pyflake` instances requested to identify entries cached by the `Pycache`

## Core modules imported
- time - used to generate timestamp values
- math - used to ensure timestamp values are `int` and not `float`

# Usage
```python
  import time
  import math
  from pyflake import PyflakeClient, generate_seed
  from pycacher import Pycache
  
  # a generator is only required if you need to generate snowflakes
  # if you already 'own' snowflake instances, this is unnecessary
  epoch = time.time()
  generator = PyflakeClient(epoch)

  pid = generate_seed(5)
  seed = generate_seed(5)
  generator.make_generator(pid, seed)

  # create a cache instance to use
  cache = Pycache()
  
  # add an item to the cache - lets assume it's brand new
  # and has not yet been assigned an ID
  # the generator returns a Snowflake instance, which
  # has multiple attribute that the `Pycache` relies on
  # to manage stored records
  idx = generator.generate()
  
  # create an entry value that will be stored in the cache
  # for this example we use an immutable data time
  # so we don't have to implement an `update()` or
  # `serialize()` method
  entry = 'test_entry'
  
  # `Pycache` requires every entry to define when the data was
  # obtained from the source
  # since we created the entry here, the 'fetched_time'
  # is 'now'
  # multiply by 1000 to return the timestamp in milliseconds
  fetched_time = math.floor(time.time() * 1000)
  
  # Pycache does not require entries to expire, but allows
  # clients to define an age, in milliseconds, at which an
  # entry may expire.
  # 60000 = 60 seconds = 1 minute
  max_age = 60000
  
  # Pycache requires that every entry has a defined data type
  # since this entry is a 'string' value, we define it here
  entry_instance = str
  
  # finally, we can add the entry to the cache
  cache.add(idx, entry, fetched_time, 60000, str)
  
  # to fetch the new entry, we need to know its ID
  found_entry = cache.get(idx)
  
  # to update an entry that already exists in the cache
  # the cache's `update()` method should be called
  # this requires all stored values to have a local
  # `update()` method that updates entry
  # values, and a `serialize()` method to return only the
  # values required to reconstruct the entry if necessary.
  
  # immutable values, such as strings and integers, are
  # not required to have `update()` or `serialize()` methods
  # as these values are updated via attribute value reassignment
  updated_entry = 'updated_test_entry'
  fetched_time = math.floor(time.time() * 1000)
  cache.update(idx, updated_entry, fetched_time)
  
  # additionally, the entry's `update()` method may be called
  # instead, making it easy to update an entry accessed outside
  # of the `Pyclient._cache`
  known_entry.update(updated_entry, fetched_time)
  
  # to find one or more records that meet a condition, the cache's
  # `find()` method should be called, and a conditional function
  # returning a `bool` value should be passed.
  def is_not_none(entry):
    # the core content of an entry is found in the entry's `value`
    # attribute. Cache-related metadata is also available, but the
    # majority of application logic will be looking toward `entry.value`
    # for most, if not all evaluation
    if not entry.value == None:
      return True
    else:
      return False
  known_entries = cache.find(is_not_none)
  
  # to remove an entry that exists in the cache, the cache's
  # `remove()` method should be called.
  # entries do not have a local `remove()` method and should
  # never be removed from an external cache that holds it by
  # calling an internal method
  
  # the `Pycache` expects to receive a fully constructed `Pyflake`
  # instance at removal
  if len(known_entries) > 0:
    for entry in known_entries:
      cache.remove(idx)
  
  # there are several methods available in a `Pycache` instance
  # that makes managing the local cache as easy as managing a
  # `dict` without being a direct extension of a `dict` data type
  
  # `cache.clear()` will clear the cache of all available entries
  cache.clear()
  
  # `cache.copy()` will return an exact copy of the cache in its current state
  # this returns a `dict`, not a `Pycache`
  cache_copy = cache.copy()
  
  # `cache.pop(idx)` will remove and return the cache entry with the
  # specified `idx`
  cache_popped = cache.pop(idx)
  
  # `cache.popitem()` will remove and return the last inserted cache entry
  cache_last = cache.popitem()
  
  # `cache.setdefault(idx, value)` will return the cache entry with
  # the specified index, inserting it if it does not exist
  # this acts like an `upsert` operation
  cache_upsert = cache.setdefault(idx, value)
  
  # `cache.keys()` will return keys for all cache entries
  cache_keys = cache.keys()

  # `cache.values()` will return all `entry.value` attribute values
  cache_values = cache.values()

  # `cache.items()` will return [ k, v ] pairs of all cache entries
  cache_items = cache.items()
  
  # `cache.length()` will return the quantity of entries in the cache
  cache_length = cache.length()
  
  # `cache.stale()` will return a `dict` of stale cache entries
  # the `freshness` of a cache entry is determined by its `max_age`
  # attribute value, representing the milliseconds the record is
  # considered `fresh` before becoming `stale`
  cache_stale = cache.stale()
  
  # `cache.fresh()` will return a `dict` of fresh cache entries
  cache_fresh = cache.fresh()
  
  # `cache.mutable()` will return a `dict` of all cache entries
  # that have a `value` attribute containing a `mutable` data type
  cache_mutable = cache.mutable()
  # `cache.immutable()` will return a `dict` of all cache entries
  # that have a `value` attribute containing an `immutable` data type
  
```
