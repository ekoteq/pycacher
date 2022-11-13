# pycacher
A simple Python 3.10 entry-based data cacher that supports mutable and immutable data types, including user-defined class instances.

# Features
- `PycacheEntry` - A wrapper class that allows `Pycache` instances to easily manage cache entries
- `Pycache` - A `dict` manager class to aid in the management of `PycacheEntry`s for their life within the cache

# Requirements
- `Python` `3.10`
- `pyflaker` `0.0.0` - required to generate the `Pyflake` instances requested by `Pyflake`s identifying cached entries

## Core modules imported
- `time` - used to generate timestamp values

# Usage
## Create a client instance
An instance of `pyflake_generator` is only required if you need to generate snowflakes IDs. If you already 'own' `Pyflake` instances for the data you intend to store in the cache, importing the `pyflaker` package is unnecessary.
```python
  import time
  from pyflaker import PyflakeClient, generate_seed
  from pycacher import Pycache
  
  epoch = int(time.time() * 1000)
  generator = PyflakeClient(epoch)

  pid = generate_seed(5)
  seed = generate_seed(5)
  generator.make_generator(pid, seed)

  cache = Pycache()
```
## Pycache.add(`snowflake: Pyflake`, `entry: entry_instance`, `fetched_time: int`, `max_age: int`, `entry_instance: dict`)
Add an item to the cache. We'll assume it's brand new and has not yet been assigned an ID. The generator returns a `Pyflake` instance, which has multiple attributes that the `Pycache` instance relies on to manage stored `_cache` entries.
```python
  snowflake = generator.generate()
```
Create an entry value that will be stored in the cache. For this example we will use an immutable data type so we don't have to implement an `update()` or `serialize()` method.
```python
  entry = 'test_entry'
```
`Pycache` requires every entry to define when the data was obtained from the source. Since we created the entry locally, the `fetched_time` is `now` multiplied by `1000` to return the timestamp in `milliseconds`
```python
  fetched_time = int(time.time() * 1000)
```  
`Pycache` does not require cached entries to expire, and allows, clients to define an age, in milliseconds, at which an entry may expire.
```python
  # 60000 = 60 seconds = 1 minute
  max_age = 60000
```
`Pycache` requires that every entry has a defined data type verifiable by calling `isinstance(value, instance)`. Since this entry is a 'string' value, we define it like so:
```python
  entry_instance = str
```
Finally, we can add the entry to the cache:
```python
  cache.add(snowflake, entry, fetched_time, max_age, entry_instance)
```
## Pycache.get(`idx: int`)
To `get()` the new entry, we need to have access to its cache key, or the `Pyflake.snowflake` attribute passed to `Pycache` when the entry was first stored.
```python
  found_entry = cache.get(snowflake.snowflake)
```
## Pycache.update(`idx: int`, `entry: entry_instance`, `fetched_time: int`)
To update an entry that already exists in the cache, the cache's `update()` method should be called. This requires all stored values to have a local `update()` method that updates entry values, and a `serialize()` method to return only the values required to reconstruct the entry using `entry_instance(entry)` if necessary.

Immutable values, such as `str`, `int`, `float`, `bool`, `complex`, `frozenset`, and `tuple` are not required to have `update()` or `serialize()` methods as these values are updated via attribute value reassignment.
```python
  updated_entry = 'updated_test_entry'
  fetched_time = int(time.time() * 1000)
  cache.update(snowflake.snowflake, updated_entry, fetched_time)
```
### PycacheEntry.update(`entry: entry_instance`, `fetched_time: int`)
Additionally, the entry's `update()` method may be called instead, making it easy to update an entry accessed outside of the `Pyclient._cache`
```python
  found_entry.update(updated_entry, fetched_time)
```
## Pycache.find(`condition: callable[entry_instance, bool]`)
To find one or more records that meet a condition, the cache's `find()` method should be called, and a conditional function accepting the entry and returning a `bool` value should be passed.
```python
  def is_not_none(entry):
    # the core content of an entry is found in the entry's `value`
    # attribute. Cache-related metadata is also available, but the
    # majority of application logic will be looking toward `entry.value`
    # for most, if not all evaluation
    if not entry.value == None:
      return True
    else:
      return False
  found_entries = cache.find(is_not_none)
```
## Pycache.remove(`snowflake: Pyflake`)
To remove an entry that exists in the cache, the cache's `remove()` method should be called. Entries do not have a local `remove()` method and should not be removed from an external cache that holds it by calling an internal method.
  
