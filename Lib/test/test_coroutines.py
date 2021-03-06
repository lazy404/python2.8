import contextlib
import inspect
import sys
import types
import unittest
import warnings
import test.test_support as support


class AsyncYieldFrom:
    def __init__(self, obj):
        self.obj = obj

    def __await__(self):
        yield from self.obj


class AsyncYield:
    def __init__(self, value):
        self.value = value

    def __await__(self):
        yield self.value


def run_async(coro):
    assert coro.__class__ in {types.GeneratorType, types.CoroutineType}

    buffer = []
    result = None
    while True:
        try:
            buffer.append(coro.send(None))
        except StopIteration as ex:
            result = ex.args[0] if ex.args else None
            break
    return buffer, result


def run_async__await__(coro):
    assert coro.__class__ is types.CoroutineType
    aw = coro.__await__()
    buffer = []
    result = None
    i = 0
    while True:
        try:
            if i % 2:
                buffer.append(next(aw))
            else:
                buffer.append(aw.send(None))
            i += 1
        except StopIteration as ex:
            result = ex.args[0] if ex.args else None
            break
    return buffer, result


@contextlib.contextmanager
def silence_coro_gc():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield
        support.gc_collect()


class AsyncBadSyntaxTest(unittest.TestCase):

    def test_badsyntax_1(self):
        with self.assertRaisesRegexp(SyntaxError, "'await' outside"):
            import test.badsyntax_async1

    def test_badsyntax_2(self):
        with self.assertRaisesRegexp(SyntaxError, "'await' outside"):
            import test.badsyntax_async2

    def test_badsyntax_3(self):
        with self.assertRaisesRegexp(SyntaxError, 'invalid syntax'):
            import test.badsyntax_async3

    def test_badsyntax_4(self):
        with self.assertRaisesRegexp(SyntaxError, 'invalid syntax'):
            import test.badsyntax_async4

    def test_badsyntax_5(self):
        with self.assertRaisesRegexp(SyntaxError, 'invalid syntax'):
            import test.badsyntax_async5

    def test_badsyntax_6(self):
        with self.assertRaisesRegexp(
            SyntaxError, "'yield' inside async function"):

            import test.badsyntax_async6

    def test_badsyntax_7(self):
        with self.assertRaisesRegexp(
            SyntaxError, "'yield from' inside async function"):

            import test.badsyntax_async7

    def test_badsyntax_8(self):
        with self.assertRaisesRegexp(SyntaxError, 'invalid syntax'):
            import test.badsyntax_async8

    def test_badsyntax_9(self):
        ns = {}
        for comp in {'(await a for a in b)',
                     '[await a for a in b]',
                     '{await a for a in b}',
                     '{await a: c for a in b}'}:

            with self.assertRaisesRegexp(SyntaxError, 'await.*in comprehen'):
                exec('async def f():\n\t{}'.format(comp), ns, ns)

    def test_badsyntax_10(self):
        # Tests for issue 24619

        samples = [
            """async def foo():
                   def bar(): pass
                   await = 1
            """,

            """async def foo():

                   def bar(): pass
                   await = 1
            """,

            """async def foo():
                   def bar(): pass
                   if 1:
                       await = 1
            """,

            """def foo():
                   async def bar(): pass
                   if 1:
                       await a
            """,

            """def foo():
                   async def bar(): pass
                   await a
            """,

            """def foo():
                   def baz(): pass
                   async def bar(): pass
                   await a
            """,

            """def foo():
                   def baz(): pass
                   # 456
                   async def bar(): pass
                   # 123
                   await a
            """,

            """async def foo():
                   def baz(): pass
                   # 456
                   async def bar(): pass
                   # 123
                   await = 2
            """,

            """def foo():

                   def baz(): pass

                   async def bar(): pass

                   await a
            """,

            """async def foo():

                   def baz(): pass

                   async def bar(): pass

                   await = 2
            """,

            """async def foo():
                   def async(): pass
            """,

            """async def foo():
                   def await(): pass
            """,

            """async def foo():
                   def bar():
                       await
            """,

            """async def foo():
                   return lambda async: await
            """,

            """async def foo():
                   return lambda a: await
            """,

            """await a()""",

            """async def foo(a=await b):
                   pass
            """,

            """async def foo(a:await b):
                   pass
            """,

            """def baz():
                   async def foo(a=await b):
                       pass
            """,

            """async def foo(async):
                   pass
            """,

            """async def foo():
                   def bar():
                        def baz():
                            async = 1
            """,

            """async def foo():
                   def bar():
                        def baz():
                            pass
                        async = 1
            """,

            """def foo():
                   async def bar():

                        async def baz():
                            pass

                        def baz():
                            42

                        async = 1
            """,

            """async def foo():
                   def bar():
                        def baz():
                            pass\nawait foo()
            """,

            """def foo():
                   def bar():
                        async def baz():
                            pass\nawait foo()
            """,

            """async def foo(await):
                   pass
            """,

            """def foo():

                   async def bar(): pass

                   await a
            """,

            """def foo():
                   async def bar():
                        pass\nawait a
            """]

        for code in samples:
            with self.assertRaises(SyntaxError):
                compile(code, "<test>", "exec")

    def test_goodsyntax_1(self):
        # Tests for issue 24619

        def foo(await):
            async def foo(): pass
            async def foo():
                pass
            return await + 1
        self.assertEqual(foo(10), 11)

        def foo(await):
            async def foo(): pass
            async def foo(): pass
            return await + 2
        self.assertEqual(foo(20), 22)

        def foo(await):

            async def foo(): pass

            async def foo(): pass

            return await + 2
        self.assertEqual(foo(20), 22)

        def foo(await):
            """spam"""
            async def foo(): \
                pass
            # 123
            async def foo(): pass
            # 456
            return await + 2
        self.assertEqual(foo(20), 22)

        def foo(await):
            def foo(): pass
            def foo(): pass
            async def bar(): return await_
            await_ = await
            try:
                bar().send(None)
            except StopIteration as ex:
                return ex.args[0]
        self.assertEqual(foo(42), 42)

        async def f():
            async def g(): pass
            await z
        await = 1
        self.assertTrue(inspect.iscoroutinefunction(f))


