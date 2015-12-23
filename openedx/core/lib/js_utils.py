"""
Utilities for dealing with Javascript and JSON.
"""
import json as jsonlib
from django.template.defaultfilters import escapejs
from mako.filters import decode
from xmodule.modulestore import EdxJSONEncoder


def _escape_json_for_html(json_string):
    """
    Escape JSON that is safe to be embedded in HTML.

    This implementation is based on escaping performed in
    simplejson.JSONEncoderForHTML.

    Arguments:
        json_string (string): The JSON string to be escaped.

    Returns:
        (string) Escaped JSON that is safe to be embedded in HTML.

    """
    json_string = json_string.replace("&", "\\u0026")
    json_string = json_string.replace(">", "\\u003e")
    json_string = json_string.replace("<", "\\u003c")
    return json_string


def escape_json_dumps(obj, cls=EdxJSONEncoder):
    """
    JSON dumps and escapes JSON that is safe to be embedded in HTML.

    Usage:
        The best practice is to use the json() version of this Mako filter
        that can be used inside a Mako template inside a <SCRIPT> as follows::

            var my_json = ${my_object | n,json}

        If you must use the cls argument, then use this method instead::

            var my_json = ${escape_json_dumps(my_object, cls) | n}

        Use the "n" Mako filter above.  It is possible that the default filter
        may include html escaping in the future, and this ensures proper
        escaping.

        Ensure ascii in json.dumps (ensure_ascii=True) allows safe skipping of
        Mako's default filter decode.utf8.

    Arguments:
        obj: The JSON object to be encoded and dumped to a string.
        cls (class): The JSON encoder class (defaults to EdxJSONEncoder).

    Returns:
        (string) Escaped encoded JSON.

    """
    encoded_json = jsonlib.dumps(obj, ensure_ascii=True, cls=cls)
    encoded_json = _escape_json_for_html(encoded_json)
    return encoded_json


def json(obj):
    """
    Mako filter that JSON dumps and escapes JSON that is safe to be embedded
    in HTML.

    See `escape_json_dumps` for usage.

    """
    return escape_json_dumps(obj)


def escape_js_string(js_string):
    """
    Mako filter that escapes text for use in a JavaScript string.

    Usage:
        The best practice is to use the js() version of this Mako filter
        that can be used inside a Mako template inside a <SCRIPT> as follows::

            var my_js_string = "${my_js_string) | n,js}"


        If you must use this as a method fro some reason, use this method
        with the more verbose name::

            var my_js_string = "${escape_js_string(my_js_string) | n}"

        In all cases, the surrounding quotes for the string must be included.

        Use the "n" Mako filter above.  It is possible that the default filter
        may include html escaping in the future, and this ensures proper
        escaping.

        Mako's default filter decode.utf8 is applied here since this default
        filter is skipped in the Mako template with "n".

    Arguments:
        js_string (string): Text to be properly escaped for use in a
            JavaScript string.

    Returns:
        (string) Text properly escaped for use in a JavaScript string as
        unicode.

    """
    js_string = decode.utf8(js_string)
    js_string = escapejs(js_string)
    return js_string


# Mako filter that escapes text for use in a JavaScript string.
js = escape_js_string  # pylint: disable=invalid-name
