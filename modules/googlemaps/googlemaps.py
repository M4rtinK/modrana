#!/usr/bin/env python

# Copyright 2009 John Kleint
#
# This is free software, licensed under the Lesser Affero General 
# Public License, available in the accompanying LICENSE.txt file.


"""
An easy-to-use Python wrapper for the Google Maps and Local Search APIs.

* **Geocoding**: convert a postal address to latitude and longitude
* **Reverse Geocoding**: find the nearest address to (lat, lng)
* **Local Search**: find places matching a query near a given location
* **Directions**: turn-by-turn directions, distance, time, etc. from A to B

"""


import urllib
import urllib2
try:
    import json
except ImportError:
    import simplejson as json       # pylint: disable-msg=F0401


VERSION = '1.0.2'
__all__ = ['GoogleMaps', 'GoogleMapsError']


def fetch_json(query_url, params={}, headers={}):       # pylint: disable-msg=W0102
    """Retrieve a JSON object from a (parameterized) URL.
    
    :param query_url: The base URL to query
    :type query_url: string
    :param params: Dictionary mapping (string) query parameters to values
    :type params: dict
    :param headers: Dictionary giving (string) HTTP headers and values
    :type headers: dict 
    :return: A `(url, json_obj)` tuple, where `url` is the final,
    parameterized, encoded URL fetched, and `json_obj` is the data 
    fetched from that URL as a JSON-format object. 
    :rtype: (string, dict or array)
    
    """
    encoded_params = urllib.urlencode(params)    
    url = query_url + encoded_params
    request = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(request)
    return (url, json.load(response))
        

class GoogleMapsError(Exception):
    """Base class for errors in the :mod:`googlemaps` module.
    
    Methods of the :class:`GoogleMaps` raise this when something goes wrong.
     
    """
    #: See http://code.google.com/apis/maps/documentation/geocoding/index.html#StatusCodes
    #: for information on the meaning of these status codes.
    G_GEO_SUCCESS               = 200
    G_GEO_SERVER_ERROR          = 500
    G_GEO_MISSING_QUERY         = 601
    G_GEO_UNKNOWN_ADDRESS       = 602
    G_GEO_UNAVAILABLE_ADDRESS   = 603
    G_GEO_BAD_KEY               = 610
    G_GEO_TOO_MANY_QUERIES      = 620   

    _STATUS_MESSAGES = {
        G_GEO_SUCCESS               : 'G_GEO_SUCCESS',
        G_GEO_SERVER_ERROR          : 'G_GEO_SERVER_ERROR',
        G_GEO_MISSING_QUERY         : 'G_GEO_MISSING_QUERY',
        G_GEO_UNKNOWN_ADDRESS       : 'G_GEO_UNKNOWN_ADDRESS',
        G_GEO_UNAVAILABLE_ADDRESS   : 'G_GEO_UNAVAILABLE_ADDRESS',
        G_GEO_BAD_KEY               : 'G_GEO_BAD_KEY',
        G_GEO_TOO_MANY_QUERIES      : 'G_GEO_TOO_MANY_QUERIES',
    }
    
    def __init__(self, status, url=None, response=None):
        """Create an exception with a status and optional full response.
        
        :param status: Either a ``G_GEO_`` code or a string explaining the 
         exception.
        :type status: int or string
        :param url: The query URL that resulted in the error, if any.
        :type url: string
        :param response: The actual response returned from Google, if any.
        :type response: dict 
        
        """
        Exception.__init__(self, status)        # Exception is an old-school class
        self.status = status
        self.response = response
        self.url = url
        
    def __str__(self):
        """Return a string representation of this :exc:`GoogleMapsError`."""
        if self.status in self._STATUS_MESSAGES:
            if self.response is not None and 'responseDetails' in self.response:
                retval = 'Error %d: %s' % (self.status, self.response['responseDetails'])
            else:
                retval = 'Error %d: %s' % (self.status, self._STATUS_MESSAGES[self.status])
        else:
            retval = str(self.status)
        return retval
    
    def __unicode__(self):
        """Return a unicode representation of this :exc:`GoogleMapsError`."""
        return unicode(self.__str__())


STATUS_OK = GoogleMapsError.G_GEO_SUCCESS


