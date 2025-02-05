# Copyright (c) 2017 Ian Stapleton Cordasco
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module containing the tests for the URIBuilder object."""
try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

import pytest

from rfc3986 import builder, uri_reference


def test_builder_default():
    """Verify the default values."""
    uribuilder = builder.URIBuilder()
    assert uribuilder.scheme is None
    assert uribuilder.userinfo is None
    assert uribuilder.host is None
    assert uribuilder.port is None
    assert uribuilder.path is None
    assert uribuilder.query is None
    assert uribuilder.fragment is None


def test_from_uri_reference():
    uri = uri_reference("http://foo.bar:1234/baz")
    uribuilder = builder.URIBuilder().from_uri(uri)
    assert uribuilder.scheme == "http"
    assert uribuilder.userinfo is None
    assert uribuilder.host == "foo.bar"
    assert uribuilder.port == "1234"
    assert uribuilder.path == "/baz"
    assert uribuilder.query is None
    assert uribuilder.fragment is None


def test_from_uri_string():
    uribuilder = builder.URIBuilder().from_uri("https://bar.foo:4321/boom")
    assert uribuilder.scheme == "https"
    assert uribuilder.userinfo is None
    assert uribuilder.host == "bar.foo"
    assert uribuilder.port == "4321"
    assert uribuilder.path == "/boom"
    assert uribuilder.query is None
    assert uribuilder.fragment is None


def test_repr():
    """Verify our repr looks like our class."""
    uribuilder = builder.URIBuilder()
    assert repr(uribuilder).startswith("URIBuilder(scheme=None")


@pytest.mark.parametrize(
    "scheme",
    [
        "https",
        "hTTps",
        "Https",
        "HtTpS",
        "HTTPS",
    ],
)
def test_add_scheme(scheme):
    """Verify schemes are normalized when added."""
    uribuilder = builder.URIBuilder().add_scheme(scheme)
    assert uribuilder.scheme == "https"


@pytest.mark.parametrize(
    "username, password, userinfo",
    [
        ("user", "pass", "user:pass"),
        ("user", None, "user"),
        ("user@domain.com", "password", "user%40domain.com:password"),
        ("user", "pass:word", "user:pass%3Aword"),
    ],
)
def test_add_credentials(username, password, userinfo):
    """Verify we normalize usernames and passwords."""
    uribuilder = builder.URIBuilder().add_credentials(username, password)
    assert uribuilder.userinfo == userinfo


def test_add_credentials_requires_username():
    """Verify one needs a username to add credentials."""
    with pytest.raises(ValueError):
        builder.URIBuilder().add_credentials(None, None)


@pytest.mark.parametrize(
    ["hostname", "expected_hostname"],
    [
        ("google.com", "google.com"),
        ("GOOGLE.COM", "google.com"),
        ("gOOgLe.COM", "google.com"),
        ("goOgLE.com", "google.com"),
        ("[::ff%etH0]", "[::ff%25etH0]"),
        ("[::ff%25etH0]", "[::ff%25etH0]"),
        ("[::FF%etH0]", "[::ff%25etH0]"),
    ],
)
def test_add_host(hostname, expected_hostname):
    """Verify we normalize hostnames in add_host."""
    uribuilder = builder.URIBuilder().add_host(hostname)
    assert uribuilder.host == expected_hostname


@pytest.mark.parametrize(
    "port",
    [
        -100,
        "-100",
        -1,
        "-1",
        65536,
        "65536",
        1000000,
        "1000000",
        "",
        "abc",
        "0b10",
    ],
)
def test_add_invalid_port(port):
    """Verify we raise a ValueError for invalid ports."""
    with pytest.raises(ValueError):
        builder.URIBuilder().add_port(port)


@pytest.mark.parametrize(
    "port, expected",
    [
        (0, "0"),
        ("0", "0"),
        (1, "1"),
        ("1", "1"),
        (22, "22"),
        ("22", "22"),
        (80, "80"),
        ("80", "80"),
        (443, "443"),
        ("443", "443"),
        (65535, "65535"),
        ("65535", "65535"),
    ],
)
def test_add_port(port, expected):
    """Verify we normalize our port."""
    uribuilder = builder.URIBuilder().add_port(port)
    assert uribuilder.port == expected


@pytest.mark.parametrize(
    "path",
    [
        "sigmavirus24/rfc3986",
        "/sigmavirus24/rfc3986",
    ],
)
def test_add_path(path):
    """Verify we normalize our path value."""
    uribuilder = builder.URIBuilder().add_path(path)
    assert uribuilder.path == "/sigmavirus24/rfc3986"


@pytest.mark.parametrize(
    "query_items, expected",
    [
        ({"a": "b c"}, "a=b+c"),
        ({"a": "b+c"}, "a=b%2Bc"),
        ([("a", "b c")], "a=b+c"),
        ([("a", "b+c")], "a=b%2Bc"),
        ([("a", "b"), ("c", "d")], "a=b&c=d"),
        ([("a", "b"), ("username", "@d")], "a=b&username=%40d"),
        ([("percent", "%")], "percent=%25"),
    ],
)
def test_add_query_from(query_items, expected):
    """Verify the behaviour of add_query_from."""
    uribuilder = builder.URIBuilder().add_query_from(query_items)
    assert uribuilder.query == expected


def test_add_query():
    """Verify we do not modify the provided query string."""
    uribuilder = builder.URIBuilder().add_query("username=@foo")
    assert uribuilder.query == "username=@foo"


def test_add_fragment():
    """Verify our handling of fragments."""
    uribuilder = builder.URIBuilder().add_fragment("section-2.5.1")
    assert uribuilder.fragment == "section-2.5.1"


@pytest.mark.parametrize(
    "uri, extend_with, expected_path",
    [
        ("https://api.github.com", "/users", "/users"),
        ("https://api.github.com", "/users/", "/users/"),
        ("https://api.github.com", "users", "/users"),
        ("https://api.github.com", "users/", "/users/"),
        ("", "users/", "/users/"),
        ("", "users", "/users"),
        ("?foo=bar", "users", "/users"),
        (
            "https://api.github.com/users/",
            "sigmavirus24",
            "/users/sigmavirus24",
        ),
        (
            "https://api.github.com/users",
            "sigmavirus24",
            "/users/sigmavirus24",
        ),
        (
            "https://api.github.com/users",
            "/sigmavirus24",
            "/users/sigmavirus24",
        ),
        (
            "https://api.github.com/user s",
            "/sigmavirus24",
            "/user%20s/sigmavirus24",
        ),
        (
            "https://api.github.com/users",
            "/sigmavirus 24",
            "/users/sigmavirus%2024",
        ),
    ],
)
def test_extend_path(uri, extend_with, expected_path):
    """Verify the behaviour of extend_path."""
    uribuilder = (
        builder.URIBuilder()
        .from_uri(uri_reference(uri))
        .extend_path(extend_with)
    )
    assert uribuilder.path == expected_path


@pytest.mark.parametrize(
    "uri, extend_with, expected_query",
    [
        (
            "https://github.com",
            [("a", "b c"), ("d", "e&f")],
            {"a": ["b c"], "d": ["e&f"]},
        ),
        (
            "https://github.com?a=0",
            [("a", "b c"), ("d", "e&f")],
            {"a": ["0", "b c"], "d": ["e&f"]},
        ),
        (
            "https://github.com?a=0&e=f",
            [("a", "b c"), ("d", "e&f")],
            {"a": ["0", "b c"], "e": ["f"], "d": ["e&f"]},
        ),
        (
            "https://github.com",
            {"a": "b c", "d": "e&f"},
            {"a": ["b c"], "d": ["e&f"]},
        ),
        (
            "https://github.com?a=0",
            {"a": "b c", "d": "e&f"},
            {"a": ["0", "b c"], "d": ["e&f"]},
        ),
        (
            "https://github.com?a=0&e=f",
            {"a": "b c", "d": "e&f"},
            {"a": ["0", "b c"], "e": ["f"], "d": ["e&f"]},
        ),
    ],
)
def test_extend_query_with(uri, extend_with, expected_query):
    """Verify the behaviour of extend_query_with."""
    uribuilder = (
        builder.URIBuilder()
        .from_uri(uri_reference(uri))
        .extend_query_with(extend_with)
    )
    assert parse_qs(uribuilder.query) == expected_query


def test_finalize():
    """Verify the whole thing."""
    uri = (
        builder.URIBuilder()
        .add_scheme("https")
        .add_credentials("sigmavirus24", "not-my-re@l-password")
        .add_host("github.com")
        .add_path("sigmavirus24/rfc3986")
        .finalize()
        .unsplit()
    )
    expected = (
        "https://sigmavirus24:not-my-re%40l-password@github.com/"
        "sigmavirus24/rfc3986"
    )
    assert expected == uri


def test_geturl():
    """Verify the short-cut to the URL."""
    uri = (
        builder.URIBuilder()
        .add_scheme("https")
        .add_credentials("sigmavirus24", "not-my-re@l-password")
        .add_host("github.com")
        .add_path("sigmavirus24/rfc3986")
        .geturl()
    )
    expected = (
        "https://sigmavirus24:not-my-re%40l-password@github.com/"
        "sigmavirus24/rfc3986"
    )
    assert expected == uri
