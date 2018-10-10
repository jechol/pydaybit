import pytest

from pydaybit.utility import optional


def test_optional():
    @optional('a', 'b', 'c')
    def foo(d, **kwargs):
        pass

    foo(d='d')
    foo(d='d', a='a')
    foo(d='d', b='b')
    foo(d='d', c='c')
    foo(d='d', a='a', b='b')
    foo(d='d', a='a', c='c')
    foo(d='d', b='b', c='c')


def test_optional_fails():
    @optional('a', 'b', 'c')
    def foo(d, **kwargs):
        pass

    with pytest.raises(TypeError):
        foo(a='a')

    with pytest.raises(TypeError):
        foo(a='a', b='b')

    with pytest.raises(TypeError):
        foo(a='a', b='b', c='c', d='d', e='e')