class GoogleMaps(object):
    """
    An easy-to-use Python wrapper for the Google Maps and Local Search APIs.

    **Geocoding**: convert a postal address to latitude and longitude
    
    >>> from googlemaps import GoogleMaps
    >>> gmaps = GoogleMaps(api_key)
    >>> address = 'Constitution Ave NW & 10th St NW, Washington, DC'
    >>> lat, lng = gmaps.address_to_latlng(address)
    >>> print lat, lng
    38.8921021 -77.0260358
    
    **Reverse Geocoding**: find the nearest address to (lat, lng)
        
    >>> destination = gmaps.latlng_to_address(38.887563, -77.019929)
    >>> print destination
    Independence and 6th SW, Washington, DC 20024, USA
    
    **Local Search**: find places matching a query near a given location
    
    >>> local = gmaps.local_search('cafe near ' + destination)
    >>> print local['responseData']['results'][0]['titleNoFormatting']
    Vie De France Bakery & Cafe
    
    **Directions**: turn-by-turn directions, distance, time, etc. from 
    point A to point B
    
    >>> directions = gmaps.directions(address, destination)
    >>> print directions['Directions']['Distance']['meters']
    1029
    >>> print directions['Directions']['Duration']['seconds']
    106
    >>> for step in directions['Directions']['Routes'][0]['Steps']:
    ...     print step['descriptionHtml']
    Head <b>east</b> on <b>Constitution Ave NW</b> toward <b>9th St NW</b>
    Take the 2nd <b>right</b> onto <b>7th St NW</b>
    Turn <b>left</b> at <b>Independence Ave SW</b>
    
    This software is in no way associated with or endorsed by Google Inc.
    Use of the Google Maps API is governed by its Terms of Service:
    http://code.google.com/apis/maps/terms.html.  Note in particular that
    you will need your own Google Maps API key to use this service,
    and that there are rate limits to the number of requests you can
    make.
    
    """

    _GEOCODE_QUERY_URL = 'http://maps.google.com/maps/geo?'
    _DIRECTIONS_QUERY_URL = 'http://maps.google.com/maps/nav?'
    _LOCAL_QUERY_URL = 'http://ajax.googleapis.com/ajax/services/search/local?'
    _LOCAL_RESULTS_PER_PAGE = 8
    MAX_LOCAL_RESULTS = 32

    def __init__(self, api_key='', referrer_url=''):
        """
        Create a new :class:`GoogleMaps` object using the given `api_key` and 
        `referrer_url`.
        
        :param api_key: Google Maps API key 
        :type api_key: string
        :param referrer_url: URL of the website using or displaying information
         from this module.
        :type referrer_url: string
        
        Google requires API users to register for an API key before using the
        geocoding service; this can be done at
        http://code.google.com/apis/maps/signup.html.
        If you are not geocoding, you do not need an API key.
        
        Use of Google Local Search requires a referrer URL, generally the website
        where the retrieved information will be used.  If you are not using
        Local Search, you do not need a referrer URL.
        
        """
        self.api_key = api_key
        self.referrer_url = referrer_url
        
    def geocode(self, query, sensor='false', oe='utf8', ll='', spn='', gl=''):       # pylint: disable-msg=C0103,R0913
        """
        Given a string address `query`, return a dictionary of information about
        that location, including its latitude and longitude.
        
        Interesting bits:
        
        >>> gmaps = GoogleMaps(api_key)
        >>> address = '350 Fifth Avenue New York, NY'
        >>> result = gmaps.geocode(address)
        >>> placemark = result['Placemark'][0]
        >>> lng, lat = placemark['Point']['coordinates'][0:2]    # Note these are backwards from usual
        >>> print lat, lng
        40.6721118 -73.9838823
        >>> details = placemark['AddressDetails']['Country']['AdministrativeArea']
        >>> street = details['Locality']['Thoroughfare']['ThoroughfareName']
        >>> city = details['Locality']['LocalityName']
        >>> state = details['AdministrativeAreaName']
        >>> zipcode = details['Locality']['PostalCode']['PostalCodeNumber']
        >>> print ', '.join((street, city, state, zipcode))
        350 5th Ave, Brooklyn, NY, 11215

        More documentation on the format of the return value can be found at 
        Google's `geocoder return value`_ reference.  (Note: Some places have 
        a `'SubAdministrativeArea'` and some don't; sometimes a `'Locality'` 
        will have a `'DependentLocality'` and some don't.)
        
        .. _`geocoder return value`: http://code.google.com/apis/maps/documentation/geocoding/index.html#JSON

        :param query: Address of location to be geocoded.
        :type query: string
        :param sensor: ``'true'`` if the address is coming from, say, a GPS device.
        :type sensor: string
        :param oe: Output Encoding; best left at ``'utf8'``.
        :type oe: string
        :param ll: `lat,lng` of the viewport center as comma-separated string;
         must be used with `spn` for Viewport Biasing
        :type ll: string  
        :param spn: The "span" of the viewport; must be used with `ll`.
        :type spn: string
        :param gl: Two-character ccTLD_ for country code biasing. 
        :type gl: string
        :returns: `geocoder return value`_ dictionary
        :rtype: dict 
        :raises GoogleMapsError: if there is something wrong with the query.
        
        More information on the types and meaning of the parameters can be found
        at the `Google HTTP Geocoder`__ site.
        
        __ http://code.google.com/apis/maps/documentation/geocoding/index.html
        .. _ccTLD: http://en.wikipedia.org/wiki/Country_code_top-level_domain
        
        """
        if (ll is None and spn is not None) or (ll is not None and spn is None):
            raise GoogleMapsError('Both ll and spn must be provided.')
        params = {
            'q':        query,
            'key':      self.api_key,
            'sensor':   sensor,
            'output':   'json',
            'oe':       oe,
            'll':       ll,
            'spn':      spn,
            'gl':       gl,
        }
        url, response = fetch_json(self._GEOCODE_QUERY_URL, params=params)
        status_code = response['Status']['code']
        if status_code != STATUS_OK:
            raise GoogleMapsError(status_code, url, response)
        return response

    def reverse_geocode(self, lat, lng, sensor='false', oe='utf8', ll='', spn='', gl=''):        # pylint: disable-msg=C0103,R0913
        """
        Converts a (latitude, longitude) pair to an address.
        
        Interesting bits:
        
        >>> gmaps = GoogleMaps(api_key)
        >>> reverse = gmaps.reverse_geocode(38.887563, -77.019929)
        >>> address = reverse['Placemark'][0]['address']
        >>> print address
        Independence and 6th SW, Washington, DC 20024, USA
        >>> accuracy = reverse['Placemark'][0]['AddressDetails']['Accuracy']
        >>> print accuracy
        9
        
        :param lat: latitude
        :type lat: float
        :param lng: longitude
        :type lng: float
        :return: `Reverse geocoder return value`_ dictionary giving closest 
            address(es) to `(lat, lng)`
        :rtype: dict
        :raises GoogleMapsError: If the coordinates could not be reverse geocoded.
        
        Keyword arguments and return value are identical to those of :meth:`geocode()`.
        
        .. _`Reverse geocoder return value`: 
            http://code.google.com/apis/maps/documentation/geocoding/index.html#ReverseGeocoding
        
        """
        return self.geocode("%f,%f" % (lat, lng), sensor=sensor, oe=oe, ll=ll, spn=spn, gl=gl)
    
    def address_to_latlng(self, address):
        """
        Given a string `address`, return a `(latitude, longitude)` pair.
        
        This is a simplified wrapper for :meth:`geocode()`.
        
        :param address: The postal address to geocode.
        :type address: string
        :return: `(latitude, longitude)` of `address`.
        :rtype: (float, float)
        :raises GoogleMapsError: If the address could not be geocoded.
        
        """
        return tuple(self.geocode(address)['Placemark'][0]['Point']['coordinates'][1::-1])
    
    def latlng_to_address(self, lat, lng):
        """
        Given a latitude `lat` and longitude `lng`, return the closest address.
        
        This is a simplified wrapper for :meth:`reverse_geocode()`.
        
        :param lat: latitude
        :type lat: float
        :param lng: longitude
        :type lng: float
        :return: Closest postal address to `(lat, lng)`, if any.
        :rtype: string
        :raises GoogleMapsError: if the coordinates could not be converted
         to an address. 
        
        """ 
        return self.reverse_geocode(lat, lng)['Placemark'][0]['address']

    def local_search(self, query, numresults=_LOCAL_RESULTS_PER_PAGE, **kwargs):
        """
        Searches Google Local for the string `query` and returns a 
        dictionary of the results.
    
        >>> gmaps = GoogleMaps(api_key)
        >>> local = gmaps.local_search('sushi san francisco, ca')
        >>> result = local['responseData']['results'][0]
        >>> print result['titleNoFormatting']
        Sushi Groove
        >>> print result['streetAddress']
        1916 Hyde St
        >>> print result['phoneNumbers'][0]['number']
        (415) 440-1905

        For more information on the available data, see Google's documentation on 
        `AJAX result structure`_ and `local result properties`_.
        
        The return value of this method is slightly different than that
        documented by Google; it attempts to stuff as many results as
        possible, from several queries (up to `numresults`), into the 
        ``['responseData']['results']`` array.  As a result, fields of
        the results referencing this array (such as ``'cursor'``, 
        ``'currentPageIndex'``, ``'moreResultsUrl'``) may not make
        complete sense.
        
        This method may return fewer results than you ask for; Google Local 
        returns a maximum of :data:`GoogleMaps.MAX_LOCAL_RESULTS` results.
        
        :param query: String containing a search and a location, such as 
         ``'Sushi San Francisco, CA'``.
        :type query: string
        :param numresults: Number of results to return, up to a maximum of :data:`MAX_LOCAL_RESULTS`.
        :type numresults: int
        :param kwargs: You can pass additional `AJAX search arguments`_ and they 
         will be tacked on to the query.
        :return: A Google `AJAX result structure`_.
        :rtype: dict
        :raises GoogleMapsError: If the query was malformed.
         
        .. _AJAX result structure: http://code.google.com/apis/ajaxsearch/documentation/#fonje
        .. _local result properties: http://code.google.com/apis/ajaxsearch/documentation/reference.html#_class_GlocalResult 
        .. _AJAX search arguments: http://code.google.com/apis/ajaxsearch/documentation/reference.html#_intro_fonje
        
        """
        params = {
            'q':        query,
            'v':        '1.0',
            'rsz':      'large',            # Return 8 results per page instead of 4
            #'key':      self.api_key,      # Google Local seems not to like empty keys
        }
        params.update(kwargs)
            
        start = 0
        results = None
        while start < numresults and start < self.MAX_LOCAL_RESULTS:
            params['start'] = start
            url, response = fetch_json(self._LOCAL_QUERY_URL, params=params, headers={'Referer': self.referrer_url})
            status_code = response['responseStatus']
            if status_code != STATUS_OK:
                raise GoogleMapsError(status_code, url=url, response=response)
            if results is None:
                results = response
            else: 
                results['responseData']['results'].extend(response['responseData']['results'])
            
            # If we didn't get a full page of results, Google has run out; don't try again
            if len(response['responseData']['results']) < self._LOCAL_RESULTS_PER_PAGE:
                break
            start += len(response['responseData']['results'])
            
        if results is not None:
            results['responseData']['results'] = results['responseData']['results'][:numresults]
        return results

    def directions(self, origin, destination, **kwargs):
        """
        Get driving directions from `origin` to `destination`.

        Interesting bits:

        >>> gmaps = GoogleMaps(api_key)
        >>> start = 'Constitution Ave NW & 10th St NW, Washington, DC'
        >>> end   = 'Independence and 6th SW, Washington, DC 20024, USA'
        >>> dirs  = gmaps.directions(start, end) 
        >>> time  = dirs['Directions']['Duration']['seconds']
        >>> dist  = dirs['Directions']['Distance']['meters']
        >>> route = dirs['Directions']['Routes'][0]
        >>> for step in route['Steps']:
        ...    print step['Point']['coordinates'][1], step['Point']['coordinates'][0] 
        ...    print step['descriptionHtml']
        38.8921 -77.02604
        Head <b>east</b> on <b>Constitution Ave NW</b> toward <b>9th St NW</b>
        38.89208 -77.02191
        Take the 2nd <b>right</b> onto <b>7th St NW</b>
        38.88757 -77.02191
        Turn <b>left</b> at <b>Independence Ave SW</b>

        :param origin: Starting address
        :type origin: string
        :param destination: Ending address
        :type destination: string
        :param kwargs: You can pass additional URL parameters as keyword arguments, 
         but this functionality is not documented.
        :return: Dictionary containing driving directions.
        :rtype: dict
        :raises GoogleMapsError: If Google Maps was unable to find directions.
        
        """
        params = {
            'q':        'from:%s to:%s' % (origin, destination),
            'output':   'json',
            'oe':       'utf8',
            'key':      self.api_key,
        }
        params.update(kwargs)

        url, response = fetch_json(self._DIRECTIONS_QUERY_URL, params=params)
        status_code = response['Status']['code']
        if status_code != STATUS_OK:
            raise GoogleMapsError(status_code, url=url, response=response)
        return response
    

if __name__ == "__main__":
    import sys
    
    def main(argv):
        """
        Geocodes a location given on the command line.
        
        Usage:
            googlemaps.py "1600 amphitheatre mountain view ca" [YOUR_API_KEY]
            googlemaps.py 37.4219720,-122.0841430 [YOUR_API_KEY]
            
        When providing a latitude and longitude on the command line, ensure
        they are separated by a comma and no space.
        
        """

        if len(argv) < 2 or len(argv) > 4:
            print main.__doc__
            sys.exit(1)
            
        query = argv[1]
        if len(argv) == 3:
            api_key = argv[2]
        else:
            api_key = raw_input("Google Maps API key: ")
            
        gmap = GoogleMaps(api_key)
        try:
            result = gmap.geocode(query)
        except GoogleMapsError, err:
            sys.stderr.write('%s\n%s\nResponse:\n' % (err.url, err))
            json.dump(err.response, sys.stderr, indent=4)
            sys.exit(1)
        json.dump(result, sys.stdout, indent=4)
        sys.stdout.write('\n')
        
    main(sys.argv)
    