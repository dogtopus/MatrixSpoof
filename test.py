#!/usr/bin/env python3

from typing import (
    Callable,
    TypeVar,
    Iterator,
    Generic,
    Any,
    Generator,
    Union,
    Type
)
import functools
import unittest
import migen

from migen import (
    Module,
)

from matrixspoof import MatrixSpoof

# TODO This is janky. Fill in more specific info later.
MigenCoroutine = Generator[Any, Any, Any]
TestBenchImpl = TypeVar('TestBenchImpl', bound=Module)

AdvanceClock = None


class MigenTestCase(unittest.TestCase, Generic[TestBenchImpl]):
    tb: TestBenchImpl

    def simulationSetUp(self, tb: TestBenchImpl) -> MigenCoroutine:
        yield from tuple()

    def configure(self, tb: TestBenchImpl, **kwargs) -> None:
        return


MigenTestCaseImpl = TypeVar('MigenTestCaseImpl', bound=MigenTestCase)
TestCaseMethodImpl = Callable[[MigenTestCaseImpl, TestBenchImpl], MigenCoroutine]
TestCaseMethodWrapper = Callable[[MigenTestCaseImpl], None]
ConfigureWrapper = Callable[[TestCaseMethodImpl], TestCaseMethodWrapper]

def simulation_test(case: TestCaseMethodImpl = None, **kwargs) -> Union[ConfigureWrapper, TestCaseMethodWrapper]:
    def configure_wrapper(case: TestCaseMethodImpl) -> TestCaseMethodWrapper:
        @functools.wraps(case)
        def wrapper(self: MigenTestCaseImpl) -> None:
            self.configure(self.tb, **kwargs)
            def setup_wrapper() -> MigenCoroutine:
                yield from self.simulationSetUp(self.tb)
                yield from case(self, self.tb)
            migen.run_simulation(self.tb, setup_wrapper(), vcd_name="test.vcd")
        return wrapper

    if case is None:
        return configure_wrapper
    else:
        return configure_wrapper(case)


class MatrixSpoofTest(MigenTestCase[MatrixSpoof]):
    def setUp(self) -> None:
        self.tb = MatrixSpoof(2, 3)

    def assertSignal(self, signal: migen.Signal, value: int) -> MigenCoroutine:
        actual = yield signal
        self.assertEqual(actual, value)

    @simulation_test
    def testXStrobe(self, tb: MatrixSpoof) -> MigenCoroutine:
        yield from (
            tb.cgin[0][0].eq(1),
            tb.cgin[0][1].eq(0),
            tb.cgin[0][2].eq(0),
            tb.cgin[1][0].eq(0),
            tb.cgin[1][1].eq(1),
            tb.cgin[1][2].eq(0),

            tb.xin[0].eq(1),
            tb.xin[1].eq(0),

            None,
        )
        yield from self.assertSignal(tb.yout[0], 1)
        yield from self.assertSignal(tb.yout[1], 0)
        yield from self.assertSignal(tb.yout[2], 0)

        yield from (
            tb.xin[0].eq(0),
            tb.xin[1].eq(1),

            None,
        )

        yield from self.assertSignal(tb.yout[0], 0)
        yield from self.assertSignal(tb.yout[1], 1)
        yield from self.assertSignal(tb.yout[2], 0)

    @simulation_test
    def test0X(self, tb: MatrixSpoof) -> MigenCoroutine:
        yield from (
            tb.cgin[0][0].eq(1),
            tb.cgin[0][1].eq(0),
            tb.cgin[0][2].eq(0),
            tb.cgin[1][0].eq(0),
            tb.cgin[1][1].eq(1),
            tb.cgin[0][2].eq(0),

            tb.xin[0].eq(0),
            tb.xin[1].eq(0),

            None,
        )

        yield from self.assertSignal(tb.yout[0], 0)
        yield from self.assertSignal(tb.yout[1], 0)


if __name__ == '__main__':
    unittest.main()