class TokenizerRegrTest(unittest.TestCase):

    def test_oneline_defs(self):
        buf = []
        for i in range(500):
            buf.append('def i{i}(): return {i}'.format(i=i))
        buf = '\n'.join(buf)

        # Test that 500 consequent, one-line defs is OK
        ns = {}
        exec(buf, ns, ns)
        self.assertEqual(ns['i499'](), 499)

        # Test that 500 consequent, one-line defs *and*
        # one 'async def' following them is OK
        buf += '\nasync def foo():\n    return'
        ns = {}
        exec(buf, ns, ns)
        self.assertEqual(ns['i499'](), 499)
        self.assertTrue(inspect.iscoroutinefunction(ns['foo']))


class CoroutineTest(unittest.TestCase):
    def setUp(self):
        # Workaround for no 'nonlocal' keyword: use self's mutable attributes
        self.N = 0
        self.CNT = 0
        self.I = 0
        self.aiter_calls = 0

    def test_gen_1(self):
        def gen(): yield
        self.assertFalse(hasattr(gen, '__await__'))

    def test_func_1(self):
        async def foo():
            return 10

        f = foo()
        self.assertIsInstance(f, types.CoroutineType)
        self.assertTrue(bool(foo.__code__.co_flags & inspect.CO_COROUTINE))
        self.assertFalse(bool(foo.__code__.co_flags & inspect.CO_GENERATOR))
        self.assertTrue(bool(f.cr_code.co_flags & inspect.CO_COROUTINE))
        self.assertFalse(bool(f.cr_code.co_flags & inspect.CO_GENERATOR))
        self.assertEqual(run_async(f), ([], 10))

        self.assertEqual(run_async__await__(foo()), ([], 10))

        def bar(): pass
        self.assertFalse(bool(bar.__code__.co_flags & inspect.CO_COROUTINE))

    def test_func_2(self):
        async def foo():
            raise StopIteration

        with self.assertRaisesRegexp(
                RuntimeError, "coroutine raised StopIteration"):

            run_async(foo())

    def test_func_3(self):
        async def foo():
            raise StopIteration

        with silence_coro_gc():
            self.assertRegexpMatches(repr(foo()), '^<coroutine object.* at 0x.*>$')

    def test_func_4(self):
        async def foo():
            raise StopIteration

        check = lambda: self.assertRaisesRegexp(
            TypeError, "'coroutine' object is not iterable")

        with check():
            list(foo())

        with check():
            tuple(foo())

        with check():
            sum(foo())

        with check():
            iter(foo())

        with silence_coro_gc(), check():
            for i in foo():
                pass

        with silence_coro_gc(), check():
            [i for i in foo()]

    def test_func_5(self):
        @types.coroutine
        def bar():
            yield 1

        async def foo():
            await bar()

        check = lambda: self.assertRaisesRegexp(
            TypeError, "'coroutine' object is not iterable")

        with check():
            for el in foo(): pass

        # the following should pass without an error
        for el in bar():
            self.assertEqual(el, 1)
        self.assertEqual([el for el in bar()], [1])
        self.assertEqual(tuple(bar()), (1,))
        self.assertEqual(next(iter(bar())), 1)

    def test_func_6(self):
        @types.coroutine
        def bar():
            yield 1
            yield 2

        async def foo():
            await bar()

        f = foo()
        self.assertEquals(f.send(None), 1)
        self.assertEquals(f.send(None), 2)
        with self.assertRaises(StopIteration):
            f.send(None)

    def test_func_7(self):
        async def bar():
            return 10

        def foo():
            yield from bar()

        with silence_coro_gc(), self.assertRaisesRegexp(
            TypeError,
            "cannot 'yield from' a coroutine object in a non-coroutine generator"):

            list(foo())

    def test_func_8(self):
        @types.coroutine
        def bar():
            return (yield from foo())

        async def foo():
            return 'spam'

        self.assertEqual(run_async(bar()), ([], 'spam') )

    def test_func_9(self):
        async def foo(): pass

        with warnings.catch_warnings(record=True) as w:
            foo()
            support.gc_collect()

            self.assertEqual(len(w), 1)
            self.assertEqual(w[0].category, RuntimeWarning)
            self.assertEqual(str(w[0].message),
                             "coroutine 'foo' was never awaited")

    def test_func_10(self):
        @types.coroutine
        def gen():
            try:
                a = yield
                yield (a ** 2)
            except ZeroDivisionError:
                self.N += 100
                raise
            finally:
                self.N += 1

        async def foo():
            await gen()

        coro = foo()
        aw = coro.__await__()
        self.assertIs(aw, iter(aw))
        next(aw)
        self.assertEqual(aw.send(10), 100)

        self.assertEqual(self.N, 0)
        aw.close()
        self.assertEqual(self.N, 1)

        coro = foo()
        aw = coro.__await__()
        next(aw)
        with self.assertRaises(ZeroDivisionError):
            aw.throw(ZeroDivisionError, None, None)
        self.assertEqual(self.N, 102)

    def test_func_11(self):
        async def func(): pass
        coro = func()
        # Test that PyCoro_Type and _PyCoroWrapper_Type types were properly
        # initialized
        self.assertIn('__await__', dir(coro))
        self.assertIn('__iter__', dir(coro.__await__()))
        self.assertIn('coroutine_wrapper', repr(coro.__await__()))
        coro.close() # avoid RuntimeWarning

    def test_func_12(self):
        async def g():
            i = me.send(None)
            await foo
        me = g()
        with self.assertRaisesRegexp(ValueError,
                                    "coroutine already executing"):
            me.send(None)

    def test_func_13(self):
        async def g():
            pass
        with self.assertRaisesRegexp(
            TypeError,
            "can't send non-None value to a just-started coroutine"):

            g().send('spam')

    def test_func_14(self):
        @types.coroutine
        def gen():
            yield
        async def coro():
            try:
                await gen()
            except GeneratorExit:
                await gen()
        c = coro()
        c.send(None)
        with self.assertRaisesRegexp(RuntimeError,
                                    "coroutine ignored GeneratorExit"):
            c.close()

    def test_cr_await(self):
        @types.coroutine
        def a():
            self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_RUNNING)
            self.assertIsNone(coro_b.cr_await)
            yield
            self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_RUNNING)
            self.assertIsNone(coro_b.cr_await)

        async def c():
            await a()

        async def b():
            self.assertIsNone(coro_b.cr_await)
            await c()
            self.assertIsNone(coro_b.cr_await)

        coro_b = b()
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_CREATED)
        self.assertIsNone(coro_b.cr_await)

        coro_b.send(None)
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_SUSPENDED)
        self.assertEqual(coro_b.cr_await.cr_await.gi_code.co_name, 'a')

        with self.assertRaises(StopIteration):
            coro_b.send(None)  # complete coroutine
        self.assertEqual(inspect.getcoroutinestate(coro_b), inspect.CORO_CLOSED)
        self.assertIsNone(coro_b.cr_await)

    def test_corotype_1(self):
        ct = types.CoroutineType
        self.assertIn('into coroutine', ct.send.__doc__)
        self.assertIn('inside coroutine', ct.close.__doc__)
        self.assertIn('in coroutine', ct.throw.__doc__)
        self.assertIn('of the coroutine', ct.__dict__['__name__'].__doc__)
        self.assertEqual(ct.__name__, 'coroutine')

        async def f(): pass
        c = f()
        self.assertIn('coroutine object', repr(c))
        c.close()

    def test_await_1(self):

        async def foo():
            await 1
        with self.assertRaisesRegexp(TypeError, "object int can.t.*await"):
            run_async(foo())

    def test_await_2(self):
        async def foo():
            await []
        with self.assertRaisesRegexp(TypeError, "object list can.t.*await"):
            run_async(foo())

    def test_await_3(self):
        async def foo():
            await AsyncYieldFrom([1, 2, 3])

        self.assertEqual(run_async(foo()), ([1, 2, 3], None))
        self.assertEqual(run_async__await__(foo()), ([1, 2, 3], None))

    def test_await_4(self):
        async def bar():
            return 42

        async def foo():
            return await bar()

        self.assertEqual(run_async(foo()), ([], 42))

    def test_await_5(self):
        class Awaitable:
            def __await__(self):
                return

        async def foo():
            return (await Awaitable())

        with self.assertRaisesRegexp(
            TypeError, "__await__.*returned non-iterator of type"):

            run_async(foo())

    def test_await_6(self):
        class Awaitable:
            def __await__(self):
                return iter([52])

        async def foo():
            return (await Awaitable())

        self.assertEqual(run_async(foo()), ([52], None))

    def test_await_7(self):
        class Awaitable:
            def __await__(self):
                yield 42
                return 100

        async def foo():
            return (await Awaitable())

        self.assertEqual(run_async(foo()), ([42], 100))

    def test_await_8(self):
        class Awaitable(object):
            pass

        async def foo(): return await Awaitable()

        with self.assertRaisesRegexp(
            TypeError, "object Awaitable can't be used in 'await' expression"):

            run_async(foo())

    def test_await_9(self):
        def wrap():
            return bar

        async def bar():
            return 42

        async def foo():
            b = bar()

            db = {'b':  lambda: wrap}

            class DB:
                b = staticmethod(wrap)

            return (await bar() + await wrap()() + await db['b']()()() +
                    await bar() * 1000 + await DB.b()())

        async def foo2():
            return -await bar()

        self.assertEqual(run_async(foo()), ([], 42168))
        self.assertEqual(run_async(foo2()), ([], -42))

    def test_await_10(self):
        async def baz():
            return 42

        async def bar():
            return baz()

        async def foo():
            return await (await bar())

        self.assertEqual(run_async(foo()), ([], 42))

    def test_await_11(self):
        def ident(val):
            return val

        async def bar():
            return 'spam'

        async def foo():
            return ident(val=await bar())

        async def foo2():
            return await bar(), 'ham'

        self.assertEqual(run_async(foo2()), ([], ('spam', 'ham')))

    def test_await_12(self):
        async def coro():
            return 'spam'

        class Awaitable:
            def __await__(self):
                return coro()

        async def foo():
            return await Awaitable()

        with self.assertRaisesRegexp(
            TypeError, "__await__\(\) returned a coroutine"):

            run_async(foo())

    def test_await_13(self):
        class Awaitable(object):
            def __await__(self):
                return self

        async def foo():
            return await Awaitable()

        with self.assertRaisesRegexp(
            TypeError, "__await__.*returned non-iterator of type"):

            run_async(foo())

    def test_await_14(self):
        class Wrapper:
            # Forces the interpreter to use CoroutineType.__await__
            def __init__(self, coro):
                assert coro.__class__ is types.CoroutineType
                self.coro = coro
            def __await__(self):
                return self.coro.__await__()

        class FutureLike:
            def __await__(self):
                return (yield)

        class Marker(Exception):
            pass

        async def coro1():
            try:
                return await FutureLike()
            except ZeroDivisionError:
                raise Marker
        async def coro2():
            return await Wrapper(coro1())

        c = coro2()
        c.send(None)
        with self.assertRaisesRegexp(StopIteration, 'spam'):
            c.send('spam')

        c = coro2()
        c.send(None)
        with self.assertRaises(Marker):
            c.throw(ZeroDivisionError)

    def test_with_1(self):
        class Manager:
            def __init__(self, name):
                self.name = name

            async def __aenter__(self):
                await AsyncYieldFrom(['enter-1-' + self.name,
                                      'enter-2-' + self.name])
                return self

            async def __aexit__(self, *args):
                await AsyncYieldFrom(['exit-1-' + self.name,
                                      'exit-2-' + self.name])

                if self.name == 'B':
                    return True


        async def foo():
            async with Manager("A") as a, Manager("B") as b:
                await AsyncYieldFrom([('managers', a.name, b.name)])
                1/0

        f = foo()
        result, _ = run_async(f)

        self.assertEqual(
            result, ['enter-1-A', 'enter-2-A', 'enter-1-B', 'enter-2-B',
                     ('managers', 'A', 'B'),
                     'exit-1-B', 'exit-2-B', 'exit-1-A', 'exit-2-A']
        )

        async def foo():
            async with Manager("A") as a, Manager("C") as c:
                await AsyncYieldFrom([('managers', a.name, c.name)])
                1/0

        with self.assertRaises(ZeroDivisionError):
            run_async(foo())

    def test_with_2(self):
        class CM:
            def __aenter__(self):
                pass

        async def foo():
            async with CM():
                pass

        with self.assertRaisesRegexp(AttributeError, '__aexit__'):
            run_async(foo())

    def test_with_3(self):
        class CM:
            def __aexit__(self):
                pass

        async def foo():
            async with CM():
                pass

        with self.assertRaisesRegexp(AttributeError, '__aenter__'):
            run_async(foo())

    def test_with_4(self):
        class CM:
            def __enter__(self):
                pass

            def __exit__(self):
                pass

        async def foo():
            async with CM():
                pass

        with self.assertRaisesRegexp(AttributeError, '__aexit__'):
            run_async(foo())

    def test_with_5(self):
        # While this test doesn't make a lot of sense,
        # it's a regression test for an early bug with opcodes
        # generation

        class CM:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc):
                pass

        async def func():
            async with CM():
                assert (1, ) == 1

        with self.assertRaises(AssertionError):
            run_async(func())

    def test_with_6(self):
        class CM:
            def __aenter__(self):
                return 123

            def __aexit__(self, *e):
                return 456

        async def foo():
            async with CM():
                pass

        with self.assertRaisesRegexp(
            TypeError, "object int can't be used in 'await' expression"):
            # it's important that __aexit__ wasn't called
            run_async(foo())

    def test_with_7(self):
        class CM:
            async def __aenter__(self):
                return self

            def __aexit__(self, *e):
                return 444

        async def foo():
            async with CM():
                1/0

        try:
            run_async(foo())
        except TypeError as exc:
            self.assertRegexpMatches(
                exc.args[0], "object int can't be used in 'await' expression")
            # NB: Removed 2.7-incompatible tests for __context__
        else:
            self.fail('invalid asynchronous context manager did not fail')


    def test_with_8(self):
        class CM:
            async def __aenter__(self):
                return self

            def __aexit__(self, *e):
                return 456

        async def foo():
            async with CM():
                self.CNT += 1


        with self.assertRaisesRegexp(
            TypeError, "object int can't be used in 'await' expression"):

            run_async(foo())

        self.assertEqual(self.CNT, 1)


    def test_with_9(self):
        class CM:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *e):
                1/0

        async def foo():
            async with CM():
                self.CNT += 1

        with self.assertRaises(ZeroDivisionError):
            run_async(foo())

        self.assertEqual(self.CNT, 1)

    def test_with_10(self):
        class CM:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *e):
                1/0

        async def foo():
            async with CM():
                async with CM():
                    raise RuntimeError

        try:
            run_async(foo())
        except ZeroDivisionError as exc:
            # NB: Removed 2.7-incompatible tests for __context__
            pass
        else:
            self.fail('exception from __aexit__ did not propagate')

    def test_with_11(self):
        class CM:
            async def __aenter__(self):
                raise NotImplementedError

            async def __aexit__(self, *e):
                1/0

        async def foo():
            async with CM():
                raise RuntimeError

        try:
            run_async(foo())
        except NotImplementedError as exc:
            # NB: Removed 2.7-incompatible tests for __context__
            pass
        else:
            self.fail('exception from __aenter__ did not propagate')

    def test_with_12(self):
        class CM:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *e):
                return True

        async def foo():
            async with CM() as cm:
                self.assertIs(cm.__class__, CM)
                raise RuntimeError

        run_async(foo())

    def test_with_13(self):
        class CM:
            async def __aenter__(self):
                1/0

            async def __aexit__(self, *e):
                return True

        async def foo():
            self.CNT += 1
            async with CM():
                self.CNT += 1000
            self.CNT += 10000

        with self.assertRaises(ZeroDivisionError):
            run_async(foo())
        self.assertEqual(self.CNT, 1)

    def test_for_1(self):
        their = self

        class AsyncIter:
            def __init__(self):
                self.i = 0

            async def __aiter__(self):
                their.aiter_calls += 1
                return self

            async def __anext__(self):
                self.i += 1

                if not (self.i % 10):
                    await AsyncYield(self.i * 10)

                if self.i > 100:
                    raise StopAsyncIteration

                return self.i, self.i


        buffer = []
        async def test1():
            async for i1, i2 in AsyncIter():
                buffer.append(i1 + i2)

        yielded, _ = run_async(test1())
        # Make sure that __aiter__ was called only once
        self.assertEqual(self.aiter_calls, 1)
        self.assertEqual(yielded, [i * 100 for i in range(1, 11)])
        self.assertEqual(buffer, [i*2 for i in range(1, 101)])


        buffer = []
        async def test2():
            async for i in AsyncIter():
                buffer.append(i[0])
                if i[0] == 20:
                    break
            else:
                buffer.append('what?')
            buffer.append('end')

        yielded, _ = run_async(test2())
        # Make sure that __aiter__ was called only once
        self.assertEqual(self.aiter_calls, 2)
        self.assertEqual(yielded, [100, 200])
        self.assertEqual(buffer, [i for i in range(1, 21)] + ['end'])


        buffer = []
        async def test3():
            async for i in AsyncIter():
                if i[0] > 20:
                    continue
                buffer.append(i[0])
            else:
                buffer.append('what?')
            buffer.append('end')

        yielded, _ = run_async(test3())
        # Make sure that __aiter__ was called only once
        self.assertEqual(self.aiter_calls, 3)
        self.assertEqual(yielded, [i * 100 for i in range(1, 11)])
        self.assertEqual(buffer, [i for i in range(1, 21)] +
                                 ['what?', 'end'])

    def test_for_2(self):
        tup = (1, 2, 3)
        refs_before = sys.getrefcount(tup)

        async def foo():
            async for i in tup:
                print('never going to happen')

        with self.assertRaisesRegexp(
                TypeError, "async for' requires an object.*__aiter__.*tuple"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(tup), refs_before)

    def test_for_3(self):
        class I(object):
            def __aiter__(self):
                return self

        aiter = I()
        refs_before = sys.getrefcount(aiter)

        async def foo():
            async for i in aiter:
                print('never going to happen')

        with self.assertRaisesRegexp(
                TypeError,
                "async for' received an invalid object.*__aiter.*\: I"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(aiter), refs_before)

    def test_for_4(self):
        class I:
            async def __aiter__(self):
                return self

            def __anext__(self):
                return ()

        aiter = I()
        refs_before = sys.getrefcount(aiter)

        async def foo():
            async for i in aiter:
                print('never going to happen')

        with self.assertRaisesRegexp(
                TypeError,
                "async for' received an invalid object.*__anext__.*tuple"):

            run_async(foo())

        self.assertEqual(sys.getrefcount(aiter), refs_before)

    def test_for_5(self):
        class I:
            async def __aiter__(self):
                return self

            def __anext__(self):
                return 123

        async def foo():
            async for i in I():
                print('never going to happen')

        with self.assertRaisesRegexp(
                TypeError,
                "async for' received an invalid object.*__anext.*int"):

            run_async(foo())

    def test_for_6(self):
        their = self
        class Manager:
            async def __aenter__(self):
                their.I += 10000

            async def __aexit__(self, *args):
                their.I += 100000

        class Iterable:
            def __init__(self):
                self.i = 0

            async def __aiter__(self):
                return self

            async def __anext__(self):
                if self.i > 10:
                    raise StopAsyncIteration
                self.i += 1
                return self.i

        ##############

        manager = Manager()
        iterable = Iterable()
        mrefs_before = sys.getrefcount(manager)
        irefs_before = sys.getrefcount(iterable)

        async def main():
            async with manager:
                async for i in iterable:
                    self.I += 1
            self.I += 1000

        run_async(main())
        self.assertEqual(self.I, 111011)

        self.assertEqual(sys.getrefcount(manager), mrefs_before)
        self.assertEqual(sys.getrefcount(iterable), irefs_before)

        ##############

        async def main():
            async with Manager():
                async for i in Iterable():
                    self.I += 1
            self.I += 1000

            async with Manager():
                async for i in Iterable():
                    self.I += 1
            self.I += 1000

        run_async(main())
        self.assertEqual(self.I, 333033)

        ##############

        async def main():
            async with Manager():
                self.I += 100
                async for i in Iterable():
                    self.I += 1
                else:
                    self.I += 10000000
            self.I += 1000

            async with Manager():
                self.I += 100
                async for i in Iterable():
                    self.I += 1
                else:
                    self.I += 10000000
            self.I += 1000

        run_async(main())
        self.assertEqual(self.I, 20555255)

    def test_for_7(self):
        class AI:
            async def __aiter__(self):
                1/0
        async def foo():
            async for i in AI():
                self.CNT += 1
            self.CNT += 10
        with self.assertRaises(ZeroDivisionError):
            run_async(foo())
        self.assertEqual(self.CNT, 0)