NOTE: `Pycache.remove()` expects to receive a fully constructed `Pyflake` as an entry ID.
```python
  if len(found_entries) > 0:
    for entry in found_entries.values():
      cache.remove(entry._snowflake)
```
## `dict`-like methods
There are several methods available in a `Pycache` instance that makes managing the local `Pycache._cache` as easy as managing a `dict` without being a direct extension of a `dict` data type.
### Pycache.clear()
Clears the `Pycache._cache` of all available entries.
```python
  cache.clear()
```
### Pycache.copy()
Returns an exact copy of the `Pycache._cache` in its current state.

NOTE: this returns a `dict`, not a `Pycache`.
```python
  cache_copy = cache.copy()
```  
### Pycache.pop(idx)
Removes and returns the `Pycache._cache` entry with the specified `idx`.
```python
  cache_popped = cache.pop(idx)
```  
### Pycache.popitem()
Removes and returns the last inserted `Pycache._cache` entry.
```python
  cache_last = cache.popitem()
```  
### Pycache.setdefault(`idx: int`, `value: dict`)
Returns the `Pycache._cache` entry with the specified `idx`, inserting it if it does not exist. This acts like an `upsert` operation.
```python
  cache_upsert = cache.setdefault(idx, value)
```  
### Pycache.keys()
Returns keys for all cache entries.
```python
  cache_keys = cache.keys()
```
### Pycache.values()
Returns all `PycacheEntry` values in the cache.
```python
  cache_values = cache.values()
```
### Pycache.items()
Returns `[ k, v ]` pairs of all cache entries.
```python
  cache_items = cache.items()
```
## Additional methods
### Pycache.length()
Returns the quantity of entries in `Pycache._cache`.
```python
  cache_length = cache.length()
```  
### Pycache.stale()
Returns a `dict` of stale cache entries.

The `freshness` of a cache entry is determined by its `max_age` attribute value, representing the milliseconds the record is considered `fresh` before becoming `stale`.
```python
  cache_stale = cache.stale()
```  
### Pycache.fresh()
Returns a `dict` of cache entries that have not yet become `stale`.
```python
  cache_fresh = cache.fresh()
```
### Pycache.mutable()
Returns a `dict` of all cache entries that have a `value` attribute containing a `mutable` data type.
```python
  cache_mutable = cache.mutable()
```
### Pycache.immutable()
Returns a `dict` of all cache entries that have a `value` attribute containing an `immutable` data type.
```python
  cache_immutable = cache.immutable()
```
### Pycache.str()
Returns a `dict` of all cache entries that have a `value` attribute containing a `str` data type.
```python
  cache_str = cache.str()
```
### Pycache.int()
Returns a `dict` of all cache entries that have a `value` attribute containing an `int` data type.
```python
  cache_int = cache.int()
```
### Pycache.complex()
Returns a `dict` of all cache entries that have a `value` attribute containing a `complex` data type.
```python
  cache_complex = cache.complex()
```
### Pycache.bool()
Returns a `dict` of all cache entries that have a `value` attribute containing a `bool` data type.
```python
  cache_bool = cache.bool()
```
### Pycache.frozenset()
Returns a `dict` of all cache entries that have a `value` attribute containing a `frozenset` data type.
```python
  cache_frozenset = cache.frozenset()
```
### Pycache.float()
Returns a `dict` of all cache entries that have a `value` attribute containing a `float` data type.
```python
  cache_float = cache.float()
```
### Pycache.tuple()
Returns a `dict` of all cache entries that have a `value` attribute containing a `tuple` data type.
```python
  cache_tuple = cache.tuple()
```