class CoroAsyncIOCompatTest(unittest.TestCase):

    @unittest.skip("no asyncio yet")   # RSI/TODO when you have asyncio
    def test_asyncio_1(self):
        import asyncio

        class MyException(Exception):
            pass

        buffer = []

        class CM:
            async def __aenter__(self):
                buffer.append(1)
                await asyncio.sleep(0.01)
                buffer.append(2)
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                await asyncio.sleep(0.01)
                buffer.append(exc_type.__name__)

        async def f():
            async with CM() as c:
                await asyncio.sleep(0.01)
                raise MyException
            buffer.append('unreachable')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(f())
        except MyException:
            pass
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        self.assertEqual(buffer, [1, 2, 'MyException'])


class SysSetCoroWrapperTest(unittest.TestCase):
    def setUp(self):
        self.wrapped = None

    def test_set_wrapper_1(self):
        async def foo():
            return 'spam'

        def wrap(gen):
            self.wrapped = gen
            return gen

        self.assertIsNone(sys.get_coroutine_wrapper())

        sys.set_coroutine_wrapper(wrap)
        self.assertIs(sys.get_coroutine_wrapper(), wrap)
        try:
            f = foo()
            self.assertTrue(self.wrapped)

            self.assertEqual(run_async(f), ([], 'spam'))
        finally:
            sys.set_coroutine_wrapper(None)

        self.assertIsNone(sys.get_coroutine_wrapper())

        self.wrapped = None
        with silence_coro_gc():
            foo()
        self.assertFalse(self.wrapped)

    def test_set_wrapper_2(self):
        self.assertIsNone(sys.get_coroutine_wrapper())
        with self.assertRaisesRegexp(TypeError, "callable expected, got int"):
            sys.set_coroutine_wrapper(1)
        self.assertIsNone(sys.get_coroutine_wrapper())

    def test_set_wrapper_3(self):
        async def foo():
            return 'spam'

        def wrapper(coro):
            async def wrap(coro):
                return await coro
            return wrap(coro)

        sys.set_coroutine_wrapper(wrapper)
        try:
            with silence_coro_gc(), self.assertRaisesRegexp(
                RuntimeError,
                "coroutine wrapper.*wrapper at 0x.*attempted to "
                "recursively wrap .* wrap .*"):

                foo()
        finally:
            sys.set_coroutine_wrapper(None)

    def test_set_wrapper_4(self):
        @types.coroutine
        def foo():
            return 'spam'

        def wrap(gen):
            self.wrapped = gen
            return gen

        sys.set_coroutine_wrapper(wrap)
        try:
            foo()
            self.assertIs(
                self.wrapped, None,
                "generator-based coroutine was wrapped via "
                "sys.set_coroutine_wrapper")
        finally:
            sys.set_coroutine_wrapper(None)


class CAPITest(unittest.TestCase):

    def test_tp_await_1(self):
        from _testcapi import awaitType as at

        async def foo():
            future = at(iter([1]))
            return (await future)

        self.assertEqual(foo().send(None), 1)

    def test_tp_await_2(self):
        # Test tp_await to __await__ mapping
        from _testcapi import awaitType as at
        future = at(iter([1]))
        self.assertEqual(next(future.__await__()), 1)

    def test_tp_await_3(self):
        from _testcapi import awaitType as at

        async def foo():
            future = at(1)
            return (await future)

        with self.assertRaisesRegexp(
                TypeError, "__await__.*returned non-iterator of type 'int'"):
            self.assertEqual(foo().send(None), 1)


def test_main():
    #with support.check_py3k_warnings(
    #        ("classic int division", DeprecationWarning)):
    support.run_unittest(AsyncBadSyntaxTest,
                         CoroutineTest,
                         CoroAsyncIOCompatTest,
                         SysSetCoroWrapperTest,
                         CAPITest)


if __name__=="__main__":
    test_main()
